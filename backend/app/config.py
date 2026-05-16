from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from backend dir first, then fall back to project root
_root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_root_env)
load_dotenv(override=False)  # also pick up any local backend/.env

OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
AZURE_ENDPOINT: str = os.environ["AZURE_ENDPOINT"]
AZURE_API_VERSION: str = os.environ["AZURE_API_VERSION"]
AZURE_DEPLOYMENT: str = os.environ["AZURE_DEPLOYMENT"]
GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]

CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:3000",
]
