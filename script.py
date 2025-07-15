import praw
import re
import os
from urllib.parse import urlparse
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# --- CONFIGURE THESE ---
REDDIT_CLIENT_ID = '0XXUZR8OB8and0sUu5E1sg'
REDDIT_CLIENT_SECRET = 'gt4z_TeU76iIDZjMI4TN5vahxSux_w'
REDDIT_USER_AGENT = 'script:userpersonabot:v1.0 (by u/Independent-Gur-168)'


# --- SETUP PRAW ---
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_CLIENT_SECRET,
                     user_agent=REDDIT_USER_AGENT)

def extract_username(url):
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    return parts[1] if len(parts) >= 2 and parts[0].lower() == 'user' else None

def get_user_data(username, limit=100):
    redditor = reddit.redditor(username)
    posts = []
    comments = []

    try:
        for submission in redditor.submissions.new(limit=limit):
            posts.append(submission)
        for comment in redditor.comments.new(limit=limit):
            comments.append(comment)
    except Exception as e:
        print(f"Error fetching user data: {e}")
    
    return posts, comments

def call_openai(messages, model="gpt-3.5-turbo", temperature=0.7):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Error generating response."
    
def infer_persona(username, posts, comments):
    persona = {
        "Username": username,
        "Summary": "",
        "Interests": [],
        "Frequent Subreddits": [],
        "Occupation": "",
        "Location": "",
        "Writing Style": "",
        "Citations": {}
    }

    all_text = []
    subreddit_counts = Counter()
    occupation_examples = []
    location_examples = []

    def cite(source):
        return f"r/{source.subreddit.display_name} - https://www.reddit.com{source.permalink}"

    for post in posts:
        text = f"{post.title} {post.selftext}"
        all_text.append(text)
        subreddit_counts[post.subreddit.display_name] += 1

        if "I work as" in text or "I'm a" in text:
            occupation_examples.append(text.strip()[:300])
            persona["Citations"]["Occupation"] = cite(post)

        if "I live in" in text or "I'm from" in text:
            location_examples.append(text.strip()[:300])
            persona["Citations"]["Location"] = cite(post)

    for comment in comments:
        all_text.append(comment.body)
        subreddit_counts[comment.subreddit.display_name] += 1

        if "I work as" in comment.body or "I'm a" in comment.body:
            occupation_examples.append(comment.body.strip()[:300])
            persona["Citations"]["Occupation"] = cite(comment)

        if "I live in" in comment.body or "I'm from" in comment.body:
            location_examples.append(comment.body.strip()[:300])
            persona["Citations"]["Location"] = cite(comment)

    # --- GPT Analysis ---
        # --- GPT Analysis ---
    sample_text = ""
    for text in all_text:
        if len(sample_text) + len(text) < 3000:
            sample_text += f"\n\n{text}"
        else:
            break

    summary_prompt = [
        {"role": "system", "content": "You are an analyst creating a Reddit user persona based on their posts."},
        {"role": "user", "content": f"Generate a user summary for someone who wrote the following:\n\n{sample_text}"}
    ]
    persona["Summary"] = call_openai(summary_prompt)

    style_prompt = [
        {"role": "system", "content": "You are a writing style expert."},
        {"role": "user", "content": f"How would you describe this user's writing style?\n\n{sample_text}"}
    ]
    persona["Writing Style"] = call_openai(style_prompt)
    persona["Citations"]["Writing Style"] = "Generated using GPT summary of writing tone."

    top_subs = subreddit_counts.most_common(10)
    persona["Frequent Subreddits"] = [f"{sub} ({count})" for sub, count in top_subs]

    interests_prompt = [
        {"role": "system", "content": "You are analyzing Reddit subreddit usage."},
        {"role": "user", "content": f"Given these subreddits: {[sub for sub, _ in top_subs]}, summarize what this person might be interested in."}
    ]
    interests = call_openai(interests_prompt)
    persona["Interests"] = interests.split(", ")

    persona["Occupation"] = occupation_examples[0] if occupation_examples else "Not clearly mentioned"
    persona["Location"] = location_examples[0] if location_examples else "Not clearly mentioned"

    return persona

def write_persona_to_file(persona, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"USER PERSONA\n{'='*50}\n")
        for key in ["Username", "Summary", "Interests", "Frequent Subreddits", "Occupation", "Location", "Writing Style"]:
            f.write(f"\n{key}:\n{persona[key]}\n")
            if key in persona["Citations"]:
                f.write(f"   ↳ Citation: {persona['Citations'][key]}\n")

def main():
    url = input("Enter Reddit user profile URL: ").strip()
    username = extract_username(url)
    if not username:
        print("Invalid Reddit URL format.")
        return

    print(f"Fetching data for: {username}...")
    posts, comments = get_user_data(username)
    print(f"Scraped {len(posts)} posts and {len(comments)} comments.")

    persona = infer_persona(username, posts, comments)
    output_file = f"{username}_persona.txt"
    write_persona_to_file(persona, output_file)
    print(f"User persona written to: {output_file}")

if __name__ == "__main__":
    main()