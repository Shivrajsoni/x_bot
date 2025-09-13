import os
import random
import json
import logging

# Attempt to import google.generativeai
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        logging.warning("GEMINI_API_KEY not found. LLM features will be disabled.")
        genai = None
except ImportError:
    logging.warning("google.generativeai not installed. LLM features will be disabled.")
    genai = None

# --- Content Generation Strategies ---

def _generate_philosophy_post(quotes, posted_quotes):
    """
    Generates a philosophy post, ensuring it has not been posted before.
    Returns a tuple of (post_string, quote_object).
    """
    if not quotes:
        return None, None

    # Find an unused quote by filtering out already posted ones
    available_quotes = [q for q in quotes if q.get("quote") not in posted_quotes]

    if not available_quotes:
        logging.warning("All philosophy quotes have been posted. Waiting for reset.")
        return None, None

    quote_obj = random.choice(available_quotes)
    quote = quote_obj["quote"]
    author = quote_obj["author"]
    
    formats = [
        f'A thought from {author}: "{quote}"\n\nWhat does this mean to you? #philosophy',
        f'"{quote}" - {author}\n\n#quotes #wisdom',
        f'Mulling over this from {author}: \n\n"{quote}" #deepthoughts',
        f'{author}. Agree or disagree? #classicphilosophy',
        f'"{quote}"\n\n- {author}'
    ]
    
    post = random.choice(formats)
    
    if random.random() < 0.3: # 30% chance
        post += f" {random.choice(['🤔', '🧐', '✨', '🤯'])}"
        
    return post, quote_obj

def _generate_llm_post(prompt):
    """Generic function to generate content using the Gemini LLM."""
    if not genai or not GEMINI_API_KEY:
        logging.error("LLM client not configured. Cannot generate post.")
        return None

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error during LLM content generation: {e}")
        return None

# --- Topic-Specific LLM Prompts ---

def _get_tech_prompt():
    max_chars = random.randint(120, 180)
    return f"""
    You are a sharp, witty, and slightly cynical tech commentator on X (formerly Twitter).
    Your task is to find a single, genuinely interesting, and recent piece of news in the tech world (AI, robotics, biotech, space-tech, etc.).
    After finding it, write a short, provocative tweet (under {max_chars} characters) about it.

    Your tweet must:
    - Have a strong, biased opinion (be skeptical, overly enthusiastic, or satirical).
    - Not just state the news, but comment on its deeper implication.
    - Use 1-3 relevant, popular hashtags.
    - Be engaging, perhaps by asking a rhetorical question or making a bold prediction.
    - DO NOT include links or mention the source.
    """

def _get_deep_thought_prompt():
    max_chars = random.randint(100, 160)
    return f"""
    You are a modern-day philosopher on X (formerly Twitter), blending deep thought with a touch of absurdity.
    Generate a single, profound, and slightly strange observation about modern life, society, or the human condition.

    Your tweet must be:
    - Under {max_chars} characters.
    - Phrased as a "shower thought" or a paradoxical question.
    - Make people stop and think, or see something familiar in a completely new light.
    - Use one or two fitting hashtags like #deepthoughts, #paradox, or #observation.
    """

def _get_humor_prompt():
    max_chars = random.randint(80, 140)
    return f"""
    You are a stand-up comedian who specializes in short, clever one-liners for Twitter.
    Write a single, original joke. It can be about technology, everyday life, or something absurd.
    The joke must be under {max_chars} characters and include 1-2 hashtags like #joke or #humor.
    """

# --- Main Content Orchestrator ---

def generate_post_content(topic, quotes, posted_quotes=None):
    """
    Generates post content based on the selected topic.
    Returns a tuple: (content_string, context_object)
    """
    if posted_quotes is None:
        posted_quotes = set()

    content, context_obj = None, None

    fallback_content = {
        "tech": "Is 'cloud-native' just a fancy term for 'someone else\'s computer' again? Discuss. #tech #satire",
        "deep thoughts": "Is a thought you have but never share truly a thought at all? #deepthoughts",
        "humor": "Why don\'t scientists trust atoms? Because they make up everything! #joke #science",
        "random observation": "Traffic is just a bunch of people who want to be in a different place. #observation"
    }

    if topic == "philosophy":
        content, context_obj = _generate_philosophy_post(quotes, posted_quotes)
    
    elif topic == "tech":
        prompt = _get_tech_prompt()
        content = _generate_llm_post(prompt)

    elif topic == "deep thoughts":
        prompt = _get_deep_thought_prompt()
        content = _generate_llm_post(prompt)

    elif topic == "humor":
        prompt = _get_humor_prompt()
        content = _generate_llm_post(prompt)
    
    if content is None:
        logging.warning(f"Using fallback content for topic: {topic}")
        content = fallback_content.get(topic, fallback_content["random observation"])
        
    return content, context_obj

def load_quotes(filename="quotes.json"):
    """Loads quotes from a JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Could not load quotes from {filename}: {e}")
        return []
