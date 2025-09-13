import logging
import sys
from dotenv import load_dotenv

# Load .env variables before importing other project modules
load_dotenv()

from content import generate_post_content, load_quotes
from x_client import verify_credentials, post_tweet
from config import TOPICS

def run_tests():
    """
    Runs a suite of tests to ensure the bot is configured correctly
    before running the main application.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    failures = 0
    
    logging.info("--- STARTING BOT HEALTH CHECK ---")

    # --- Test 1: Verify X (Twitter) Credentials ---
    logging.info("\n[1/2] Testing X API Credentials...")
    if verify_credentials():
        logging.info("✅ SUCCESS: X credentials are valid.")
    else:
        logging.error("❌ FAILURE: X credentials failed verification. Check your X API keys in the .env file.")
        failures += 1

    # --- Test 2: Generate content for all topics ---
    logging.info("\n[2/2] Testing Content Generation Engine...")
    philosophy_quotes = load_quotes()
    posted_quotes = set(q['quote'] for q in philosophy_quotes[:5])

    for topic in TOPICS:
        logging.info(f"  - Attempting to generate content for topic: '{topic}'...")
        content, _ = generate_post_content(topic, philosophy_quotes, posted_quotes)
        
        if content and len(content) > 0:
            logging.info(f"    ✅ SUCCESS: Generated content for '{topic}'.")
            logging.info(f"      -> Preview: '{content[:80].replace('\n', ' ')}...'")
        else:
            import os
            is_llm_topic = topic not in ["philosophy"]
            if is_llm_topic and not os.getenv("GEMINI_API_KEY"):
                logging.warning(f"    ⚠️ SKIPPED: LLM topic '{topic}' requires GEMINI_API_KEY. This is not a failure.")
            else:
                logging.error(f"    ❌ FAILURE: Failed to generate content for '{topic}'.")
                failures += 1
    
    # --- Final Report ---
    logging.info("\n--- TEST REPORT ---")
    if failures == 0:
        logging.info("🎉 All safe tests passed successfully!")
        logging.info("You can now run a live post test with: myenv/bin/python test_app.py --live")
    else:
        logging.error(f"🔥 {failures} test(s) failed. Please review the errors above.")

def run_live_post_test():
    """
    Posts a real tweet to the configured X account to verify end-to-end functionality.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logging.info("--- RUNNING LIVE POST TEST ---")
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"This is a live test tweet from my automated bot. All systems are go! 🚀 (Test ID: {timestamp})"
    
    logging.info(f"Attempting to post the following content to your X account:\n-> {test_content}")
    
    if post_tweet(test_content):
        logging.info("✅ SUCCESS: Live test tweet was posted successfully. Please check your X account.")
    else:
        logging.error("❌ FAILURE: Failed to post the live test tweet. Check the error logs from the API.")

if __name__ == "__main__":
    # Check for a '--live' flag to run the dangerous test
    if "--live" in sys.argv:
        run_live_post_test()
    else:
        run_tests()
