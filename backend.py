from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil, os
from tender_analyzer_local import (
    TENDER_MEMORY, 
    compute_relative_rank, 
    extract_text_from_file, 
    extract_features_mock, 
    compute_final_score,
    save_tender_to_memory
)

app = FastAPI()

# Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_tender_file(filename, text_content):
    """
    Analyze tender from raw text content.
    """
    # Extract features
    features = extract_features_mock(text_content)

    # Compute final score
    final_score = compute_final_score(features)

    # Save to memory using the original function
    save_tender_to_memory(filename, features, final_score)

@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract text from the uploaded file (handles PDF, DOCX, TXT, Excel)
        text = extract_text_from_file(filepath)

        # Analyze tender
        analyze_tender_file(file.filename, text)

        # Get the last added tender
        last_tender = TENDER_MEMORY[-1]
        percentile, rank, total = compute_relative_rank(last_tender["final_score"])

        return {
            "filename": last_tender["filename"],
            "features": last_tender["features"],
            "final_score": last_tender["final_score"],
            "rank": rank,
            "percentile": percentile
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/tenders")
def get_all_tenders():
    return TENDER_MEMORY
