import logging
import sys
from dotenv import load_dotenv

# Load .env variables before importing other project modules
load_dotenv()

from x_client import verify_credentials, post_tweet

def run_tests():
    """
    Runs a suite of tests to ensure the bot is configured correctly
    before running the main application.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    failures = 0
    
    logging.info("--- STARTING BOT HEALTH CHECK ---")

    # --- Test 1: Verify X (Twitter) Credentials ---
    logging.info("\n[1/1] Testing X API Credentials...")
    if verify_credentials():
        logging.info("✅ SUCCESS: X credentials are valid.")
    else:
        logging.error("❌ FAILURE: X credentials failed verification. Check your X API keys in the .env file.")
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