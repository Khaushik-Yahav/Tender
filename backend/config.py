"""
config.py
Configuration with comprehensive debugging
"""

import os
import sys
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path, verbose=True)
    print(f"✅ python-dotenv loaded successfully")
    print(f"✅ Loaded .env from: {env_path.absolute()}")
except ImportError:
    print("⚠️ python-dotenv not installed")
except Exception as e:
    print(f"⚠️ Error loading .env: {e}")

class Config:
    """Application configuration"""
    
    def __init__(self):
        # Get values
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.USE_LLM_EXTRACTION = os.getenv("USE_LLM_EXTRACTION", "true").lower() == "true"
        self.API_HOST = os.getenv("API_HOST", "127.0.0.1")
        self.API_PORT = int(os.getenv("API_PORT", "8000"))
        
        # Debug output
        print("\n" + "="*70)
        print("🔧 CONFIGURATION LOADED")
        print("="*70)
        print(f"USE_LLM_EXTRACTION: {self.USE_LLM_EXTRACTION}")
        print(f"GROQ_MODEL: {self.GROQ_MODEL}")
        print(f"GROQ_API_KEY present: {bool(self.GROQ_API_KEY)}")
        if self.GROQ_API_KEY:
            print(f"  → Key starts with: {self.GROQ_API_KEY[:10]}")
            print(f"  → Key ends with: ...{self.GROQ_API_KEY[-4:]}")
            print(f"  → Key length: {len(self.GROQ_API_KEY)}")
        else:
            print(f"  → ❌ NO API KEY FOUND")
        print("="*70 + "\n")

# Create global instance
config = Config()
