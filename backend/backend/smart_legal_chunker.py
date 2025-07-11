"""
Smart Legal Document Chunker for Arabic Legal Documents
Preserves legal hierarchy and structure while maintaining token limits
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LegalChunk:
    """A chunk of legal document with metadata"""
    content: str
    title: str
    chunk_index: int
    total_chunks: int
    hierarchy_level: str  # "chapter", "section", "article"
    metadata: Dict[str, Any]
    parent_document: str


class SmartLegalChunker:
    """Smart chunker that preserves Arabic legal document structure"""
    
    def __init__(self, max_tokens_per_chunk: int = 6000):
        self.max_tokens_per_chunk = max_tokens_per_chunk
        
        # Arabic legal structure patterns
        self.chapter_patterns = [
            r'الباب\s+[الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+]',
            r'الجزء\s+[الأول|الثاني|الثالث|الرابع|الخامس|\d+]',
            r'القسم\s+[الأول|الثاني|الثالث|الرابع|الخامس|\d+]'
        ]
        
        self.section_patterns = [
            r'الفصل\s+[الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|\d+]',
            r'المبحث\s+[الأول|الثاني|الثالث|الرابع|الخامس|\d+]'
        ]
        
        self.article_patterns = [
            r'المادة\s+[الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|\d+]',
            r'المادة\s+\(\s*\d+\s*\)',
            r'المادة\s+رقم\s+\d+'
        ]

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Arabic text"""
        # Arabic text typically has ~2 characters per token
        return len(text) // 2

    def find_legal_splits(self, content: str) -> List[Dict[str, Any]]:
        """Find optimal split points in legal document"""
        splits = []
        
        # Find all chapter splits
        for pattern in self.chapter_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                splits.append({
                    'position': match.start(),
                    'type': 'chapter',
                    'title': match.group(),
                    'level': 1
                })
        
        # Find all section splits
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                splits.append({
                    'position': match.start(),
                    'type': 'section', 
                    'title': match.group(),
                    'level': 2
                })
        
        # Find all article splits
        for pattern in self.article_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                splits.append({
                    'position': match.start(),
                    'type': 'article',
                    'title': match.group(),
                    'level': 3
                })
        
        # Sort by position
        splits.sort(key=lambda x: x['position'])
        return splits

    def chunk_legal_document(self, content: str, title: str) -> List[LegalChunk]:
        """Chunk legal document while preserving structure"""
        chunks = []
        
        # Find legal structure splits
        splits = self.find_legal_splits(content)
        
        if not splits:
            # Fallback: split by paragraphs if no legal structure found
            return self.fallback_chunk(content, title)
        
        current_chapter = 1
        current_section = 1
        
        for i, split in enumerate(splits):
            # Determine content boundaries
            start_pos = split['position']
            end_pos = splits[i + 1]['position'] if i + 1 < len(splits) else len(content)
            
            chunk_content = content[start_pos:end_pos].strip()
            
            # Skip very small chunks
            if len(chunk_content) < 100:
                continue
            
            # Check if chunk is too large
            if self.estimate_tokens(chunk_content) > self.max_tokens_per_chunk:
                # Split large chunk further
                sub_chunks = self.split_large_chunk(chunk_content, split)
                chunks.extend(sub_chunks)
            else:
                # Create chunk with proper metadata
                chunk_title = f"{title} - {split['title']}"
                
                # Update counters
                if split['type'] == 'chapter':
                    current_chapter += 1
                    current_section = 1
                elif split['type'] == 'section':
                    current_section += 1
                
                chunk = LegalChunk(
                    content=chunk_content,
                    title=chunk_title,
                    chunk_index=len(chunks) + 1,
                    total_chunks=0,  # Will be updated later
                    hierarchy_level=split['type'],
                    metadata={
                        'chapter': current_chapter,
                        'section': current_section if split['type'] != 'chapter' else 1,
                        'legal_type': split['type']
                    },
                    parent_document=title
                )
                chunks.append(chunk)
        
        # Update total_chunks for all chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks

    def split_large_chunk(self, content: str, split_info: Dict[str, Any]) -> List[LegalChunk]:
        """Split a large chunk into smaller pieces"""
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = content.split('\n\n')
        current_content = ""
        chunk_index = 1
        
        for paragraph in paragraphs:
            test_content = current_content + "\n\n" + paragraph if current_content else paragraph
            
            if self.estimate_tokens(test_content) > self.max_tokens_per_chunk and current_content:
                # Create chunk from current content
                chunk_title = f"{split_info['title']} - جزء {chunk_index}"
                
                chunk = LegalChunk(
                    content=current_content.strip(),
                    title=chunk_title,
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will be updated later
                    hierarchy_level=split_info['type'],
                    metadata={
                        'split_reason': 'large_chunk',
                        'original_section': split_info['title']
                    },
                    parent_document=""  # Will be set by caller
                )
                chunks.append(chunk)
                
                current_content = paragraph
                chunk_index += 1
            else:
                current_content = test_content
        
        # Add remaining content
        if current_content.strip():
            chunk_title = f"{split_info['title']} - جزء {chunk_index}"
            
            chunk = LegalChunk(
                content=current_content.strip(),
                title=chunk_title,
                chunk_index=chunk_index,
                total_chunks=0,
                hierarchy_level=split_info['type'],
                metadata={
                    'split_reason': 'large_chunk',
                    'original_section': split_info['title']
                },
                parent_document=""
            )
            chunks.append(chunk)
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks

    def fallback_chunk(self, content: str, title: str) -> List[LegalChunk]:
        """Fallback chunking when no legal structure is detected"""
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_content = ""
        chunk_index = 1
        
        for paragraph in paragraphs:
            test_content = current_content + "\n\n" + paragraph if current_content else paragraph
            
            if self.estimate_tokens(test_content) > self.max_tokens_per_chunk and current_content:
                # Create chunk
                chunk = LegalChunk(
                    content=current_content.strip(),
                    title=f"{title} - قسم {chunk_index}",
                    chunk_index=chunk_index,
                    total_chunks=0,
                    hierarchy_level="section",
                    metadata={'split_method': 'paragraph'},
                    parent_document=title
                )
                chunks.append(chunk)
                
                current_content = paragraph
                chunk_index += 1
            else:
                current_content = test_content
        
        # Add remaining content
        if current_content.strip():
            chunk = LegalChunk(
                content=current_content.strip(),
                title=f"{title} - قسم {chunk_index}",
                chunk_index=chunk_index,
                total_chunks=0,
                hierarchy_level="section",
                metadata={'split_method': 'paragraph'},
                parent_document=title
            )
            chunks.append(chunk)
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
