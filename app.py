from dotenv import load_dotenv
import os, re, json, pathlib
import requests
import tweepy
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from themes import today_theme

load_dotenv()

# Twitter API keyleri
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Ayarlar
DRY_RUN = int(os.getenv("DRY_RUN", "1"))
MAX_TWEETS = int(os.getenv("MAX_TWEETS", "1"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))

# --- PubMed functions ---
def pubmed_search(term, retmax=5):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db":"pubmed","term":term,"retmode":"json","retmax":retmax, "sort":"pub+date"}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("esearchresult",{}).get("idlist",[])

def pubmed_summary_batch(pmids):
    ids = ",".join(pmids)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    r = requests.get(url, params={"db":"pubmed","id":ids,"retmode":"json"})
    r.raise_for_status()
    return r.json().get("result",{})

def pubmed_abstract(pmid):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params={"db":"pubmed","id":pmid,"rettype":"abstract","retmode":"text"}
    r = requests.get(url, params=params)
    if r.status_code==200:
        return r.text.strip()
    return ""

# --- OpenAI Summarization ---
def summarize_with_gpt(title, abstract):
    prompt = f"""
You are a medical summarizer for endocrinology research.

Title: {title}
Abstract: {abstract}

Task:
- Return ONLY valid JSON.
- Format:
{{
  "conclusion": "single concise sentence",
  "findings": [
    "emoji + key point 1",
    "emoji + key point 2",
    "emoji + key point 3"
  ]
}}
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.4,
            response_format={"type":"json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        return data
    except Exception as e:
        print("GPT summarization failed:", e)
        return {"conclusion":"No conclusion available.","findings":[]}

# --- Bold converter (for title) ---
def bold_text(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    bold = "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘵𝘶𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    trans = str.maketrans(normal, bold)
    return text.translate(trans)

# --- Tweet builder ---
def build_single_tweet(title, summary, findings, url, hashtags):
    text = f"📑 {bold_text(title)}\n\n"
    if summary:
        text += f"💡 {summary}\n\n"
    if findings:
        for f in findings:
            text += f"{f}\n"
        text += "\n"
    text += f"🔗 {url}\n{hashtags}"
    return text

# --- Main ---
def main():
    theme_label, queries, hashtags = today_theme()
    print(f"[theme] {theme_label} | queries={queries} | tags={hashtags}")

    pmids = pubmed_search(" OR ".join(queries), retmax=MAX_TWEETS)
    print(f"[debug] PubMed {len(pmids)} makale buldu")

    if not pmids:
        return

    summary = pubmed_summary_batch(pmids)
    auth_client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )

    for pmid in pmids:
        s = summary.get(str(pmid),{})
        if not s: continue
        title = s.get("title","No title")
        doi=None
        if "articleids" in s:
            for aid in s["articleids"]:
                if aid.get("idtype")=="doi":
                    doi=aid.get("value")
                    break
        url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        abstract = pubmed_abstract(pmid)
        gpt = summarize_with_gpt(title, abstract)
        tweet_text = build_single_tweet(title, gpt["conclusion"], gpt["findings"], url, " ".join(hashtags))

        print("\n--- Tweet Preview ---\n")
        print(tweet_text)
        print("\n--- End Preview ---\n")

        if DRY_RUN==0:
            try:
                res = auth_client.create_tweet(text=tweet_text)
                print(f"✅ Tek tweet gönderildi! ID: {res.data['id']}")
            except Exception as e:
                print(f"❌ Tweet gönderilemedi: {e}")

if __name__=="__main__":
    main()
