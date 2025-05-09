import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model configs
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "chroma_db")

# Basic check (optional but nice)
if OPENAI_API_KEY is None:
    raise ValueError("⚠️ OPENAI_API_KEY is missing! Please set it in your .env file.")

# from app.core.config import OPENAI_API_KEY, EMBEDDING_MODEL_NAME
