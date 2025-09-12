from dotenv import load_dotenv
import os, json
import requests
import tweepy
import pandas as pd
import feedparser
from xml.etree import ElementTree
from openai import OpenAI
from datetime import datetime, timedelta
from themes import today_theme  # THEMES ayrı dosyada
import random

# .env load
load_dotenv()

# API Keys
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Clients
client = OpenAI(api_key=OPENAI_API_KEY)
auth_client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Settings
DRY_RUN = int(os.getenv("DRY_RUN", "0"))
MAX_TWEETS = int(os.getenv("MAX_TWEETS", "1"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "90"))
HISTORY_FILE = "data/history.json"
MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", str(MAX_TWEETS * 10)))
TWEETS_PER_DAY = int(os.getenv("TWEETS_PER_DAY", "3"))  # günlük tweet sayısı

# SCImago CSV
SCIMAGO_CSV = "scimago.csv"
df = pd.read_csv(SCIMAGO_CSV, sep=";", encoding="utf-8", engine="python")
df["Title_clean"] = df["Title"].str.lower().str.strip()

# ----------------- History -----------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, ensure_ascii=False, indent=2)

# ----------------- ERP RSS -----------------
def fetch_erp_articles(history):
    url = "https://endocrinolrespract.org/current-issue/rss"
    feed = feedparser.parse(url)

    records = []
    for entry in feed.entries:
        if entry.link in history:
            continue
        records.append({
            "title": entry.title,
            "journal": "Endocrinology Research and Practice",
            "abstract": entry.summary if "summary" in entry else "",
            "link": entry.link,
            "quartile": "Q4"
        })
    return records

# ----------------- DOI Resolver -----------------
def resolve_doi(doi):
    """Resolve DOI to publisher page instead of doi.org"""
    try:
        url = f"https://doi.org/{doi}"
        r = requests.get(url, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            return r.url
        else:
            return url
    except Exception as e:
        print(f"[DOI Resolve Failed] {doi}: {e}")
        return f"https://doi.org/{doi}"

# ----------------- PubMed API -----------------
def pubmed_search(query, retmax=10):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    end_date = datetime.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    # 📌 [Date - Publication] yerine [Date - Entrez] kullanalım
    date_range = f'("{start_date.strftime("%Y/%m/%d")}"[Date - Entrez] : "{end_date.strftime("%Y/%m/%d")}"[Date - Entrez])'

    term = f"({query}) AND {date_range}"
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


def pubmed_fetch(pmids, history):
    if not pmids:
        return []
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

        pmid = article.findtext(".//MedlineCitation/PMID")
        doi = article.findtext(".//ArticleIdList/ArticleId[@IdType='doi']")

        if doi:
            link = resolve_doi(doi)
        elif pmid:
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        else:
            link = "https://pubmed.ncbi.nlm.nih.gov/"

        if link in history:
            continue

        records.append({
            "title": title,
            "journal": journal,
            "abstract": abstract,
            "link": link
        })
    return records

# ----------------- SCImago Filtering -----------------
def filter_q_journals(pubmed_entries, history):
    filtered = []
    priority = []

    for e in pubmed_entries:
        if not e["journal"] or e["link"] in history:
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
                if "endocrinology research and practice" in journal_norm:
                    priority.append(record)
                else:
                    filtered.append(record)

    return priority + filtered

# ----------------- GPT Summarization -----------------
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
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print("GPT summarization failed:", e)
        return {"conclusion": "No conclusion", "findings": []}

# ----------------- Tweet Builder -----------------
def build_tweet(title, summary, findings, url, hashtags):
    text = f"📑 {title}\n\n"
    if summary:
        text += f"💡 {summary}\n\n"
    for f in findings:
        text += f"{f}\n"
    text += f"\n🔗 {url}\n{' '.join(hashtags)}"
    return text

# ----------------- Main -----------------
def main():
    theme_query, hashtags = today_theme()
    print(f"[theme] {theme_query} | tags={hashtags}")

    history = load_history()

    # 1. ERP makaleleri önce kontrol et
    erp_records = fetch_erp_articles(history)

    if erp_records:
        print(f"[ERP] Found {len(erp_records)} new ERP article(s)")
        candidates = erp_records
    else:
        # 2. PubMed’den makale bul
        pmids = pubmed_search(theme_query, retmax=MAX_CANDIDATES)
        records = pubmed_fetch(pmids, history)
        candidates = filter_q_journals(records, history)

    if not candidates:
        print("[Main] No new records found. Exiting.")
        return

    # Günlük 3 farklı makale seç
    q_records = random.sample(candidates, min(TWEETS_PER_DAY, len(candidates)))

    for e in q_records:
        # History’yi önce güncelle ki tekrar seçilmesin
        history.add(e["link"])
        save_history(history)

        gpt = summarize_with_gpt(e["title"], e.get("abstract", ""))
        tweet_text = build_tweet(e["title"], gpt["conclusion"], gpt["findings"], e["link"], hashtags)

        print("\n--- Tweet Preview ---\n")
        print(tweet_text)
        print("\n--- End Preview ---\n")

        if DRY_RUN == 0:
            try:
                res = auth_client.create_tweet(text=tweet_text)
                print(f"✅ Tweet sent! ID: {res.data['id']}")
            except Exception as ex:
                print(f"❌ Failed to tweet: {ex}")

if __name__ == "__main__":
    main()
