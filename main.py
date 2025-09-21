import os
import random
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from config import TOPICS
from content import generate_post_content
from x_client import post_tweet, verify_credentials

def main():
    """Main function to run the bot logic."""
    logging.info("Bot run started.")

    if not verify_credentials():
        logging.error("Failed to verify credentials. Exiting.")
        return

    try:
        topic = random.choice(TOPICS)
        logging.info(f"Selected topic: {topic}")
        content, _ = generate_post_content(topic)

        if content and len(content) <= 280:
            logging.info(f"Generated content: {content}")
            success = post_tweet(content)
            if success:
                logging.info("Successfully posted.")
            else:
                logging.error("Failed to post tweet.")
        elif content:
            logging.warning(f"Generated content is too long ({len(content)} characters) or empty. Skipping post.")
        else:
            logging.warning("Generated content is empty. Skipping post.")

    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)

    logging.info("Bot run finished.")

if __name__ == "__main__":
    main()
