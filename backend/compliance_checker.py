"""
compliance_checker.py
Check compliance of company submissions against requirements
Uses keyword matching and fuzzy string matching (no ML dependencies)
"""

import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from models import Requirement, ComplianceResult, ComplianceReport
import fitz
import docx

class ComplianceChecker:
    
    def __init__(self):
        self.similarity_threshold_high = 0.6  # Strong match
        self.similarity_threshold_medium = 0.4  # Partial match
        print("✅ Compliance Checker initialized (using keyword matching)")
    
    def extract_text_from_file(self, filepath: str) -> str:
        """Extract text from various file formats"""
        ext = filepath.lower().split('.')[-1]
        text = ""
        
        try:
            if ext == 'pdf':
                with fitz.open(filepath) as doc:
                    for page in doc:
                        text += page.get_text() + "\n\n"
            elif ext == 'docx':
                doc = docx.Document(filepath)
                text = "\n".join([para.text for para in doc.paragraphs])
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
        except Exception as e:
            print(f"Error extracting text from {filepath}: {e}")
        
        return text
    
    def check_compliance(
        self,
        requirements: List[Requirement],
        company_documents: Dict[str, str],
        company_name: str,
        tender_id: str
    ) -> ComplianceReport:
        """
        Check compliance of company documents against requirements
        
        Args:
            requirements: List of Requirement objects
            company_documents: Dict of document_type: filepath
            company_name: Name of company
            tender_id: Tender ID
        
        Returns:
            ComplianceReport object
        """
        # Extract text from all company documents
        all_company_text = ""
        for doc_type, filepath in company_documents.items():
            text = self.extract_text_from_file(filepath)
            all_company_text += f"\n\n===== {doc_type.upper()} =====\n\n{text}"
        
        # Split into sentences for better matching
        sentences = self._split_into_sentences(all_company_text)
        
        # Analyze each requirement
        detailed_results = []
        requirements_met = []
        requirements_missing = []
        requirements_partial = []
        
        print(f"Analyzing {len(requirements)} requirements for {company_name}...")
        
        for idx, req in enumerate(requirements, 1):
            print(f"  [{idx}/{len(requirements)}] Checking {req.req_id}...")
            result = self._analyze_requirement(req, sentences, all_company_text)
            detailed_results.append(result)
            
            if result.status == "met":
                requirements_met.append(req.req_id)
            elif result.status == "partial":
                requirements_partial.append(req.req_id)
            else:
                requirements_missing.append(req.req_id)
        
        # Calculate compliance percentage
        met_count = len(requirements_met)
        partial_count = len(requirements_partial) * 0.5  # Partial counts as 50%
        total_count = len(requirements)
        
        compliance_percentage = ((met_count + partial_count) / total_count * 100) if total_count > 0 else 0
        
        from datetime import datetime
        report = ComplianceReport(
            company_name=company_name,
            tender_id=tender_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_requirements=total_count,
            requirements_met=requirements_met,
            requirements_missing=requirements_missing,
            requirements_partial=requirements_partial,
            compliance_percentage=round(compliance_percentage, 2),
            detailed_results=detailed_results
        )
        
        print(f"✅ Analysis complete: {compliance_percentage:.1f}% compliance")
        return report
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        return sentences
    
    def _analyze_requirement(self, requirement: Requirement, sentences: List[str], full_text: str) -> ComplianceResult:
        """
        Analyze if a requirement is met using:
        1. Keyword matching
        2. Fuzzy string matching
        3. Pattern matching
        """
        req_text = requirement.requirement_text.lower()
        req_keywords = [kw.lower() for kw in requirement.keywords]
        
        matched_sections = []
        max_similarity = 0.0
        keyword_match_count = 0
        
        # Method 1: Check for exact keyword matches
        full_text_lower = full_text.lower()
        for keyword in req_keywords:
            if keyword in full_text_lower:
                keyword_match_count += 1
        
        # Method 2: Fuzzy string matching with sentences
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Calculate similarity
            similarity = self._calculate_similarity(req_text, sentence_lower)
            
            if similarity > self.similarity_threshold_medium:
                matched_sections.append(sentence[:200] + "...")
                max_similarity = max(max_similarity, similarity)
        
        # Method 3: Check for requirement-specific patterns
        pattern_match = self._check_patterns(requirement, full_text_lower)
        
        # Combine all matching methods
        total_confidence = max(
            max_similarity,
            (keyword_match_count / len(req_keywords)) if req_keywords else 0,
            pattern_match
        )
        
        # Determine status
        if total_confidence >= self.similarity_threshold_high or keyword_match_count >= len(req_keywords) * 0.7:
            status = "met"
            reasoning = f"Strong match found (confidence: {total_confidence:.2f}, keywords: {keyword_match_count}/{len(req_keywords)})"
        elif total_confidence >= self.similarity_threshold_medium or keyword_match_count >= 2:
            status = "partial"
            reasoning = f"Partial match found (confidence: {total_confidence:.2f}, keywords: {keyword_match_count}/{len(req_keywords)})"
        else:
            status = "missing"
            reasoning = f"No significant match found (confidence: {total_confidence:.2f})"
        
        return ComplianceResult(
            req_id=requirement.req_id,
            requirement_text=requirement.requirement_text,
            status=status,
            confidence_score=round(total_confidence, 3),
            matched_sections=matched_sections[:3],  # Top 3 matches
            reasoning=reasoning
        )
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings using SequenceMatcher"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _check_patterns(self, requirement: Requirement, text: str) -> float:
        """Check for specific patterns based on requirement category"""
        score = 0.0
        req_text_lower = requirement.requirement_text.lower()
        
        # Extract key terms from requirement
        key_terms = self._extract_key_terms(req_text_lower)
        
        # Check how many key terms are present in the text
        present_terms = sum(1 for term in key_terms if term in text)
        
        if key_terms:
            score = present_terms / len(key_terms)
        
        return score
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from requirement text"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'shall'
        }
        
        # Split into words and filter
        words = re.findall(r'\b[a-z]+\b', text.lower())
        key_terms = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Return unique terms
        return list(set(key_terms))[:10]
