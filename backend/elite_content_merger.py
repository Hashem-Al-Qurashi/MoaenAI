import re
import hashlib
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from difflib import SequenceMatcher

@dataclass
class LegalFact:
    """Structured legal fact with metadata"""
    content: str
    article_reference: Optional[str]
    confidence: float
    source_agent: str
    fact_type: str  # penalty, right, procedure, etc.
    importance_score: float
    
class EliteContentMerger:
    """
    🎯 INDUSTRIAL-STRENGTH CONTENT MERGER
    
    Handles sophisticated legal document merging with:
    - Semantic deduplication (not just string matching)
    - Legal citation consolidation
    - Hierarchical content organization
    - Cross-reference validation
    - Professional legal memo formatting
    """
    
    def __init__(self):
        self.legal_patterns = {
            'articles': r'المادة\s*\(?\s*(\d+)\s*\)?\s*من\s+([^،\.\n]+)',
            'decisions': r'القرار\s+رقم\s+(\d+(?:/\d+)?)',
            'penalties': r'(غرامة|عقوبة|جزاء)[^\.]*',
            'rights': r'(حق|حقوق)[^\.]*',
            'procedures': r'(إجراء|خطوة|مرحلة)[^\.]*',
            'deadlines': r'خلال\s+(\d+)\s*(يوم|أسبوع|شهر)',
            'amounts': r'(\d+(?:,\d{3})*)\s*(ريال|درهم)',
        }
        
        self.fact_importance_weights = {
            'penalty': 10,
            'fine': 9,
            'deadline': 8,
            'procedure': 7,
            'right': 6,
            'general': 3
        }
    
    def merge_multi_intent_outputs(
        self, 
        intent_outputs: Dict[str, str],
        original_query: str,
        complexity_level: str = "simple"
    ) -> str:
        """
        Advanced multi-intent merging with sophisticated deduplication
        
        Args:
            intent_outputs: {intent_type: content} from multiple agents
            original_query: Original user query for context
            complexity_level: simple|complex for formatting depth
        
        Returns:
            Unified, professional legal memorandum
        """
        
        # Step 1: Extract structured legal facts from all outputs
        all_facts = []
        for intent_type, content in intent_outputs.items():
            facts = self._extract_legal_facts(content, intent_type)
            all_facts.extend(facts)
        
        # Step 2: Intelligent deduplication using semantic similarity
        unique_facts = self._deduplicate_facts_advanced(all_facts)
        
        # Step 3: Cross-validate citations and references
        validated_facts = self._validate_cross_references(unique_facts)
        
        # Step 4: Organize by legal hierarchy and importance
        organized_content = self._organize_by_legal_hierarchy(validated_facts)
        
        # Step 5: Generate final memo based on complexity level
        if complexity_level == "complex":
            return self._generate_professional_memo(organized_content, original_query)
        else:
            return self._generate_simple_explanation(organized_content, original_query)
    
    def _extract_legal_facts(self, content: str, intent_type: str) -> List[LegalFact]:
        """Extract structured legal facts from raw content"""
        
        facts = []
        sentences = self._split_arabic_sentences(content)
        
        for sentence in sentences:
            if len(sentence.strip()) < 20:  # Skip very short sentences
                continue
            
            # Extract article references
            article_ref = self._extract_article_reference(sentence)
            
            # Determine fact type
            fact_type = self._classify_fact_type(sentence, intent_type)
            
            # Calculate importance score
            importance = self._calculate_importance(sentence, fact_type)
            
            # Calculate confidence based on citation presence and structure
            confidence = self._calculate_fact_confidence(sentence, article_ref)
            
            fact = LegalFact(
                content=sentence.strip(),
                article_reference=article_ref,
                confidence=confidence,
                source_agent=intent_type,
                fact_type=fact_type,
                importance_score=importance
            )
            
            facts.append(fact)
        
        return facts
    
    def _deduplicate_facts_advanced(self, facts: List[LegalFact]) -> List[LegalFact]:
        """Advanced deduplication using multiple similarity metrics"""
        
        unique_facts = []
        seen_hashes = set()
        
        # Sort by importance to keep the highest-quality version of duplicates
        facts_sorted = sorted(facts, key=lambda f: f.importance_score, reverse=True)
        
        for fact in facts_sorted:
            # Create semantic fingerprint
            fingerprint = self._create_semantic_fingerprint(fact.content)
            
            # Check for exact duplicates
            if fingerprint in seen_hashes:
                continue
            
            # Check for semantic similarity with existing facts
            is_duplicate = False
            for existing_fact in unique_facts:
                similarity = self._calculate_semantic_similarity(
                    fact.content, 
                    existing_fact.content
                )
                
                # High similarity threshold for legal content
                if similarity > 0.85:
                    # Keep the higher quality version
                    if fact.confidence > existing_fact.confidence:
                        unique_facts.remove(existing_fact)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_facts.append(fact)
                seen_hashes.add(fingerprint)
        
        return unique_facts
    
    def _validate_cross_references(self, facts: List[LegalFact]) -> List[LegalFact]:
        """Validate and consolidate legal citations across facts"""
        
        # Group facts by article reference
        article_groups = defaultdict(list)
        for fact in facts:
            if fact.article_reference:
                article_groups[fact.article_reference].append(fact)
        
        # Validate consistency within article groups
        validated_facts = []
        for fact in facts:
            if fact.article_reference and len(article_groups[fact.article_reference]) > 1:
                # Multiple facts reference same article - validate consistency
                group = article_groups[fact.article_reference]
                consensus_confidence = sum(f.confidence for f in group) / len(group)
                fact.confidence = min(fact.confidence, consensus_confidence)
            
            validated_facts.append(fact)
        
        return validated_facts
    
    def _organize_by_legal_hierarchy(self, facts: List[LegalFact]) -> Dict[str, List[LegalFact]]:
        """Organize facts by legal importance and logical flow"""
        
        organized = {
            'penalties_and_fines': [],
            'legal_rights': [],
            'procedures_and_steps': [],
            'deadlines_and_timeframes': [],
            'contact_information': [],
            'general_provisions': []
        }
        
        for fact in facts:
            # Classify into categories based on content analysis
            if any(keyword in fact.content for keyword in ['عقوبة', 'غرامة', 'جزاء']):
                organized['penalties_and_fines'].append(fact)
            elif any(keyword in fact.content for keyword in ['حق', 'حقوق']):
                organized['legal_rights'].append(fact)
            elif any(keyword in fact.content for keyword in ['إجراء', 'خطوة', 'مرحلة']):
                organized['procedures_and_steps'].append(fact)
            elif any(keyword in fact.content for keyword in ['خلال', 'مهلة', 'موعد']):
                organized['deadlines_and_timeframes'].append(fact)
            elif any(keyword in fact.content for keyword in ['هاتف', 'موقع', 'جهة']):
                organized['contact_information'].append(fact)
            else:
                organized['general_provisions'].append(fact)
        
        # Sort each category by importance
        for category in organized:
            organized[category].sort(key=lambda f: f.importance_score, reverse=True)
        
        return organized
    
    def _generate_professional_memo(self, organized_content: Dict, query: str) -> str:
        """Generate professional legal memorandum format"""
        
        memo_parts = []
        
        # Memo header
        memo_parts.append("# 📋 مذكرة قانونية")
        memo_parts.append(f"**الموضوع:** {query}")
        memo_parts.append(f"**التاريخ:** {datetime.now().strftime('%Y-%m-%d')}")
        memo_parts.append("---")
        
        # Executive summary
        memo_parts.append("## 📊 الملخص التنفيذي")
        summary = self._generate_executive_summary(organized_content)
        memo_parts.append(summary)
        memo_parts.append("")
        
        # Main sections
        section_titles = {
            'penalties_and_fines': '⚖️ العقوبات والغرامات',
            'legal_rights': '🔍 الحقوق القانونية',
            'procedures_and_steps': '📋 الإجراءات المطلوبة',
            'deadlines_and_timeframes': '⏰ المواعيد والمهل',
            'contact_information': '📞 معلومات التواصل',
            'general_provisions': '📜 أحكام عامة'
        }
        
        for category, title in section_titles.items():
            facts = organized_content.get(category, [])
            if facts:
                memo_parts.append(f"## {title}")
                
                for i, fact in enumerate(facts, 1):
                    confidence_indicator = "🟢" if fact.confidence > 0.8 else "🟡" if fact.confidence > 0.6 else "🔴"
                    memo_parts.append(f"{i}️⃣ {confidence_indicator} {fact.content}")
                    
                    if fact.article_reference:
                        memo_parts.append(f"   📚 **المرجع:** {fact.article_reference}")
                
                memo_parts.append("")
        
        # Legal disclaimer
        memo_parts.append("---")
        memo_parts.append("⚠️ **تنويه قانوني:** هذه المذكرة تحتوي على معلومات قانونية عامة وليست بديلاً عن الاستشارة القانونية المتخصصة.")
        
        return "\n".join(memo_parts)
    
    def _generate_simple_explanation(self, organized_content: Dict, query: str) -> str:
        """Generate simplified explanation format"""
        
        explanation_parts = []
        
        # Simple header
        explanation_parts.append("## 💡 الإجابة القانونية")
        explanation_parts.append("")
        
        # Priority content first
        priority_categories = ['penalties_and_fines', 'legal_rights', 'procedures_and_steps']
        
        for category in priority_categories:
            facts = organized_content.get(category, [])
            if facts:
                # Take top 3 most important facts from each category
                top_facts = facts[:3]
                
                for fact in top_facts:
                    explanation_parts.append(f"🔹 {fact.content}")
                
                explanation_parts.append("")
        
        # Contact info if available
        contact_facts = organized_content.get('contact_information', [])
        if contact_facts:
            explanation_parts.append("## 📞 للمزيد من المساعدة")
            for fact in contact_facts[:2]:  # Top 2 contact methods
                explanation_parts.append(f"• {fact.content}")
        
        return "\n".join(explanation_parts)
    
    # Helper methods
    def _split_arabic_sentences(self, text: str) -> List[str]:
        """Advanced Arabic sentence splitting"""
        # Handle Arabic punctuation and legal formatting
        sentences = re.split(r'(?<=[.؟!:])\s+|(?<=\n)\s*(?=\d+[\.)])|(?<=\n)\s*(?=[•▪])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_article_reference(self, sentence: str) -> Optional[str]:
        """Extract legal article references"""
        article_match = re.search(self.legal_patterns['articles'], sentence)
        if article_match:
            return f"المادة {article_match.group(1)} من {article_match.group(2)}"
        
        decision_match = re.search(self.legal_patterns['decisions'], sentence)
        if decision_match:
            return f"القرار رقم {decision_match.group(1)}"
        
        return None
    
    def _classify_fact_type(self, sentence: str, intent_type: str) -> str:
        """Classify fact type based on content and intent"""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['عقوبة', 'غرامة', 'جزاء']):
            return 'penalty'
        elif any(word in sentence_lower for word in ['حق', 'حقوق']):
            return 'right'
        elif any(word in sentence_lower for word in ['إجراء', 'خطوة']):
            return 'procedure'
        else:
            return intent_type
    
    def _calculate_importance(self, sentence: str, fact_type: str) -> float:
        """Calculate importance score for ranking"""
        base_score = self.fact_importance_weights.get(fact_type, 3)
        
        # Boost for specific legal indicators
        if re.search(r'\d+', sentence):  # Contains numbers (amounts, dates, etc.)
            base_score += 2
        
        if re.search(self.legal_patterns['articles'], sentence):  # Has article reference
            base_score += 3
        
        # Length factor (very short or very long sentences are less important)
        length_factor = 1.0
        if len(sentence) < 30:
            length_factor = 0.8
        elif len(sentence) > 200:
            length_factor = 0.9
        
        return base_score * length_factor
    
    def _calculate_fact_confidence(self, sentence: str, article_ref: Optional[str]) -> float:
        """Calculate confidence score for the fact"""
        base_confidence = 0.7
        
        if article_ref:
            base_confidence += 0.2
        
        # Check for uncertainty indicators
        uncertainty_words = ['ربما', 'يمكن', 'قد', 'عادة', 'غالباً']
        if any(word in sentence for word in uncertainty_words):
            base_confidence -= 0.15
        
        # Check for definitiveness indicators
        definitive_words = ['يجب', 'ملزم', 'محظور', 'مطلوب']
        if any(word in sentence for word in definitive_words):
            base_confidence += 0.1
        
        return max(0.1, min(1.0, base_confidence))
    
    def _create_semantic_fingerprint(self, text: str) -> str:
        """Create semantic fingerprint for deduplication"""
        # Normalize Arabic text
        normalized = re.sub(r'[^\w\s]', '', text)
        normalized = re.sub(r'\s+', ' ', normalized).strip().lower()
        
        # Create hash
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Simple but effective for Arabic legal text
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _generate_executive_summary(self, organized_content: Dict) -> str:
        """Generate executive summary from organized content"""
        summary_parts = []
        
        # Count facts by category
        total_penalties = len(organized_content.get('penalties_and_fines', []))
        total_rights = len(organized_content.get('legal_rights', []))
        total_procedures = len(organized_content.get('procedures_and_steps', []))
        
        if total_penalties > 0:
            summary_parts.append(f"• تم تحديد {total_penalties} عقوبة أو غرامة قانونية")
        
        if total_rights > 0:
            summary_parts.append(f"• تم توضيح {total_rights} حق قانوني")
        
        if total_procedures > 0:
            summary_parts.append(f"• تم شرح {total_procedures} إجراء مطلوب")
        
        if not summary_parts:
            summary_parts.append("• تم تحليل الموقف القانوني وتقديم التوضيحات اللازمة")
        
        return "\n".join(summary_parts)

# Usage example integration point
def integrate_content_merger_with_orchestrator():
    """Example of how to integrate with the main orchestrator"""
    
    # In your process_legal_query_streaming method, after multi-intent processing:
    
    merger = EliteContentMerger()
    
    # Collect outputs from multiple intents
    intent_outputs = {
        "penalty_explanation": penalty_content,
        "procedure_guide": procedure_content,
        "legal_dispute": dispute_content
    }
    
    # Merge intelligently
    final_merged_content = merger.merge_multi_intent_outputs(
        intent_outputs=intent_outputs,
        original_query=query,
        complexity_level=complexity_level
    )
    
    return final_merged_content