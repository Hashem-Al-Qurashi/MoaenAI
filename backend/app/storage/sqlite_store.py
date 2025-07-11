"""
SQLite Vector Store Implementation
File-based vector storage perfect for development and small-scale production
"""

import json
import sqlite3
import aiosqlite
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
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
                    # Serialize embedding as binary (proper BLOB storage)
                    embedding_blob = np.array(chunk.embedding).tobytes() if chunk.embedding is not None else None
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
                        embedding_blob,
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
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar chunks using cosine similarity"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get all chunks with embeddings
                query = "SELECT id, content, title, embedding, metadata FROM chunks WHERE embedding IS NOT NULL"
                params = []
                
                # Add basic metadata filters if provided
                if filters:
                    for key, value in filters.items():
                        # Simple metadata filtering - look for key in JSON
                        query += " AND metadata LIKE ?"
                        params.append(f'%"{key}":"{value}"%')
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                
                if not rows:
                    logger.warning("No chunks with embeddings found")
                    return []
                
                # Calculate similarities
                results = []
                query_vector_np = np.array(query_vector)
                
                for row in rows:
                    chunk_id, content, title, embedding_blob, metadata_json = row
                    
                    # Parse embedding
                    try:
                        # Parse embedding (handle both JSON and binary)
                        # Parse embedding (handle both JSON and binary)
                        chunk_embedding = None
                        if embedding_blob:
                            if isinstance(embedding_blob, str):
                                # Old JSON format
                                chunk_embedding = json.loads(embedding_blob)
                            else:
                                # New binary format
                                chunk_embedding = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
                        
                        if not chunk_embedding or len(chunk_embedding) != 1536:
                            continue
                        
                        # Calculate cosine similarity
                        chunk_embedding_np = np.array(chunk_embedding)
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
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to process chunk {chunk_id}: {e}")
                        continue
                
                # Sort by similarity (highest first) and return top_k
                results.sort(key=lambda x: x.similarity_score, reverse=True)
                
                logger.info(f"Found {len(results)} similar chunks, returning top {top_k}")
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
                
                chunk_id, content, title, embedding_blob, metadata_json = row
                
                # Parse embedding and metadata
                embedding = json.loads(embedding_blob) if embedding_blob else None
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
    async def search_hybrid(
        self,
        query_text: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[SearchResult]:
        """Hybrid search combining semantic + keyword search for Arabic legal content"""
        
        # Extract Arabic legal keywords
        legal_keywords = self._extract_legal_keywords(query_text)
        
        # Get embedding for semantic search
        from openai import AsyncOpenAI
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = await client.embeddings.create(
            model='text-embedding-ada-002',
            input=query_text
        )
        query_embedding = response.data[0].embedding
        
        # Perform semantic search
        semantic_results = await self.search_similar(query_embedding, top_k=top_k*2)
        
        # Perform keyword search
        keyword_results = await self._search_keywords(legal_keywords, top_k=top_k*2)
        
        # Fuse results with smart ranking
        fused_results = self._fuse_search_results(
            semantic_results, keyword_results, 
            semantic_weight, keyword_weight
        )
        
        return fused_results[:top_k]
    
    def _extract_legal_keywords(self, query_text: str) -> List[str]:
        """Extract Arabic legal terms and concepts"""
        
        # Arabic legal term patterns
        legal_patterns = {
            'articles': r'المادة\s*[الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|\d+]',
            'chapters': r'الباب\s*[الأول|الثاني|الثالث|الرابعة|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+]',
            'sections': r'الفصل\s*[الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+]',
            'paragraphs': r'\d+/\d+',  # Like ١/٩
        }
        
        # Legal domain keywords
        legal_keywords = [
            'السجين', 'الموقوف', 'المتهم', 'المدعي', 'المدعى', 'الشاهد',
            'الحكم', 'القاضي', 'المحكمة', 'الدعوى', 'الجلسة', 'التبليغ',
            'العقوبة', 'الغرامة', 'السجن', 'التوقيف', 'الإفراج',
            'العمل', 'العامل', 'الموظف', 'الوظيفة', 'الراتب', 'الأجر',
            'الإجازة', 'ساعات', 'العمل', 'صاحب', 'رب', 'العمل'
        ]
        
        extracted = []
        
        # Extract structured references (articles, chapters, etc.)
        import re
        for pattern_type, pattern in legal_patterns.items():
            matches = re.findall(pattern, query_text)
            extracted.extend(matches)
        
        # Extract legal keywords
        query_words = query_text.split()
        for word in query_words:
            clean_word = word.strip('،.؟!()[]{}')
            if clean_word in legal_keywords:
                extracted.append(clean_word)
            # Add root forms and variations
            if 'سجن' in clean_word:
                extracted.extend(['السجين', 'المسجون', 'سجن'])
            if 'عمل' in clean_word:
                extracted.extend(['العامل', 'العمل', 'الموظف', 'الوظيفة'])
            if 'حضور' in clean_word:
                extracted.extend(['حضور', 'الحضور', 'يحضر'])
        
        return list(set(extracted))  # Remove duplicates
    
    async def _search_keywords(self, keywords: List[str], top_k: int = 10) -> List[SearchResult]:
        """Search for chunks containing specific Arabic keywords"""
        if not keywords:
            return []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Build SQL query for keyword matching
                keyword_conditions = []
                params = []
                
                for keyword in keywords:
                    keyword_conditions.append("(content LIKE ? OR title LIKE ?)")
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                
                query = f"""
                    SELECT id, content, title, embedding, metadata,
                           ({' + '.join(['(CASE WHEN content LIKE ? OR title LIKE ? THEN 1 ELSE 0 END)' for _ in keywords])}) as keyword_score
                    FROM chunks 
                    WHERE {' OR '.join(keyword_conditions)}
                    ORDER BY keyword_score DESC, length(content) ASC
                """
                
                # Duplicate params for scoring
                score_params = []
                for keyword in keywords:
                    score_params.extend([f'%{keyword}%', f'%{keyword}%'])
                
                all_params = score_params + params
                
                async with db.execute(query, all_params) as cursor:
                    rows = await cursor.fetchall()
                
                results = []
                for row in rows[:top_k]:
                    chunk_id, content, title, embedding_blob, metadata_json, keyword_score = row
                    
                    # Parse metadata
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    # Parse embedding  
                    embedding = None
                    if embedding_blob:
                        if isinstance(embedding_blob, str):
                            embedding = json.loads(embedding_blob)
                        else:
                            embedding = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
                    
                    # Create chunk
                    chunk = Chunk(
                        id=chunk_id,
                        content=content,
                        title=title,
                        embedding=embedding,
                        metadata=metadata
                    )
                    
                    # Keyword score as similarity (0-1 range)
                    similarity_score = min(keyword_score / len(keywords), 1.0)
                    
                    results.append(SearchResult(
                        chunk=chunk,
                        similarity_score=similarity_score
                    ))
                
                return results
                
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def _fuse_search_results(
        self, 
        semantic_results: List[SearchResult], 
        keyword_results: List[SearchResult],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """Intelligently fuse semantic and keyword search results"""
        
        # Create a map of all unique chunks
        chunk_scores = {}
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result.chunk.id
            chunk_scores[chunk_id] = {
                'chunk': result.chunk,
                'semantic_score': result.similarity_score,
                'keyword_score': 0.0
            }
        
        # Add keyword results
        for result in keyword_results:
            chunk_id = result.chunk.id
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id]['keyword_score'] = result.similarity_score
            else:
                chunk_scores[chunk_id] = {
                    'chunk': result.chunk,
                    'semantic_score': 0.0,
                    'keyword_score': result.similarity_score
                }
        
        # Calculate final scores
        final_results = []
        for chunk_id, scores in chunk_scores.items():
            final_score = (
                scores['semantic_score'] * semantic_weight + 
                scores['keyword_score'] * keyword_weight
            )
            
            final_results.append(SearchResult(
                chunk=scores['chunk'],
                similarity_score=final_score
            ))
        
        # Sort by final score
        final_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return final_results

    async def search_elite(
        self,
        query_text: str,
        top_k: int = 5,
        prefer_legislation: bool = True
    ) -> List[SearchResult]:
        """Elite search with legislation vs court intelligence"""
        
        from app.retrieval.elite_classifier import EliteLegalClassifier
        
        # Initialize classifier
        classifier = EliteLegalClassifier()
        
        # Get search strategy
        strategy = classifier.get_search_strategy(query_text)
        
        # Perform hybrid search
        hybrid_results = await self.search_hybrid(
            query_text, 
            top_k=top_k*3,  # Get more for filtering
            semantic_weight=strategy['semantic_weight'],
            keyword_weight=strategy['keyword_weight']
        )
        
        # Classify and re-rank results
        elite_results = []
        for result in hybrid_results:
            # Classify the chunk
            classification = classifier.classify_content(
                result.chunk.title, 
                result.chunk.content
            )
            
            # Calculate elite score
            elite_score = self._calculate_elite_score(
                result.similarity_score,
                classification,
                strategy
            )
            
            # Add classification metadata
            result.chunk.metadata['elite_classification'] = {
                'content_type': classification.content_type,
                'legal_domain': classification.legal_domain,
                'hierarchy_level': classification.hierarchy_level,
                'authority_score': classification.authority_score,
                'search_priority': classification.search_priority
            }
            
            # Update similarity with elite score
            result.similarity_score = elite_score
            elite_results.append(result)
        
        # Sort by elite score and apply domain/type filtering
        elite_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Smart filtering based on query strategy
        filtered_results = self._apply_elite_filtering(
            elite_results, strategy, top_k
        )
        
        return filtered_results[:top_k]
    
    def _calculate_elite_score(
        self, 
        base_score: float, 
        classification, 
        strategy: Dict[str, Any]
    ) -> float:
        """Calculate elite ranking score"""
        
        # Base similarity score
        elite_score = base_score * 0.5
        
        # Authority bonus
        elite_score += classification.authority_score * strategy['authority_weight']
        
        # Content type preference
        if strategy['prefer_legislation'] and classification.content_type == 'legislation':
            elite_score += 0.2
        elif not strategy['prefer_legislation'] and classification.content_type == 'court_ruling':
            elite_score += 0.15
        
        # Domain match bonus
        if classification.legal_domain == strategy['legal_domain']:
            elite_score += 0.15
        
        # Hierarchy level bonus (articles are most valuable)
        if classification.hierarchy_level == 'article':
            elite_score += 0.1
        elif classification.hierarchy_level in ['law', 'supreme_court']:
            elite_score += 0.08
        
        return min(elite_score, 1.0)
    
    def _apply_elite_filtering(
        self, 
        results: List[SearchResult], 
        strategy: Dict[str, Any], 
        target_count: int
    ) -> List[SearchResult]:
        """Apply intelligent filtering for elite results"""
        
        if not results:
            return results
        
        # Separate legislation and court rulings
        legislation_results = [r for r in results 
                             if r.chunk.metadata.get('elite_classification', {}).get('content_type') == 'legislation']
        court_results = [r for r in results 
                        if r.chunk.metadata.get('elite_classification', {}).get('content_type') == 'court_ruling']
        
        # Smart mixing based on query type
        if strategy['prefer_legislation']:
            # Prioritize legislation, add court examples
            filtered = legislation_results[:max(target_count-1, target_count*2//3)]
            remaining = target_count - len(filtered)
            if remaining > 0:
                filtered.extend(court_results[:remaining])
        else:
            # Prioritize court rulings, add legislation context
            filtered = court_results[:max(target_count-1, target_count*2//3)]
            remaining = target_count - len(filtered)
            if remaining > 0:
                filtered.extend(legislation_results[:remaining])
        
        return filtered
