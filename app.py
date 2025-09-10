from dotenv import load_dotenv
import os, re, json, pathlib
import requests
import tweepy
from openai import OpenAI
from datetime import datetime, UTC
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from themes import today_theme

# .env dosyasını yükle
load_dotenv()

# === Ortam ayarları ===
DRY_RUN = int(os.getenv("DRY_RUN", "1"))
MAX_TWEETS = int(os.getenv("MAX_TWEETS", "3"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))

# Twitter API
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Kayıt/tekrar önleme
DATA_DIR = pathlib.Path("data"); DATA_DIR.mkdir(exist_ok=True)
HISTORY_PATH = DATA_DIR / "history.jsonl"

def already_tweeted(key: str) -> bool:
    if not HISTORY_PATH.exists():
        return False
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("key") == key:
                    return True
            except Exception:
                continue
    return False

def mark_tweeted(key: str, title: str, url: str, theme: str, tweet_id: str | None):
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "key": key,
            "title": title,
            "url": url,
            "theme": theme,
            "tweet_id": tweet_id,
            "ts": datetime.now(UTC).isoformat()
        }, ensure_ascii=False) + "\n")

def ist_weekday() -> int:
    try:
        return datetime.now(ZoneInfo("Europe/Istanbul")).weekday()
    except ZoneInfoNotFoundError:
        return datetime.now().weekday()

# === PubMed aramaları ===
def pubmed_search(query_terms, retmax=12):
    term = " AND ".join(query_terms + ["endocrinology"])
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "most+recent",
        "reldate": str(LOOKBACK_DAYS)
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    return ids

def pubmed_summary_batch(pmids):
    if not pmids:
        return {}
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("result", {})

def pubmed_abstract(pmid: str) -> str:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    text = r.text or ""
    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    # Abstract kısmını ayır
    parts = re.split(r"(?i)\babstract\b\s*:?", text, maxsplit=1)
    if len(parts) == 2:
        text = parts[1].strip()
    return text

def build_items(query_terms, max_items=MAX_TWEETS):
    pmids = pubmed_search(query_terms, retmax=20)
    if not pmids:
        return []
    summary = pubmed_summary_batch(pmids)
    items = []
    for pmid in pmids:
        s = summary.get(str(pmid), {})
        if not s:
            continue
        title = s.get("title", "").strip() or "No Title"

        # DOI bulmaya çalış
        doi = None
        if "elocationid" in s and s["elocationid"].startswith("10."):
            doi = s["elocationid"]
        if "articleids" in s:
            for aid in s["articleids"]:
                if aid.get("idtype") == "doi":
                    doi = aid.get("value")
                    break

        if doi:
            url = f"https://doi.org/{doi}"
        else:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        key = url.lower()
        if already_tweeted(key):
            continue
        items.append({"pmid": pmid, "title": title, "url": url})
        if len(items) >= max_items:
            break
    return items


# === GPT özetleme ===
def summarize_with_gpt(title, abstract):
    prompt = f"""
    You are a medical summarizer for endocrinology research.

    Title: {title}
    Abstract: {abstract}

    Task:
    - Return ONLY valid JSON.
    - No extra text.
    - Format:
    {{
      "conclusion": "single concise sentence, plain language, no affiliations/authors",
      "findings": [
        "emoji + short bullet point 1",
        "emoji + short bullet point 2",
        "emoji + short bullet point 3"
      ]
    }}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            response_format={"type": "json_object"}  # JSON garantisi
        )
        data = json.loads(resp.choices[0].message.content)
        return data
    except Exception as e:
        print("GPT summarization failed:", e)
        return {
            "conclusion": "💡 No conclusion available.",
            "findings": ["⚡ No findings available."]
        }

# === Thread oluşturma ===
def compose_thread_gpt(item, hashtags, weekday):
    title = item["title"].strip()
    url = item["url"]
    tags = " ".join(hashtags)

    intro = "😵 Monday Syndrome:\n" if weekday == 0 else ""

    abs_text = ""
    try:
        abs_text = pubmed_abstract(item["pmid"])
    except:
        pass

    summary = summarize_with_gpt(title, abs_text)

    conclusion = summary.get("conclusion", "")
    findings = summary.get("findings", [])

    # Tweet 1: Başlık + Conclusion
    t1 = f"{intro}📑 {title}\n\n{conclusion}"

    # Tweet 2: Bulgular
    t2 = "\n".join(findings)

    # Tweet 3: Link + hashtag
    t3 = f"🔗 {url}\n{tags}"

    return [t1, t2, t3]

# === Tweet gönderme ===
def post_thread(texts):
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    first_id = None
    last_id = None
    for i, t in enumerate(texts):
        if i == 0:
            resp = client.create_tweet(text=t)
            last_id = resp.data.get("id"); first_id = last_id
        else:
            resp = client.create_tweet(text=t, reply={"in_reply_to_tweet_id": last_id})
            last_id = resp.data.get("id")
    return first_id

# === Ana akış ===
def main():
    theme_label, queries, hashtags = today_theme()
    weekday = ist_weekday()
    print(f"[theme] {theme_label} | weekday={weekday} | queries={queries} | tags={hashtags}")
    items = build_items(queries, max_items=MAX_TWEETS)
    if not items:
        print("No articles found"); return
    for it in items:
        key = it["url"].lower()
        thread_texts = compose_thread_gpt(it, hashtags, weekday)
        print("\n--- Thread Preview ---")
        for idx, part in enumerate(thread_texts, start=1):
            print(f"\n[{idx}/{len(thread_texts)}]\n{part}\n")
        print("--- End Preview ---\n")
        tweet_id = None
        if not DRY_RUN:
            try:
                tweet_id = post_thread(thread_texts)
                print(f"✅ Thread gönderildi! İlk Tweet ID: {tweet_id}")
            except Exception as e:
                print(f"❌ Thread gönderilemedi: {e}")
        mark_tweeted(key, it["title"], it["url"], theme_label, tweet_id)

if __name__ == "__main__":
    main()
