import os
import random
import time
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import threading
from flask import Flask

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from config import TOPICS
from content import generate_post_content
from x_client import post_tweet

# ============ WEB SERVER for RENDER DEPLOYMENT =============
app = Flask(__name__)

@app.route('/')
def health_check():
    """Render health check endpoint."""
    return "Worker is running."

def run_web_server():
    """Runs the Flask app."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def log_post_to_history(content, filename="post_history.log"):
    """Appends a successfully posted tweet to a local log file (optional)."""
    try:
        with open(filename, "a") as f:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            f.write(f"[{timestamp}]\n{content}\n{'-'*40}\n")
    except Exception as e:
        logging.error(f"Failed to write to post history log: {e}")

# ============ MAIN LOOP =============

def main_loop():
    """The main loop of the bot."""
    logging.info("Starting X-Post bot...")

    while True:
        # Set a regular interval for posting
        post_interval_hours = random.uniform(6, 12)
        post_interval_seconds = post_interval_hours * 3600
        
        logging.info("Time to post a new tweet.")

        # 1. Generate content
        topic = random.choice(TOPICS)
        logging.info(f"Selected topic: {topic}")
        content, _ = generate_post_content(
            topic,
            quotes=[] # No quotes from DB
        )
        
        if content and len(content) <= 280:
            # 2. Post to X
            logging.info(f"Generated content: {content}")
            success = post_tweet(content)
            
            # 3. If successful, log
            if success:
                log_post_to_history(content)
                logging.info("Successfully posted.")

        elif content:
            logging.warning(f"Generated content is too long ({len(content)} characters) or empty. Skipping post.")

        # Sleep for the calculated interval
        logging.info(f"Sleeping for {post_interval_hours:.2f} hours...")
        time.sleep(post_interval_seconds)

worker_thread = threading.Thread(target=main_loop)
worker_thread.daemon = True
worker_thread.start()

if __name__ == "__main__":
    run_web_server()
