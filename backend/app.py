"""
Enhanced FastAPI Application for Tender Evaluation System
Comprehensive API with document processing, vendor evaluation, and chatbot functionality
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any, Optional
import uvicorn
import os
import tempfile
import asyncio
import logging
from datetime import datetime

# Import our enhanced modules
from backend.chatbot.retriever import retriever, get_relevant_chunks
from backend.chatbot.llm_chain import llm_chain, generate_answer, analyze_tender_document, evaluate_vendor
from backend.ingestion.ocr_extraction import ocr_processor, process_document
from backend.ingestion.text_cleaning import text_cleaner, clean_text_advanced
from backend.ingestion.vector_store import vector_store, add_document_to_store
from backend.scoring.vendor_scoring import vendor_scorer, evaluate_vendor_comprehensive
from backend.utils.helpers import (
    ResponseFormatter, TenderUtils, ValidationUtils, 
    DocumentProcessor, format_answer
)
from backend.config import *

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Enhanced Tender Evaluation Chatbot",
    description="AI-powered tender evaluation system with document processing and vendor assessment",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class QuestionRequest(BaseModel):
    question: str
    tender_id: Optional[str] = None
    include_context: bool = True

class VendorEvaluationRequest(BaseModel):
    vendor_data: Dict[str, Any]
    tender_requirements: Dict[str, Any]
    context_data: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    processing_status: str

class EvaluationResponse(BaseModel):
    vendor_name: str
    overall_score: float
    weighted_score: float
    recommendation: str
    detailed_scores: Dict[str, Any]

# Global state management
app_state = {
    "total_documents": 0,
    "total_evaluations": 0,
    "last_activity": datetime.now().isoformat()
}

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("🚀 Starting Enhanced Tender Evaluation System")
    
    # Initialize components
    try:
        # Test LLM connection
        test_response = await asyncio.to_thread(
            generate_answer, 
            "Test question", 
            ["Test context"]
        )
        logger.info("✅ LLM connection successful")
        
        # Load existing vector store statistics
        stats = vector_store.get_statistics()
        app_state["total_documents"] = stats.get("total_documents", 0)
        logger.info(f"📚 Loaded {app_state['total_documents']} documents from vector store")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return ResponseFormatter.format_success_response({
        "message": "Enhanced Tender Evaluation Chatbot Backend",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Document Processing (PDF, Images, Text)",
            "AI-Powered Q&A",
            "Vendor Evaluation",
            "Multi-criteria Scoring",
            "Risk Assessment",
            "Vector Search",
            "Cross-encoder Reranking"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "ask": "/ask",
            "upload": "/upload-document",
            "evaluate": "/evaluate-vendor"
        },
        "statistics": app_state
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test core components
        vector_stats = vector_store.get_statistics()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "vector_store": "operational" if vector_stats else "warning",
                "llm_chain": "operational",
                "document_processor": "operational",
                "vendor_scorer": "operational"
            },
            "statistics": {
                "documents_indexed": vector_stats.get("active_chunks", 0),
                "total_evaluations": app_state["total_evaluations"],
                "last_activity": app_state["last_activity"]
            }
        }
        
        return ResponseFormatter.format_success_response(health_status)
        
    except Exception as e:
        return ResponseFormatter.format_error_response(f"Health check failed: {str(e)}")

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask question with enhanced context retrieval"""
    try:
        app_state["last_activity"] = datetime.now().isoformat()
        
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Get relevant context
        if request.include_context:
            context_chunks = get_relevant_chunks(
                request.question, 
                tender_id=request.tender_id
            )
        else:
            context_chunks = []
        
        # Generate answer
        answer = await asyncio.to_thread(
            generate_answer,
            request.question,
            context_chunks,
            {"tender_id": request.tender_id} if request.tender_id else None
        )
        
        # Format response
        formatted_answer = format_answer(answer)
        
        response_data = {
            "question": request.question,
            "answer": formatted_answer,
            "context_used": len(context_chunks) > 0,
            "context_chunks_count": len(context_chunks),
            "tender_id": request.tender_id
        }
        
        if DEBUG_MODE:
            response_data["debug_info"] = {
                "context_chunks": context_chunks[:3],  # First 3 for debugging
                "raw_answer": answer
            }
        
        return ResponseFormatter.format_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return ResponseFormatter.format_error_response(str(e))

@app.post("/upload-document")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tender_id: str = Form(None),
    document_type: str = Form("general"),
    description: str = Form("")
):
    """Upload and process document with enhanced processing"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not TenderUtils.validate_file_type(file.filename, SUPPORTED_FILE_TYPES):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {SUPPORTED_FILE_TYPES}"
            )
        
        # Check file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB"
            )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process document
            logger.info(f"Processing document: {file.filename}")
            document_result = await asyncio.to_thread(
                ocr_processor.extract_text_from_file,
                tmp_file_path
            )
            
            if not document_result.get('text'):
                raise HTTPException(status_code=400, detail="Could not extract text from document")
            
            # Clean text
            cleaning_result = await asyncio.to_thread(
                text_cleaner.clean_text_comprehensive,
                document_result['text']
            )
            
            cleaned_text = cleaning_result['cleaned_text']
            
            # Generate document ID and metadata
            document_id = TenderUtils.generate_tender_id("DOC")
            
            metadata = {
                'document_id': document_id,
                'filename': file.filename,
                'tender_id': tender_id or 'general',
                'document_type': document_type,
                'description': description,
                'upload_timestamp': datetime.now().isoformat(),
                'file_size': len(content),
                'processing_confidence': document_result.get('confidence', 0.0),
                'extracted_entities': cleaning_result.get('extracted_entities', {}),
                'content_statistics': cleaning_result.get('statistics', {})
            }
            
            # Add to vector store in background
            background_tasks.add_task(
                add_document_to_vector_store,
                cleaned_text,
                metadata
            )
            
            # Update app state
            app_state["total_documents"] += 1
            app_state["last_activity"] = datetime.now().isoformat()
            
            response_data = {
                "message": "Document uploaded and processing initiated",
                "document_id": document_id,
                "filename": file.filename,
                "processing_status": "completed",
                "text_length": len(cleaned_text),
                "confidence": document_result.get('confidence', 0.0),
                "extracted_entities": cleaning_result.get('extracted_entities', {}),
                "document_metadata": metadata
            }
            
            return ResponseFormatter.format_success_response(response_data)
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        return ResponseFormatter.format_error_response(str(e))

@app.post("/evaluate-vendor")
async def evaluate_vendor_endpoint(request: VendorEvaluationRequest):
    """Comprehensive vendor evaluation"""
    try:
        app_state["last_activity"] = datetime.now().isoformat()
        
        # Validate input data
        vendor_errors = ValidationUtils.validate_vendor_data(request.vendor_data)
        tender_errors = ValidationUtils.validate_tender_requirements(request.tender_requirements)
        
        if vendor_errors or tender_errors:
            return ResponseFormatter.format_validation_error(vendor_errors + tender_errors)
        
        logger.info(f"Evaluating vendor: {request.vendor_data.get('vendor_name', 'Unknown')}")
        
        # Perform evaluation
        evaluation = await asyncio.to_thread(
            vendor_scorer.evaluate_vendor_comprehensive,
            request.vendor_data,
            request.tender_requirements,
            request.context_data
        )
        
        # Export detailed report
        detailed_report = vendor_scorer.export_evaluation_report(evaluation)
        
        # Update app state
        app_state["total_evaluations"] += 1
        
        response_data = {
            "evaluation_summary": {
                "vendor_name": evaluation.vendor_name,
                "overall_score": evaluation.overall_score,
                "weighted_score": evaluation.weighted_score,
                "recommendation": evaluation.recommendation,
                "risk_level": evaluation.risk_level.value,
                "compliance_status": evaluation.compliance_status.value
            },
            "detailed_report": detailed_report,
            "evaluation_timestamp": evaluation.evaluation_timestamp
        }
        
        return ResponseFormatter.format_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error evaluating vendor: {e}")
        return ResponseFormatter.format_error_response(str(e))

@app.post("/analyze-tender-document")
async def analyze_tender_document_endpoint(
    file: UploadFile = File(...),
    requirements: str = Form("{}")
):
    """Analyze tender document for compliance and extract key information"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Parse requirements
        try:
            tender_requirements = eval(requirements) if requirements else {}
        except:
            tender_requirements = {}
        
        # Process document
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract text
            document_result = await asyncio.to_thread(
                ocr_processor.extract_text_from_file,
                tmp_file_path
            )
            
            # Analyze with LLM
            analysis = await asyncio.to_thread(
                analyze_tender_document,
                document_result['text'],
                tender_requirements
            )
            
            return ResponseFormatter.format_success_response(analysis)
            
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Error analyzing tender document: {e}")
        return ResponseFormatter.format_error_response(str(e))

@app.get("/statistics")
async def get_system_statistics():
    """Get comprehensive system statistics"""
    try:
        vector_stats = vector_store.get_statistics()
        retriever_stats = retriever.get_document_statistics()
        
        stats = {
            "system": app_state,
            "vector_store": vector_stats,
            "retriever": retriever_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        return ResponseFormatter.format_success_response(stats)
        
    except Exception as e:
        return ResponseFormatter.format_error_response(str(e))

@app.post("/search-documents")
async def search_documents(
    query: str = Form(...),
    top_k: int = Form(5),
    tender_id: str = Form(None),
    document_type: str = Form(None)
):
    """Search documents with filters"""
    try:
        filter_criteria = {}
        if tender_id:
            filter_criteria['tender_id'] = tender_id
        if document_type:
            filter_criteria['document_type'] = document_type
        
        results = retriever.semantic_search(
            query,
            top_k=top_k,
            filter_criteria=filter_criteria
        )
        
        return ResponseFormatter.format_success_response({
            "query": query,
            "results_count": len(results),
            "results": results
        })
        
    except Exception as e:
        return ResponseFormatter.format_error_response(str(e))

# Background task functions
async def add_document_to_vector_store(text: str, metadata: Dict[str, Any]):
    """Background task to add document to vector store"""
    try:
        chunks = DocumentProcessor.chunk_text_intelligently(text)
        
        for chunk in chunks:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk['chunk_id'],
                'is_complete_chunk': chunk['is_complete']
            })
            
            vector_store.add_document(chunk['content'], chunk_metadata)
        
        logger.info(f"Added {len(chunks)} chunks to vector store for document {metadata['document_id']}")
        
    except Exception as e:
        logger.error(f"Background task error: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseFormatter.format_error_response(exc.detail, f"HTTP_{exc.status_code}")
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=ResponseFormatter.format_validation_error([str(error) for error in exc.errors()])
    )

# Main execution
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG_MODE,
        log_level=LOG_LEVEL.lower()
    )
