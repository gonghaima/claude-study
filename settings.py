import os
from dotenv import load_dotenv

load_dotenv()

# Set PROVIDER to "ollama" or "openrouter"
PROVIDER = os.environ.get("PROVIDER", "openrouter")

if PROVIDER == "openrouter":
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
    }
else:  # ollama
    API_URL = "http://localhost:11434/api/chat"
    MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
    HEADERS = {"Content-Type": "application/json"}
