"""
Enhanced Configuration for Tender Evaluation System
Building upon medical RAG chatbot patterns with tender-specific features
"""
import os
from pathlib import Path
from typing import Optional

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
TENDERS_DIR = DATA_DIR / "tenders"
UPLOADS_DIR = BASE_DIR / "uploads"

# Ensure directories exist
for directory in [DATA_DIR, EMBEDDINGS_DIR, TENDERS_DIR, UPLOADS_DIR]:
    directory.mkdir(exist_ok=True)

# Azure OpenAI Configuration (primary LLM)
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://YOUR_AZURE_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "YOUR_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4")
AZURE_API_VERSION = "2023-12-01-preview"

# OpenAI Fallback Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Embedding Model Configuration (same as medical RAG)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Vector Database Configuration
VECTOR_DB_PATH = str(EMBEDDINGS_DIR / "faiss_index")
CHROMA_DB_PATH = str(EMBEDDINGS_DIR / "chroma_db")

# Document Processing Configuration
MAX_FILE_SIZE_MB = 50
SUPPORTED_FILE_TYPES = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"]

# OCR Configuration
TESSERACT_CONFIG = r"--oem 3 --psm 6"

# Retrieval Configuration (enhanced from medical RAG)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5
SIMILARITY_THRESHOLD = 0.7

# Reranking Configuration (cross-encoder like medical RAG)
USE_CROSS_ENCODER = True
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANK_TOP_K = 3

# LLM Generation Configuration
TEMPERATURE = 0.1
MAX_TOKENS = 2000
TOP_P = 0.9

# Tender Evaluation Criteria Weights
EVALUATION_WEIGHTS = {
    "financial_proposal": 0.25,      # 25%
    "technical_compliance": 0.20,    # 20%
    "company_profile": 0.15,         # 15%
    "methodology": 0.15,             # 15%
    "credentials": 0.10,             # 10%
    "references": 0.10,              # 10%
    "timeline": 0.05                 # 5%
}

# Risk Assessment Thresholds
RISK_THRESHOLDS = {
    "financial_risk": {
        "very_low_bid": 0.5,    # 50% below estimated value
        "very_high_bid": 1.5     # 50% above estimated value
    },
    "compliance_risk": {
        "missing_documents": 0.3,
        "expired_certifications": 0.2
    }
}

# Database Configuration (for storing evaluation results)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tender_evaluations.db")

# FastAPI Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
DEBUG_MODE = os.getenv("DEBUG", "True").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Authentication Configuration (for production)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Oracle ERP Integration (future enhancement)
ORACLE_ERP_ENDPOINT = os.getenv("ORACLE_ERP_ENDPOINT", "")
ORACLE_ERP_USERNAME = os.getenv("ORACLE_ERP_USERNAME", "")
ORACLE_ERP_PASSWORD = os.getenv("ORACLE_ERP_PASSWORD", "")

# Email Configuration (for notifications)
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
