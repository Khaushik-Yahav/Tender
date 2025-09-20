"""
Enhanced Retriever for Tender Evaluation System
Incorporates advanced retrieval patterns from medical RAG with tender-specific optimizations
"""
import os
import numpy as np
import pickle
import logging
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
import faiss

from backend.config import (
    EMBEDDING_MODEL_NAME, VECTOR_DB_PATH, TOP_K_RETRIEVAL, 
    SIMILARITY_THRESHOLD, USE_CROSS_ENCODER, CROSS_ENCODER_MODEL, RERANK_TOP_K
)

logger = logging.getLogger(__name__)

class EnhancedRetriever:
    def __init__(self):
        self.embedding_model = None
        self.cross_encoder = None
        self.vector_index = None
        self.document_chunks = []
        self.document_metadata = []
        self._initialize_models()
        self._load_or_create_index()
    
    def _initialize_models(self):
        """Initialize embedding and cross-encoder models"""
        try:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            
            if USE_CROSS_ENCODER:
                logger.info(f"Loading cross-encoder model: {CROSS_ENCODER_MODEL}")
                self.cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        try:
            if os.path.exists(f"{VECTOR_DB_PATH}.index"):
                logger.info("Loading existing FAISS index")
                self.vector_index = faiss.read_index(f"{VECTOR_DB_PATH}.index")
                
                # Load document chunks and metadata
                with open(f"{VECTOR_DB_PATH}_chunks.pkl", 'rb') as f:
                    self.document_chunks = pickle.load(f)
                with open(f"{VECTOR_DB_PATH}_metadata.pkl", 'rb') as f:
                    self.document_metadata = pickle.load(f)
                    
                logger.info(f"Loaded {len(self.document_chunks)} document chunks")
            else:
                logger.info("Creating new FAISS index")
                # Create empty index
                dimension = self.embedding_model.get_sentence_embedding_dimension()
                self.vector_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                
        except Exception as e:
            logger.error(f"Error with FAISS index: {e}")
            # Create empty index as fallback
            dimension = 384  # Default dimension
            self.vector_index = faiss.IndexFlatIP(dimension)
    
    def add_documents(self, chunks: List[str], metadata: List[Dict[str, Any]]):
        """Add document chunks to the vector store"""
        try:
            logger.info(f"Adding {len(chunks)} document chunks to index")
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks, show_progress_bar=True)
            embeddings = embeddings.astype('float32')
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to FAISS index
            self.vector_index.add(embeddings)
            
            # Store chunks and metadata
            self.document_chunks.extend(chunks)
            self.document_metadata.extend(metadata)
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Successfully added documents. Total chunks: {len(self.document_chunks)}")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def _save_index(self):
        """Save FAISS index and associated data to disk"""
        try:
            os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)
            
            faiss.write_index(self.vector_index, f"{VECTOR_DB_PATH}.index")
            
            with open(f"{VECTOR_DB_PATH}_chunks.pkl", 'wb') as f:
                pickle.dump(self.document_chunks, f)
            with open(f"{VECTOR_DB_PATH}_metadata.pkl", 'wb') as f:
                pickle.dump(self.document_metadata, f)
                
            logger.info("FAISS index and data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def semantic_search(self, query: str, top_k: int = TOP_K_RETRIEVAL, 
                       filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search with optional filtering
        """
        try:
            if not self.document_chunks:
                logger.warning("No documents in index")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding.astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS index
            search_k = min(top_k * 3, len(self.document_chunks))  # Get more for reranking
            scores, indices = self.vector_index.search(query_embedding, search_k)
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= len(self.document_chunks):
                    continue
                    
                if score < SIMILARITY_THRESHOLD:
                    continue
                
                result = {
                    'content': self.document_chunks[idx],
                    'metadata': self.document_metadata[idx],
                    'similarity_score': float(score),
                    'index': int(idx)
                }
                
                # Apply filters if provided
                if self._passes_filter(result['metadata'], filter_criteria):
                    results.append(result)
            
            # Rerank using cross-encoder if available
            if USE_CROSS_ENCODER and self.cross_encoder and results:
                results = self._rerank_results(query, results, top_k)
            else:
                results = results[:top_k]
            
            logger.info(f"Retrieved {len(results)} relevant chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _passes_filter(self, metadata: Dict[str, Any], filter_criteria: Optional[Dict[str, Any]]) -> bool:
        """Check if metadata passes filter criteria"""
        if not filter_criteria:
            return True
        
        for key, value in filter_criteria.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder"""
        try:
            if not results:
                return results
            
            # Prepare query-passage pairs for cross-encoder
            pairs = [(query, result['content']) for result in results]
            
            # Get cross-encoder scores
            cross_scores = self.cross_encoder.predict(pairs)
            
            # Update results with cross-encoder scores
            for i, result in enumerate(results):
                result['cross_encoder_score'] = float(cross_scores[i])
            
            # Sort by cross-encoder score and return top_k
            results.sort(key=lambda x: x['cross_encoder_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return results[:top_k]
    
    def get_relevant_chunks(self, query: str, tender_id: Optional[str] = None, 
                          document_type: Optional[str] = None) -> List[str]:
        """
        Get relevant chunks for a query (backward compatibility function)
        """
        # Prepare filter criteria
        filter_criteria = {}
        if tender_id:
            filter_criteria['tender_id'] = tender_id
        if document_type:
            filter_criteria['document_type'] = document_type
        
        results = self.semantic_search(query, filter_criteria=filter_criteria)
        return [result['content'] for result in results]
    
    def search_by_tender_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for documents matching specific tender criteria
        """
        query_parts = []
        
        # Build query from criteria
        if 'technical_requirements' in criteria:
            query_parts.append(f"Technical requirements: {criteria['technical_requirements']}")
        if 'financial_requirements' in criteria:
            query_parts.append(f"Financial requirements: {criteria['financial_requirements']}")
        if 'compliance_requirements' in criteria:
            query_parts.append(f"Compliance requirements: {criteria['compliance_requirements']}")
        
        query = " ".join(query_parts)
        return self.semantic_search(query)
    
    def find_similar_tenders(self, tender_description: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar tender documents based on description
        """
        filter_criteria = {'document_type': 'tender_document'}
        return self.semantic_search(tender_description, top_k=top_k, filter_criteria=filter_criteria)
    
    def search_vendor_information(self, vendor_name: str, criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for vendor-specific information
        """
        query = f"Vendor: {vendor_name}"
        if criteria:
            query += f" {criteria}"
        
        filter_criteria = {'document_type': 'vendor_proposal'}
        return self.semantic_search(query, filter_criteria=filter_criteria)
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the document index
        """
        if not self.document_metadata:
            return {"total_documents": 0}
        
        stats = {
            "total_chunks": len(self.document_chunks),
            "total_documents": len(set(meta.get('document_id', '') for meta in self.document_metadata)),
        }
        
        # Count by document type
        doc_types = {}
        for meta in self.document_metadata:
            doc_type = meta.get('document_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        stats['document_types'] = doc_types
        
        # Count by tender
        tender_counts = {}
        for meta in self.document_metadata:
            tender_id = meta.get('tender_id', 'unknown')
            tender_counts[tender_id] = tender_counts.get(tender_id, 0) + 1
        stats['tender_distribution'] = tender_counts
        
        return stats
    
    def clear_index(self):
        """Clear the entire index (for testing or reset)"""
        dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.vector_index = faiss.IndexFlatIP(dimension)
        self.document_chunks = []
        self.document_metadata = []
        self._save_index()
        logger.info("Index cleared successfully")

# Global retriever instance
retriever = EnhancedRetriever()

# Convenience functions for backward compatibility
def get_relevant_chunks(query: str, tender_id: Optional[str] = None) -> List[str]:
    """Get relevant chunks for a query"""
    return retriever.get_relevant_chunks(query, tender_id)

def add_documents_to_index(chunks: List[str], metadata: List[Dict[str, Any]]):
    """Add documents to the search index"""
    retriever.add_documents(chunks, metadata)

def search_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search documents and return detailed results"""
    return retriever.semantic_search(query, top_k)
