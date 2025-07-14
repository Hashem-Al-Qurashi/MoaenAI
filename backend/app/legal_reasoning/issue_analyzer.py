"""
Enhanced Legal Issue Analyzer - Conversation-Aware Legal Reasoning
Analyzes user queries AND conversation context for intelligent legal advice
Solves repetition and conversation flow issues identified by legal experts
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re


@dataclass
class ConversationContext:
    """Represents conversation flow and context"""
    is_follow_up: bool           # True if this continues previous topic
    is_repetition: bool          # True if asking same thing differently  
    previous_topic: Optional[str] # What was discussed before
    conversation_flow: str       # 'first_message', 'continuation', 'topic_change'
    reference_needed: bool       # Should reference previous discussion
    topics_discussed: List[str]  # All legal topics covered so far


@dataclass
class LegalIssue:
    """Enhanced legal issue analysis with conversation awareness"""
    issue_type: str              # 'criminal_procedure', 'contract_dispute', etc.
    legal_domain: str            # 'criminal', 'civil', 'commercial', 'administrative'
    user_position: str           # 'defendant', 'plaintiff', 'seeking_advice'
    urgency_level: str           # 'emergency', 'planning', 'research'
    advice_type: str             # 'defense_strategy', 'procedural_guide', etc.
    
    # NEW: Conversation intelligence
    conversation_context: ConversationContext
    prompt_strategy: str         # How to structure the response
    avoid_repetition: List[str]  # Topics to avoid repeating


class EnhancedLegalIssueAnalyzer:
    """
    Enhanced Legal Issue Analyzer with Conversation Intelligence
    Solves academic repetition and conversation flow problems
    """
    
    def __init__(self):
        """Initialize with legal pattern recognition and conversation intelligence"""
        
        # Existing legal patterns (keep unchanged)
        self.criminal_patterns = {
            'keywords': ['سجين', 'موقوف', 'متهم', 'جريمة', 'عقوبة', 'قصاص', 'حد', 'تعزير', 'جزائية'],
            'procedures': ['حضور', 'جلسة', 'محاكمة', 'استجواب', 'تحقيق']
        }
        
        self.civil_patterns = {
            'keywords': ['دعوى', 'مرافعة', 'خصومة', 'استئناف', 'طعن', 'تبليغ', 'مدنية'],
            'procedures': ['تقديم', 'رفع', 'إجراءات', 'موعد']
        }
        
        self.contract_patterns = {
            'keywords': ['قرض', 'عقد', 'اتفاق', 'شركة', 'تجارة', 'استثمار', 'أعمال'],
            'disputes': ['نزاع', 'خلاف', 'مطالبة', 'رد', 'تعويض']
        }
        
        self.employment_patterns = {
            'keywords': ['عمل', 'عامل', 'موظف', 'راتب', 'أجر', 'إجازة', 'وظيفة', 'صاحب'],
            'issues': ['حقوق', 'التزامات', 'فصل', 'استقالة']
        }
        
        self.administrative_patterns = {
            'keywords': ['ترخيص', 'تصريح', 'شروط', 'متطلبات', 'محاماة', 'مزاولة'],
            'procedures': ['تقديم', 'حصول', 'تجديد']
        }
        
        # NEW: Conversation flow patterns
        self.follow_up_patterns = [
            'وماذا', 'وما هي', 'وكيف', 'ولكن', 'إذن', 'هل يجوز أيضاً', 'وفي حالة',
            'بناءً على ما ذكرت', 'كما ذكرت', 'بالإضافة', 'أيضاً', 'كذلك',
            'وماذا لو', 'في هذه الحالة', 'أما إذا', 'والآن'
        ]
        
        self.repetition_patterns = [
            'أعيد السؤال', 'مرة أخرى', 'لم أفهم', 'غير واضح', 'اشرح أكثر',
            'تفصيل أكثر', 'بشكل أوضح', 'مرة ثانية'
        ]
        
        self.topic_change_patterns = [
            'سؤال آخر', 'موضوع مختلف', 'أريد أن أسأل عن', 'بخصوص موضوع آخر',
            'انتقل إلى', 'الآن أريد', 'سؤال جديد'
        ]

    async def analyze_issue_with_context(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> LegalIssue:
        """
        Enhanced analysis with conversation context awareness
        
        Args:
            query: Current user's legal question
            conversation_history: Previous messages in conversation
            
        Returns:
            Enhanced LegalIssue with conversation intelligence
        """
        
        query_lower = query.lower()
        
        # Stage 1: Analyze conversation context
        conversation_context = self._analyze_conversation_context(
            query_lower, conversation_history or []
        )
        
        # Stage 2: Standard legal issue analysis (unchanged)
        issue_type, legal_domain = self._classify_issue_type(query_lower)
        user_position = self._determine_user_position(query_lower, issue_type)
        urgency_level = self._assess_urgency(query_lower)
        advice_type = self._determine_advice_type(query_lower, user_position)
        
        # Stage 3: Determine prompt strategy based on conversation flow
        prompt_strategy = self._determine_prompt_strategy(
            conversation_context, issue_type, conversation_history or []
        )
        
        # Stage 4: Identify topics to avoid repeating
        avoid_repetition = self._identify_repetition_topics(
            conversation_context, conversation_history or []
        )
        
        return LegalIssue(
            issue_type=issue_type,
            legal_domain=legal_domain,
            user_position=user_position,
            urgency_level=urgency_level,
            advice_type=advice_type,
            conversation_context=conversation_context,
            prompt_strategy=prompt_strategy,
            avoid_repetition=avoid_repetition
        )
    
    # Backward compatibility method
    async def analyze_issue(self, query: str) -> LegalIssue:
        """
        Backward compatible method for existing code
        """
        return await self.analyze_issue_with_context(query, None)
    
    def _analyze_conversation_context(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> ConversationContext:
        """Analyze conversation flow and context"""
        
        if not conversation_history:
            # First message in conversation
            return ConversationContext(
                is_follow_up=False,
                is_repetition=False,
                previous_topic=None,
                conversation_flow='first_message',
                reference_needed=False,
                topics_discussed=[]
            )
        
        # Get recent messages for analysis
        recent_messages = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        user_messages = [msg['content'] for msg in recent_messages if msg['role'] == 'user']
        assistant_messages = [msg['content'] for msg in recent_messages if msg['role'] == 'assistant']
        
        # Detect follow-up patterns
        is_follow_up = any(pattern in query for pattern in self.follow_up_patterns)
        
        # Detect repetition patterns
        is_repetition = (
            any(pattern in query for pattern in self.repetition_patterns) or
            self._is_semantic_repetition(query, user_messages)
        )
        
        # Detect topic change
        is_topic_change = any(pattern in query for pattern in self.topic_change_patterns)
        
        # Determine conversation flow
        if is_topic_change:
            conversation_flow = 'topic_change'
        elif is_follow_up or self._is_same_legal_domain(query, recent_messages):
            conversation_flow = 'continuation'
        else:
            conversation_flow = 'new_topic'
        
        # Extract previous topics discussed
        topics_discussed = self._extract_discussed_topics(recent_messages)
        previous_topic = topics_discussed[-1] if topics_discussed else None
        
        # Determine if reference to previous discussion is needed
        reference_needed = (
         is_follow_up and len(conversation_history) > 0 and
        (conversation_flow == 'continuation' and not is_repetition)
        )
        
        return ConversationContext(
            is_follow_up=is_follow_up,
            is_repetition=is_repetition,
            previous_topic=previous_topic,
            conversation_flow=conversation_flow,
            reference_needed=reference_needed,
            topics_discussed=topics_discussed
        )
    
    def _is_semantic_repetition(self, current_query: str, previous_user_messages: List[str]) -> bool:
        """Detect if user is asking the same thing in different words"""
        
        if not previous_user_messages:
            return False
        
        # Get the last few user messages
        recent_messages = previous_user_messages[-3:]
        
        # Extract key legal terms from current query
        current_terms = self._extract_key_legal_terms(current_query)
        
        for prev_message in recent_messages:
            prev_terms = self._extract_key_legal_terms(prev_message)
            
            # Calculate term overlap
            if current_terms and prev_terms:
                overlap = len(current_terms.intersection(prev_terms))
                similarity = overlap / len(current_terms.union(prev_terms))
                
                # If 70%+ overlap in legal terms, likely repetition
                if similarity >= 0.7:
                    return True
        
        return False
    
    def _extract_key_legal_terms(self, text: str) -> set:
        """Extract key legal terms from text for comparison"""
        
        # All legal keywords from patterns
        all_legal_terms = []
        for patterns in [self.criminal_patterns, self.civil_patterns, 
                        self.contract_patterns, self.employment_patterns, 
                        self.administrative_patterns]:
            for term_group in patterns.values():
                all_legal_terms.extend(term_group)
        
        # Find legal terms in text
        found_terms = set()
        text_lower = text.lower()
        
        for term in all_legal_terms:
            if term in text_lower:
                found_terms.add(term)
        
        return found_terms
    
    def _is_same_legal_domain(self, query: str, recent_messages: List[Dict[str, str]]) -> bool:
        """Check if current query is in same legal domain as recent discussion"""
        
        if not recent_messages:
            return False
        
        # Get current domain
        _, current_domain = self._classify_issue_type(query.lower())
        
        # Check recent user messages for domain
        recent_user_messages = [msg['content'] for msg in recent_messages[-3:] if msg['role'] == 'user']
        
        for msg in recent_user_messages:
            _, prev_domain = self._classify_issue_type(msg.lower())
            if current_domain == prev_domain and current_domain != 'general':
                return True
        
        return False
    
    def _extract_discussed_topics(self, messages: List[Dict[str, str]]) -> List[str]:
        """Extract legal topics that have been discussed"""
        
        topics = []
        
        for msg in messages:
            if msg['role'] == 'user':
                issue_type, _ = self._classify_issue_type(msg['content'].lower())
                if issue_type != 'general_legal':
                    topics.append(issue_type)
        
        # Remove duplicates while preserving order
        unique_topics = []
        for topic in topics:
            if topic not in unique_topics:
                unique_topics.append(topic)
        
        return unique_topics
    
    def _determine_prompt_strategy(
        self, 
        context: ConversationContext, 
        issue_type: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Determine how to structure the response based on conversation flow"""
        
        if context.conversation_flow == 'first_message':
            return 'comprehensive_first_response'
        
        elif context.is_repetition:
            return 'clarification_focused'
        
        elif context.is_follow_up and context.reference_needed:
            return 'build_on_previous'
        
        elif context.conversation_flow == 'continuation':
            return 'continue_topic'
        
        elif context.conversation_flow == 'topic_change':
            return 'new_topic_acknowledge'
        
        else:
            return 'standard_response'
    
    def _identify_repetition_topics(
        self, 
        context: ConversationContext,
        conversation_history: List[Dict[str, str]]
    ) -> List[str]:
        """Identify topics/concepts that have been covered and shouldn't be repeated"""
        
        if not conversation_history or context.conversation_flow == 'first_message':
            return []
        
        # Extract key concepts from assistant responses
        covered_concepts = []
        assistant_messages = [msg['content'] for msg in conversation_history if msg['role'] == 'assistant']
        
        for response in assistant_messages[-2:]:  # Last 2 assistant responses
            # Look for key legal concepts that were explained
            if 'المادة' in response:
                covered_concepts.append('legal_articles')
            if 'إجراءات' in response:
                covered_concepts.append('procedures')
            if 'حقوق' in response:
                covered_concepts.append('rights')
            if 'التزامات' in response:
                covered_concepts.append('obligations')
            if 'شروط' in response:
                covered_concepts.append('requirements')
        
        return list(set(covered_concepts))
    
    # Keep all existing methods unchanged for backward compatibility
    def _classify_issue_type(self, query: str) -> tuple[str, str]:
        """Classify the type of legal issue (unchanged)"""
        
        criminal_score = self._calculate_pattern_score(query, self.criminal_patterns)
        civil_score = self._calculate_pattern_score(query, self.civil_patterns)
        contract_score = self._calculate_pattern_score(query, self.contract_patterns)
        employment_score = self._calculate_pattern_score(query, self.employment_patterns)
        admin_score = self._calculate_pattern_score(query, self.administrative_patterns)
        
        scores = {
            'criminal_procedure': (criminal_score, 'criminal'),
            'civil_procedure': (civil_score, 'civil'),
            'contract_dispute': (contract_score, 'commercial'),
            'employment_law': (employment_score, 'commercial'),
            'administrative_law': (admin_score, 'administrative')
        }
        
        best_match = max(scores.items(), key=lambda x: x[1][0])
        
        if best_match[1][0] > 0:
            return best_match[0], best_match[1][1]
        else:
            return 'general_legal', 'general'
    
    def _calculate_pattern_score(self, query: str, patterns: Dict) -> int:
        """Calculate how well query matches legal patterns (unchanged)"""
        score = 0
        
        for pattern_group in patterns.values():
            for pattern in pattern_group:
                if pattern in query:
                    score += 1
        
        return score
    
    def _determine_user_position(self, query: str, issue_type: str) -> str:
        """Determine user's position in legal matter (unchanged)"""
        
        defense_indicators = ['مدعى عليه', 'متهم', 'رد على', 'دفاع', 'دفع']
        plaintiff_indicators = ['مدعي', 'شاكي', 'رفع دعوى', 'مقاضاة']
        advice_indicators = ['ما هي', 'كيف', 'ماذا', 'متى', 'شروط', 'إجراءات']
        
        if any(indicator in query for indicator in defense_indicators):
            return 'defendant'
        elif any(indicator in query for indicator in plaintiff_indicators):
            return 'plaintiff'
        elif any(indicator in query for indicator in advice_indicators):
            return 'seeking_advice'
        else:
            return 'general_inquiry'
    
    def _assess_urgency(self, query: str) -> str:
        """Assess urgency level of legal matter (unchanged)"""
        
        emergency_indicators = ['عاجل', 'فوري', 'حال', 'أمس', 'غد', 'اليوم']
        planning_indicators = ['أريد', 'أنوي', 'سأقوم', 'تخطيط', 'مستقبل']
        
        if any(indicator in query for indicator in emergency_indicators):
            return 'emergency'
        elif any(indicator in query for indicator in planning_indicators):
            return 'planning'
        else:
            return 'research'
    
    def _determine_advice_type(self, query: str, user_position: str) -> str:
        """Determine what type of legal advice is needed (unchanged)"""
        
        if user_position == 'defendant':
            return 'defense_strategy'
        elif user_position == 'plaintiff':
            return 'action_strategy'
        elif 'شروط' in query or 'متطلبات' in query:
            return 'compliance_guide'
        elif 'حقوق' in query or 'التزامات' in query:
            return 'rights_explanation'
        elif 'إجراءات' in query or 'كيف' in query:
            return 'procedural_guide'
        else:
            return 'general_advice'


# Backward compatibility alias
LegalIssueAnalyzer = EnhancedLegalIssueAnalyzer