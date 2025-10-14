#!/usr/bin/env python3
"""
tender_analyzer_local.py
Tender Analyzer core logic.
Handles file/text extraction, feature scoring, and memory storage.
"""

import os
import json
import time
import random
import fitz              # pymupdf
import pandas as pd
import docx
from typing import Dict, Optional

# -------------------------
# Memory
# -------------------------
TENDER_MEMORY_FILE = "tender_memory.json"
TENDER_MEMORY = []

def load_memory():
    global TENDER_MEMORY
    if os.path.exists(TENDER_MEMORY_FILE):
        try:
            with open(TENDER_MEMORY_FILE, "r") as f:
                TENDER_MEMORY = json.load(f)
            print(f"💾 Loaded {len(TENDER_MEMORY)} tenders from memory.")
        except Exception:
            print("⚠️ Could not load memory file, starting fresh.")
            TENDER_MEMORY = []

def save_tender_to_memory(filename: str, features: Dict[str, float], score: float):
    entry = {
        "filename": filename,
        "features": features,
        "final_score": score,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    TENDER_MEMORY.append(entry)
    try:
        with open(TENDER_MEMORY_FILE, "w") as f:
            json.dump(TENDER_MEMORY, f, indent=2)
    except Exception as e:
        print("⚠️ Could not write memory file:", e)

# -------------------------
# File/Text Extraction
# -------------------------
def extract_text_from_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    text = ""
    try:
        if ext == ".pdf":
            with fitz.open(filepath) as doc:
                text = "".join([page.get_text() for page in doc])
        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif ext == ".csv":
            df = pd.read_csv(filepath)
            text = df.to_string()
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)
            text = df.to_string()
        elif ext == ".docx":
            doc_file = docx.Document(filepath)
            text = "\n".join([p.text for p in doc_file.paragraphs])
        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        print(f"❌ Error reading file {filepath}: {e}")
    return text

# -------------------------
# Feature Extraction (Mock)
# -------------------------
def extract_features_mock(text: str) -> Dict[str, float]:
    random.seed(min(999999, len(text)))
    return {
        "technical_clarity": round(random.uniform(0.6, 0.95), 3),
        "pricing_transparency": round(random.uniform(0.5, 0.9), 3),
        "timeline_feasibility": round(random.uniform(0.5, 0.95), 3),
        "scope_similarity_score": round(random.uniform(0.4, 0.95), 3),
        "compliance_adherence": round(random.uniform(0.6, 0.9), 3),
        "risk_mitigation": round(random.uniform(0.5, 0.9), 3),
        "topic_coverage_score": round(random.uniform(0.5, 0.9), 3),
    }

# -------------------------
# Compute final score & ranking
# -------------------------
def compute_final_score(features: Dict[str, float]) -> float:
    weights = {
        "technical_clarity": 0.20,
        "pricing_transparency": 0.10,
        "timeline_feasibility": 0.15,
        "scope_similarity_score": 0.20,
        "compliance_adherence": 0.10,
        "risk_mitigation": 0.10,
        "topic_coverage_score": 0.15,
    }
    score = sum(features.get(k, 0) * w for k, w in weights.items()) * 100
    return round(score, 2)

def compute_relative_rank(score: float):
    if not TENDER_MEMORY:
        return 100.0, 1, 1
    scores = [t["final_score"] for t in TENDER_MEMORY] + [score]
    scores.sort(reverse=True)
    rank = scores.index(score) + 1
    percentile = 100 * (1 - (rank - 1) / len(scores))
    return percentile, rank, len(scores)

# -------------------------
# Analyze tender
# -------------------------
def analyze_tender(filepath: str):
    filename = os.path.basename(filepath)
    print(f"\n📂 Reading {filename}...")
    text = extract_text_from_file(filepath)
    if not text.strip():
        print("❌ No readable text found. Skipping.")
        return
    features = extract_features_mock(text)
    final_score = compute_final_score(features)
    save_tender_to_memory(filename, features, final_score)
    print(f"✅ '{filename}' analyzed with score {final_score}")

def analyze_tender_text(filename: str, text_content: str):
    text = text_content.strip()
    if not text:
        print("❌ No readable text provided. Skipping.")
        return
    features = extract_features_mock(text)
    final_score = compute_final_score(features)
    save_tender_to_memory(filename, features, final_score)
    print(f"✅ '{filename}' analyzed from text input with score {final_score}")
