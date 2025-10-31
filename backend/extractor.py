"""
extractor.py
FAISS RAG Requirements Extractor - FIXED
"""

import json
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
        self.emb_model = SentenceTransformer('all-MiniLM-L6-v2')
        dim = self.emb_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(dim)
        print(f"✅ Extractor ready")

    def extract(self, text: str) -> List[Requirement]:
        print(f"\n{'='*70}")
        print("🎯 EXTRACTING REQUIREMENTS")
        print(f"{'='*70}\n")
        
        # Chunk
        chunks = self._chunk(text)
        print(f"✅ Created {len(chunks)} chunks")
        
        if not chunks:
            return []
        
        # Embed
        embeds = self.emb_model.encode(chunks, convert_to_numpy=True)
        self.index.add(np.array(embeds, dtype=np.float32))
        
        # Search
        queries = [
            "requirements submission proposal",
            "qualification technical experience",
            "deliverables methodology approach",
            "team personnel resources staff",
            "certification compliance standards",
            "company profile capabilities"
        ]
        
        rel_chunks = set()
        for q in queries:
            q_emb = self.emb_model.encode(q, convert_to_numpy=True)
            _, idx = self.index.search(np.array([q_emb], dtype=np.float32), k=3)
            for i in idx[0]:
                if 0 <= i < len(chunks):
                    rel_chunks.add(chunks[i])
        
        rel_text = "\n\n".join(list(rel_chunks)[:15])
        print(f"✅ Found {len(rel_chunks)} relevant chunks")
        print(f"📝 Relevant text length: {len(rel_text)} chars\n")
        
        # Extract
        print("🤖 Calling LLM...")
        reqs = self._llm_extract(rel_text)
        
        if not reqs:
            print("⚠️ LLM returned 0, trying fallback with full document...")
            reqs = self._llm_extract_fallback(text[:20000])
        
        # Dedup
        reqs = self._dedup(reqs)
        
        for i, r in enumerate(reqs, 1):
            r.req_id = f"REQ{i:03d}"
        
        print(f"✅ Final: {len(reqs)} requirements\n")
        return reqs

    def _chunk(self, text: str) -> List[str]:
        paras = text.split('\n\n')
        chunks, curr = [], ""
        for p in paras:
            if len(curr) + len(p) <= 1000:
                curr += p + "\n\n"
            else:
                if curr.strip():
                    chunks.append(curr.strip())
                curr = p + "\n\n"
        if curr.strip():
            chunks.append(curr.strip())
        return [c for c in chunks if len(c) > 100]

    def _llm_extract(self, text: str) -> List[Requirement]:
        """Extract with better error handling"""
        sys_msg = """You are a procurement expert. Extract ONLY requirements.

Requirements have: must, shall, required, mandatory, should.

Return ONLY valid JSON:
{"requirements": [{"requirement_text": "...", "category": "Technical", "mandatory": true, "keywords": []}]}

If no requirements, return: {"requirements": []}"""
        
        user_msg = f"""From this text, extract only requirements:\n\n{text}\n\nReturn ONLY JSON, no other text."""
        
        try:
            print("   📤 Sending to Groq...")
            resp = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg}
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=3000
            )
            
            content = resp.choices[0].message.content
            
            if not content or not content.strip():
                print(f"   ❌ Empty response from LLM")
                return []
            
            print(f"   📥 Got response: {content[:100]}...")
            
            # Try to extract JSON from response
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try to find JSON in response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print(f"   ❌ No valid JSON found")
                    return []
            
            reqs = []
            for r in data.get("requirements", []):
                req_text = r.get("requirement_text", "").strip()
                if len(req_text) > 20:
                    reqs.append(Requirement(
                        req_id="",
                        requirement_text=req_text,
                        category=r.get("category", "General"),
                        mandatory=r.get("mandatory", True),
                        keywords=r.get("keywords", [])
                    ))
            
            print(f"   ✅ Extracted {len(reqs)} requirements")
            return reqs
            
        except Exception as e:
            print(f"   ❌ LLM error: {type(e).__name__}: {e}")
            return []

    def _llm_extract_fallback(self, text: str) -> List[Requirement]:
        """Fallback: simpler extraction"""
        sys_msg = """Extract requirements from tender document.
Return JSON with requirements list."""
        
        user_msg = f"""Tender:\n\n{text}\n\nExtract requirements. Return JSON only."""
        
        try:
            print("   📤 Fallback: Sending to Groq...")
            resp = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg}
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=3000
            )
            
            content = resp.choices[0].message.content
            
            if not content or not content.strip():
                print(f"   ⚠️ Fallback: Empty response")
                return []
            
            print(f"   📥 Got: {content[:100]}...")
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print(f"   ⚠️ Fallback: No valid JSON")
                    return []
            
            reqs = []
            for r in data.get("requirements", []):
                req_text = r.get("requirement_text", "").strip()
                if len(req_text) > 20:
                    reqs.append(Requirement(
                        req_id="",
                        requirement_text=req_text,
                        category=r.get("category", "General"),
                        mandatory=r.get("mandatory", True),
                        keywords=r.get("keywords", [])
                    ))
            
            print(f"   ✅ Fallback: {len(reqs)} requirements")
            return reqs
            
        except Exception as e:
            print(f"   ⚠️ Fallback error: {type(e).__name__}: {e}")
            return []

    def _dedup(self, reqs: List[Requirement]) -> List[Requirement]:
        seen = set()
        unique = []
        for r in reqs:
            t = r.requirement_text.lower().strip()
            if len(t) > 20 and t not in seen:
                seen.add(t)
                unique.append(r)
        return unique
