"""
Enhanced Text Cleaning for Tender Evaluation System
Domain-specific text processing for government procurement documents
"""
import re
import unicodedata
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import string

logger = logging.getLogger(__name__)

class AdvancedTextCleaner:
    def __init__(self):
        # Tender-specific patterns
        self.tender_patterns = {
            'tender_id': re.compile(r'(?:tender|rfp|rfq)[-_\s]*(?:no\.?|number|id)[-_\s]*:?\s*([a-zA-Z0-9\-_/]+)', re.IGNORECASE),
            'amount': re.compile(r'(?:rs\.?|inr|usd|\$|₹)\s*([0-9,]+(?:\.[0-9]{2})?)', re.IGNORECASE),
            'date': re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?91[-\s]?)?[6-9]\d{9}\b'),
            'pin_code': re.compile(r'\b[1-9]\d{5}\b'),
            'gst_number': re.compile(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b'),
            'pan_number': re.compile(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'),
        }
        
        # Common abbreviations in procurement
        self.procurement_abbreviations = {
            'EMD': 'Earnest Money Deposit',
            'PBG': 'Performance Bank Guarantee',
            'BOQ': 'Bill of Quantities',
            'SOR': 'Schedule of Rates',
            'DGS&D': 'Directorate General of Supplies and Disposals',
            'CPPP': 'Central Public Procurement Portal',
            'MSE': 'Micro and Small Enterprise',
            'OEM': 'Original Equipment Manufacturer',
            'PO': 'Purchase Order',
            'LOI': 'Letter of Intent',
            'TC': 'Technical Compliance',
            'FC': 'Financial Compliance'
        }
        
        # Technical terms that should be preserved
        self.technical_terms = {
            'specifications', 'requirements', 'compliance', 'evaluation',
            'criteria', 'methodology', 'implementation', 'deliverables',
            'milestones', 'warranty', 'maintenance', 'support', 'training'
        }
    
    def clean_text_comprehensive(self, text: str, preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Comprehensive text cleaning with metadata extraction
        """
        if not text or not isinstance(text, str):
            return {
                'cleaned_text': '',
                'extracted_entities': {},
                'statistics': {'original_length': 0, 'cleaned_length': 0}
            }
        
        original_length = len(text)
        
        # Extract entities before cleaning
        extracted_entities = self._extract_entities(text)
        
        # Clean the text
        cleaned_text = self._clean_text_step_by_step(text, preserve_structure)
        
        # Generate statistics
        statistics = {
            'original_length': original_length,
            'cleaned_length': len(cleaned_text),
            'reduction_ratio': 1 - (len(cleaned_text) / original_length) if original_length > 0 else 0,
            'word_count': len(cleaned_text.split()),
            'sentence_count': len([s for s in cleaned_text.split('.') if s.strip()]),
            'paragraph_count': len([p for p in cleaned_text.split('\n\n') if p.strip()])
        }
        
        return {
            'cleaned_text': cleaned_text,
            'extracted_entities': extracted_entities,
            'statistics': statistics,
            'abbreviations_expanded': self._get_expanded_abbreviations(text)
        }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract structured entities from text"""
        entities = {}
        
        for entity_type, pattern in self.tender_patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates
        
        return entities
    
    def _clean_text_step_by_step(self, text: str, preserve_structure: bool) -> str:
        """Step-by-step text cleaning process"""
        
        # Step 1: Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Step 2: Fix common OCR errors
        text = self._fix_ocr_errors(text)
        
        # Step 3: Handle special characters and symbols
        text = self._handle_special_characters(text)
        
        # Step 4: Normalize whitespace
        text = self._normalize_whitespace(text, preserve_structure)
        
        # Step 5: Expand abbreviations
        text = self._expand_abbreviations(text)
        
        # Step 6: Remove redundant information
        text = self._remove_redundant_content(text)
        
        # Step 7: Final cleanup
        text = self._final_cleanup(text)
        
        return text.strip()
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors in scanned documents"""
        ocr_corrections = {
            # Common character substitutions
            r'\b0(?=\w)': 'O',  # 0 -> O at word beginning
            r'(?<=\w)0(?=\w)': 'o',  # 0 -> o in middle of word
            r'\bl(?=\w)': 'I',  # l -> I at word beginning
            r'rn': 'm',  # rn -> m
            r'vv': 'w',  # vv -> w
            r'\|': 'l',  # | -> l
            
            # Common word corrections
            r'\btlie\b': 'the',
            r'\barcl\b': 'and',
            r'\bwitli\b': 'with',
            r'\btliat\b': 'that',
            r'\bliave\b': 'have',
            r'\bwlien\b': 'when',
            r'\bwliicli\b': 'which',
            r'\btliis\b': 'this',
            r'\btliey\b': 'they',
            r'\btliere\b': 'there',
            
            # Fix spacing around punctuation
            r'\s+([,.;:!?])': r'\1',
            r'([,.;:!?])(?=[a-zA-Z])': r'\1 ',
        }
        
        for pattern, replacement in ocr_corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _handle_special_characters(self, text: str) -> str:
        """Handle special characters and symbols"""
        
        # Replace common symbols with text equivalents
        symbol_replacements = {
            '&': ' and ',
            '@': ' at ',
            '%': ' percent ',
            '₹': ' INR ',
            '$': ' USD ',
            '€': ' EUR ',
            '£': ' GBP ',
            '°C': ' degrees Celsius ',
            '°F': ' degrees Fahrenheit ',
            '©': ' copyright ',
            '®': ' registered ',
            '™': ' trademark ',
        }
        
        for symbol, replacement in symbol_replacements.items():
            text = text.replace(symbol, replacement)
        
        # Remove or replace problematic characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)  # Control characters
        text = re.sub(r'[""''„"‚']', '"', text)  # Normalize quotes
        text = re.sub(r'[–—―]', '-', text)  # Normalize dashes
        text = re.sub(r'…', '...', text)  # Normalize ellipsis
        
        return text
    
    def _normalize_whitespace(self, text: str, preserve_structure: bool) -> str:
        """Normalize whitespace while optionally preserving structure"""
        
        if preserve_structure:
            # Preserve paragraph breaks but normalize other whitespace
            paragraphs = text.split('\n\n')
            cleaned_paragraphs = []
            
            for paragraph in paragraphs:
                # Within each paragraph, normalize whitespace
                paragraph = re.sub(r'\s+', ' ', paragraph.strip())
                if paragraph:
                    cleaned_paragraphs.append(paragraph)
            
            text = '\n\n'.join(cleaned_paragraphs)
        else:
            # Aggressive whitespace normalization
            text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common procurement abbreviations"""
        
        for abbrev, expansion in self.procurement_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, f"{abbrev} ({expansion})", text, flags=re.IGNORECASE)
        
        return text
    
    def _get_expanded_abbreviations(self, text: str) -> Dict[str, str]:
        """Get list of abbreviations that were expanded"""
        found_abbreviations = {}
        
        for abbrev, expansion in self.procurement_abbreviations.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            if re.search(pattern, text, flags=re.IGNORECASE):
                found_abbreviations[abbrev] = expansion
        
        return found_abbreviations
    
    def _remove_redundant_content(self, text: str) -> str:
        """Remove redundant or unnecessary content"""
        
        # Remove excessive repetition of words
        text = re.sub(r'\b(\w+)\s+\1(?:\s+\1)*\b', r'\1', text, flags=re.IGNORECASE)
        
        # Remove header/footer patterns
        header_footer_patterns = [
            r'page \d+ of \d+',
            r'confidential|proprietary',
            r'copyright \d{4}',
            r'all rights reserved',
            r'tender document',
            r'government of india',
        ]
        
        for pattern in header_footer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        text = re.sub(r'[_]{3,}', '___', text)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and normalization"""
        
        # Remove extra spaces around punctuation
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        text = re.sub(r'([,.;:!?])\s+', r'\1 ', text)
        
        # Ensure proper sentence spacing
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Remove multiple consecutive punctuation
        text = re.sub(r'([.!?])\1+', r'\1', text)
        
        # Final whitespace cleanup
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        
        return text
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from tender documents"""
        
        structured_data = {
            'tender_details': {},
            'financial_info': {},
            'dates': {},
            'contact_info': {},
            'requirements': [],
            'compliance_items': []
        }
        
        # Extract tender details
        tender_id_match = self.tender_patterns['tender_id'].search(text)
        if tender_id_match:
            structured_data['tender_details']['tender_id'] = tender_id_match.group(1)
        
        # Extract financial information
        amounts = self.tender_patterns['amount'].findall(text)
        if amounts:
            structured_data['financial_info']['amounts'] = amounts
        
        # Extract dates
        dates = self.tender_patterns['date'].findall(text)
        if dates:
            structured_data['dates']['found_dates'] = dates
        
        # Extract contact information
        emails = self.tender_patterns['email'].findall(text)
        phones = self.tender_patterns['phone'].findall(text)
        
        if emails:
            structured_data['contact_info']['emails'] = emails
        if phones:
            structured_data['contact_info']['phones'] = phones
        
        # Extract requirements (simple keyword-based extraction)
        requirement_indicators = [
            'must', 'shall', 'required', 'mandatory', 'essential',
            'minimum', 'maximum', 'not less than', 'at least'
        ]
        
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in requirement_indicators):
                if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                    structured_data['requirements'].append(sentence)
        
        return structured_data
    
    def clean_for_vector_storage(self, text: str) -> str:
        """Optimized cleaning for vector storage and retrieval"""
        
        # Basic cleaning
        result = self.clean_text_comprehensive(text, preserve_structure=False)
        cleaned_text = result['cleaned_text']
        
        # Additional optimizations for vector storage
        
        # Remove very short words (less than 3 characters) except important ones
        important_short_words = {'is', 'in', 'on', 'at', 'to', 'of', 'or', 'no', 'if'}
        words = cleaned_text.split()
        filtered_words = [
            word for word in words 
            if len(word) >= 3 or word.lower() in important_short_words
        ]
        
        # Remove excessive stopwords while preserving meaning
        excessive_stopwords = {
            'the', 'and', 'that', 'this', 'with', 'for', 'from', 'they', 'them',
            'their', 'there', 'then', 'than', 'when', 'where', 'which', 'what'
        }
        
        # Keep only if not more than 30% of the text
        stopword_count = sum(1 for word in filtered_words if word.lower() in excessive_stopwords)
        if stopword_count / len(filtered_words) > 0.3:
            filtered_words = [
                word for word in filtered_words 
                if word.lower() not in excessive_stopwords or word.lower() in self.technical_terms
            ]
        
        return ' '.join(filtered_words)

# Global text cleaner instance
text_cleaner = AdvancedTextCleaner()

# Convenience functions for backward compatibility
def clean_text(text: str) -> str:
    """Basic text cleaning function"""
    result = text_cleaner.clean_text_comprehensive(text, preserve_structure=False)
    return result['cleaned_text']

def clean_text_advanced(text: str) -> Dict[str, Any]:
    """Advanced text cleaning with metadata"""
    return text_cleaner.clean_text_comprehensive(text)

def extract_entities(text: str) -> Dict[str, Any]:
    """Extract structured entities from text"""
    return text_cleaner.extract_structured_data(text)

def clean_for_search(text: str) -> str:
    """Clean text optimized for search and retrieval"""
    return text_cleaner.clean_for_vector_storage(text)
