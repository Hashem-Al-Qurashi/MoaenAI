"""
Fixed Clarification Controller - Production Ready
Resolves import issues and simplifies for real-world deployment
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import hashlib
import re
from datetime import datetime

class ClarificationTrigger(Enum):
    """Types of clarification triggers"""
    LOW_CONFIDENCE = "low_confidence"
    AMBIGUOUS_INTENT = "ambiguous_intent"
    MULTI_INTERPRETATION = "multi_interpretation"
    MISSING_CONTEXT = "missing_context"
    CONFLICTING_INDICATORS = "conflicting_indicators"
    LEGAL_COMPLEXITY = "legal_complexity"

class ClarificationStatus(Enum):
    """Status of clarification attempts"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FAILED = "failed"
    EXCEEDED_LIMIT = "exceeded_limit"
    FALLBACK_APPLIED = "fallback_applied"

@dataclass
class ClarificationAttempt:
    """Single clarification attempt record"""
    attempt_number: int
    trigger: ClarificationTrigger
    question_generated: str
    timestamp: float
    user_response: Optional[str] = None
    resolution_success: bool = False
    confidence_improvement: float = 0.0
    processing_time_ms: int = 0

@dataclass
class ClarificationSession:
    """Complete clarification session tracking"""
    session_id: str
    original_query: str
    initial_confidence: float
    current_confidence: float
    attempts: List[ClarificationAttempt] = field(default_factory=list)
    status: ClarificationStatus = ClarificationStatus.PENDING
    max_attempts: int = 3
    confidence_threshold: float = 0.75
    fallback_reason: Optional[str] = None
    resolution_path: List[str] = field(default_factory=list)

class AdvancedClarificationController:
    """
    🎯 PRODUCTION-READY CLARIFICATION LOOP CONTROL
    
    Features:
    - Intelligent clarification question generation
    - Loop prevention with adaptive limits
    - Multi-layered fallback strategies
    - Context-aware question templates
    - Session management and analytics
    """
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.active_sessions: Dict[str, ClarificationSession] = {}
        self.question_templates = self._initialize_question_templates()
        self.fallback_strategies = self._initialize_fallback_strategies()
        self.confidence_analyzers = self._initialize_confidence_analyzers()
    
    async def should_trigger_clarification(
        self,
        query: str,
        validation_result: Dict,
        conversation_context: Optional[List[Dict]] = None
    ) -> Tuple[bool, Optional[ClarificationTrigger], float]:
        """
        Intelligent decision on whether clarification is needed
        
        Returns:
            (should_clarify, trigger_reason, confidence_score)
        """
        
        confidence = validation_result.get('confidence', 0.8)
        intents = validation_result.get('recommended_intents', [])
        
        # Analyze multiple factors
        triggers = []
        
        # 1. Low confidence threshold
        if confidence < 0.6:
            triggers.append((ClarificationTrigger.LOW_CONFIDENCE, 1.0 - confidence))
        
        # 2. Multiple competing intents
        if len(intents) > 2:
            triggers.append((ClarificationTrigger.MULTI_INTERPRETATION, len(intents) * 0.2))
        
        # 3. Ambiguous language patterns
        ambiguity_score = await self._analyze_ambiguity(query)
        if ambiguity_score > 0.7:
            triggers.append((ClarificationTrigger.AMBIGUOUS_INTENT, ambiguity_score))
        
        # 4. Missing critical context
        context_completeness = self._analyze_context_completeness(query, conversation_context)
        if context_completeness < 0.5:
            triggers.append((ClarificationTrigger.MISSING_CONTEXT, 1.0 - context_completeness))
        
        # 5. Conflicting indicators
        conflict_score = self._detect_conflicting_indicators(query, validation_result)
        if conflict_score > 0.6:
            triggers.append((ClarificationTrigger.CONFLICTING_INDICATORS, conflict_score))
        
        # 6. Legal complexity requiring specificity
        complexity_score = self._assess_legal_complexity(query)
        if complexity_score > 0.8 and confidence < 0.8:
            triggers.append((ClarificationTrigger.LEGAL_COMPLEXITY, complexity_score))
        
        # Select highest-priority trigger
        if triggers:
            primary_trigger, trigger_strength = max(triggers, key=lambda x: x[1])
            return True, primary_trigger, confidence
        
        return False, None, confidence
    
    async def generate_clarification_question(
        self,
        query: str,
        trigger: ClarificationTrigger,
        validation_result: Dict,
        session: ClarificationSession
    ) -> str:
        """
        Generate intelligent clarification question based on trigger type
        """
        
        # Check if we have a template-based solution first
        template_question = self._try_template_based_question(trigger, validation_result, session)
        if template_question:
            return template_question
        
        # Generate AI-powered clarification question
        ai_question = await self._generate_ai_clarification(query, trigger, validation_result, session)
        
        # Validate and refine the generated question
        refined_question = self._refine_clarification_question(ai_question, session)
        
        return refined_question
    
    def create_clarification_session(
        self,
        query: str,
        initial_confidence: float,
        max_attempts: int = 3
    ) -> ClarificationSession:
        """Create new clarification session"""
        
        session_id = self._generate_session_id(query)
        
        session = ClarificationSession(
            session_id=session_id,
            original_query=query,
            initial_confidence=initial_confidence,
            current_confidence=initial_confidence,
            max_attempts=max_attempts,
            status=ClarificationStatus.PENDING
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def process_clarification_response(
        self,
        session_id: str,
        user_response: str,
        new_validation_result: Dict
    ) -> Tuple[bool, float, str]:
        """
        Process user's clarification response
        
        Returns:
            (is_resolved, new_confidence, next_action)
        """
        
        if session_id not in self.active_sessions:
            return False, 0.0, "Session not found"
        
        session = self.active_sessions[session_id]
        
        # Update current attempt
        if session.attempts:
            current_attempt = session.attempts[-1]
            current_attempt.user_response = user_response
            current_attempt.processing_time_ms = int((time.time() - current_attempt.timestamp) * 1000)
        
        # Analyze improvement
        new_confidence = new_validation_result.get('confidence', 0.0)
        confidence_improvement = new_confidence - session.current_confidence
        
        # Update session
        session.current_confidence = new_confidence
        if session.attempts:
            session.attempts[-1].confidence_improvement = confidence_improvement
            session.attempts[-1].resolution_success = new_confidence >= session.confidence_threshold
        
        # Check resolution criteria
        if new_confidence >= session.confidence_threshold:
            session.status = ClarificationStatus.RESOLVED
            session.resolution_path.append("confidence_threshold_met")
            return True, new_confidence, "resolved"
        
        # Check if we should continue or fallback
        if len(session.attempts) >= session.max_attempts:
            session.status = ClarificationStatus.EXCEEDED_LIMIT
            fallback_response = self._apply_fallback_strategy(session)
            return False, new_confidence, fallback_response
        
        # Check for improvement stagnation
        if confidence_improvement < 0.05 and len(session.attempts) >= 2:
            session.status = ClarificationStatus.FALLBACK_APPLIED
            session.fallback_reason = "improvement_stagnation"
            fallback_response = self._apply_fallback_strategy(session)
            return False, new_confidence, fallback_response
        
        # Continue clarification
        return False, new_confidence, "continue"
    
    def _try_template_based_question(
        self,
        trigger: ClarificationTrigger,
        validation_result: Dict,
        session: ClarificationSession
    ) -> Optional[str]:
        """Try to use pre-defined templates for common scenarios"""
        
        intents = validation_result.get('recommended_intents', [])
        
        # Multi-intent templates
        if trigger == ClarificationTrigger.MULTI_INTERPRETATION:
            intent_combinations = frozenset(intents)
            
            if intent_combinations in self.question_templates['multi_intent']:
                template = self.question_templates['multi_intent'][intent_combinations]
                return template.format(
                    attempt_number=len(session.attempts) + 1,
                    original_query=session.original_query
                )
        
        # Low confidence templates
        if trigger == ClarificationTrigger.LOW_CONFIDENCE:
            confidence = validation_result.get('confidence', 0.0)
            
            if confidence < 0.3:
                return self.question_templates['low_confidence']['very_low']
            elif confidence < 0.5:
                return self.question_templates['low_confidence']['moderate']
        
        # Context-specific templates
        if trigger == ClarificationTrigger.MISSING_CONTEXT:
            primary_intent = intents[0] if intents else 'general'
            
            if primary_intent in self.question_templates['missing_context']:
                return self.question_templates['missing_context'][primary_intent]
        
        return None
    
    async def _generate_ai_clarification(
        self,
        query: str,
        trigger: ClarificationTrigger,
        validation_result: Dict,
        session: ClarificationSession
    ) -> str:
        """Generate AI-powered clarification question"""
        
        clarification_prompt = f"""أنت خبير في تحليل الاستفسارات القانونية الغامضة.

**الاستفسار الأصلي:**
{query}

**سبب الحاجة للتوضيح:**
{trigger.value}

**نتائج التحليل:**
الثقة: {validation_result.get('confidence', 0.8):.1%}
النوايا المحتملة: {', '.join(validation_result.get('recommended_intents', []))}

**محاولات التوضيح السابقة:**
{len(session.attempts)} محاولة

**مهمتك:**
صياغة سؤال توضيحي ذكي وقصير يساعد في حل الغموض.

**معايير السؤال:**
- واضح ومباشر (أقل من 30 كلمة)
- يركز على نقطة واحدة محددة
- يتطلب إجابة بسيطة (نعم/لا أو اختيار)
- مصاغ بلغة مفهومة للمستخدم العادي

**أمثلة جيدة:**
- "هل تقصد معرفة العقوبات أم كيفية تصحيح الوضع؟"
- "هل المشكلة حدثت بالفعل أم تريد معرفة كيفية تجنبها؟"
- "هل أنت موظف أم صاحب عمل في هذه الحالة؟"

أجب بسؤال توضيحي واحد فقط:"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast, cheap for clarification
                messages=[{"role": "user", "content": clarification_prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI clarification generation failed: {e}")
            return self._get_generic_clarification_fallback(trigger)
    
    def _refine_clarification_question(self, question: str, session: ClarificationSession) -> str:
        """Refine and validate the generated clarification question"""
        
        # Remove common AI artifacts
        question = question.replace("سؤال توضيحي:", "").strip()
        question = question.replace("السؤال:", "").strip()
        
        # Ensure question mark
        if not question.endswith('؟'):
            question += '؟'
        
        # Add context indicator
        attempt_number = len(session.attempts) + 1
        if attempt_number > 1:
            prefix = f"للتوضيح أكثر ({attempt_number}/{session.max_attempts}): "
            question = prefix + question
        
        return question
    
    def _apply_fallback_strategy(self, session: ClarificationSession) -> str:
        """Apply appropriate fallback strategy when clarification fails"""
        
        fallback_type = self._determine_fallback_type(session)
        
        if fallback_type == "best_guess_with_disclaimer":
            return self.fallback_strategies['best_guess'].format(
                confidence=int(session.current_confidence * 100),
                original_query=session.original_query
            )
        
        elif fallback_type == "multiple_scenarios":
            return self.fallback_strategies['multiple_scenarios'].format(
                original_query=session.original_query
            )
        
        elif fallback_type == "expert_referral":
            return self.fallback_strategies['expert_referral']
        
        else:
            return self.fallback_strategies['generic_fallback']
    
    def _determine_fallback_type(self, session: ClarificationSession) -> str:
        """Determine appropriate fallback strategy"""
        
        # High confidence but exceeded attempts - use best guess
        if session.current_confidence > 0.6:
            return "best_guess_with_disclaimer"
        
        # Multiple clear intents but low confidence - show scenarios
        if len(session.resolution_path) > 0 and session.current_confidence > 0.4:
            return "multiple_scenarios"
        
        # Very low confidence or legal complexity - refer to expert
        if session.current_confidence < 0.3 or ClarificationTrigger.LEGAL_COMPLEXITY in [a.trigger for a in session.attempts]:
            return "expert_referral"
        
        return "generic_fallback"
    
    def _initialize_question_templates(self) -> Dict:
        """Initialize pre-approved clarification question templates"""
        return {
            'multi_intent': {
                frozenset(['penalty_explanation', 'procedure_guide']): 
                    "هل تريد معرفة العقوبات فقط، أم تحتاج أيضاً لخطوات تصحيح الوضع؟",
                
                frozenset(['rights_inquiry', 'legal_dispute']): 
                    "هل تريد معرفة حقوقك العامة، أم لديك نزاع قانوني محدد تحتاج المساعدة فيه؟",
                
                frozenset(['procedure_guide', 'legal_dispute']): 
                    "هل تريد معرفة الإجراءات للوقاية، أم لديك مشكلة قانونية حالية تحتاج حلها؟",
                
                frozenset(['penalty_explanation', 'rights_inquiry', 'procedure_guide']): 
                    "سؤالك يغطي عدة جوانب. ما الأهم لك الآن: معرفة العقوبات، أم حقوقك، أم الخطوات المطلوبة؟"
            },
            
            'low_confidence': {
                'very_low': "يبدو أن سؤالك يحتاج توضيح أكثر. هل يمكنك إعادة صياغته بطريقة أخرى؟",
                'moderate': "لفهم سؤالك بشكل أفضل، هل يمكنك إضافة المزيد من التفاصيل؟"
            },
            
            'missing_context': {
                'penalty_explanation': "لتحديد العقوبات بدقة، هل المخالفة حدثت بالفعل أم تريد معرفة العقوبات المحتملة؟",
                'legal_dispute': "لفهم وضعك القانوني، هل أنت المدعي أم المدعى عليه في هذا النزاع؟",
                'rights_inquiry': "لتوضيح حقوقك، هل أنت موظف، عميل، أم طرف آخر في هذه الحالة؟",
                'procedure_guide': "لتقديم الإجراءات الصحيحة، في أي مرحلة أنت الآن من هذه العملية؟"
            },
            
            'conflicting_indicators': {
                'business_personal': "هل تسأل عن وضعك كفرد أم كصاحب عمل/شركة؟",
                'past_future': "هل تسأل عن حالة حدثت بالفعل أم تريد معرفة ما يجب فعله مستقبلاً؟",
                'self_other': "هل السؤال عن وضعك الشخصي أم عن شخص آخر؟"
            }
        }
    
    def _initialize_fallback_strategies(self) -> Dict:
        """Initialize fallback response templates"""
        return {
            'best_guess': """⚠️ **تنبيه:** لم نتمكن من فهم سؤالك بدقة 100% بعد عدة محاولات توضيح.

سنقدم أفضل تقدير قانوني لسؤالك (مستوى الثقة: {confidence}%) مع التأكيد على ضرورة مراجعة محامٍ مختص للتأكد.

**سؤالك الأصلي:** {original_query}

**الإجابة المقدرة:**""",
            
            'multiple_scenarios': """🔀 **سيناريوهات متعددة:** لم نتمكن من تحديد قصدك بدقة، لذا سنعرض الاحتمالات الأكثر ترجيحاً:

**السيناريو الأول:** إذا كنت تقصد...
**السيناريو الثاني:** إذا كنت تقصد...
**السيناريو الثالث:** إذا كنت تقصد...

يرجى اختيار السيناريو الأقرب لحالتك أو إعادة صياغة السؤال.""",
            
            'expert_referral': """👨‍⚖️ **يُنصح بالاستشارة المتخصصة**

سؤالك يتضمن تعقيدات قانونية تتطلب تحليلاً متخصصاً من محامٍ مؤهل.

**للحصول على استشارة دقيقة:**
• 📞 الخط الساخن للاستشارات القانونية: 19993
• 💻 منصة "استشارات": consult.sa
• 🏛️ نقابة المحامين السعوديين: saudibar.org

**يمكننا تقديم معلومات قانونية عامة، لكن حالتك تحتاج رأي قانوني متخصص.**""",
            
            'generic_fallback': """❓ **صعوبة في الفهم**

لم نتمكن من فهم سؤالك بوضوح بعد عدة محاولات.

**يُرجى:**
• إعادة كتابة السؤال بطريقة أبسط
• تقسيم السؤال إلى أسئلة أصغر
• إضافة تفاصيل أكثر عن الحالة

**أو التواصل مع:**
📞 خدمة العملاء: 19993"""
        }
    
    def _initialize_confidence_analyzers(self) -> Dict:
        """Initialize confidence analysis tools"""
        return {
            'ambiguity_patterns': [
                r'\b(ربما|يمكن|قد|محتمل|غالب)\b',
                r'\b(أو|إما|سواء)\b.*\b(أو|إما|سواء)\b',
                r'\?.*\?',  # Multiple question marks
                r'\b(مش متأكد|غير واضح|لا أعرف)\b'
            ],
            
            'context_indicators': {
                'timeline_markers': [r'\b(أمس|اليوم|غداً|الأسبوع|الشهر)\b'],
                'role_markers': [r'\b(موظف|مدير|عميل|زبون|مستهلك)\b'],
                'location_markers': [r'\b(في الرياض|بجدة|في المملكة)\b'],
                'amount_markers': [r'\d+\s*(ريال|درهم|دولار)']
            },
            
            'conflict_patterns': [
                ('business_personal', [r'\b(شركة|مؤسسة)\b', r'\b(شخصي|فردي)\b']),
                ('past_future', [r'\b(حدث|حصل|تم)\b', r'\b(سأ|سوف|مستقبل)\b']),
                ('self_other', [r'\b(أنا|لي|عندي)\b', r'\b(له|لها|عندهم)\b'])
            ]
        }
    
    # Analysis helper methods
    async def _analyze_ambiguity(self, query: str) -> float:
        """Analyze linguistic ambiguity in the query"""
        ambiguity_score = 0.0
        
        for pattern in self.confidence_analyzers['ambiguity_patterns']:
            matches = len(re.findall(pattern, query, re.IGNORECASE))
            ambiguity_score += matches * 0.2
        
        # Check for vague terms
        vague_terms = ['شيء', 'حاجة', 'موضوع', 'قضية', 'مسألة']
        vague_count = sum(1 for term in vague_terms if term in query)
        ambiguity_score += vague_count * 0.15
        
        return min(ambiguity_score, 1.0)
    
    def _analyze_context_completeness(self, query: str, context: Optional[List[Dict]]) -> float:
        """Analyze how complete the context information is"""
        completeness_score = 0.0
        
        # Check for context indicators in query
        for category, patterns in self.confidence_analyzers['context_indicators'].items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    completeness_score += 0.2
        
        # Bonus for conversation context
        if context and len(context) > 0:
            completeness_score += 0.3
        
        # Check query length (very short queries often lack context)
        if len(query.split()) > 10:
            completeness_score += 0.2
        
        return min(completeness_score, 1.0)
    
    def _detect_conflicting_indicators(self, query: str, validation_result: Dict) -> float:
        """Detect conflicting indicators in the query"""
        conflict_score = 0.0
        
        for conflict_type, (pattern1, pattern2) in self.confidence_analyzers['conflict_patterns']:
            has_pattern1 = any(re.search(p, query, re.IGNORECASE) for p in pattern1)
            has_pattern2 = any(re.search(p, query, re.IGNORECASE) for p in pattern2)
            
            if has_pattern1 and has_pattern2:
                conflict_score += 0.3
        
        # Check for conflicting intents
        intents = validation_result.get('recommended_intents', [])
        if len(intents) > 2:
            conflict_score += 0.4
        
        return min(conflict_score, 1.0)
    
    def _assess_legal_complexity(self, query: str) -> float:
        """Assess legal complexity requiring clarification"""
        complexity_indicators = [
            'تحكيم', 'استئناف', 'تمييز', 'دستوري', 'إداري',
            'تجاري متقدم', 'شركات مساهمة', 'اندماج', 'استحواذ',
            'ملكية فكرية', 'براءة اختراع', 'حقوق مؤلف'
        ]
        
        complexity_score = 0.0
        for indicator in complexity_indicators:
            if indicator in query:
                complexity_score += 0.3
        
        return min(complexity_score, 1.0)
    
    def _generate_session_id(self, query: str) -> str:
        """Generate unique session ID"""
        timestamp = str(int(time.time() * 1000))
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()[:8]
        return f"clarify_{timestamp}_{query_hash}"
    
    def _get_generic_clarification_fallback(self, trigger: ClarificationTrigger) -> str:
        """Get generic clarification question as last resort"""
        fallbacks = {
            ClarificationTrigger.LOW_CONFIDENCE: "هل يمكنك توضيح سؤالك أكثر؟",
            ClarificationTrigger.AMBIGUOUS_INTENT: "ما الهدف الرئيسي من سؤالك؟",
            ClarificationTrigger.MULTI_INTERPRETATION: "أي جانب تريد التركيز عليه أكثر؟",
            ClarificationTrigger.MISSING_CONTEXT: "هل يمكنك إضافة المزيد من التفاصيل؟",
            ClarificationTrigger.CONFLICTING_INDICATORS: "هل يمكنك توضيح الحالة بدقة أكثر؟",
            ClarificationTrigger.LEGAL_COMPLEXITY: "هل تحتاج شرح مبسط أم تحليل قانوني متقدم؟"
        }
        
        return fallbacks.get(trigger, "هل يمكنك إعادة صياغة سؤالك؟")
    
    # Session management methods
    def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a clarification session"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'total_attempts': len(session.attempts),
            'confidence_improvement': session.current_confidence - session.initial_confidence,
            'status': session.status.value,
            'resolution_time_ms': sum(a.processing_time_ms for a in session.attempts),
            'triggers_used': [a.trigger.value for a in session.attempts],
            'final_confidence': session.current_confidence,
            'success_rate': len([a for a in session.attempts if a.resolution_success]) / max(len(session.attempts), 1)
        }
    
    def cleanup_completed_sessions(self, max_age_hours: int = 24):
        """Clean up old completed sessions"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session.status in [ClarificationStatus.RESOLVED, ClarificationStatus.FAILED, ClarificationStatus.EXCEEDED_LIMIT]:
                latest_attempt_time = max([a.timestamp for a in session.attempts]) if session.attempts else 0
                if current_time - latest_attempt_time > max_age_seconds:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        return len(sessions_to_remove)