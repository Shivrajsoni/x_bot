import logging
from dotenv import load_dotenv

# Load .env variables before importing other project modules
load_dotenv()

from content import generate_post_content, load_quotes
from x_client import verify_credentials
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
        logging.error("❌ FAILURE: X credentials failed verification. Check your X_BEARER_TOKEN.")
        failures += 1

    # --- Test 2: Generate content for all topics ---
    logging.info("\n[2/2] Testing Content Generation Engine...")
    philosophy_quotes = load_quotes()
    # Use a dummy set of posted quotes to simulate the real scenario
    posted_quotes = set(q['quote'] for q in philosophy_quotes[:5])

    for topic in TOPICS:
        logging.info(f"  - Attempting to generate content for topic: '{topic}'...")
        # The 'context_obj' is the second item in the tuple, which we ignore here
        content, _ = generate_post_content(topic, philosophy_quotes, posted_quotes)
        
        if content and len(content) > 0:
            logging.info(f"    ✅ SUCCESS: Generated content for '{topic}'.")
            logging.info(f"      -> Preview: '{content[:80].replace('\n', ' ')}...'")
        else:
            # This is a critical failure if the LLM is configured, but not if it's intentionally disabled
            is_llm_topic = topic in ["tech", "deep thoughts", "humor", "random observation"]
            import os
            if is_llm_topic and not os.getenv("GEMINI_API_KEY"):
                logging.warning(f"    ⚠️ SKIPPED: LLM topic '{topic}' requires GEMINI_API_KEY. Using fallback.")
            else:
                logging.error(f"    ❌ FAILURE: Failed to generate content for '{topic}'.")
                failures += 1
    
    # --- Final Report ---
    logging.info("\n--- TEST REPORT ---")
    if failures == 0:
        logging.info("🎉 All tests passed successfully! The bot is configured correctly and ready to run.")
        logging.info("You can now start the bot with: python3 main.py")
    else:
        logging.error(f"🔥 {failures} test(s) failed. Please review the errors above before running the main application.")

if __name__ == "__main__":
    run_tests()
