# reddit-persona-analyzer

Analyze a Reddit user's activity and generate a detailed persona using GPT and Reddit API.

---

## 📦 Features
- Scrapes user posts and comments using PRAW (Reddit API)
- Uses OpenAI GPT to summarize personality traits, interests, writing style
- Outputs a structured user persona with citations

---

## ⚙️ Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/Trishachinnu/reddit-persona-analyzer.git
cd reddit-persona-analyzer
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables:
```bash
Create a .env file like this: env

OPENAI_API_KEY=your_openai_key
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
```
4. Run the script:
```bash
python script.py
```
