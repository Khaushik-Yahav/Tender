"""
extractor.py
FAISS RAG Requirements Extractor - TOKEN-SAFE + ROBUST JSON SALVAGE
"""

import json
import re
from typing import List

from sentence_transformers import SentenceTransformer
from groq import Groq
from models import Requirement
import numpy as np
import faiss


class Extractor:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if not api_key:
            raise ValueError("API key required")

        self.client = Groq(api_key=api_key)
        self.model = model

        print("📥 Loading embedding model...")
        self.emb_model = SentenceTransformer("all-MiniLM-L6-v2")
        dim = self.emb_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(dim)
        print("✅ Extractor ready")

    # ------------------------------------------------------------------ #
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------ #
    def extract(self, text: str) -> List[Requirement]:
        """
        Main extraction pipeline.

        1. Chunk the full tender text
        2. Use embeddings + queries to retrieve relevant chunks (RAG)
        3. Add all requirement-like sentences (shall/must/required/…)
        4. Ask LLM to extract structured requirements
        5. Fallback with truncated full doc if needed
        6. Deduplicate and assign REQ IDs
        """
        print(f"\n{'=' * 70}")
        print("🎯 EXTRACTING REQUIREMENTS (RAG + RULE-BASED)")
        print(f"{'=' * 70}\n")

        # 1) Chunk
        chunks = self._chunk(text)
        print(f"✅ Created {len(chunks)} chunks")

        if not chunks:
            return []

        # 2) Embed chunks once
        embeds = self.emb_model.encode(chunks, convert_to_numpy=True)
        self.index.reset()
        self.index.add(np.array(embeds, dtype=np.float32))

        # 3) RAG queries tuned for all requirement types
        queries = [
            # Submission / admin
            "submission requirements language validity oracle system deadlines communications",
            # Technical + scope
            "technical requirements scope of work deliverables platform development implementation methodology workplan timelines",
            # Financial / commercial
            "financial proposal fees reimbursable expenses taxes currency usd exchange rate payment terms",
            # Eligibility / organisation
            "eligibility criteria company profile experience qualifications certifications accreditations key staff cvs",
            # Compliance / policies / legal
            "compliance ethics code of conduct data protection confidentiality environmental social safeguarding whistleblower anti corruption sexual harassment",
            # Evaluation rules
            "evaluation criteria scoring mandatory requirements two stage evaluation multiattribute ranking technical financial opening of financial proposals",
            # Contractual obligations
            "consultant obligations scope of services time frame reports contract period services shall",
        ]

        rel_chunks = set()
        for q in queries:
            q_emb = self.emb_model.encode(q, convert_to_numpy=True)
            # fewer chunks per query to keep context small
            _, idx = self.index.search(np.array([q_emb], dtype=np.float32), k=3)
            for i in idx[0]:
                if 0 <= i < len(chunks):
                    rel_chunks.add(chunks[i])

        # 4) Add all requirement-like sentences (rule-based)
        requirement_sentences = self._extract_requirement_like_sentences(text)
        print(f"✅ Found {len(requirement_sentences)} requirement-like sentences (rule-based)")

        # Build final context: relevant chunks + requirement sentences
        rel_text_parts = list(rel_chunks)
        if requirement_sentences:
            rel_text_parts.append("\n".join(requirement_sentences))

        rel_text = "\n\n".join(rel_text_parts)

        # 🔒 HARD LIMIT on context size to avoid Groq token/TPM errors
        MAX_CHARS = 30000  # ~7000 tokens, safe under 12k TPM
        if len(rel_text) > MAX_CHARS:
            print(
                f"⚠️ Truncating context from {len(rel_text)} to {MAX_CHARS} chars "
                "to avoid token limit..."
            )
            rel_text = rel_text[:MAX_CHARS]

        print(f"✅ Relevant text length sent to LLM: {len(rel_text)} chars\n")

        # 5) Call LLM on focused text
        print("🤖 Calling LLM (focused RAG context)...")
        reqs = self._llm_extract(rel_text)

        # 6) Fallback: if the focused context fails, try with truncated full doc
        if not reqs:
            print("⚠️ LLM returned 0 requirements, trying fallback with full document...")
            fallback_text = text[:20000]  # extra safety
            reqs = self._llm_extract_fallback(fallback_text)

        # 7) Deduplicate and assign IDs
        reqs = self._dedup(reqs)
        for i, r in enumerate(reqs, 1):
            r.req_id = f"REQ{i:03d}"

        print(f"✅ Final: {len(reqs)} requirements\n")
        return reqs

    # ------------------------------------------------------------------ #
    # CHUNKING & REQUIREMENT-SENTENCE MINING
    # ------------------------------------------------------------------ #
    def _chunk(self, text: str) -> List[str]:
        """Chunk text into ~1000–1500 char blocks by paragraphs."""
        paras = text.split("\n\n")
        chunks, curr = [], ""
        max_len = 1500

        for p in paras:
            if len(curr) + len(p) <= max_len:
                curr += p + "\n\n"
            else:
                if curr.strip():
                    chunks.append(curr.strip())
                curr = p + "\n\n"

        if curr.strip():
            chunks.append(curr.strip())

        # Filter out tiny chunks
        return [c for c in chunks if len(c) > 100]

    def _extract_requirement_like_sentences(self, text: str) -> List[str]:
        """
        Collect sentences that *look like* requirements to make sure
        we don't miss compliance / legal / scope clauses.

        Heuristics: sentence length + presence of modal verbs like
        shall, must, required, mandatory, will, should, is to, are to.
        """
        requirement_markers = [
            "shall",
            "must",
            "required to",
            "is required to",
            "are required to",
            "mandatory",
            "should",
            "need to",
            "needs to",
            "has to",
            "have to",
            "will be",
            "will not",
            "is to",
            "are to",
        ]

        # Simple sentence split on punctuation
        raw_sentences = re.split(r"(?<=[\.\?\!])\s+", text)
        candidates = []

        for s in raw_sentences:
            sent = s.strip()
            if len(sent) < 40:
                continue
            lower = sent.lower()
            if any(m in lower for m in requirement_markers):
                candidates.append(sent)

        # De-duplicate and cap to a reasonable number
        unique: List[str] = []
        seen = set()
        for s in candidates:
            if s not in seen:
                seen.add(s)
                unique.append(s)
            # limit sentences so we don't blow up context
            if len(unique) >= 40:
                break

        return unique

    # ------------------------------------------------------------------ #
    # LLM CALLS
    # ------------------------------------------------------------------ #
    def _llm_extract(self, text: str) -> List[Requirement]:
        """Extract requirements from a focused RAG context."""
        sys_msg = """
You are a senior public procurement expert.

From the given tender/RFP text, extract ALL explicit, atomic REQUIREMENTS that a bidder
or consultant must comply with. Include:

- Submission & administrative requirements (language, portal, deadlines, validity, communications, etc.)
- Technical requirements and scope of work (platform features, deliverables, reports, methodologies, timelines, etc.)
- Financial & commercial requirements (fees, reimbursables, taxes, currency, exchange rates, payment terms, etc.)
- Eligibility / qualification requirements (experience, references, certifications, key staff CVs, etc.)
- Compliance / policy / legal obligations (code of conduct, ethics, data protection, safeguarding, ESHS, whistleblower, confidentiality, applicable law, anti-corruption, sexual harassment, etc.)
- Evaluation rules that affect qualification (two-stage evaluation, mandatory vs optional, conditions for financial opening).
- Contractual obligations on the consultant (scope of services, reporting, time frame).

RULES:
- Do NOT include generic introductions, definitions, or background text.
- Each requirement must be a single clear obligation or rule, written as one sentence.
- If non-compliance clearly disqualifies or contradicts the tender, mark it as mandatory = true.
- Use the following categories when possible:
  ["Technical","Financial","Administrative","Compliance","Scope","Evaluation","Eligibility","Timeline","Other"].
- RETURN ONLY RAW JSON. DO NOT wrap it in ``` fences or any markdown.
- The JSON must have a top-level key "requirements" which is a list.
- Return at most 40 requirements, picking the most important and explicit ones.

Format exactly:

{
  "requirements": [
    {
      "requirement_text": "<full requirement sentence>",
      "category": "Technical | Financial | Administrative | Compliance | Scope | Evaluation | Eligibility | Timeline | Other",
      "mandatory": true or false,
      "keywords": ["short key phrase 1", "phrase 2"]
    }
  ]
}
""".strip()

        user_msg = (
            "Extract ALL important requirements from this tender text (max 40). Include "
            "submission, technical, financial, eligibility, compliance/policy, scope and evaluation rules.\n\n"
            f"{text}\n\nReturn ONLY valid JSON as specified. No markdown, no explanation."
        )

        try:
            print("   📤 Sending to Groq (main extractor)...")
            resp = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1600,
            )

            content = resp.choices[0].message.content

            if not content or not content.strip():
                print("   ❌ Empty response from LLM")
                return []

            print(f"   📥 Raw LLM response (first 120 chars): {content[:120]}...")

            data = self._safe_json_loads(content)
            if data is None:
                print("   ❌ Could not parse JSON from LLM response")
                return []

            return self._build_requirements_from_json(data)

        except Exception as e:
            print(f"   ❌ LLM error: {type(e).__name__}: {e}")
            return []

    def _llm_extract_fallback(self, text: str) -> List[Requirement]:
        """Fallback: simpler extraction using truncated full document."""
        sys_msg = """
You are a procurement expert.

From this tender/RFP text, extract all requirements in the same JSON structure as before.
Cover submission, technical, financial, eligibility, compliance, scope, and evaluation rules.

Return ONLY raw JSON with a top-level 'requirements' array. Do NOT use markdown fences.
Return at most 40 requirements.
""".strip()

        user_msg = f"Tender text (possibly truncated):\n\n{text}\n\nExtract requirements and return only JSON."

        try:
            print("   📤 Fallback: Sending to Groq...")
            resp = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1600,
            )

            content = resp.choices[0].message.content

            if not content or not content.strip():
                print("   ⚠️ Fallback: Empty response")
                return []

            print(f"   📥 Fallback LLM response (first 120 chars): {content[:120]}...")

            data = self._safe_json_loads(content)
            if data is None:
                print("   ⚠️ Fallback: No valid JSON")
                return []

            return self._build_requirements_from_json(data)

        except Exception as e:
            print(f"   ⚠️ Fallback error: {type(e).__name__}: {e}")
            return []

    # ------------------------------------------------------------------ #
    # JSON PARSING + REQUIREMENT OBJECT CREATION
    # ------------------------------------------------------------------ #
    def _safe_json_loads(self, content: str):
        """
        Try hard to load JSON from the LLM response, even if:
        - Wrapped in ``` or ```json fences
        - Surrounded by text
        - Has trailing commas
        - Overall array is partially broken (salvage objects)
        """
        text = content.strip()

        # Remove ```json / ``` fences anywhere
        text = text.replace("```json", "```")
        text = text.replace("```JSON", "```")
        # strip leading/trailing fences
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Extract from first '{' to last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        json_str = text[start : end + 1]

        # First attempt: direct parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Second attempt: remove trailing commas before } or ]
        json_str_clean = re.sub(r",(\s*[}\]])", r"\1", json_str)
        try:
            return json.loads(json_str_clean)
        except json.JSONDecodeError:
            pass

        # Third attempt: SALVAGE individual requirement objects
        print("   ⚠️ Whole JSON invalid, attempting to salvage individual requirement objects...")
        objects = []
        for match in re.finditer(
            r"\{[^{}]*\"requirement_text\"[^{}]*\}", json_str_clean, re.DOTALL
        ):
            obj_str = match.group()
            # remove trailing commas inside the object
            obj_str_clean = re.sub(r",(\s*[}\]])", r"\1", obj_str)
            try:
                obj = json.loads(obj_str_clean)
                objects.append(obj)
            except json.JSONDecodeError:
                continue

        if objects:
            print(f"   ✅ Salvaged {len(objects)} requirement objects from malformed JSON")
            return {"requirements": objects}

        return None

    def _build_requirements_from_json(self, data) -> List[Requirement]:
        """Convert parsed JSON into a list of Requirement objects."""
        reqs: List[Requirement] = []

        items = data.get("requirements", [])
        if not isinstance(items, list):
            print("   ⚠️ 'requirements' is not a list in JSON")
            return reqs

        for r in items:
            if not isinstance(r, dict):
                continue

            # Try multiple possible keys for the text
            req_text = (
                r.get("requirement_text")
                or r.get("description")
                or r.get("text")
                or ""
            )
            req_text = str(req_text).strip()
            if len(req_text) <= 20:
                continue

            # Category: accept 'category' or 'type'
            category = r.get("category") or r.get("type") or "Other"
            category = str(category)

            # Mandatory: accept 'mandatory' or 'is_mandatory'; default heuristic
            if "mandatory" in r:
                mandatory = bool(r.get("mandatory"))
            elif "is_mandatory" in r:
                mandatory = bool(r.get("is_mandatory"))
            else:
                lower = req_text.lower()
                mandatory = any(
                    kw in lower for kw in ["must", "shall", "required", "mandatory"]
                )

            # Keywords
            keywords = r.get("keywords") or []
            if not isinstance(keywords, list):
                keywords = [str(keywords)]
            keywords = [str(k) for k in keywords][:5]

            reqs.append(
                Requirement(
                    req_id="",
                    requirement_text=req_text,
                    category=category,
                    mandatory=mandatory,
                    keywords=keywords,
                )
            )

        print(f"   ✅ Parsed {len(reqs)} requirements from JSON")
        return reqs

    # ------------------------------------------------------------------ #
    # DEDUPLICATION
    # ------------------------------------------------------------------ #
    def _dedup(self, reqs: List[Requirement]) -> List[Requirement]:
        """Remove duplicate or near-duplicate requirement texts."""
        seen = set()
        unique: List[Requirement] = []

        for r in reqs:
            t = r.requirement_text.lower().strip()
            if len(t) <= 20:
                continue
            if t not in seen:
                seen.add(t)
                unique.append(r)

        return unique
