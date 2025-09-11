# 🧵 Endocrine Daily Tweets Bot

This project scans the latest endocrinology articles from the **PubMed API**,
filters them using **SCImago Journal Rank (Q1–Q4)**, summarizes them with GPT,
and automatically posts them on Twitter.

## 🚀 Features

* Daily theme-based article selection (`themes.py`)
* PubMed API + SCImago integration
* GPT-powered summarization (OpenAI API)
* Automatic tweet posting (Tweepy)
* Scheduled automation via GitHub Actions (09:00, 15:00, 21:00 Istanbul time)

## 📂 Project Structure

```
endocrine-daily-tweets/
│
├── app.py                # Main script (PubMed + SCImago + GPT + Tweet)
├── themes.py             # Daily themes and hashtags
├── scimago.csv           # SCImago Journal Rank (CSV)
├── requirements.txt      # Python dependencies
├── .gitignore            # Excludes unnecessary/secret files
├── .env.example          # Example environment variables
│
└── .github/
    └── workflows/
        └── daily.yml     # GitHub Actions cron job
```

## ⚙️ Local Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/dreaydemir/endocrine-daily-tweets.git
   cd endocrine-daily-tweets
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Mac/Linux
   .venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file (see `.env.example` for reference).

5. Test the script:

   ```bash
   python app.py
   ```

## 🤖 Automation (GitHub Actions)

* The `daily.yml` workflow runs the bot automatically at **09:00, 15:00, and 21:00 Istanbul time**.
* Add your API keys to GitHub repo **Settings → Secrets → Actions**:

  * `TWITTER_API_KEY`
  * `TWITTER_API_SECRET`
  * `TWITTER_ACCESS_TOKEN`
  * `TWITTER_ACCESS_TOKEN_SECRET`
  * `OPENAI_API_KEY`

## 🛡️ Security

* `.env` must **never** be committed (excluded in `.gitignore`).
* API keys are stored **only** in GitHub Secrets.
* `scimago.csv` stays in the repo (required for journal filtering).

---

📌 With this setup:

* `.gitignore` ensures sensitive files never leak.
* `requirements.txt` manages dependencies for both local and GitHub Actions.
* `README.md` makes it clear what the project does and how to use it.

---

## 📜 Example Log Output

When the bot runs (locally or via GitHub Actions), you’ll see logs like this:
[theme] diabetes OR obesity | tags=['#Endocrinology', '#Diabetes', '#Obesity']
[PubMed] Query: diabetes OR obesity AND ("2025/08/12"[Date - Publication] : "2025/09/11"[Date - Publication])

--- Tweet Preview ---

📑 IMPACT OF OBESITY ON INSULIN RESISTANCE IN TYPE 2 DIABETES

💡 Obesity significantly worsens insulin resistance in patients with type 2 diabetes.

🧬 Increased inflammatory markers observed  
📉 Reduced insulin sensitivity across cohorts  
🩺 Lifestyle changes improve outcomes

🔗 https://doi.org/10.1234/example
#Endocrinology #Diabetes #Obesity

--- End Preview ---




