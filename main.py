import os
import random
import time
import logging
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import threading
from flask import Flask
import psycopg2
from psycopg2 import sql

# Load environment variables from .env file
load_dotenv()

from config import TOPICS
from content import generate_post_content
from x_client import post_tweet

# ============ DATABASE CONFIGURATION =============
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Creates and returns a new database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Could not connect to the database: {e}")
        return None

def init_db():
    """Initializes the database by creating tables if they don't exist."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            # Main posts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL UNIQUE,
                    topic VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
                );
            """)
            # Philosophy quotes table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS philosophy_quotes (
                    id SERIAL PRIMARY KEY,
                    quote TEXT NOT NULL UNIQUE,
                    author VARCHAR(255) NOT NULL
                );
            """)
            # Used philosophy quotes tracking table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS used_quote_ids (
                    quote_id INTEGER UNIQUE NOT NULL REFERENCES philosophy_quotes(id)
                );
            """)
            conn.commit()
            logging.info("Database initialized successfully.")
    except psycopg2.Error as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

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

# ============ STATE MANAGEMENT (DATABASE) =============

def should_post_now(min_interval_hours=6, max_interval_hours=12):
    """Determines if it's time to post based on the last post time in the DB."""
    conn = get_db_connection()
    if not conn:
        return False # Cannot connect to DB, so don't post

    last_post_time = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1;")
            result = cur.fetchone()
            if result:
                last_post_time = result[0]
    except psycopg2.Error as e:
        logging.error(f"Error fetching last post time: {e}")
        return False # Error, so don't post
    finally:
        if conn:
            conn.close()

    now = datetime.now(timezone.utc)
    if last_post_time is None:
        logging.info("No previous post found in the database. Will post now.")
        return True

    next_post_interval = timedelta(hours=random.uniform(min_interval_hours, max_interval_hours))
    next_post_time = last_post_time + next_post_interval
    logging.info(f"Next scheduled post time is around: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    return now >= next_post_time

def is_post_in_db(content):
    """Checks if a post with the exact same content already exists."""
    conn = get_db_connection()
    if not conn:
        return True # Assume it exists to prevent duplicates on DB error

    exists = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM posts WHERE content = %s);", (content,))
            exists = cur.fetchone()[0]
    except psycopg2.Error as e:
        logging.error(f"Error checking for post uniqueness: {e}")
        return True # Assume it exists on error
    finally:
        if conn:
            conn.close()
    return exists

def save_post_to_db(content, topic):
    """Saves a new post to the database."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO posts (content, topic) VALUES (%s, %s);", (content, topic))
            conn.commit()
            logging.info("Saved new post to the database.")
    except psycopg2.Error as e:
        logging.error(f"Error saving post to database: {e}")
    finally:
        if conn:
            conn.close()

def load_unused_philosophy_quotes_from_db():
    """Loads all philosophy quotes that have not been used yet."""
    conn = get_db_connection()
    if not conn:
        return []

    quotes = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT q.id, q.quote, q.author 
                FROM philosophy_quotes q
                LEFT JOIN used_quote_ids u ON q.id = u.quote_id
                WHERE u.quote_id IS NULL;
            """)
            for row in cur.fetchall():
                quotes.append({"id": row[0], "quote": row[1], "author": row[2]})
    except psycopg2.Error as e:
        logging.error(f"Error loading unused philosophy quotes: {e}")
    finally:
        if conn:
            conn.close()
    return quotes

def mark_philosophy_quote_as_used(quote_id):
    """Marks a philosophy quote as used by adding its ID to the used_quote_ids table."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO used_quote_ids (quote_id) VALUES (%s) ON CONFLICT (quote_id) DO NOTHING;", (quote_id,))
            conn.commit()
    except psycopg2.Error as e:
        logging.error(f"Error marking quote as used: {e}")
    finally:
        if conn:
            conn.close()

def reset_used_philosophy_quotes():
    """Clears the used_quote_ids table."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM used_quote_ids;")
            conn.commit()
            logging.info("Reset the used philosophy quotes history.")
    except psycopg2.Error as e:
        logging.error(f"Error resetting used quotes: {e}")
    finally:
        if conn:
            conn.close()

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting X-Post bot...")

    while True:
        if should_post_now():
            logging.info("Time to post a new tweet.")

            # Load unused philosophy quotes from the DB for this cycle
            unused_philosophy_quotes = load_unused_philosophy_quotes_from_db()
            if not unused_philosophy_quotes:
                logging.info("All philosophy quotes have been used. Resetting history.")
                reset_used_philosophy_quotes()
                unused_philosophy_quotes = load_unused_philosophy_quotes_from_db()

            # 1. Generate content
            topic = random.choice(TOPICS)
            logging.info(f"Selected topic: {topic}")
            content, context_obj = generate_post_content(
                topic,
                quotes=unused_philosophy_quotes
            )
            
            if content and len(content) <= 280:
                # 2. Check for uniqueness in the database
                if is_post_in_db(content):
                    logging.warning(f"Generated content already exists in the database. Skipping. Content: {content}")
                    continue

                # 3. Post to X
                logging.info(f"Generated content: {content}")
                success = post_tweet(content)
                
                # 4. If successful, save to DB and log
                if success:
                    save_post_to_db(content, topic)
                    log_post_to_history(content)
                    
                    if topic == "philosophy" and context_obj:
                        quote_id_to_mark = context_obj.get("id")
                        if quote_id_to_mark:
                            mark_philosophy_quote_as_used(quote_id_to_mark)
                    
                    logging.info("Successfully posted and updated state in the database.")

            elif content:
                logging.warning(f"Generated content is too long ({len(content)} characters) or empty. Skipping post.")

        # Sleep for a while before checking again
        check_interval_minutes = 15
        logging.info(f"Sleeping for {check_interval_minutes} minutes...")
        time.sleep(60 * check_interval_minutes)

if __name__ == "__main__":
    init_db()
    worker_thread = threading.Thread(target=main_loop)
    worker_thread.daemon = True
    worker_thread.start()
    run_web_server()