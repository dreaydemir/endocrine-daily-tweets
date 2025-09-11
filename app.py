from dotenv import load_dotenv
import os, json
import requests
import tweepy
import pandas as pd
from xml.etree import ElementTree
from openai import OpenAI
from datetime import datetime, timedelta
from themes import today_theme   # THEMES artık ayrı dosyada

# .env yükle
load_dotenv()

# API Keys
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI ve Twitter Client
client = OpenAI(api_key=OPENAI_API_KEY)
auth_client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Settings
DRY_RUN = int(os.getenv("DRY_RUN", "1"))
MAX_TWEETS = int(os.getenv("MAX_TWEETS", "1"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))

# SCImago CSV yükle
SCIMAGO_CSV = "scimago.csv"
df = pd.read_csv(SCIMAGO_CSV, sep=";", encoding="utf-8", engine="python")
df["Title_clean"] = df["Title"].str.lower().str.strip()

# ----------------- PubMed API -----------------
def pubmed_search(query, retmax=10):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    # Tarih aralığını hesapla
    end_date = datetime.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    date_range = f'("{start_date.strftime("%Y/%m/%d")}"[Date - Publication] : "{end_date.strftime("%Y/%m/%d")}"[Date - Publication])'

    # PubMed sorgusu → query + tarih filtresi
    term = f"{query} AND {date_range}"

    # 🔹 Debug çıktısı
    print(f"[PubMed] Query: {term}")

    params = {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "sort": "date",
        "retmode": "json"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

def pubmed_fetch(pmids):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    root = ElementTree.fromstring(r.content)

    records = []
    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle")
        journal = article.findtext(".//Journal/Title")
        abstract = " ".join([t.text for t in article.findall(".//AbstractText") if t.text])
        url_id = article.findtext(".//ArticleIdList/ArticleId[@IdType='doi']")
        link = f"https://doi.org/{url_id}" if url_id else "https://pubmed.ncbi.nlm.nih.gov/"
        records.append({
            "title": title,
            "journal": journal,
            "abstract": abstract,
            "link": link
        })
    return records

# ----------------- SCImago Filtreleme -----------------
def filter_q_journals(pubmed_entries):
    filtered = []
    priority = []

    for e in pubmed_entries:
        if not e["journal"]:
            continue
        journal_norm = e["journal"].lower().strip()
        row = df[df["Title_clean"] == journal_norm]
        if not row.empty:
            quartile = row["SJR Quartile"].values[0]
            categories = row["Categories"].values[0]
            if quartile in ["Q1", "Q2", "Q3", "Q4"] and "Endocrinology" in categories:
                record = {
                    "title": e["title"],
                    "journal": row["Title"].values[0],
                    "quartile": quartile,
                    "link": e["link"],
                    "abstract": e["abstract"]
                }
                # Öncelikli dergi
                if "endocrinology research and practice" in journal_norm:
                    priority.append(record)
                else:
                    filtered.append(record)

    return priority + filtered

# ----------------- GPT Özetleme -----------------
def summarize_with_gpt(title, abstract=""):
    prompt = f"""
Summarize the endocrinology article.

Title: {title}
Abstract: {abstract}

Format as JSON:
{{
 "conclusion": "short one-sentence conclusion",
 "findings": ["emoji + finding 1", "emoji + finding 2", "emoji + finding 3"]
}}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.4,
            response_format={"type":"json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print("GPT summarization failed:", e)
        return {"conclusion":"No conclusion","findings":[]}

# ----------------- Tweet Yapıcı -----------------
def build_tweet(title, summary, findings, url, hashtags):
    text = f"📑 {title.upper()}\n\n"
    if summary:
        text += f"💡 {summary}\n\n"
    for f in findings:
        text += f"{f}\n"
    text += f"\n🔗 {url}\n{' '.join(hashtags)}"
    return text

# ----------------- Ana Fonksiyon -----------------
def main():
    theme_query, hashtags = today_theme()
    print(f"[theme] {theme_query} | tags={hashtags}")

    pmids = pubmed_search(theme_query, retmax=MAX_TWEETS*5)
    records = pubmed_fetch(pmids)
    q_records = filter_q_journals(records)[:MAX_TWEETS]

    for e in q_records:
        gpt = summarize_with_gpt(e["title"], e["abstract"])
        tweet_text = build_tweet(e["title"], gpt["conclusion"], gpt["findings"], e["link"], hashtags)

        print("\n--- Tweet Preview ---\n")
        print(tweet_text)
        print("\n--- End Preview ---\n")

        if DRY_RUN == 0:
            try:
                res = auth_client.create_tweet(text=tweet_text)
                print(f"✅ Tweet gönderildi! ID: {res.data['id']}")
            except Exception as e:
                print(f"❌ Tweet gönderilemedi: {e}")

if __name__ == "__main__":
    main()
