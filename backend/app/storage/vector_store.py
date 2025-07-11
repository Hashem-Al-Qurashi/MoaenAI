"""
Vector Store Interface - Storage Abstraction Layer
Defines the contract for all vector storage implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Chunk:
    """Document chunk with metadata"""
    id: str
    content: str
    title: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "title": self.title,
            "embedding": self.embedding,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Create chunk from dictionary"""
        return cls(
            id=data["id"],
            content=data["content"],
            title=data["title"],
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {})
        )


@dataclass
class SearchResult:
    """Search result with similarity score"""
    chunk: Chunk
    similarity_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary"""
        return {
            "chunk": self.chunk.to_dict(),
            "similarity_score": self.similarity_score
        }


@dataclass
class StorageStats:
    """Storage statistics"""
    total_chunks: int
    storage_size_mb: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "total_chunks": self.total_chunks,
            "storage_size_mb": self.storage_size_mb,
            "last_updated": self.last_updated.isoformat()
        }


class VectorStore(ABC):
    """
    Abstract base class for vector storage implementations
    
    This interface ensures all storage backends (SQLite, Qdrant, Pinecone)
    provide the same methods, allowing seamless switching between them.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the storage backend
        
        This method should:
        - Set up database connections
        - Create necessary tables/collections
        - Prepare the storage for operations
        """
        pass
    
    @abstractmethod
    async def store_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Store document chunks with embeddings
        
        Args:
            chunks: List of Chunk objects with content and embeddings
            
        Returns:
            bool: True if successful, False otherwise
            
        This method should:
        - Store chunks with their embeddings
        - Handle duplicate detection
        - Update existing chunks if they already exist
        """
        pass
    
    @abstractmethod
    async def search_similar(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar chunks using vector similarity
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List[SearchResult]: Ranked results with similarity scores
            
        This method should:
        - Perform vector similarity search (cosine similarity)
        - Apply metadata filters if provided
        - Return results sorted by similarity (highest first)
        """
        pass
    
    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a specific chunk by ID
        
        Args:
            chunk_id: Unique identifier for the chunk
            
        Returns:
            Optional[Chunk]: The chunk if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_chunks(self, chunk_ids: List[str]) -> int:
        """
        Delete chunks by their IDs
        
        Args:
            chunk_ids: List of chunk IDs to delete
            
        Returns:
            int: Number of chunks successfully deleted
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> StorageStats:
        """
        Get storage statistics
        
        Returns:
            StorageStats: Current storage statistics
            
        This method should return:
        - Total number of stored chunks
        - Storage size in MB
        - Last update timestamp
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the storage backend is healthy and responsive
        
        Returns:
            bool: True if storage is accessible, False otherwise
        """
        pass
    
    # Optional: Utility methods that implementations can override
    
    async def clear_all(self) -> bool:
        """
        Clear all stored data (use with caution!)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Default implementation using delete_chunks
        try:
            stats = await self.get_stats()
            if stats.total_chunks == 0:
                return True
                
            # This is a basic implementation - each backend can optimize
            # For now, we'll let each implementation handle this
            raise NotImplementedError("Each storage backend should implement clear_all")
        except Exception:
            return False
    
    async def chunk_exists(self, chunk_id: str) -> bool:
        """
        Check if a chunk exists without retrieving it
        
        Args:
            chunk_id: Chunk ID to check
            
        Returns:
            bool: True if chunk exists, False otherwise
        """
        chunk = await self.get_chunk_by_id(chunk_id)
        return chunk is not None