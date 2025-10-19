"""
config.py
Configuration and environment variables
"""

import os
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded .env file from {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables.")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

class Config:
    """Application configuration"""
    
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    # Use LLM for requirements extraction
    USE_LLM_EXTRACTION = os.getenv("USE_LLM_EXTRACTION", "true").lower() == "true"
    
    # API Settings
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    def __init__(self):
        """Validate configuration on init"""
        if self.USE_LLM_EXTRACTION and not self.GROQ_API_KEY:
            print("⚠️ WARNING: USE_LLM_EXTRACTION is True but GROQ_API_KEY is not set!")
            print("⚠️ LLM extraction will be disabled. Please set GROQ_API_KEY in .env file")
        elif self.USE_LLM_EXTRACTION and self.GROQ_API_KEY:
            print(f"✅ LLM extraction enabled with model: {self.GROQ_MODEL}")
            print(f"✅ API Key found: {self.GROQ_API_KEY[:10]}...")
        else:
            print("⚠️ LLM extraction disabled (USE_LLM_EXTRACTION=false)")

# Create global config instance
config = Config()
