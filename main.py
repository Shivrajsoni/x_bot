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
from x_client import post_tweet, verify_credentials

class Bot:
    def __init__(self):
        self.user_id = None

    def initialize(self):
        """Initializes the bot by verifying credentials."""
        self.user_id = verify_credentials()
        if not self.user_id:
            logging.error("Failed to get user ID. Bot will not run.")
            return False
        return True

    def create_post(self):
        """Generates the content for a new post."""
        topic = random.choice(TOPICS)
        logging.info(f"Selected topic: {topic}")
        content, _ = generate_post_content(topic)
        return content

    def publish_post(self, content):
        """Publishes the post to X."""
        if content and len(content) <= 280:
            logging.info(f"Generated content: {content}")
            success = post_tweet(content)
            if success:
                log_post_to_history(content)
                logging.info("Successfully posted.")
            else:
                logging.error("Failed to post tweet. See previous error for details.")
        elif content:
            logging.warning(f"Generated content is too long ({len(content)} characters) or empty. Skipping post.")

    def run(self):
        """The main loop of the bot."""
        if not self.initialize():
            return

        while True:
            try:
                post_interval_hours = random.uniform(6, 12)
                post_interval_seconds = post_interval_hours * 3600

                logging.info("Time to post a new tweet.")
                content = self.create_post()
                self.publish_post(content)

                logging.info(f"Sleeping for {post_interval_hours:.2f} hours...")
                time.sleep(post_interval_seconds)

            except Exception as e:
                logging.critical(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
                time.sleep(60)

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

if __name__ == "__main__":
    bot = Bot()
    worker_thread = threading.Thread(target=bot.run)
    worker_thread.daemon = True
    worker_thread.start()

    run_web_server()