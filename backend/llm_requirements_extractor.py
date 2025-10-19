import json
from typing import List
from groq import Groq
from models import Requirement

class LLMRequirementsExtractor:
    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile"):
        if not api_key:
            raise ValueError("API key is required for LLM extraction")
        # Only use api_key
        self.client = Groq(api_key=api_key)
        self.model = model
        print(f"✅ LLM Requirements Extractor initialized (model: {self.model})")

    def extract_requirements(self, document_text: str, max_chunk_size: int = 10000) -> List[Requirement]:
        print(f"\n🤖 LLM REQUIREMENTS EXTRACTION (Groq)")
        chunks = self._split_text(document_text, max_chunk_size)
        all_requirements = []
        for idx, chunk in enumerate(chunks, 1):
            chunk_reqs = self._extract_from_chunk(chunk, idx)
            all_requirements.extend(chunk_reqs)
        unique_requirements = self._deduplicate_requirements(all_requirements)
        for idx, req in enumerate(unique_requirements, 1):
            req.req_id = f"REQ{idx:03d}"
        print(f"✅ Total deduplicated requirements: {len(unique_requirements)}")
        return unique_requirements

    def _split_text(self, text: str, max_size: int) -> List[str]:
        if len(text) <= max_size:
            return [text]
        chunks = []
        current_chunk = ""
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para + "\n\n"
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _extract_from_chunk(self, text_chunk: str, chunk_num: int) -> List[Requirement]:
        system_prompt = """You are an expert procurement analyst specializing in government tender analysis. 
Your task is to extract ONLY the specific, actionable requirements that vendors must fulfill.

STRICT RULES:
1. Extract ONLY requirements containing: must, shall, required, should, need to
2. Each requirement must be a complete, standalone statement
3. DO NOT extract:
   - Background information or context
   - Administrative procedures (like "submit by date")
   - General descriptions
   - Headings or titles
   - Contact information
4. Focus on extracting:
   - Technical specifications (performance, capacity, standards)
   - Qualification criteria (experience, certifications)
   - Compliance requirements (certifications, standards)
   - Eligibility criteria (turnover, years in business)
   - Quality standards (ISO, industry standards)

Return ONLY valid JSON in this EXACT format:
{
  "requirements": [
    {
      "requirement_text": "Complete requirement statement",
      "category": "Technical|Financial|Compliance|Eligibility|General",
      "mandatory": true|false,
      "keywords": ["key", "terms"]
    }
  ]
}"""

        user_prompt = f"""Extract the specific requirements from this tender document excerpt.

DOCUMENT TEXT:
{text_chunk}

Return ONLY the JSON response. Be strict - only extract clear, actionable requirements."""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            response_text = chat_completion.choices[0].message.content
            response_data = json.loads(response_text)
            requirements = []
            for req_data in response_data.get("requirements", []):
                req_text = req_data.get("requirement_text", "").strip()
                if len(req_text) < 20:
                    continue
                req = Requirement(
                    req_id="",  # Will be assigned later
                    requirement_text=req_text,
                    category=req_data.get("category", "General"),
                    mandatory=req_data.get("mandatory", True),
                    keywords=req_data.get("keywords", [])
                )
                requirements.append(req)
            return requirements
        except Exception as e:
            print(f"❌ Error from Groq LLM chunk {chunk_num}: {e}")
            return []

    def _deduplicate_requirements(self, requirements: List[Requirement]) -> List[Requirement]:
        if not requirements:
            return []
        unique_reqs = []
        seen_texts = set()
        for req in requirements:
            normalized = req.requirement_text.lower().strip()
            if len(normalized) < 20:
                continue
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique_reqs.append(req)
        return unique_reqs
