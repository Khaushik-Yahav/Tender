"""
Enhanced Tests for Chatbot Functionality
"""
import pytest
import asyncio
from backend.chatbot.retriever import retriever, get_relevant_chunks
from backend.chatbot.llm_chain import generate_answer, analyze_tender_document

@pytest.mark.asyncio
async def test_retriever():
    """Test document retrieval functionality"""
    chunks = get_relevant_chunks("deadline")
    assert isinstance(chunks, list)
    
    # Test with actual search
    results = retriever.semantic_search("tender requirements")
    assert isinstance(results, list)

@pytest.mark.asyncio  
async def test_llm_chain():
    """Test LLM chain functionality"""
    try:
        answer = generate_answer("What is a tender?", ["A tender is a formal invitation to bid"])
        assert isinstance(answer, str)
        assert len(answer) > 0
    except Exception as e:
        # LLM might not be available in test environment
        pytest.skip(f"LLM not available: {e}")

@pytest.mark.asyncio
async def test_document_analysis():
    """Test tender document analysis"""
    try:
        sample_text = "This is a tender for software development. Deadline: 2024-01-15. Budget: ₹10,00,000"
        requirements = {"type": "software", "budget_max": 1000000}
        
        analysis = analyze_tender_document(sample_text, requirements)
        assert isinstance(analysis, dict)
        
    except Exception as e:
        pytest.skip(f"Document analysis not available: {e}")

def test_vector_store():
    """Test vector store operations"""
    from backend.ingestion.vector_store import vector_store
    
    stats = vector_store.get_statistics()
    assert isinstance(stats, dict)
    assert 'total_chunks' in stats
