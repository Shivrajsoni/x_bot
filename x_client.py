import os
import requests
import logging

# Using OAuth 1.0a is more robust and required for user-context endpoints.
try:
    from requests_oauthlib import OAuth1
except ImportError:
    logging.error("requests_oauthlib is not installed. Please run 'pip install -r requirements.txt'")
    OAuth1 = None

# Load credentials from .env file
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

def _get_oauth1_auth():
    """Helper function to create an OAuth1 session."""
    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
        logging.error("OAuth 1.0a API credentials are not fully configured. Please check your .env file.")
        return None
    if OAuth1 is None:
        return None
    return OAuth1(API_KEY, client_secret=API_SECRET,
                  resource_owner_key=ACCESS_TOKEN,
                  resource_owner_secret=ACCESS_SECRET)

def post_tweet(text):
    """
    Posts a tweet using the X API v2 and OAuth 1.0a authentication.
    """
    auth = _get_oauth1_auth()
    if not auth:
        return False

    url = "https://api.twitter.com/2/tweets"
    headers = {"Content-Type": "application/json"}
    data = {"text": text}
    
    resp = requests.post(url, json=data, headers=headers, auth=auth)
    
    if resp.status_code == 201:
        logging.info("Posted successfully: %s", text)
        return True
    else:
        logging.error(f"Error posting: {resp.status_code} {resp.text}")
        return False

def verify_credentials():
    """
    Verifies credentials using OAuth 1.0a by fetching the authenticated user's info.
    """
    auth = _get_oauth1_auth()
    if not auth:
        return False

    url = "https://api.twitter.com/2/users/me"
    try:
        resp = requests.get(url, auth=auth)
        if resp.status_code == 200:
            user_data = resp.json().get("data", {})
            logging.info(f"Successfully verified credentials for user: @{user_data.get('username')}")
            return True
        else:
            logging.error(f"Credential verification failed. Status: {resp.status_code}, Response: {resp.text}")
            return False
    except Exception as e:
        logging.error(f"An exception occurred during credential verification: {e}")
        return False