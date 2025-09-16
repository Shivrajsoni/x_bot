import os
import random
import json
import logging
import requests

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



def _generate_llm_post(prompt):
    """Generic function to generate content using the Gemini LLM."""
    # Check for GEMINI_API_KEY inside the function to make it more testable
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not genai or not gemini_api_key:
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

def _get_philosophy_prompt():
    max_chars = random.randint(150, 260)
    return f"""
    You are a philosopher for the modern age, sharing deep, original thoughts on X.
    Generate a single, thought-provoking philosophical question or statement under {max_chars} characters.
    It should be about a timeless human concern (e.g., consciousness, meaning, freedom, ethics) but framed in a fresh, modern way.
    Your tone is insightful, slightly provocative, and designed to make people pause and think. Avoid cliches.
    Use a single, relevant hashtag like #philosophy, #consciousness, or #ethics if necessary then only else don't use tags too much.
    """

def _get_tech_prompt():
    max_chars = random.randint(120, 260)
    prompt = f"""
    You are 'Cyberskeptic', a tech commentator on X with a sharp, insightful, and strongly opinionated wit.
    Find a recent, hyped-up tech news story about a new innovation.
    Write a tweet under {max_chars} characters that cuts through the hype. Give your sharp opinion on the potential downside, the overlooked consequence, or the comical absurdity of it.
    Your tone is dry, witty, and knowledgeable. Be bold in your opinion. Only use a hashtag if it is very specific and adds to the wit.
    """
    return prompt

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
    The post must be under {max_chars} characters. You can add a hashtag like #corporate or #workhumor if it feels natural, but it's not required.
    """


def _get_world_news_prompt():
    max_chars = random.randint(180, 260)
    prompt = f"""
    You are 'The Modern Observer', a thoughtful commentator on X who reflects on the significant events of our time.
    Find a significant news story from the last 24 hours about art, culture, a recent mishap, or a new innovation.
    Write a tweet under {max_chars} characters that offers a sharp, opinionated, and human take on its deeper meaning. Don't just report the news, give a unique perspective.
    Your tone is analytical, and human. If a hashtag is needed, use one or two specific ones. Avoid generic tags.
    """
    return prompt

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
    A hashtag is not required, but if you use one, make it specific and relevant. Avoid generic tags like #history.
    """

def _get_cs_tip_prompt():
    max_chars = random.randint(150, 260)
    return f"""
    You are 'CodeWise', a senior software engineer who enjoys sharing practical advice on X.
    Generate a short, insightful tip or a lesser-known fact about a niche computer science topic. This could be about a specific programming language (like Python or Rust), a database optimization trick, a useful command-line tool, a design pattern, or a data structure.
    The post must be under {max_chars} characters. It should be clear, concise, and immediately useful to other developers.
    You can use one or two relevant hashtags, like the name of the technology (e.g., #python, #git).
    """

# --- Main Content Orchestrator ---

def generate_post_content(topic):
    """
    Generates post content based on the selected topic.
    Returns a tuple: (content_string, context_object)
    """
    content, context_obj = None, None

    fallback_content = {
        "tech": "Is 'cloud-native' just a fancy term for 'someone else\'s computer' again? Discuss. #tech #satire",
        "philosophy": "What is the nature of consciousness? #philosophy",
        "deep thoughts": "Is a thought you have but never share truly a thought at all? #deepthoughts",

        "humor": "Why don\'t scientists trust atoms? Because they make up everything! #joke #science",
        "world news": "In world news today, things happened. Experts are cautiously optimistic that other things may happen tomorrow. #news",
        "engaging question": "What is a simple thing that still brings you joy?",
        "history fact": "Did you know that the first computer programmer was Ada Lovelace, in the 1840s? She worked on an analytical engine that was never even built!",
        "cs_tip": "Pro-tip: Use `git stash --include-untracked` to stash untracked files along with your other changes. #git"
    }

    
    
    if topic == "philosophy":
        prompt = _get_philosophy_prompt()
        content = _generate_llm_post(prompt)
    
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
    
    elif topic == "cs_tip":
        prompt = _get_cs_tip_prompt()
        content = _generate_llm_post(prompt)
    
    if content is None:
        logging.warning(f"Using fallback content for topic: {topic}")
        content = fallback_content.get(topic, "This is a random thought.")
        
    return content, context_obj
