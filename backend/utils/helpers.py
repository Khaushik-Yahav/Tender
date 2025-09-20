"""
Enhanced Helper Utilities for Tender Evaluation System
Common utilities and helper functions for the tender evaluation system
"""
import os
import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
import unicodedata
import mimetypes

logger = logging.getLogger(__name__)

class TenderUtils:
    """Utility functions for tender processing"""
    
    @staticmethod
    def generate_tender_id(prefix: str = "TND") -> str:
        """Generate unique tender ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        random_suffix = uuid.uuid4().hex[:8].upper()
        return f"{prefix}-{timestamp}-{random_suffix}"
    
    @staticmethod
    def generate_document_hash(content: Union[str, bytes]) -> str:
        """Generate hash for document content"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """Validate file type based on extension"""
        if not filename:
            return False
        
        file_extension = Path(filename).suffix.lower()
        return file_extension in [ext.lower() for ext in allowed_types]
    
    @staticmethod
    def get_file_mime_type(filepath: str) -> str:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(filepath)
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove non-printable characters
        filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
        
        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]
        
        return f"{name}{ext}"
    
    @staticmethod
    def extract_amount_from_text(text: str) -> List[Tuple[float, str]]:
        """Extract monetary amounts from text"""
        patterns = [
            (r'₹\s*([0-9,]+(?:\.[0-9]{2})?)', 'INR'),
            (r'Rs\.?\s*([0-9,]+(?:\.[0-9]{2})?)', 'INR'),
            (r'USD\s*([0-9,]+(?:\.[0-9]{2})?)', 'USD'),
            (r'\$\s*([0-9,]+(?:\.[0-9]{2})?)', 'USD'),
            (r'([0-9,]+(?:\.[0-9]{2})?)\s*lakhs?', 'INR_LAKH'),
            (r'([0-9,]+(?:\.[0-9]{2})?)\s*crores?', 'INR_CRORE'),
        ]
        
        amounts = []
        for pattern, currency in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if currency == 'INR_LAKH':
                        amount *= 100000
                        currency = 'INR'
                    elif currency == 'INR_CRORE':
                        amount *= 10000000
                        currency = 'INR'
                    amounts.append((amount, currency))
                except ValueError:
                    continue
        
        return amounts
    
    @staticmethod
    def parse_date_from_text(text: str) -> List[datetime]:
        """Extract dates from text"""
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Try different date formats
                    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d', 
                               '%d-%m-%y', '%d/%m/%y', '%d %b %Y']:
                        try:
                            date_obj = datetime.strptime(match, fmt)
                            dates.append(date_obj)
                            break
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return dates

class ResponseFormatter:
    """Format responses for consistent API output"""
    
    @staticmethod
    def format_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Format successful response"""
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def format_error_response(error: str, code: str = "ERROR") -> Dict[str, Any]:
        """Format error response"""
        return {
            "status": "error",
            "error_code": code,
            "message": error,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def format_validation_error(errors: List[str]) -> Dict[str, Any]:
        """Format validation error response"""
        return {
            "status": "validation_error",
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

class DocumentProcessor:
    """Document processing utilities"""
    
    @staticmethod
    def chunk_text_intelligently(text: str, chunk_size: int = 1000, 
                                overlap: int = 200) -> List[Dict[str, Any]]:
        """Intelligent text chunking with metadata"""
        if len(text) <= chunk_size:
            return [{
                'content': text,
                'start_pos': 0,
                'end_pos': len(text),
                'chunk_id': 0,
                'is_complete': True
            }]
        
        chunks = []
        start = 0
        chunk_id = 0
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'content': current_chunk.strip(),
                    'start_pos': current_start,
                    'end_pos': current_start + len(current_chunk),
                    'chunk_id': chunk_id,
                    'is_complete': True
                })
                
                chunk_id += 1
                current_start = current_start + len(current_chunk) - overlap
                current_chunk = current_chunk[-overlap:] + para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    current_start = start
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'start_pos': current_start,
                'end_pos': current_start + len(current_chunk),
                'chunk_id': chunk_id,
                'is_complete': True
            })
        
        return chunks
    
    @staticmethod
    def extract_document_metadata(filepath: str, content: str) -> Dict[str, Any]:
        """Extract metadata from document"""
        path = Path(filepath)
        
        metadata = {
            'filename': path.name,
            'file_extension': path.suffix.lower(),
            'file_size': path.stat().st_size if path.exists() else 0,
            'mime_type': TenderUtils.get_file_mime_type(str(path)),
            'created_at': datetime.now().isoformat(),
            'content_length': len(content),
            'content_hash': TenderUtils.generate_document_hash(content),
            'word_count': len(content.split()),
            'line_count': len(content.split('\n')),
            'extracted_amounts': TenderUtils.extract_amount_from_text(content),
            'extracted_dates': [d.isoformat() for d in TenderUtils.parse_date_from_text(content)]
        }
        
        # Document type classification
        if any(keyword in content.lower() for keyword in ['tender', 'rfp', 'request for proposal']):
            metadata['document_category'] = 'tender_document'
        elif any(keyword in content.lower() for keyword in ['proposal', 'bid', 'quotation']):
            metadata['document_category'] = 'vendor_proposal'
        elif any(keyword in content.lower() for keyword in ['contract', 'agreement']):
            metadata['document_category'] = 'contract'
        else:
            metadata['document_category'] = 'general'
        
        return metadata

class ValidationUtils:
    """Validation utilities for tender data"""
    
    @staticmethod
    def validate_vendor_data(vendor_data: Dict[str, Any]) -> List[str]:
        """Validate vendor data structure"""
        errors = []
        
        required_fields = ['vendor_name', 'contact_email', 'financial_proposal']
        for field in required_fields:
            if field not in vendor_data or not vendor_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        email = vendor_data.get('contact_email', '')
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append("Invalid email format")
        
        # Validate financial proposal
        financial = vendor_data.get('financial_proposal', {})
        if isinstance(financial, dict):
            if 'total_amount' not in financial or not isinstance(financial['total_amount'], (int, float)):
                errors.append("Invalid financial proposal: missing or invalid total_amount")
        
        return errors
    
    @staticmethod
    def validate_tender_requirements(tender_req: Dict[str, Any]) -> List[str]:
        """Validate tender requirements structure"""
        errors = []
        
        required_fields = ['title', 'estimated_value', 'submission_deadline']
        for field in required_fields:
            if field not in tender_req or not tender_req[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate dates
        deadline = tender_req.get('submission_deadline')
        if deadline:
            try:
                if isinstance(deadline, str):
                    datetime.fromisoformat(deadline)
                elif not isinstance(deadline, datetime):
                    errors.append("Invalid submission_deadline format")
            except ValueError:
                errors.append("Invalid submission_deadline format")
        
        return errors

class ConfigUtils:
    """Configuration and environment utilities"""
    
    @staticmethod
    def get_env_var(var_name: str, default: Any = None, required: bool = False) -> Any:
        """Get environment variable with validation"""
        value = os.getenv(var_name, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable {var_name} not set")
        
        return value
    
    @staticmethod
    def load_json_config(filepath: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {filepath}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {filepath}: {e}")
            return {}

class LoggingUtils:
    """Logging utilities"""
    
    @staticmethod
    def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
        """Setup logger with consistent formatting"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @staticmethod
    def log_function_call(func_name: str, args: Tuple, kwargs: Dict[str, Any]):
        """Log function call with parameters"""
        logger.info(f"Calling {func_name} with args={args}, kwargs={kwargs}")

# Convenience functions for backward compatibility
def format_answer(answer: str) -> str:
    """Format answer with basic processing"""
    if not answer:
        return ""
    
    # Basic formatting
    answer = answer.strip()
    
    # Capitalize first letter
    if answer and answer[0].islower():
        answer = answer[0].upper() + answer[1:]
    
    # Ensure proper ending punctuation
    if answer and answer[-1] not in '.!?':
        answer += '.'
    
    return answer

def validate_file_upload(filename: str, max_size_mb: int = 50) -> bool:
    """Validate file upload"""
    if not filename:
        return False
    
    allowed_extensions = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']
    return TenderUtils.validate_file_type(filename, allowed_extensions)

def generate_unique_id(prefix: str = "") -> str:
    """Generate unique identifier"""
    return f"{prefix}{uuid.uuid4().hex}" if prefix else uuid.uuid4().hex

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate basic text similarity score"""
    if not text1 or not text2:
        return 0.0
    
    # Simple word-based similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0
