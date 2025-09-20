"""
Enhanced Vector Store for Tender Evaluation System
Advanced document processing and vector storage from medical RAG patterns
"""
import faiss
import numpy as np
import pickle
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import hashlib
from datetime import datetime
from sentence_transformers import SentenceTransformer

from backend.config import (
    VECTOR_DB_PATH, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP,
    EMBEDDINGS_DIR
)

logger = logging.getLogger(__name__)

class AdvancedVectorStore:
    def __init__(self, index_name: str = "main"):
        self.index_name = index_name
        self.index_path = Path(EMBEDDINGS_DIR) / f"{index_name}.index"
        self.chunks_path = Path(EMBEDDINGS_DIR) / f"{index_name}_chunks.pkl"
        self.metadata_path = Path(EMBEDDINGS_DIR) / f"{index_name}_metadata.pkl"
        self.stats_path = Path(EMBEDDINGS_DIR) / f"{index_name}_stats.pkl"
        
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        self.index = None
        self.chunks = []
        self.metadata = []
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'last_updated': None,
            'document_hashes': set()
        }
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        try:
            if self.index_path.exists():
                logger.info(f"Loading existing FAISS index: {self.index_name}")
                self.index = faiss.read_index(str(self.index_path))
                
                # Load chunks and metadata
                if self.chunks_path.exists():
                    with open(self.chunks_path, 'rb') as f:
                        self.chunks = pickle.load(f)
                
                if self.metadata_path.exists():
                    with open(self.metadata_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                
                if self.stats_path.exists():
                    with open(self.stats_path, 'rb') as f:
                        self.stats = pickle.load(f)
                
                logger.info(f"Loaded {len(self.chunks)} chunks from index")
            else:
                logger.info(f"Creating new FAISS index: {self.index_name}")
                self._create_new_index()
                
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.chunks = []
        self.metadata = []
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'last_updated': datetime.now().isoformat(),
            'document_hashes': set()
        }
    
    def _save_index(self):
        """Save index and associated data to disk"""
        try:
            # Ensure directory exists
            os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save chunks and metadata
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            # Update and save stats
            self.stats['last_updated'] = datetime.now().isoformat()
            with open(self.stats_path, 'wb') as f:
                pickle.dump(self.stats, f)
            
            logger.info(f"Index {self.index_name} saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, 
                   overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Advanced text chunking with overlap
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_break = text.rfind('.', start, end)
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1
                else:
                    # Look for word boundary
                    word_break = text.rfind(' ', start, end)
                    if word_break > start + chunk_size // 2:
                        end = word_break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_document_hash(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate unique hash for document"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        metadata_str = str(sorted(metadata.items()))
        metadata_hash = hashlib.md5(metadata_str.encode()).hexdigest()
        return f"{content_hash}_{metadata_hash}"
    
    def add_document(self, content: str, metadata: Dict[str, Any], 
                    update_if_exists: bool = False) -> bool:
        """
        Add a single document to the vector store
        """
        try:
            # Generate document hash
            doc_hash = self._generate_document_hash(content, metadata)
            
            # Check if document already exists
            if doc_hash in self.stats['document_hashes'] and not update_if_exists:
                logger.info(f"Document already exists: {metadata.get('filename', 'unknown')}")
                return False
            
            # Chunk the document
            chunks = self._chunk_text(content)
            logger.info(f"Created {len(chunks)} chunks for document: {metadata.get('filename', 'unknown')}")
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
            embeddings = embeddings.astype('float32')
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            start_idx = len(self.chunks)
            self.index.add(embeddings)
            
            # Store chunks and metadata
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'document_hash': doc_hash,
                    'vector_index': start_idx + i,
                    'added_timestamp': datetime.now().isoformat()
                })
                
                self.chunks.append(chunk)
                self.metadata.append(chunk_metadata)
            
            # Update stats
            self.stats['total_documents'] += 1
            self.stats['total_chunks'] += len(chunks)
            self.stats['document_hashes'].add(doc_hash)
            
            logger.info(f"Successfully added document with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def add_documents(self, documents: List[Tuple[str, Dict[str, Any]]], 
                     batch_size: int = 100) -> Dict[str, int]:
        """
        Add multiple documents in batches
        """
        results = {'added': 0, 'skipped': 0, 'errors': 0}
        
        for i, (content, metadata) in enumerate(documents):
            try:
                if self.add_document(content, metadata):
                    results['added'] += 1
                else:
                    results['skipped'] += 1
                
                # Save periodically
                if (i + 1) % batch_size == 0:
                    self._save_index()
                    logger.info(f"Processed {i + 1}/{len(documents)} documents")
                    
            except Exception as e:
                logger.error(f"Error processing document {i}: {e}")
                results['errors'] += 1
        
        # Final save
        self._save_index()
        
        logger.info(f"Batch processing complete: {results}")
        return results
    
    def search(self, query: str, top_k: int = 5, 
              filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        """
        try:
            if len(self.chunks) == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            query_embedding = query_embedding.astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search
            search_k = min(top_k * 3, len(self.chunks))  # Get extra for filtering
            scores, indices = self.index.search(query_embedding, search_k)
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= len(self.chunks):
                    continue
                
                result = {
                    'content': self.chunks[idx],
                    'metadata': self.metadata[idx],
                    'similarity_score': float(score),
                    'index': int(idx)
                }
                
                # Apply metadata filter
                if self._matches_filter(result['metadata'], filter_metadata):
                    results.append(result)
                
                if len(results) >= top_k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], 
                       filter_metadata: Optional[Dict[str, Any]]) -> bool:
        """Check if metadata matches filter criteria"""
        if not filter_metadata:
            return True
        
        for key, value in filter_metadata.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
        
        return True
    
    def get_document_by_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        results = []
        for i, metadata in enumerate(self.metadata):
            if metadata.get('document_id') == document_id:
                results.append({
                    'content': self.chunks[i],
                    'metadata': metadata,
                    'index': i
                })
        return results
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks from the index"""
        # Note: FAISS doesn't support deletion, so we'd need to rebuild
        # For now, we'll mark as deleted in metadata
        deleted_count = 0
        for metadata in self.metadata:
            if metadata.get('document_id') == document_id:
                metadata['deleted'] = True
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_index()
            logger.info(f"Marked {deleted_count} chunks as deleted for document {document_id}")
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the vector store"""
        active_chunks = sum(1 for meta in self.metadata if not meta.get('deleted', False))
        
        stats = self.stats.copy()
        stats.update({
            'active_chunks': active_chunks,
            'deleted_chunks': len(self.metadata) - active_chunks,
            'index_dimension': self.dimension,
            'index_size_mb': self.index_path.stat().st_size / (1024 * 1024) if self.index_path.exists() else 0
        })
        
        # Document type distribution
        doc_types = {}
        tender_counts = {}
        
        for meta in self.metadata:
            if meta.get('deleted', False):
                continue
            
            doc_type = meta.get('document_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            tender_id = meta.get('tender_id', 'unknown')
            tender_counts[tender_id] = tender_counts.get(tender_id, 0) + 1
        
        stats['document_types'] = doc_types
        stats['tender_distribution'] = tender_counts
        
        return stats
    
    def rebuild_index(self):
        """Rebuild the index excluding deleted documents"""
        logger.info("Rebuilding index to remove deleted documents")
        
        # Get active documents
        active_chunks = []
        active_metadata = []
        
        for i, meta in enumerate(self.metadata):
            if not meta.get('deleted', False):
                active_chunks.append(self.chunks[i])
                active_metadata.append(meta)
        
        # Create new index
        self._create_new_index()
        
        if active_chunks:
            # Generate embeddings for active chunks
            embeddings = self.embedding_model.encode(active_chunks, show_progress_bar=True)
            embeddings = embeddings.astype('float32')
            faiss.normalize_L2(embeddings)
            
            # Add to new index
            self.index.add(embeddings)
            self.chunks = active_chunks
            self.metadata = active_metadata
            
            # Update stats
            self.stats['total_chunks'] = len(active_chunks)
            self.stats['total_documents'] = len(set(meta.get('document_id') for meta in active_metadata))
        
        self._save_index()
        logger.info(f"Index rebuilt with {len(active_chunks)} active chunks")

# Global vector store instance
vector_store = AdvancedVectorStore()

# Convenience functions for backward compatibility
def build_vector_store(docs: List[Tuple[str, Dict[str, Any]]]) -> Tuple[Any, Any]:
    """Build vector store from documents"""
    results = vector_store.add_documents(docs)
    return vector_store.index, vector_store.chunks

def query_vector_store(query: str, top_k: int = 3) -> Tuple[List[float], List[int]]:
    """Query vector store and return scores and indices"""
    results = vector_store.search(query, top_k)
    
    scores = [result['similarity_score'] for result in results]
    indices = [result['index'] for result in results]
    
    return scores, indices

def add_document_to_store(content: str, metadata: Dict[str, Any]) -> bool:
    """Add single document to store"""
    return vector_store.add_document(content, metadata)
