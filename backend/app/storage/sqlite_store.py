"""
SQLite Vector Store Implementation
File-based vector storage perfect for development and small-scale production
"""
import pickle
import json
import sqlite3
import aiosqlite
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
from app.legal_reasoning.ai_domain_classifier import AIDomainClassifier
from datetime import datetime
import logging

from .vector_store import VectorStore, Chunk, SearchResult, StorageStats

logger = logging.getLogger(__name__)


class SqliteVectorStore(VectorStore):
    """
    SQLite-based vector storage implementation
    
    Uses SQLite with JSON columns for metadata and BLOB for embeddings.
    Implements cosine similarity search in Python for compatibility.
    Perfect for development and small to medium datasets.
    """
    
    def __init__(self, db_path: str = "data/vectors.db"):
        """
        Initialize SQLite vector store
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.initialized = False
        
        # Ensure data directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(exist_ok=True)
        
        logger.info(f"SQLite Vector Store initialized with path: {db_path}")
    
    async def initialize(self) -> None:
        """Initialize SQLite database with required tables"""
        if self.initialized:
            return
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Enable JSON extension if available
                try:
                    await db.execute("SELECT json('{}');")
                except sqlite3.OperationalError:
                    logger.warning("JSON extension not available - using TEXT for metadata")
                
                # Create chunks table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        title TEXT NOT NULL,
                        embedding BLOB,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index on title for faster searches
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_title 
                    ON chunks(title)
                """)
                
                # Create index on created_at for stats
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_created_at 
                    ON chunks(created_at)
                """)
                
                await db.commit()
                
            self.initialized = True
            logger.info("SQLite vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite store: {e}")
            raise
    
    async def store_chunks(self, chunks: List[Chunk]) -> bool:
        """Store chunks in SQLite database"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for chunk in chunks:
                    # Serialize embedding as JSON (more portable than BLOB)
                    embedding_json = json.dumps(chunk.embedding) if chunk.embedding else None
                    metadata_json = json.dumps(chunk.metadata) if chunk.metadata else "{}"
                    
                    # Use INSERT OR REPLACE for upsert behavior
                    await db.execute("""
                        INSERT OR REPLACE INTO chunks 
                        (id, content, title, embedding, metadata, updated_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        chunk.id,
                        chunk.content,
                        chunk.title,
                        embedding_json,
                        metadata_json
                    ))
                
                await db.commit()
                
            logger.info(f"Successfully stored {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store chunks: {e}")
            return False
    
    async def search_similar(
    self, 
    query_vector: List[float], 
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    query_text: Optional[str] = None,
    openai_client: Optional[Any] = None
) -> List[SearchResult]:
        """
        Search for similar chunks using AI domain classification + cosine similarity
        Now with intelligent domain filtering for better Arabic legal search
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Step 1: AI Domain Classification (if query text provided)
                domain_filter_sql = "1=1"  # Default: no filter
                # Debug the actual parameter values
                print(f"🚨 PARAMETER DEBUG:")
                print(f"  query_text: {repr(query_text)}")
                print(f"  query_text type: {type(query_text)}")
                print(f"  openai_client: {repr(openai_client)}")
                print(f"  openai_client type: {type(openai_client)}")
                print(f"  Condition result: {bool(query_text and openai_client)}")
                if query_text and openai_client:
                    print(f"🔥 DEBUG A: query_text exists: {bool(query_text)}")
                    print(f"🔥 DEBUG B: openai_client exists: {bool(openai_client)}")
                    try:
                        from app.legal_reasoning.ai_domain_classifier import AIDomainClassifier
                        classifier = AIDomainClassifier(openai_client)
                        print(f"🔥 DEBUG C: AIDomainClassifier created successfully")
                        # Get AI domain classification
                        classification = await classifier.classify_query(query_text)
                        print(f"🔥 DEBUG D: Classification result: {classification}")
                        domain = classification["domain"]
                        confidence = classification["confidence"]
                        print(f"🔥 DEBUG E: Domain: {domain}, Confidence: {confidence}")
                        
                        # Use domain filter if confidence is high enough
                        if confidence >= 0.8:
                            print(f"🔥 DEBUG F: Confidence >= 0.8, generating filter...")
                            domain_filter_sql = classifier.get_domain_filter_sql(domain)
                            print(f"🔥 DEBUG G: Generated filter: {domain_filter_sql}")
                            logger.info(f"🎯 AI classified as {domain.value} (confidence: {confidence:.2f})")
                            logger.info(f"📋 Domain filter: {domain_filter_sql[:100]}...")
                        else:
                            print(f"🔥 DEBUG H: Confidence too low ({confidence}), using default filter")
                            logger.info(f"⚠️ Low confidence ({confidence:.2f}), searching all documents")
                            
                    except Exception as e:
                        print(f"🚨 DOMAIN CLASSIFICATION EXCEPTION: {e}")
                        print(f"🚨 Exception type: {type(e)}")
                        import traceback
                        print(f"🚨 Full traceback: {traceback.format_exc()}")
                        logger.warning(f"AI domain classification failed: {e}, using all documents")
                
                # Step 2: Get domain-filtered chunks with embeddings
                base_query = """
                    SELECT id, content, title, embedding, metadata 
                    FROM chunks 
                    WHERE embedding IS NOT NULL
                """
                
                # Add domain filter
                print(f"🔥 FILTER DEBUG: domain_filter_sql = '{domain_filter_sql}'")
                print(f"🔥 FILTER DEBUG: domain_filter_sql != '1=1' = {domain_filter_sql != '1=1'}")
                if domain_filter_sql != "1=1":
                    query_sql = f"{base_query} AND ({domain_filter_sql})"
                else:
                    query_sql = base_query
                
                # Add basic metadata filters if provided
                params = []
                if filters:
                    for key, value in filters.items():
                        query_sql += " AND metadata LIKE ?"
                        params.append(f'%"{key}":"{value}"%')


                print(f"🔍 EXECUTING SQL: {query_sql[:200]}...")
                async with db.execute(query_sql, params) as cursor:
                    rows = await cursor.fetchall()
                    
                    if not rows:
                        logger.warning("No chunks found with current filters")
                        return []
                    
                    logger.info(f"Domain filtering returned {len(rows)} candidate documents")
                
                # Step 3: Calculate similarities
                results = []
                query_vector_np = np.array(query_vector)
                processed_count = 0
                
                for row in rows:
                    chunk_id, content, title, embedding_data, metadata_json = row
                    
                    try:
                        # Unpickle the stored embedding
                        chunk_embedding = pickle.loads(embedding_data) if embedding_data else None
                        if not chunk_embedding:
                            continue
                        
                        chunk_embedding_np = np.array(chunk_embedding)
                        
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(query_vector_np, chunk_embedding_np)
                        
                        # Parse metadata
                        metadata = json.loads(metadata_json) if metadata_json else {}
                        
                        # Create chunk object
                        chunk = Chunk(
                            id=chunk_id,
                            content=content,
                            title=title,
                            embedding=chunk_embedding,
                            metadata=metadata
                        )
                        
                        results.append(SearchResult(
                            chunk=chunk,
                            similarity_score=similarity
                        ))
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to process chunk {chunk_id}: {e}")
                        continue
                
                # Step 4: Sort by similarity and return top_k
                results.sort(key=lambda x: x.similarity_score, reverse=True)
                
                logger.info(f"Successfully processed {processed_count} chunks, returning top {top_k}")
                logger.info(f"Top result similarity: {results[0].similarity_score:.3f}" if results else "No results")
                
                return results[:top_k]
                
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            return []

    async def get_chunk_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """Retrieve a specific chunk by ID"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT id, content, title, embedding, metadata 
                    FROM chunks WHERE id = ?
                """, (chunk_id,)) as cursor:
                    row = await cursor.fetchone()
                
                if not row:
                    return None
                
                chunk_id, content, title, embedding_json, metadata_json = row
                
                # Parse embedding and metadata
                embedding = json.loads(embedding_json) if embedding_json else None
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                return Chunk(
                    id=chunk_id,
                    content=content,
                    title=title,
                    embedding=embedding,
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            return None
    
    async def delete_chunks(self, chunk_ids: List[str]) -> int:
        """Delete chunks by their IDs"""
        if not self.initialized:
            await self.initialize()
        
        if not chunk_ids:
            return 0
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Use parameterized query for safety
                placeholders = ",".join("?" * len(chunk_ids))
                result = await db.execute(
                    f"DELETE FROM chunks WHERE id IN ({placeholders})",
                    chunk_ids
                )
                
                await db.commit()
                deleted_count = result.rowcount
                
                logger.info(f"Deleted {deleted_count} chunks")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            return 0
    
    async def get_stats(self) -> StorageStats:
        """Get storage statistics"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total chunk count
                async with db.execute("SELECT COUNT(*) FROM chunks") as cursor:
                    row = await cursor.fetchone()
                    total_chunks = row[0] if row else 0
                
                # Get last updated timestamp
                async with db.execute("""
                    SELECT MAX(updated_at) FROM chunks
                """) as cursor:
                    row = await cursor.fetchone()
                    last_updated_str = row[0] if row and row[0] else None
                
                # Parse timestamp
                if last_updated_str:
                    try:
                        last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                    except ValueError:
                        last_updated = datetime.now()
                else:
                    last_updated = datetime.now()
                
                # Get database file size
                try:
                    db_size_bytes = Path(self.db_path).stat().st_size
                    storage_size_mb = db_size_bytes / (1024 * 1024)
                except FileNotFoundError:
                    storage_size_mb = 0.0
                
                return StorageStats(
                    total_chunks=total_chunks,
                    storage_size_mb=round(storage_size_mb, 2),
                    last_updated=last_updated
                )
                
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return StorageStats(
                total_chunks=0,
                storage_size_mb=0.0,
                last_updated=datetime.now()
            )
    
    async def health_check(self) -> bool:
        """Check if SQLite database is accessible"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT 1") as cursor:
                    await cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all stored data"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM chunks")
                await db.commit()
                
            logger.info("Cleared all chunks from SQLite store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all chunks: {e}")
            return False
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Handle zero vectors
            if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            # Ensure result is in valid range [-1, 1]
            return float(np.clip(similarity, -1.0, 1.0))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    # Debug and utility methods
    
    async def get_all_chunk_ids(self) -> List[str]:
        """Get all chunk IDs (utility method for debugging)"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT id FROM chunks ORDER BY created_at") as cursor:
                    rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get chunk IDs: {e}")
            return []
    
    async def get_chunks_without_embeddings(self) -> List[str]:
        """Get chunk IDs that don't have embeddings"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT id FROM chunks WHERE embedding IS NULL OR embedding = ''
                """) as cursor:
                    rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get chunks without embeddings: {e}")
            return []