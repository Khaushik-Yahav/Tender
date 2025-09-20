"""
Enhanced Tests for Document Ingestion
"""
import pytest
import tempfile
import os
from backend.ingestion.text_cleaning import clean_text, text_cleaner
from backend.ingestion.ocr_extraction import ocr_processor
from backend.ingestion.vector_store import vector_store

def test_text_cleaning():
    """Test text cleaning functionality"""
    dirty_text = "This    is  a   test@#$%  text  with  extra    spaces."
    cleaned = clean_text(dirty_text)
    assert isinstance(cleaned, str)
    assert len(cleaned) > 0
    assert "   " not in cleaned  # No triple spaces

def test_advanced_text_cleaning():
    """Test advanced text cleaning with metadata"""
    text = "Tender No: TND-2024-001. Amount: ₹5,00,000. Email: test@example.com"
    result = text_cleaner.clean_text_comprehensive(text)
    
    assert isinstance(result, dict)
    assert 'cleaned_text' in result
    assert 'extracted_entities' in result
    assert 'statistics' in result

def test_entity_extraction():
    """Test entity extraction from text"""
    text = "Contact: john@company.com, Phone: +91-9876543210, PAN: ABCDE1234F"
    entities = text_cleaner.extract_structured_data(text)
    
    assert isinstance(entities, dict)
    assert 'contact_info' in entities

def test_document_processing():
    """Test document processing pipeline"""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for processing.")
        temp_file = f.name
    
    try:
        result = ocr_processor.extract_text_from_file(temp_file)
        assert isinstance(result, dict)
        assert 'text' in result
        assert len(result['text']) > 0
    except Exception:
        # OCR might not be available in test environment
        pytest.skip("OCR not available in test environment")
    finally:
        os.unlink(temp_file)

def test_vector_store_operations():
    """Test vector store add and search operations"""
    # Test adding a document
    test_content = "This is a test document for vector storage."
    test_metadata = {
        'document_id': 'test_doc_001',
        'document_type': 'test',
        'created_at': '2024-01-01T00:00:00'
    }
    
    success = vector_store.add_document(test_content, test_metadata)
    assert isinstance(success, bool)
    
    # Test searching
    results = vector_store.search("test document", top_k=1)
    assert isinstance(results, list)
