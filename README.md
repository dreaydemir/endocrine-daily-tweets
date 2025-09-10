# 🧵 Endocrine Daily Tweets Bot

This bot automatically fetches the latest peer-reviewed articles from PubMed, summarizes them using OpenAI GPT, and posts them on Twitter (X) every day according to a predefined endocrinology theme.

---

## 🔑 Features
- Daily themes for tweets:
  - **Monday** → Endocrine syndromes (*Monday’s Syndrome*)
  - **Tuesday** → Obesity
  - **Wednesday** → Thyroid disorders
  - **Thursday** → Diabetes
  - **Friday** → Bone health, osteoporosis, parathyroid
  - **Saturday** → AI/ML in endocrinology
  - **Sunday** → Case reports
- PubMed E-utilities for article search and abstracts.
- Summarization with **OpenAI GPT** (concise conclusion + bullet findings).
- Tweets formatted with emojis, **bold titles**, links, and hashtags.
- Support for **X Premium (long tweets)** → no 280 char limit.
- Automated daily posting via **GitHub Actions** (no need to keep your PC on).

---

## ⚙️ Installation (local)

1. Clone the repository:
   ```bash
   git clone https://github.com/dreaydemir/endocrine-daily-tweets.git
   cd endocrine-daily-tweets
````

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

3. Create a `.env` file:

   ```env
   TWITTER_API_KEY=xxxx
   TWITTER_API_SECRET=xxxx
   TWITTER_ACCESS_TOKEN=xxxx
   TWITTER_ACCESS_TOKEN_SECRET=xxxx
   OPENAI_API_KEY=sk-xxxx

   # Local settings
   DRY_RUN=1      # 1 = preview only, 0 = post tweets
   MAX_TWEETS=1
   LOOKBACK_DAYS=30
   ```

4. Run locally:

   ```bash
   python app.py
   ```

   With `DRY_RUN=1`, tweets will only be shown as preview in the console.

---

## 🤖 GitHub Actions Automation

1. Push the repository to GitHub (make sure `.env` is in `.gitignore`).

2. Go to **Settings → Secrets and variables → Actions**.

3. Add the following repository secrets:

   * `TWITTER_API_KEY`
   * `TWITTER_API_SECRET`
   * `TWITTER_ACCESS_TOKEN`
   * `TWITTER_ACCESS_TOKEN_SECRET`
   * `OPENAI_API_KEY`
   * `DRY_RUN=0`  (for real posting)

4. Workflow file: `.github/workflows/daily.yml`

   * Runs every day at **09:00, 15:00, 21:00 Istanbul time**.
   * Or can be manually triggered from the **Actions** tab.

---

## 📤 Example Tweet

```
📑 𝗧𝗵𝗲 𝗥𝗼𝗹𝗲 𝗼𝗳 𝗧𝗵𝘆𝗿𝗼𝗶𝗱 𝗛𝗼𝗿𝗺𝗼𝗻𝗲𝘀 𝗶𝗻 𝗠𝗲𝘁𝗮𝗯𝗼𝗹𝗶𝗰 𝗛𝗲𝗮𝗹𝘁𝗵

💡 Conclusion: Thyroid hormones strongly influence lipid metabolism and insulin sensitivity.

🔬 T3 and T4 levels linked with metabolic syndrome.
📊 Subclinical hypothyroidism shows increased T2DM risk.
✅ New evidence from prospective cohort studies.

🔗 https://doi.org/xxxxxx
#Endocrinology #Thyroid
```

---

## 📌 Notes

* Requires a **Twitter Developer App** with **Read and Write** permissions + OAuth 1.0a tokens.
* Requires an **OpenAI API key**.
* Works best with **X Premium accounts** (no 280 char limit).

---

## 📜 License

MIT License – free to use and modify.

```

---



