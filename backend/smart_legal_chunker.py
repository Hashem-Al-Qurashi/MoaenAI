import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class LegalChunk:
    """Smart legal document chunk with hierarchy"""
    content: str
    title: str
    parent_document: str
    hierarchy_level: str  # "chapter", "section", "article"
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any]

class SmartLegalChunker:
    """Arabic legal document intelligent chunker"""
    
    # Arabic legal structure patterns
    CHAPTER_PATTERNS = [
        r'الباب\s+(الأول|الثاني|الثالث|الرابع|الخامس|\d+)',
        r'القسم\s+(الأول|الثاني|الثالث|\d+)'
    ]
    
    SECTION_PATTERNS = [
        r'الفصل\s+(الأول|الثاني|الثالث|\d+)',
        r'الجزء\s+(الأول|الثاني|الثالث|\d+)'
    ]
    
    ARTICLE_PATTERNS = [
        r'المادة\s+(الأولى|الثانية|الثالثة|\d+)',
        r'البند\s+(\d+)',
        r'الفقرة\s+(\d+)'
    ]
    
    def __init__(self, max_tokens_per_chunk: int = 6000):
        self.max_tokens_per_chunk = max_tokens_per_chunk
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation for Arabic text"""
        # Arabic text roughly 2-3 characters per token
        return len(text) // 2
    
    def chunk_legal_document(self, content: str, title: str) -> List[LegalChunk]:
        """Smart chunking based on Arabic legal structure"""
        
        # First, try to split by chapters
        chapters = self._split_by_pattern(content, self.CHAPTER_PATTERNS)
        
        if len(chapters) > 1:
            return self._process_chapters(chapters, title)
        
        # If no chapters, try sections
        sections = self._split_by_pattern(content, self.SECTION_PATTERNS)
        
        if len(sections) > 1:
            return self._process_sections(sections, title)
        
        # If no sections, try articles
        articles = self._split_by_pattern(content, self.ARTICLE_PATTERNS)
        
        if len(articles) > 1:
            return self._process_articles(articles, title)
        
        # Fallback: intelligent paragraph splitting
        return self._split_by_paragraphs(content, title)
    
    def _split_by_pattern(self, text: str, patterns: List[str]) -> List[str]:
        """Split text by Arabic legal patterns"""
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if len(matches) > 1:
                chunks = []
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    chunks.append(text[start:end].strip())
                return chunks
        return [text]  # No pattern found
    
    def _process_chapters(self, chapters: List[str], title: str) -> List[LegalChunk]:
        """Process chapters, further split if needed"""
        chunks = []
        
        for i, chapter in enumerate(chapters):
            if self.estimate_tokens(chapter) > self.max_tokens_per_chunk:
                # Chapter too big, split by sections
                sections = self._split_by_pattern(chapter, self.SECTION_PATTERNS)
                for j, section in enumerate(sections):
                    chunks.append(LegalChunk(
                        content=section,
                        title=f"{title} - الباب {i+1} - الفصل {j+1}",
                        parent_document=title,
                        hierarchy_level="section",
                        chunk_index=len(chunks),
                        total_chunks=0,  # Will be updated later
                        metadata={"chapter": i+1, "section": j+1}
                    ))
            else:
                chunks.append(LegalChunk(
                    content=chapter,
                    title=f"{title} - الباب {i+1}",
                    parent_document=title,
                    hierarchy_level="chapter",
                    chunk_index=len(chunks),
                    total_chunks=0,
                    metadata={"chapter": i+1}
                ))
        
        # Update total chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _process_sections(self, sections: List[str], title: str) -> List[LegalChunk]:
        """Process sections, further split if needed"""
        chunks = []
        
        for i, section in enumerate(sections):
            if self.estimate_tokens(section) > self.max_tokens_per_chunk:
                # Section too big, split by articles
                articles = self._split_by_pattern(section, self.ARTICLE_PATTERNS)
                for j, article in enumerate(articles):
                    chunks.append(LegalChunk(
                        content=article,
                        title=f"{title} - الفصل {i+1} - المادة {j+1}",
                        parent_document=title,
                        hierarchy_level="article",
                        chunk_index=len(chunks),
                        total_chunks=0,
                        metadata={"section": i+1, "article": j+1}
                    ))
            else:
                chunks.append(LegalChunk(
                    content=section,
                    title=f"{title} - الفصل {i+1}",
                    parent_document=title,
                    hierarchy_level="section",
                    chunk_index=len(chunks),
                    total_chunks=0,
                    metadata={"section": i+1}
                ))
        
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _process_articles(self, articles: List[str], title: str) -> List[LegalChunk]:
        """Process articles"""
        chunks = []
        
        for i, article in enumerate(articles):
            chunks.append(LegalChunk(
                content=article,
                title=f"{title} - المادة {i+1}",
                parent_document=title,
                hierarchy_level="article",
                chunk_index=i,
                total_chunks=len(articles),
                metadata={"article": i+1}
            ))
        
        return chunks
    
    def _split_by_paragraphs(self, content: str, title: str) -> List[LegalChunk]:
        """Fallback: intelligent paragraph splitting"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if self.estimate_tokens(test_chunk) > self.max_tokens_per_chunk and current_chunk:
                # Save current chunk
                chunks.append(LegalChunk(
                    content=current_chunk.strip(),
                    title=f"{title} - جزء {chunk_index + 1}",
                    parent_document=title,
                    hierarchy_level="paragraph",
                    chunk_index=chunk_index,
                    total_chunks=0,
                    metadata={"paragraph_group": chunk_index + 1}
                ))
                current_chunk = paragraph
                chunk_index += 1
            else:
                current_chunk = test_chunk
        
        # Add final chunk
        if current_chunk:
            chunks.append(LegalChunk(
                content=current_chunk.strip(),
                title=f"{title} - جزء {chunk_index + 1}",
                parent_document=title,
                hierarchy_level="paragraph",
                chunk_index=chunk_index,
                total_chunks=0,
                metadata={"paragraph_group": chunk_index + 1}
            ))
        
        # Update total chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks

# Test the chunker
if __name__ == "__main__":
    chunker = SmartLegalChunker()
    
    # Test with sample Saudi legal text
    test_content = """
    الباب الأول: الأحكام العامة
    الفصل الأول: التعريفات
    المادة الأولى: يُقصد بالعبارات والألفاظ التالية أينما وردت في هذا النظام المعاني المبينة أمامها...
    المادة الثانية: تطبق أحكام هذا النظام على جميع المعاملات المدنية...
    الفصل الثاني: نطاق التطبيق
    المادة الثالثة: يسري هذا النظام على جميع الأشخاص...
    الباب الثاني: العقود
    الفصل الأول: أحكام عامة
    المادة الرابعة: العقد هو ارتباط الإيجاب بالقبول...
    """
    
    chunks = chunker.chunk_legal_document(test_content, "نظام المعاملات المدنية")
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"- {chunk.title} ({chunk.hierarchy_level}): {len(chunk.content)} chars")
