"""
Document Management Service
Pure database-driven document management for RAG system
Handles adding, removing, and listing documents in vector storage
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI
import logging
from smart_legal_chunker import SmartLegalChunker, LegalChunk
from app.storage.vector_store import VectorStore, Chunk

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for managing documents in vector storage
    
    Provides clean API for adding, removing, and managing documents
    without any hardcoded content - pure database operations
    """
    
    def __init__(self, storage: VectorStore, ai_client: AsyncOpenAI):
        """
        Initialize document service
        
        Args:
            storage: Vector storage implementation
            ai_client: AI client for generating embeddings
        """
        self.storage = storage
        self.ai_client = ai_client
        
        logger.info(f"DocumentService initialized with {type(storage).__name__}")

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough estimation)"""
        return len(text) // 2

    def should_chunk_document(self, content: str) -> bool:
        """Determine if document needs chunking"""
        return self.estimate_tokens(content) > 6000
    
    async def add_document(
        self, 
        title: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> bool:
        """
        Add a single document to storage
        
        Args:
            title: Document title
            content: Document content
            metadata: Optional metadata dictionary
            document_id: Optional custom ID (auto-generated if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate ID if not provided
            if not document_id:
                document_id = f"doc_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Adding document: {title[:50]}...")
            
            # Generate embedding
            response = await self.ai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=content
            )
            
            # Create chunk object
            chunk = Chunk(
                id=document_id,
                title=title,
                content=content,
                embedding=response.data[0].embedding,
                metadata=metadata or {}
            )
            
            # Store in database
            success = await self.storage.store_chunks([chunk])
            
            if success:
                logger.info(f"Successfully added document: {document_id}")
            else:
                logger.error(f"Failed to store document: {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    async def add_documents_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add multiple documents in batch
        
        Args:
            documents: List of document dictionaries with keys:
                      - title: Document title
                      - content: Document content  
                      - metadata: Optional metadata
                      - id: Optional custom ID
        
        Returns:
            Dictionary with success/failure statistics
        """
        try:
            logger.info(f"Adding {len(documents)} documents in batch...")
            
            chunks_to_store = []
            success_count = 0
            error_count = 0
            errors = []
            
            # Process each document
            for i, doc_data in enumerate(documents):
                try:
                    # Validate required fields
                    if 'title' not in doc_data or 'content' not in doc_data:
                        error_msg = f"Document {i+1}: Missing required fields (title, content)"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    
                    # Generate base ID if not provided
                    base_doc_id = doc_data.get('id', f"doc_{uuid.uuid4().hex[:8]}")
                    
                    logger.info(f"Processing document {i+1}/{len(documents)}: {doc_data['title'][:30]}...")
                    
                    # SMART CHUNKING LOGIC
                    if self.should_chunk_document(doc_data['content']):
                        logger.info(f"📏 Large document detected ({self.estimate_tokens(doc_data['content'])} tokens) - using smart chunker")
                        
                        # Initialize chunker
                        chunker = SmartLegalChunker(max_tokens_per_chunk=6000)
                        legal_chunks = chunker.chunk_legal_document(doc_data['content'], doc_data['title'])
                        
                        logger.info(f"✂️ Split into {len(legal_chunks)} chunks")
                        
                        # Process each chunk
                        for chunk_idx, legal_chunk in enumerate(legal_chunks):
                            try:
                                # Generate unique chunk ID
                                chunk_id = f"{base_doc_id}_chunk_{chunk_idx+1}"
                                
                                # Generate embedding for chunk
                                response = await self.ai_client.embeddings.create(
                                    model="text-embedding-ada-002",
                                    input=legal_chunk.content
                                )
                                
                                # Enhanced metadata with chunk info
                                chunk_metadata = {
                                    **doc_data.get('metadata', {}),
                                    'parent_document_id': base_doc_id,
                                    'chunk_index': legal_chunk.chunk_index,
                                    'total_chunks': legal_chunk.total_chunks,
                                    'hierarchy_level': legal_chunk.hierarchy_level,
                                    'legal_structure': legal_chunk.metadata,
                                    'is_chunk': True
                                }
                                
                                # Create chunk object
                                chunk = Chunk(
                                    id=chunk_id,
                                    title=legal_chunk.title,
                                    content=legal_chunk.content,
                                    embedding=response.data[0].embedding,
                                    metadata=chunk_metadata
                                )
                                
                                chunks_to_store.append(chunk)
                                
                            except Exception as chunk_error:
                                error_msg = f"Document {i+1} chunk {chunk_idx+1}: {str(chunk_error)}"
                                errors.append(error_msg)
                                error_count += 1
                                logger.error(error_msg)
                        
                        success_count += 1
                        
                    else:
                        # Small document - process normally (unchanged)
                        logger.info(f"📄 Small document ({self.estimate_tokens(doc_data['content'])} tokens) - processing normally")
                        
                        # Generate embedding
                        response = await self.ai_client.embeddings.create(
                            model="text-embedding-ada-002",
                            input=doc_data['content']
                        )
                        
                        # Create chunk object
                        chunk = Chunk(
                            id=base_doc_id,
                            title=doc_data['title'],
                            content=doc_data['content'],
                            embedding=response.data[0].embedding,
                            metadata={**doc_data.get('metadata', {}), 'is_chunk': False}
                        )
                        
                        chunks_to_store.append(chunk)
                        success_count += 1
                    
                except Exception as e:
                    error_msg = f"Document {i+1} ({doc_data.get('title', 'Unknown')}): {str(e)}"
                    errors.append(error_msg)
                    error_count += 1
                    logger.error(error_msg)
            
            # Store all successfully processed chunks
            if chunks_to_store:
                storage_success = await self.storage.store_chunks(chunks_to_store)
                
                if not storage_success:
                    logger.error("Failed to store chunks in database")
                    return {
                        "success": False,
                        "message": "Failed to store chunks in database",
                        "processed": success_count,
                        "errors": error_count,
                        "error_details": errors
                    }
            
            logger.info(f"Batch processing complete: {success_count} successful, {error_count} errors")
            
            return {
                "success": True,
                "message": f"Successfully processed {success_count} documents",
                "total_documents": len(documents),
                "successful": success_count,
                "errors": error_count,
                "error_details": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error in batch document processing: {e}")
            return {
                "success": False,
                "message": f"Batch processing failed: {str(e)}",
                "total_documents": len(documents),
                "successful": 0,
                "errors": len(documents)
            }
    
    async def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from storage
        
        Args:
            document_id: ID of document to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Removing document: {document_id}")
            
            deleted_count = await self.storage.delete_chunks([document_id])
            
            if deleted_count > 0:
                logger.info(f"Successfully removed document: {document_id}")
                return True
            else:
                logger.warning(f"Document not found: {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing document {document_id}: {e}")
            return False
    
    async def remove_documents_batch(self, document_ids: List[str]) -> Dict[str, Any]:
        """
        Remove multiple documents in batch
        
        Args:
            document_ids: List of document IDs to remove
            
        Returns:
            Dictionary with deletion statistics
        """
        try:
            logger.info(f"Removing {len(document_ids)} documents in batch...")
            
            deleted_count = await self.storage.delete_chunks(document_ids)
            
            logger.info(f"Successfully removed {deleted_count} documents")
            
            return {
                "success": True,
                "message": f"Successfully removed {deleted_count} documents",
                "requested": len(document_ids),
                "deleted": deleted_count,
                "not_found": len(document_ids) - deleted_count
            }
            
        except Exception as e:
            logger.error(f"Error in batch document removal: {e}")
            return {
                "success": False,
                "message": f"Batch removal failed: {str(e)}",
                "requested": len(document_ids),
                "deleted": 0
            }
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID
        
        Args:
            document_id: ID of document to retrieve
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            chunk = await self.storage.get_chunk_by_id(document_id)
            
            if chunk:
                return {
                    "id": chunk.id,
                    "title": chunk.title,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "has_embedding": chunk.embedding is not None
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def list_documents(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        List all documents in storage
        
        Args:
            limit: Optional limit on number of results
            
        Returns:
            Dictionary with document list and statistics
        """
        try:
            # Get storage statistics
            stats = await self.storage.get_stats()
            
            # For now, we'll return basic stats
            # TODO: Implement get_all_chunks method in storage interface
            
            return {
                "success": True,
                "total_documents": stats.total_chunks,
                "storage_size_mb": stats.storage_size_mb,
                "last_updated": stats.last_updated.isoformat(),
                "message": f"Storage contains {stats.total_chunks} documents"
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return {
                "success": False,
                "message": f"Failed to list documents: {str(e)}"
            }
    
    async def clear_all_documents(self) -> bool:
        """
        Clear all documents from storage (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.warning("Clearing ALL documents from storage")
            
            success = await self.storage.clear_all()
            
            if success:
                logger.info("Successfully cleared all documents")
            else:
                logger.error("Failed to clear documents")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing all documents: {e}")
            return False
    
    async def get_storage_health(self) -> Dict[str, Any]:
        """
        Get storage health and statistics
        
        Returns:
            Dictionary with health information
        """
        try:
            # Check storage health
            is_healthy = await self.storage.health_check()
            
            # Get statistics
            stats = await self.storage.get_stats()
            
            return {
                "healthy": is_healthy,
                "total_documents": stats.total_chunks,
                "storage_size_mb": stats.storage_size_mb,
                "last_updated": stats.last_updated.isoformat(),
                "storage_type": type(self.storage).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting storage health: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Utility functions for common operations

async def create_document_service(storage: VectorStore, ai_client: AsyncOpenAI) -> DocumentService:
    """
    Create and initialize document service
    
    Args:
        storage: Vector storage implementation
        ai_client: AI client for embeddings
        
    Returns:
        Initialized DocumentService instance
    """
    service = DocumentService(storage, ai_client)
    
    # Initialize storage if needed
    await storage.initialize()
    
    return service


def prepare_document_from_dict(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare document dictionary for service consumption
    
    Args:
        doc_dict: Raw document dictionary
        
    Returns:
        Cleaned document dictionary ready for service
    """
    return {
        "id": doc_dict.get("id"),
        "title": doc_dict.get("title", "Untitled Document"),
        "content": doc_dict.get("content", ""),
        "metadata": {
            "source": doc_dict.get("source"),
            "authority": doc_dict.get("authority"),
            "type": doc_dict.get("type"),
            "created_at": datetime.now().isoformat(),
            **doc_dict.get("metadata", {})
        }
    }


async def load_documents_from_list(
    service: DocumentService, 
    documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Helper function to load documents from a list
    
    Args:
        service: DocumentService instance
        documents: List of document dictionaries
        
    Returns:
        Loading results dictionary
    """
    # Prepare documents for service
    prepared_docs = [prepare_document_from_dict(doc) for doc in documents]
    
    # Load in batch
    result = await service.add_documents_batch(prepared_docs)
    
    return result