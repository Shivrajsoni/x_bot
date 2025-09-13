import os
import random
import time
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import threading
from flask import Flask

# Load environment variables from .env file
load_dotenv()

from config import TOPICS
from content import generate_post_content, load_quotes
from x_client import post_tweet

# ============ WEB SERVER for RENDER DEPLOYMENT =============
app = Flask(__name__)

@app.route('/')
def health_check():
    """Render health check endpoint."""
    return "Worker is running."

def run_web_server():
    """Runs the Flask app."""
    # Render provides the PORT environment variable.
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============ STATE MANAGEMENT =============

def should_post_now(last_post_time, min_interval_hours=8, max_interval_hours=20):
    """Randomizes intervals to ensure post times are not too regular."""
    now = datetime.utcnow()
    if last_post_time is None:
        return True
    next_post_interval = timedelta(hours=random.uniform(min_interval_hours, max_interval_hours))
    next_post_time = last_post_time + next_post_interval
    logging.info(f"Next scheduled post time is around: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    return now >= next_post_time

def load_last_post_time(filename="last_post_time.txt"):
    """Loads the timestamp of the last post from a file."""
    try:
        with open(filename, "r") as f:
            s = f.read().strip()
            return datetime.fromisoformat(s)
    except (FileNotFoundError, ValueError):
        logging.info("Last post time file not found or invalid. Will post now.")
        return None

def save_last_post_time(dt, filename="last_post_time.txt"):
    """Saves the timestamp of the last post to a file."""
    with open(filename, "w") as f:
        f.write(dt.isoformat())

def load_posted_quotes(filename="posted_quotes.json"):
    """Loads the set of posted quote texts from a file for uniqueness checks."""
    try:
        with open(filename, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_posted_quote(quote_text, filename="posted_quotes.json"):
    """Adds a new quote text to the list of posted quotes."""
    posted_set = load_posted_quotes(filename)
    posted_set.add(quote_text)
    with open(filename, "w") as f:
        json.dump(list(posted_set), f, indent=2)

def log_post_to_history(content, filename="post_history.log"):
    """Appends a successfully posted tweet to a log file."""
    try:
        with open(filename, "a") as f:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            f.write(f"[{timestamp}]\n{content}\n{'-'*40}\n")
    except Exception as e:
        logging.error(f"Failed to write to post history log: {e}")

# ============ MAIN LOOP =============

def main_loop():
    """The main loop of the bot."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting X-Post bot...")
    
    # Load knowledge bases and state
    philosophy_quotes = load_quotes("quotes.json")
    posted_philosophy_quotes = load_posted_quotes()
    last_post = load_last_post_time()
    
    logging.info(f"Loaded {len(philosophy_quotes)} philosophy quotes.")
    logging.info(f"Loaded {len(posted_philosophy_quotes)} already posted quotes.")

    while True:
        if should_post_now(last_post):
            logging.info("Time to post a new tweet.")

            # Check if we need to reset the philosophy quotes history
            if len(philosophy_quotes) > 0 and len(posted_philosophy_quotes) >= len(philosophy_quotes):
                logging.info("All philosophy quotes have been posted. Resetting history.")
                posted_philosophy_quotes = set()
                # Clear the history file
                with open("posted_quotes.json", "w") as f:
                    json.dump([], f)

            # 1. Generate content
            topic = random.choice(TOPICS)
            logging.info(f"Selected topic: {topic}")
            content, context_obj = generate_post_content(
                topic,
                quotes=philosophy_quotes,
                posted_quotes=posted_philosophy_quotes
            )
            
            if content and len(content) <= 280:
                # 2. Post to X
                logging.info(f"Generated content: {content}")
                success = post_tweet(content)
                
                # 3. If successful, update state and log the post
                if success:
                    last_post = datetime.utcnow()
                    save_last_post_time(last_post)
                    log_post_to_history(content)
                    
                    # If it was a philosophy quote, save it to our history
                    if topic == "philosophy" and context_obj:
                        quote_text_to_save = context_obj.get("quote")
                        if quote_text_to_save:
                            save_posted_quote(quote_text_to_save)
                            # Also update the in-memory set for the current session
                            posted_philosophy_quotes.add(quote_text_to_save)
                    
                    logging.info("Successfully posted and updated state.")
            elif content:
                logging.warning(f"Generated content is too long ({len(content)} characters) or empty. Skipping post.")

        # Sleep for a while before checking again
        check_interval_minutes = 15
        logging.info(f"Sleeping for {check_interval_minutes} minutes...")
        time.sleep(60 * check_interval_minutes)

if __name__ == "__main__":
    # Run the main loop in a background thread
    worker_thread = threading.Thread(target=main_loop)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Run the web server in the main thread
    run_web_server()