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
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error during LLM content generation: {e}")
        return None

# --- Topic-Specific LLM Prompts ---

def _get_tech_prompt():
    max_chars = random.randint(120, 260)
    return f"""
    You are 'Cyberskeptic', a tech commentator on X with a sharp, insightful, and slightly pessimistic wit.
    Find a recent, hyped-up tech news story (in AI, VR, blockchain, etc.).
    Write a tweet under {max_chars} characters that cuts through the hype and points out the potential downside, the overlooked consequence, or the comical absurdity of it.
    Your tone is dry, witty, and knowledgeable. End with a single, cutting hashtag.
    """

def _get_deep_thought_prompt():
    max_chars = random.randint(100, 200)
    return f"""
    You are a poet who uses X to post fleeting, modern koans.
    Generate a single, three-line observation about the strange intersection of technology and human existence, or the quiet absurdities of modern life.
    The post must be under {max_chars} characters. It should be evocative and leave the reader thinking. Do not use hashtags.
    """

def _get_humor_prompt():
    max_chars = random.randint(100, 240)
    return f"""
    You are a jaded office worker who secretly runs a popular humor account on X.
    Write a short, relatable, and sarcastic joke about corporate life, meetings, emails, or the daily grind.
    The post must be under {max_chars} characters. Use the #corporate and #workhumor hashtags.
    """

def _get_world_news_prompt():
    max_chars = random.randint(180, 260)
    return f"""
    You are 'The Global Analyst', a commentator on X who breaks down complex world events for a general audience.
    Find one significant, non-tech world news story that developed in the last 24 hours.
    Write a tweet under {max_chars} characters that doesn't just state the news, but offers a sharp, opinionated take on its deeper meaning or asks a critical question about the future.
    Your tone is serious, analytical, and human. Use 2-3 relevant hashtags like #geopolitics, #worldnews, or #economy.
    """

def _get_engaging_question_prompt():
    max_chars = random.randint(80, 150)
    return f"""
    You are a master of sparking conversations on X.
    Your task is to create one open-ended, fun, and slightly unusual question under {max_chars} characters that is easy for anyone to answer.
    It should not be about a controversial topic. The goal is to maximize engagement and replies.
    Think "would you rather" or "what's one thing..." style questions.
    The question should be phrased in a friendly and inviting way. No hashtags.
    """

def _get_history_fact_prompt():
    max_chars = random.randint(150, 250)
    return f"""
    You are 'PastForward', a popular history account on X that makes the past feel relevant.
    Find a single, interesting, and surprising historical fact.
    Write a tweet under {max_chars} characters that first states the fact clearly, and then adds a short, witty observation connecting it to modern life, culture, or technology.
    Use 1-2 relevant hashtags like #history or #onthisday.
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
        "world news": "In world news today, things happened. Experts are cautiously optimistic that other things may happen tomorrow. #news",
        "engaging question": "What is a simple thing that still brings you joy?",
        "history fact": "Did you know that the first computer programmer was Ada Lovelace, in the 1840s? She worked on an analytical engine that was never even built!"
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

    elif topic == "world news":
        prompt = _get_world_news_prompt()
        content = _generate_llm_post(prompt)

    elif topic == "engaging question":
        prompt = _get_engaging_question_prompt()
        content = _generate_llm_post(prompt)

    elif topic == "history fact":
        prompt = _get_history_fact_prompt()
        content = _generate_llm_post(prompt)
    
    if content is None:
        logging.warning(f"Using fallback content for topic: {topic}")
        content = fallback_content.get(topic, "This is a random thought.")
        
    return content, context_obj

def load_quotes(filename="quotes.json"):
    """Loads quotes from a JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Could not load quotes from {filename}: {e}")
        return []
