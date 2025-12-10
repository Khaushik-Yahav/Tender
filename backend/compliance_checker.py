"""
compliance_checker.py
Check compliance of company submissions against requirements
Simple SEMANTIC similarity based comparison (no 'extra' field needed).
"""

import re
from typing import List, Dict
from difflib import SequenceMatcher
from datetime import datetime

from models import Requirement, ComplianceResult, ComplianceReport

import fitz  # PyMuPDF
import docx

from sentence_transformers import SentenceTransformer
import numpy as np


class ComplianceChecker:

    def __init__(self):
        # Simple, clear thresholds for semantic similarity (cosine)
        # You can tune these later based on real data
        self.met_threshold = 0.60       # >= 0.60 -> met
        self.partial_threshold = 0.40   # 0.40–0.60 -> partial

        print("📥 Loading semantic model for compliance checker (all-MiniLM-L6-v2)...")
        self.emb_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embedding_dim = self.emb_model.get_sentence_embedding_dimension()
        print("✅ Compliance Checker initialized (simple semantic matching)")

    # ------------------------------------------------------------------ #
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------ #
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
        using semantic similarity + simple thresholds.
        """

        # 1) Extract and concatenate all company texts
        all_company_text = ""
        for doc_type, filepath in company_documents.items():
            text = self.extract_text_from_file(filepath)
            all_company_text += f"\n\n===== {doc_type.upper()} =====\n\n{text}"

        # 2) Split into sentences
        sentences = self._split_into_sentences(all_company_text)
        print(f"📄 Found {len(sentences)} sentences in company documents.")

        # 3) Encode all sentences ONCE
        if sentences:
            print("🧠 Encoding company sentences...")
            sentence_embeddings = self.emb_model.encode(
                sentences, convert_to_numpy=True
            ).astype(np.float32)
        else:
            sentence_embeddings = np.zeros((0, self.embedding_dim), dtype=np.float32)

        # 4) Analyze each requirement
        detailed_results: List[ComplianceResult] = []
        requirements_met: List[str] = []
        requirements_missing: List[str] = []
        requirements_partial: List[str] = []

        print(f"🔍 Analyzing {len(requirements)} requirements for {company_name}.")

        for idx, req in enumerate(requirements, 1):
            print(f"\n  [{idx}/{len(requirements)}] {req.req_id}:")
            result = self._analyze_requirement(
                requirement=req,
                sentences=sentences,
                full_text=all_company_text,
                sentence_embeddings=sentence_embeddings,
            )
            detailed_results.append(result)

            print(
                f"     → status={result.status}, "
                f"confidence={result.confidence_score}"
            )

            if result.status == "met":
                requirements_met.append(req.req_id)
            elif result.status == "partial":
                requirements_partial.append(req.req_id)
            else:
                requirements_missing.append(req.req_id)

        # 5) Compute compliance percentage
        met_count = len(requirements_met)
        partial_count = len(requirements_partial) * 0.5  # partial = 50%
        total_count = len(requirements)

        compliance_percentage = (
            (met_count + partial_count) / total_count * 100 if total_count > 0 else 0
        )

        report = ComplianceReport(
            company_name=company_name,
            tender_id=tender_id,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_requirements=total_count,
            requirements_met=requirements_met,
            requirements_missing=requirements_missing,
            requirements_partial=requirements_partial,
            compliance_percentage=round(compliance_percentage, 2),
            detailed_results=detailed_results,
        )

        print(f"\n✅ Analysis complete: {report.compliance_percentage:.2f}% compliance")
        print(
            f"   Met={len(requirements_met)}, "
            f"Partial={len(requirements_partial)}, "
            f"Missing={len(requirements_missing)}"
        )
        return report

    # ------------------------------------------------------------------ #
    # INTERNAL HELPERS
    # ------------------------------------------------------------------ #
    def _split_into_sentences(self, text: str) -> List[str]:
        """Very simple sentence splitter."""
        # Split on . ! ? and keep sentences that are not too short
        raw = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in raw if len(s.strip()) > 20]
        return sentences

    def _analyze_requirement(
        self,
        requirement: Requirement,
        sentences: List[str],
        full_text: str,
        sentence_embeddings: np.ndarray,
    ) -> ComplianceResult:
        """
        SIMPLE version:
        - Compute semantic similarity between requirement text and all sentences.
        - Take the max similarity as the main signal.
        - Use thresholds:
            >= met_threshold      → met
            >= partial_threshold  → partial
            else                  → missing
        - Add a little boost if requirement keywords appear in full text.
        """
        req_text = requirement.requirement_text.strip()
        req_text_lower = req_text.lower()
        req_keywords = [kw.lower() for kw in requirement.keywords]

        matched_sections: List[str] = []
        full_text_lower = full_text.lower()

        # ===== Semantic similarity =====
        max_sim = 0.0
        best_sentence = None

        if len(sentence_embeddings) > 0 and req_text:
            req_emb = self.emb_model.encode(
                req_text, convert_to_numpy=True
            ).astype(np.float32)

            # Normalize
            req_norm = np.linalg.norm(req_emb) + 1e-8
            sent_norms = np.linalg.norm(sentence_embeddings, axis=1, keepdims=True) + 1e-8

            normed_sent_embeds = sentence_embeddings / sent_norms
            normed_req_emb = req_emb / req_norm

            sims = np.dot(normed_sent_embeds, normed_req_emb)
            max_sim = float(np.max(sims))
            best_idx = int(np.argmax(sims))
            best_sentence = sentences[best_idx].strip()

            if best_sentence:
                matched_sections.append(
                    best_sentence[:300] + ("..." if len(best_sentence) > 300 else "")
                )

        # ===== Keyword coverage (tiny bonus) =====
        keyword_match_count = 0
        if req_keywords:
            for keyword in req_keywords:
                if keyword and keyword in full_text_lower:
                    keyword_match_count += 1

        keyword_coverage = (
            keyword_match_count / len(req_keywords) if req_keywords else 0.0
        )

        # A tiny boost if many requirement keywords appear anywhere
        keyword_boost = 0.1 * keyword_coverage  # max +0.1

        # ===== Fuzzy similarity as backup =====
        fuzzy_sim = 0.0
        if best_sentence:
            fuzzy_sim = self._calculate_similarity(
                req_text_lower, best_sentence.lower()
            )

        fuzzy_boost = 0.05 * fuzzy_sim  # very small influence

        # ===== Total confidence =====
        total_confidence = max_sim + keyword_boost + fuzzy_boost
        total_confidence = max(0.0, min(1.0, total_confidence))

        # ===== Decide status based on simple thresholds =====
        if max_sim >= self.met_threshold or total_confidence >= (self.met_threshold + 0.05):
            status = "met"
            reasoning = (
                f"Best semantic similarity {max_sim:.2f} with a proposal sentence. "
                f"Keywords matched: {keyword_match_count}/{len(req_keywords)}. "
                f"Fuzzy similarity {fuzzy_sim:.2f}."
            )
        elif max_sim >= self.partial_threshold or total_confidence >= (self.partial_threshold + 0.05):
            status = "partial"
            reasoning = (
                f"Moderate semantic similarity {max_sim:.2f}. "
                f"Some relation to the requirement, but not fully aligned."
            )
        else:
            status = "missing"
            reasoning = (
                f"Low semantic similarity {max_sim:.2f}. "
                f"Requirement not clearly addressed in the proposal."
            )

        return ComplianceResult(
            req_id=requirement.req_id,
            requirement_text=requirement.requirement_text,
            status=status,
            confidence_score=round(total_confidence, 3),
            matched_sections=matched_sections[:3],
            reasoning=reasoning,
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate rough string similarity."""
        return SequenceMatcher(None, text1, text2).ratio()
