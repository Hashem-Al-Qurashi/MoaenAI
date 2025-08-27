"""
Legal Memo Processor - Handles 25K lines with court-specific intelligence
Integrates with existing RAG system without breaking changes
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.storage.vector_store import VectorStore, Chunk

@dataclass
class LegalMemo:
    """Represents a single legal memo extracted from 25K lines"""
    content: str
    court_system: str
    memo_type: str
    complexity_level: str
    confidence_score: float
    start_line: int
    end_line: int

class LegalMemoProcessor:
    """Processes 25K legal memo lines with court-specific intelligence"""
    
    def __init__(self, storage: VectorStore):
        self.storage = storage
        
        # Court system patterns from your 9-sample analysis
        self.court_patterns = {
            'execution': {
                'start_patterns': [
                    r'فضيلة رئيس محكمة التنفيذ',
                    r'منازعة تنفيذ',
                    r'إشارة إلى القرار القضائي'
                ],
                'indicators': ['منفذ ضده', 'طالب تنفيذ', 'نظام التنفيذ'],
                'memo_types': ['منازعة_تنفيذ', 'تنفيذ_أحكام_أجنبية']
            },
            'civil': {
                'start_patterns': [
                    r'فضيلة رئيس وأعضاء محكمة الاستئناف',
                    r'لائحة اعتراضية',
                    r'المحكمة العامة'
                ],
                'indicators': ['مدعي', 'مدعى عليه', 'نظام المرافعات'],
                'memo_types': ['لائحة_اعتراضية', 'طلب_مستعجل']
            },
            'family': {
                'start_patterns': [
                    r'صاحب الفضيلة رئيس دائرة الأحوال الشخصية',
                    r'مذكرة جوابية',
                    r'دعوى معارضة في صك حصر إرث'
                ],
                'indicators': ['حصر إرث', 'زواج', 'أحوال شخصية'],
                'memo_types': ['مذكرة_جوابية_أحوال', 'معارضة_حصر_إرث']
            },
            'criminal': {
                'start_patterns': [
                    r'محكمة الاستئناف.*الجزائية',
                    r'المحكمة الجزائية',
                    r'هيئة التحقيق والادعاء العام'
                ],
                'indicators': ['تعزير', 'جريمة', 'متهم', 'جزائية'],
                'memo_types': ['استئناف_جزائي', 'دفاع_جنائي']
            },
            'administrative': {
                'start_patterns': [
                    r'محكمة الاستئناف الإداري لديوان المظالم',
                    r'الدائرة الإدارية بديوان المظالم'
                ],
                'indicators': ['ديوان المظالم', 'هيئة حكومية'],
                'memo_types': ['تعويض_إداري', 'طعن_قرار_إداري']
            }
        }
        
        self.document_end_patterns = [
            r'والله الموفق',
            r'وتفضلوا بقبول',
            r'والله أعلم',
            r'التوقيع:',
            r'التاريخ:'
        ]
    
    async def extract_individual_memos(self, file_path: str) -> List[LegalMemo]:
        """Extract individual memos from 25K lines file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        memos = []
        current_memo_lines = []
        start_line = 0
        
        for i, line in enumerate(lines):
            # Check for memo start
            if self._is_memo_start(line):
                # Save previous memo if exists
                if current_memo_lines:
                    memo = self._create_memo_from_lines(
                        current_memo_lines, start_line, i-1
                    )
                    if memo:
                        memos.append(memo)
                
                # Start new memo
                current_memo_lines = [line]
                start_line = i
            else:
                current_memo_lines.append(line)
        
        # Don't forget the last memo
        if current_memo_lines:
            memo = self._create_memo_from_lines(
                current_memo_lines, start_line, len(lines)-1
            )
            if memo:
                memos.append(memo)
        
        return memos
    
    def _is_memo_start(self, line: str) -> bool:
        """Check if line indicates start of new memo"""
        for court_system, patterns in self.court_patterns.items():
            for pattern in patterns['start_patterns']:
                if re.search(pattern, line):
                    return True
        return False
    
    def _create_memo_from_lines(self, lines: List[str], start_line: int, end_line: int) -> Optional[LegalMemo]:
        """Create memo object from lines"""
        content = ''.join(lines).strip()
        
        # Skip if too short
        if len(content) < 100:
            return None
        
        # Classify court system
        court_system, confidence = self._classify_court_system(content)
        memo_type = self._determine_memo_type(content, court_system)
        complexity = self._assess_complexity(content)
        
        return LegalMemo(
            content=content,
            court_system=court_system,
            memo_type=memo_type,
            complexity_level=complexity,
            confidence_score=confidence,
            start_line=start_line,
            end_line=end_line
        )
    
    def _classify_court_system(self, content: str) -> Tuple[str, float]:
        """Classify memo by court system with confidence score"""
        scores = {}
        
        for court_system, patterns in self.court_patterns.items():
            score = 0
            
            # Check start patterns
            for pattern in patterns['start_patterns']:
                if re.search(pattern, content):
                    score += 3
            
            # Check indicators
            for indicator in patterns['indicators']:
                if indicator in content:
                    score += 1
            
            scores[court_system] = score
        
        # Find best match
        best_court = max(scores, key=scores.get)
        max_score = scores[best_court]
        
        # Calculate confidence
        confidence = min(max_score / 5.0, 1.0)  # Normalize to 0-1
        
        return best_court if confidence > 0.4 else 'unknown', confidence
    
    def _determine_memo_type(self, content: str, court_system: str) -> str:
        """Determine specific memo type within court system"""
        if court_system == 'unknown':
            return 'unknown'
        
        memo_types = self.court_patterns[court_system]['memo_types']
        
        # Simple keyword matching - can be enhanced
        for memo_type in memo_types:
            if memo_type.replace('_', ' ') in content:
                return memo_type
        
        return memo_types[0]  # Default to first type
    
    def _assess_complexity(self, content: str) -> str:
        """Assess memo complexity based on content"""
        # Count legal indicators
        article_count = len(re.findall(r'المادة\s*\d+', content))
        fiqh_indicators = len(re.findall(r'(المبسوط|العناية|التاج والإكليل)', content))
        precedent_indicators = len(re.findall(r'(قضت|حكمت|قرار)', content))
        
        total_score = article_count + fiqh_indicators * 2 + precedent_indicators
        
        if total_score >= 10:
            return 'very_high'
        elif total_score >= 6:
            return 'high'
        elif total_score >= 3:
            return 'medium'
        else:
            return 'simple'
    
    def chunk_legal_memo(self, memo: LegalMemo) -> List[Chunk]:
        """Chunk memo based on court-specific structure"""
        
        if memo.court_system == 'execution':
            return self._chunk_by_numbered_defenses(memo)
        elif memo.court_system == 'civil':
            return self._chunk_by_categorized_arguments(memo)
        elif memo.court_system == 'family':
            return self._chunk_family_law_memo(memo)
        elif memo.court_system == 'criminal':
            return self._chunk_criminal_defense(memo)
        else:
            return self._chunk_semantically(memo)
    
    def _chunk_by_numbered_defenses(self, memo: LegalMemo) -> List[Chunk]:
        """Chunk execution court memos by numbered defenses (١- ٢- ٣-)"""
        import uuid
        
        # Split by defense numbers
        defense_pattern = r'([١٢٣٤٥]-.*?)(?=[١٢٣٤٥]-|$)'
        defenses = re.findall(defense_pattern, memo.content, re.DOTALL)
        
        chunks = []
        for i, defense in enumerate(defenses):
            chunk = Chunk(
                id=str(uuid.uuid4()),
                title=f"دفع تنفيذي رقم {i+1}",
                content=defense.strip(),
                metadata={
                    'chunk_type': 'execution_defense',
                    'defense_number': i+1,
                    'court_system': 'execution',
                    'memo_type': memo.memo_type,
                    'complexity': memo.complexity_level,
                    'argument_structure': 'numbered_defense'
                }
            )
            chunks.append(chunk)
        
        return chunks if chunks else [self._create_single_chunk(memo)]
    
    def _chunk_by_categorized_arguments(self, memo: LegalMemo) -> List[Chunk]:
        """Chunk civil court memos by categories (أولاً، ثانياً، ثالثاً)"""
        import uuid
        
        # Split by Arabic ordinals
        category_pattern = r'((?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً).*?)(?=(?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً)|$)'
        categories = re.findall(category_pattern, memo.content, re.DOTALL)
        
        chunks = []
        for i, category in enumerate(categories):
            chunk = Chunk(
                id=str(uuid.uuid4()),
                title=f"حجة مدنية رقم {i+1}",
                content=category.strip(),
                metadata={
                    'chunk_type': 'civil_argument',
                    'argument_number': i+1,
                    'court_system': 'civil',
                    'memo_type': memo.memo_type,
                    'complexity': memo.complexity_level,
                    'argument_structure': 'categorized_argument'
                }
            )
            chunks.append(chunk)
        
        return chunks if chunks else [self._create_single_chunk(memo)]
    
    def _chunk_family_law_memo(self, memo: LegalMemo) -> List[Chunk]:
        """Chunk family court memos with fiqh consideration"""
        import uuid
        
        # Look for numbered arguments and fiqh references
        numbered_pattern = r'([١٢٣٤٥].*?)(?=[١٢٣٤٥]|$)'
        numbered_args = re.findall(numbered_pattern, memo.content, re.DOTALL)
        
        chunks = []
        for i, arg in enumerate(numbered_args):
            chunk = Chunk(
                id=str(uuid.uuid4()),
                title=f"دفع شرعي رقم {i+1}",
                content=arg.strip(),
                metadata={
                    'chunk_type': 'family_law_argument',
                    'argument_number': i+1,
                    'court_system': 'family',
                    'memo_type': memo.memo_type,
                    'complexity': memo.complexity_level,
                    'fiqh_intensive': True,
                    'argument_structure': 'numbered_with_fiqh'
                }
            )
            chunks.append(chunk)
        
        return chunks if chunks else [self._create_single_chunk(memo)]
    
    def _chunk_criminal_defense(self, memo: LegalMemo) -> List[Chunk]:
        """Chunk criminal memos by substantive/procedural parts"""
        import uuid
        
        # Look for two-part structure
        parts = []
        if 'الشق الأول' in memo.content and 'الشق الثاني' in memo.content:
            parts_pattern = r'(الشق (?:الأول|الثاني).*?)(?=الشق (?:الأول|الثاني)|$)'
            parts = re.findall(parts_pattern, memo.content, re.DOTALL)
        
        chunks = []
        for i, part in enumerate(parts):
            part_type = 'موضوعي' if 'الأول' in part else 'شكلي'
            chunk = Chunk(
                id=str(uuid.uuid4()),
                title=f"الشق {part_type}",
                content=part.strip(),
                metadata={
                    'chunk_type': 'criminal_defense_part',
                    'part_type': part_type,
                    'court_system': 'criminal',
                    'memo_type': memo.memo_type,
                    'complexity': memo.complexity_level,
                    'argument_structure': 'two_part_defense'
                }
            )
            chunks.append(chunk)
        
        return chunks if chunks else [self._create_single_chunk(memo)]
    
    def _chunk_semantically(self, memo: LegalMemo) -> List[Chunk]:
        """Fallback semantic chunking for unknown patterns"""
        import uuid
        
        # Simple paragraph-based chunking
        paragraphs = [p.strip() for p in memo.content.split('\n\n') if p.strip()]
        
        chunks = []
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 50:  # Skip very short paragraphs
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    title=f"فقرة قانونية {i+1}",
                    content=paragraph,
                    metadata={
                        'chunk_type': 'semantic_paragraph',
                        'paragraph_number': i+1,
                        'court_system': memo.court_system,
                        'memo_type': memo.memo_type,
                        'complexity': memo.complexity_level,
                        'argument_structure': 'semantic'
                    }
                )
                chunks.append(chunk)
        
        return chunks if chunks else [self._create_single_chunk(memo)]
    
    def _create_single_chunk(self, memo: LegalMemo) -> Chunk:
        """Create single chunk when pattern matching fails"""
        import uuid
        
        return Chunk(
            id=str(uuid.uuid4()),
            title=f"مذكرة {memo.court_system}",
            content=memo.content,
            metadata={
                'chunk_type': 'complete_memo',
                'court_system': memo.court_system,
                'memo_type': memo.memo_type,
                'complexity': memo.complexity_level,
                'argument_structure': 'complete'
            }
        )