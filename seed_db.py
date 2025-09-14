import os
import json
import psycopg2
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
DATABASE_URL = os.getenv("DATABASE_URL")
QUOTES_FILE = "quotes.json"

# --- MAIN SCRIPT ---
def seed_database():
    """Reads quotes from a JSON file and inserts them into the philosophy_quotes table."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if not DATABASE_URL:
        logging.error("DATABASE_URL environment variable not set. Please check your .env file.")
        return

    # 1. Read the JSON file
    try:
        with open(QUOTES_FILE, 'r') as f:
            quotes_data = json.load(f)
        logging.info(f"Loaded {len(quotes_data)} quotes from {QUOTES_FILE}.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Could not read or parse {QUOTES_FILE}: {e}")
        return

    # 2. Connect to the database and insert data
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            inserted_count = 0
            skipped_count = 0
            for item in quotes_data:
                quote = item.get("quote")
                author = item.get("author")

                if not quote or not author:
                    logging.warning(f"Skipping invalid quote object: {item}")
                    continue

                # Check if the quote already exists to avoid duplicates
                cur.execute("SELECT id FROM philosophy_quotes WHERE quote = %s;", (quote,))
                if cur.fetchone():
                    # logging.info(f"Quote already exists, skipping: '{quote[:50]}...' ")
                    skipped_count += 1
                    continue

                # Insert the new quote
                cur.execute(
                    "INSERT INTO philosophy_quotes (quote, author) VALUES (%s, %s);",
                    (quote, author)
                )
                inserted_count += 1
            
            conn.commit()
            logging.info(f"Successfully inserted {inserted_count} new quotes.")
            logging.info(f"Skipped {skipped_count} already existing quotes.")

    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback() # Rollback any partial changes
    finally:
        if conn:
            conn.close()
        logging.info("Database connection closed.")

if __name__ == "__main__":
    seed_database()
