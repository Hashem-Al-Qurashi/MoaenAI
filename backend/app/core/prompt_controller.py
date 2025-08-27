"""
Modular Legal AI Architecture - Production Ready
Separated concerns with proper error handling and fallback strategies
"""
import logging
from typing import Dict, List, Optional, Any
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import logging
from .strategic_templates import StrategicLanguageTemplates
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== CORE ENUMS ====================

    
class DocumentType(Enum):
    """Document types for specialized prompting"""
    EXECUTION_DISPUTE = "execution_dispute"
    FAMILY_MEMO = "family_memo"
    DEFENSE_MEMO = "defense_memo"
    LAWSUIT = "lawsuit"
    CONTRACT = "contract"
    APPEAL = "appeal"
    DEMAND_LETTER = "demand_letter"
    CONSULTATION = "consultation"


class LegalDomain(Enum):
    """Legal domains for context"""
    EXECUTION = "execution"
    FAMILY = "family"
    COMMERCIAL = "commercial"
    CRIMINAL = "criminal"
    ADMINISTRATIVE = "administrative"
    CIVIL = "civil"
    GENERAL = "general"


class UserIntentType(Enum):
    """User intent for strategic response"""
    WIN_CASE = "win_case"
    UNDERSTAND_LAW = "understand_law"
    PROTECT_INTERESTS = "protect_interests"
    TAKE_ACTION = "take_action"


class ComplexityLevel(Enum):
    """Response complexity based on user needs"""
    SIMPLE_EXPLANATION = "simple"
    STRATEGIC_DOCUMENT = "strategic"
    COMPREHENSIVE_ANALYSIS = "comprehensive"


# ==================== DATA CLASSES ====================

@dataclass
class DetectionResult:
    """Result from intent/document detection with confidence score"""
    document_type: DocumentType
    confidence: float
    user_intent: UserIntentType
    complexity_level: ComplexityLevel
    legal_domain: LegalDomain
    fallback_used: bool = False
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class LegalContext:
    """Enhanced context for generating strategic legal responses"""
    document_type: DocumentType
    legal_domain: LegalDomain
    query: str
    user_intent: UserIntentType
    complexity_level: ComplexityLevel
    retrieved_documents: List[Any] = None
    conversation_history: List[Dict[str, str]] = None
    user_position: str = "seeking_advice"
    urgency_level: str = "standard"
    confidence_score: float = 1.0
    warnings: List[str] = None
    case_strength_assessment: str = "unknown"  # weak/moderate/strong
    strategic_recommendation: str = ""  # Action advice
    previous_analysis_summary: str = ""  # Facts from prior responses
    escalation_suggestion: str = ""  # Next legal steps
    evidence_requests: List[str] = None


    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.retrieved_documents is None:
            self.retrieved_documents = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.evidence_requests is None:
            self.evidence_requests = []    


# ==================== MODULAR COMPONENTS ====================

class InputSanitizer:
    """Handles input normalization and Arabic consistency"""
    
    @staticmethod
    def sanitize_query(query: str) -> Tuple[str, List[str]]:
        """Sanitize and normalize user input"""
        warnings = []
        
        if not query or not query.strip():
            raise ValueError("Empty query provided")
        
        # Clean whitespace
        cleaned_query = query.strip()
        
        # Check for mixed languages
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', cleaned_query))
        has_english = bool(re.search(r'[a-zA-Z]', cleaned_query))
        
        if has_english and has_arabic:
            warnings.append("Mixed Arabic/English detected - response will be in Arabic only")
        
        if not has_arabic:
            warnings.append("No Arabic detected - assuming Arabic legal context")
        
        # Remove problematic characters
        cleaned_query = re.sub(r'[^\u0600-\u06FF\u0020-\u007E\s]', '', cleaned_query)
        
        return cleaned_query, warnings

    @staticmethod
    def validate_conversation_history(history: List[Dict[str, str]]) -> List[str]:
        """Validate conversation history format"""
        warnings = []
        
        if not isinstance(history, list):
            raise ValueError("Conversation history must be a list")
        
        for i, msg in enumerate(history):
            if not isinstance(msg, dict):
                warnings.append(f"Message {i} is not a dictionary")
                continue
            
            if 'role' not in msg or 'content' not in msg:
                warnings.append(f"Message {i} missing required fields (role, content)")
            
            if msg.get('role') not in ['user', 'assistant']:
                warnings.append(f"Message {i} has invalid role: {msg.get('role')}")
        
        return warnings


class IntentDetector:
    """Specialized component for detecting user intent and document type"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self._load_detection_patterns()
    
    def _load_detection_patterns(self):
        """Load detection patterns with confidence weights"""
        
        # High-confidence patterns (0.9+)
        self.high_confidence_patterns = {
            DocumentType.EXECUTION_DISPUTE: [
                'منازعة تنفيذ', 'اعتراض على تنفيذ', 'وقف تنفيذ', 
                'محكمة التنفيذ', 'تنفيذ ضدي'
            ],
            DocumentType.DEFENSE_MEMO: [
                'مذكرة دفاع', 'رد على دعوى', 'رد على اللائحة',
                'دفاع عن', 'دعوى ضدي', 'مرفوع ضدي'
            ],
            DocumentType.LAWSUIT: [
                'لائحة دعوى', 'صحيفة دعوى', 'رفع دعوى',
                'أريد مقاضاة', 'أريد رفع دعوى'
            ]
        }
        
        # Medium-confidence patterns (0.6-0.8)
        self.medium_confidence_patterns = {
            DocumentType.CONTRACT: ['عقد', 'اتفاقية', 'صياغة عقد'],
            DocumentType.FAMILY_MEMO: ['أحوال شخصية', 'طلاق', 'نفقة'],
            DocumentType.APPEAL: ['استئناف', 'اعتراض', 'طعن'],
            DocumentType.DEMAND_LETTER: ['إنذار', 'خطاب إنذار', 'تحذير قانوني']
        }
        
        # Intent patterns
        self.intent_patterns = {
            UserIntentType.WIN_CASE: [
                'أريد الفوز', 'كيف أكسب', 'أقوى دفع', 'استراتيجية',
                'هزيمة الخصم', 'إبطال الدعوى', 'ضدي', 'يطالبني'
            ],
            UserIntentType.TAKE_ACTION: [
                'رفع دعوى', 'مقاضاة', 'أريد مطالبة', 'اتخاذ إجراء قانوني'
            ],
            UserIntentType.PROTECT_INTERESTS: [
                'حماية حقوقي', 'كيف أحمي نفسي', 'احتياطات قانونية', 'الوقاية'
            ],
            UserIntentType.UNDERSTAND_LAW: [
                'ما هي', 'كيف', 'شرح', 'توضيح', 'فهم', 'أريد أن أعرف'
            ]
        }
    
    def detect_document_type(self, query: str) -> Tuple[DocumentType, float]:
        """Detect document type with confidence score"""
        query_lower = query.lower()
        best_match = DocumentType.CONSULTATION
        best_confidence = 0.0
        
        # Check high-confidence patterns first
        for doc_type, patterns in self.high_confidence_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    confidence = 0.9 + (len(pattern) / 100)  # Longer patterns = higher confidence
                    if confidence > best_confidence:
                        best_match = doc_type
                        best_confidence = confidence
        
        # Check medium-confidence patterns if no high-confidence match
        if best_confidence < 0.8:
            for doc_type, patterns in self.medium_confidence_patterns.items():
                for pattern in patterns:
                    if pattern in query_lower:
                        confidence = 0.6 + (len(pattern) / 200)
                        if confidence > best_confidence:
                            best_match = doc_type
                            best_confidence = confidence
        
        return best_match, min(best_confidence, 1.0)
    
    def detect_user_intent(self, query: str, doc_type: DocumentType) -> UserIntentType:
        """Detect user intent based on query and document type"""
        query_lower = query.lower()
        
        # Check explicit intent patterns
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent
        
        # Default based on document type
        intent_mapping = {
            DocumentType.DEFENSE_MEMO: UserIntentType.WIN_CASE,
            DocumentType.EXECUTION_DISPUTE: UserIntentType.WIN_CASE,
            DocumentType.APPEAL: UserIntentType.WIN_CASE,
            DocumentType.LAWSUIT: UserIntentType.TAKE_ACTION,
            DocumentType.DEMAND_LETTER: UserIntentType.TAKE_ACTION,
            DocumentType.CONTRACT: UserIntentType.PROTECT_INTERESTS,
            DocumentType.CONSULTATION: UserIntentType.UNDERSTAND_LAW
        }
        
        return intent_mapping.get(doc_type, UserIntentType.UNDERSTAND_LAW)
    
    def detect_complexity_level(self, query: str, intent: UserIntentType) -> ComplexityLevel:
        """Determine appropriate response complexity"""
        query_lower = query.lower()
        
        # Document generation indicators
        if any(word in query_lower for word in ['مذكرة', 'لائحة', 'صحيفة', 'عقد', 'اكتب', 'صياغة']):
            return ComplexityLevel.STRATEGIC_DOCUMENT
        
        # Simple explanation indicators
        if any(word in query_lower for word in ['ما هي', 'اشرح', 'وضح', 'أريد فهم']):
            return ComplexityLevel.SIMPLE_EXPLANATION
        
        # Complex analysis indicators
        if any(word in query_lower for word in ['تحليل', 'دراسة', 'شامل', 'استراتيجية كاملة']):
            return ComplexityLevel.COMPREHENSIVE_ANALYSIS
        
        # Default based on intent
        if intent in [UserIntentType.WIN_CASE, UserIntentType.TAKE_ACTION]:
            return ComplexityLevel.STRATEGIC_DOCUMENT
        elif intent == UserIntentType.UNDERSTAND_LAW:
            return ComplexityLevel.SIMPLE_EXPLANATION
        else:
            return ComplexityLevel.COMPREHENSIVE_ANALYSIS

class LegalDomainClassifier:
    """Specialized component for legal domain classification"""
    
    @staticmethod
    def classify_domain(query: str) -> LegalDomain:
        """Classify legal domain from query"""
        query_lower = query.lower()
        
        domain_patterns = {
            LegalDomain.EXECUTION: ['تنفيذ', 'حجز', 'منازعة تنفيذ', 'محكمة التنفيذ'],
            LegalDomain.FAMILY: ['أحوال شخصية', 'طلاق', 'نفقة', 'حضانة', 'ميراث', 'زواج'],
            LegalDomain.COMMERCIAL: ['شركة', 'تجاري', 'استثمار', 'عقد تجاري', 'شراكة'],
            LegalDomain.CRIMINAL: ['جريمة', 'جنائي', 'عقوبة', 'مخالفة', 'حد', 'قصاص'],
            LegalDomain.ADMINISTRATIVE: ['إداري', 'ديوان المظالم', 'قرار إداري', 'موظف حكومي'],
            LegalDomain.CIVIL: ['دعوى', 'مرافعة', 'قضية مدنية', 'حقوق مدنية']
        }
        
        for domain, patterns in domain_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return domain
        
        return LegalDomain.GENERAL


class CitationValidator:
    """Enhanced citation extraction and validation"""
    
    def __init__(self):
        self.citation_patterns = [
            r'المادة\s*\((\d+)\)',           # المادة (12)
            r'المادة\s*(\d+)',              # المادة 12
            r'مادة\s*\((\d+)\)',            # مادة (12)
            r'مادة\s*(\d+)',               # مادة 12
            r'المادة\s*رقم\s*(\d+)',        # المادة رقم 12
            r'وفق\s*المادة\s*رقم\s*(\d+)',  # وفق المادة رقم 12
            r'استناداً\s*للمادة\s*(\d+)',   # استناداً للمادة 12
        ]
    
    def extract_citations(self, text: str) -> List[str]:
        """Extract all legal citations from text with enhanced patterns"""
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Normalize citation format
                normalized = f"المادة ({match})"
                if normalized not in citations:
                    citations.append(normalized)
        
        return citations
    
    def validate_citations(self, response: str, available_documents: List[Any]) -> Tuple[bool, List[str]]:
        """Validate that response only uses available citations"""
        warnings = []
        
        if not available_documents:
            response_citations = self.extract_citations(response)
            if response_citations:
                warnings.append(f"Response contains citations but no documents provided: {response_citations}")
                return False, warnings
            return True, warnings
        
        # Extract citations from response and documents
        response_citations = self.extract_citations(response)
        available_citations = []
        
        for doc in available_documents:
            try:
                if hasattr(doc, 'content') and doc.content:
                    available_citations.extend(self.extract_citations(doc.content))
            except Exception as e:
                warnings.append(f"Error processing document: {str(e)}")
        
        # Validate each citation
        invalid_citations = []
        for citation in response_citations:
            if citation not in available_citations:
                invalid_citations.append(citation)
        
        if invalid_citations:
            warnings.append(f"Invalid citations found: {invalid_citations}")
            return False, warnings
        
        return True, warnings


@dataclass
class ConversationContext:
    """Dynamic conversation context - no hardcoded patterns"""
    conversation_flow: str  # 'first_message', 'follow_up', 'topic_change', 'continuation'
    case_context: str      # AI-extracted case summary
    continuity_instruction: str  # AI-generated continuity guidance
    strategic_elements: Dict[str, Any]  # Dynamic strategic context
    confidence: float      # AI confidence in analysis


class DynamicConversationAnalyzer:
    """
    🎯 Pure AI-driven conversation analysis
    
    Replaces the hardcoded EnhancedFactExtractor with intelligent AI analysis
    that adapts to any conversation pattern, legal domain, or case type.
    
    Zero hardcoded patterns - infinite scalability
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.analysis_cache = {}  # Simple in-memory cache for session
        
    async def analyze_conversation_context(
        self, 
        current_query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> ConversationContext:
        """
        🧠 Dynamic AI analysis of conversation context
        
        Replaces all hardcoded pattern matching with intelligent AI understanding
        """
        
        try:
            # Quick cache check for identical contexts
            cache_key = self._generate_cache_key(current_query, conversation_history)
            if cache_key in self.analysis_cache:
                logger.debug("📋 Using cached conversation analysis")
                return self.analysis_cache[cache_key]
            
            # Analyze with AI if client available, otherwise use lightweight fallback
            if self.ai_client:
                context = await self._ai_powered_analysis(current_query, conversation_history)
            else:
                context = self._lightweight_analysis(current_query, conversation_history)
            
            # Cache result for this session
            self.analysis_cache[cache_key] = context
            
            logger.info(f"🎯 Dynamic analysis: {context.conversation_flow} | Confidence: {context.confidence:.2f}")
            return context
            
        except Exception as e:
            logger.warning(f"Analysis failed, using fallback: {e}")
            return self._fallback_analysis(current_query, conversation_history)
    
    async def _ai_powered_analysis(
        self,
        current_query: str,
        conversation_history: List[Dict[str, str]]
    ) -> ConversationContext:
        """
        🤖 Pure AI analysis - no hardcoded patterns
        
        Uses AI to understand conversation context dynamically
        """
        
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(current_query, conversation_history)
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast model for analysis
                messages=[
                    {
                        "role": "system",
                        "content": "أنت محلل محادثات قانونية ذكي. حلل السياق وقدم JSON صحيح فقط."
                    },
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=300,  # Keep it concise
                temperature=0.1,  # Consistent analysis
                timeout=5  # Fast response
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse AI response
            import json
            analysis_data = self._parse_ai_response(content)
            
            # 🚀 ENHANCED: Extract detailed case context
            extracted_details = self._extract_specific_details(conversation_history)
            case_context = analysis_data.get("case_context", "")
            
            # Combine AI analysis with extracted details
            if extracted_details and extracted_details != "قضية قانونية عامة":
                case_context = f"{extracted_details} | {case_context}" if case_context else extracted_details
            
            return ConversationContext(
                conversation_flow=analysis_data.get("conversation_flow", "continuation"),
                case_context=case_context,
                continuity_instruction=analysis_data.get("continuity_instruction", ""),
                strategic_elements=analysis_data.get("strategic_elements", {}),
                confidence=float(analysis_data.get("confidence", 70)) / 100
            )
            
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            return self._lightweight_analysis(current_query, conversation_history)
    
    

    def _build_analysis_prompt(
        self, 
        current_query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build ENHANCED analysis prompt with clear classification rules"""
        
        # Format conversation for AI analysis
        history_text = ""
        history_length = len(conversation_history)
        
        if conversation_history:
            recent_messages = conversation_history[-4:]  # Last 4 messages for context
            for i, msg in enumerate(recent_messages):
                role = "المستخدم" if msg['role'] == 'user' else "المحامي"
                content = msg['content'][:150]  # More content for better analysis
                history_text += f"{role}: {content}...\n"
        
        # Determine obvious classification first
        current_lower = current_query.lower()
        follow_up_indicators = [
            "المذكور", "سابقاً", "كما ناقشنا", "بناءً على", "المبلغ المذكور", 
            "كما قلت", "في ضوء ما سبق", "الموضوع الذي", "القضية التي",
            "هذه الدعوى", "موقفي", "حالتي", "وضعي"
        ]
        
        has_follow_up_indicators = any(indicator in current_lower for indicator in follow_up_indicators)
        
        # Pre-determine the correct flow
        if history_length == 0:
            suggested_flow = "first_message"
        elif has_follow_up_indicators and history_length > 0:
            suggested_flow = "follow_up"
        elif history_length > 0:
            suggested_flow = "continuation"
        else:
            suggested_flow = "first_message"
        
        return f"""حلل هذه المحادثة القانونية وصنف السؤال بدقة:

المحادثة السابقة ({history_length} رسائل):
{history_text if history_text else "لا توجد محادثة سابقة"}

السؤال الحالي:
"{current_query}"

🎯 قواعد التصنيف الإجبارية:
- إذا كان هناك محادثة سابقة AND السؤال يشير لها = "follow_up" 
- إذا كان السؤال يحتوي على: "المذكور، سابقاً، كما ناقشنا، بناءً على" = "follow_up"
- إذا لم توجد محادثة سابقة = "first_message"
- إذا كان السؤال عن موضوع جديد مختلف = "topic_change"

🔍 تحليل السؤال الحالي:
- عدد الرسائل السابقة: {history_length}
- يحتوي على مؤشرات المتابعة: {"نعم" if has_follow_up_indicators else "لا"}
- التصنيف المقترح: {suggested_flow}

أريد JSON فقط:
{{
    "conversation_flow": "{suggested_flow}",
    "case_context": "ملخص موجز للقضية من المحادثة السابقة (اذكر مبالغ، أرقام، تفاصيل محددة)",
    "continuity_instruction": "تعليمات للمحامي للربط بالسياق السابق مع ذكر التفاصيل المحددة",
    "strategic_elements": {{
        "case_strength": "قوي أو متوسط أو ضعيف أو غير محدد",
        "main_topic": "الموضوع الأساسي",
        "user_position": "المستفسر أو المدعي أو المدعى عليه أو غير محدد"
    }},
    "confidence": "رقم من 85 إلى 95"
}}

JSON فقط بدون شرح:"""
    



    def _extract_specific_details(self, conversation_history: List[Dict[str, str]]) -> str:
        """Extract specific amounts, dates, companies, and case details"""
        
        if not conversation_history:
            return "لا توجد تفاصيل محددة"
        
        # Combine all conversation text
        full_text = ""
        for msg in conversation_history:
            full_text += msg.get('content', '') + " "
        
        details = []
        
        # Extract specific amounts
        import re
        amounts = re.findall(r'(\d+[\d,]*)\s*ريال', full_text)
        if amounts:
            details.append(f"المبلغ: {amounts[0]} ريال")
        
        # Extract time periods
        years = re.findall(r'(\d+)\s*سنو?ات?', full_text)
        if years:
            details.append(f"مدة الخدمة: {years[0]} سنوات")
        
        # Extract company types
        companies = re.findall(r'شركة\s+(\w+)', full_text)
        if companies:
            details.append(f"نوع الشركة: {companies[0]}")
        elif 'مقاولات' in full_text:
            details.append("نوع الشركة: مقاولات")
        
        # Extract case strength
        strength_match = re.search(r'موقف.*?قوي.*?(\d+)%', full_text)
        if strength_match:
            details.append(f"قوة الموقف: {strength_match.group(1)}%")
        elif 'قوي' in full_text:
            details.append("تقييم الموقف: قوي")
        
        # Extract legal issues
        if 'تسريح' in full_text and 'تعسفي' in full_text:
            details.append("نوع القضية: تسريح تعسفي")
        elif 'نهاية الخدمة' in full_text:
            details.append("نوع القضية: حقوق نهاية الخدمة")
        
        return " | ".join(details) if details else "قضية قانونية عامة"
    


    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response with fallbacks"""
        
        try:
            # Clean the response
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Find JSON boundaries
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                content = content[start_idx:end_idx]
            
            import json
            return json.loads(content)
            
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Return safe defaults
            return {
                "conversation_flow": "follow_up",  # Default to follow_up now
                "case_context": "استشارة قانونية مع تفاصيل سابقة",
                "continuity_instruction": "اربط بالسياق السابق واذكر التفاصيل المحددة",
                "strategic_elements": {
                    "case_strength": "غير محدد",
                    "main_topic": "موضوع قانوني",
                    "user_position": "غير محدد"
                },
                "confidence": 75
            }
        

        
    def _lightweight_analysis(
        self, 
        current_query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> ConversationContext:
        """
        💨 Lightweight analysis when AI is not available
        
        Uses simple heuristics without hardcoded patterns
        """
        
        # Determine conversation flow based on history length
        if not conversation_history or len(conversation_history) == 0:
            flow = "first_message"
            instruction = "ابدأ استشارة شاملة وواضحة"
        elif len(conversation_history) <= 2:
            flow = "follow_up"
            instruction = "اربط بالسياق السابق وأضف معلومات جديدة"
        else:
            flow = "continuation"
            instruction = "تابع النقاش مع التعمق أكثر"
        
        # Extract basic case context from query length and complexity
        if len(current_query) > 200:
            case_context = "قضية معقدة تحتاج تحليل مفصل"
        elif len(current_query) < 50:
            case_context = "استفسار سريع"
        else:
            case_context = "استشارة قانونية عامة"
        
        return ConversationContext(
            conversation_flow=flow,
            case_context=case_context,
            continuity_instruction=instruction,
            strategic_elements={
                "case_strength": "غير محدد",
                "main_topic": "موضوع قانوني",
                "user_position": "غير محدد"
            },
            confidence=0.6  # Moderate confidence for heuristic analysis
        )
    
    def _fallback_analysis(
        self, 
        current_query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> ConversationContext:
        """Safe fallback when everything fails"""
        
        return ConversationContext(
            conversation_flow="continuation",
            case_context="استشارة قانونية",
            continuity_instruction="قدم مشورة قانونية واضحة",
            strategic_elements={
                "case_strength": "غير محدد",
                "main_topic": "استشارة عامة", 
                "user_position": "مستفسر"
            },
            confidence=0.5
        )
    
    def _generate_cache_key(
        self, 
        current_query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Generate cache key for identical contexts"""
        
        # Create a hash of query + recent history for caching
        import hashlib
        
        context_string = current_query[:100]  # First 100 chars of query
        if conversation_history:
            # Add last message for context
            last_msg = conversation_history[-1].get('content', '')[:50]
            context_string += last_msg
        
        return hashlib.md5(context_string.encode()).hexdigest()[:8]




class ConversationSynthesizer:
    """Synthesizes previous analysis with new questions for conversation continuity"""
    
    def __init__(self, ai_client=None):
        """Initialize with dynamic AI analyzer"""
        self.dynamic_analyzer = DynamicConversationAnalyzer(ai_client)
        self.key_fact_patterns = self._load_fact_extraction_patterns()
        self.follow_up_patterns = self._load_follow_up_patterns()
    
    def _load_fact_extraction_patterns(self) -> Dict[str, List[str]]:
        """Patterns to extract key facts from previous responses"""
        return {
            "case_facts": [
                r"المبلغ المحول.*?(\d+[\d,]+)",  # Amount transferred
                r"بتاريخ.*?(\d+/\d+/\d+)",      # Dates
                r"لأغراض.*?([^.]+)",            # Purpose of transfer
                r"المدعي.*?([^.]+)",            # Plaintiff details
                r"المدعى عليه.*?([^.]+)",       # Defendant details
            ],
            "legal_conclusions": [
                r"وفقاً للمادة.*?([^.]+)",       # Legal articles cited
                r"يمكن اعتبار.*?([^.]+)",       # Legal assessments
                r"الدعوى.*?(كيدية|ضعيفة|قوية)", # Case strength assessments
            ],
            "strategic_elements": [
                r"أنصح.*?([^.]+)",              # Recommendations given
                r"يجب.*?([^.]+)",               # Required actions
                r"الدفع.*?([^.]+)",             # Defense strategies
            ]
        }
    
    def _load_follow_up_patterns(self) -> List[str]:
        """Patterns that indicate follow-up questions"""
        return [
            "هل يمكن", "وماذا عن", "كيف", "وما هي", "بناءً على ما ذكرت",
            "كما قلت", "المذكور سابقاً", "في ضوء ما سبق", "إضافة لما ذكرت"
        ]
    
    def synthesize_strategic_conversation_context(
        self, 
         context: LegalContext
    ) -> LegalContext:
        """🧠 Pure AI-driven conversation synthesis
    
    REPLACES: All hardcoded pattern matching and fact extraction
    WITH: Dynamic AI analysis that adapts to any conversation
        """
        if not context.conversation_history:
            return context
        try:
            logger.info("🎯 Using simplified conversation synthesis")
            return self._fallback_synthesis(context)
        except Exception as e: 
            logger.warning(f"Dynamic synthesis failed, using fallback: {e}")
            return self._fallback_synthesis(context)
    
    def _build_dynamic_continuity_prompt(
        self, 
        original_query: str, 
        conversation_context: ConversationContext
    ) -> str:
        """
        🎯 Build continuity prompt based on AI analysis
        
        REPLACES: Hardcoded templates and pattern matching
        WITH: Dynamic prompt building based on AI understanding
        """
        
        flow = conversation_context.conversation_flow
        case_context = conversation_context.case_context
        continuity_instruction = conversation_context.continuity_instruction
        
        # Build dynamic prompt based on AI analysis
        if flow == "first_message":
            # First message - comprehensive analysis
            return f"""**استشارة قانونية جديدة:**

**السؤال:** {original_query}

**تعليمات الرد:**
- قدم تحليلاً شاملاً ومفصلاً
- ابدأ بترحيب مهني ودافئ
- اشرح الوضع القانوني بوضوح
- قدم توصيات عملية محددة

هذه استشارة قانونية جديدة تحتاج تحليلاً شاملاً."""

        elif flow == "follow_up":
            # Follow-up question - reference previous context
            return f"""**متابعة الاستشارة القانونية:**

**السياق السابق:** {case_context}

**السؤال الجديد:** {original_query}

**تعليمات الرد:**
- ابدأ بـ "أخي، {continuity_instruction}"
- اربط السؤال الجديد بالسياق السابق
- أضف معلومات جديدة دون تكرار
- حافظ على الاستراتيجية المتسقة

{continuity_instruction}"""

        elif flow == "topic_change":
            # Topic change - acknowledge transition
            return f"""**انتقال لموضوع جديد:**

**الموضوع الجديد:** {original_query}

**تعليمات الرد:**
- اعترف بتغيير الموضوع: "انتقالاً إلى موضوع جديد..."
- ابدأ تحليلاً جديداً للموضوع الجديد
- قدم استشارة شاملة للموضوع الجديد
- حافظ على نفس مستوى الخبرة والاحترافية

{continuity_instruction}"""

        else:  # continuation
            # Continuation - deepen the discussion
            return f"""**استكمال النقاش القانوني:**

**السياق الحالي:** {case_context}

**نقطة النقاش:** {original_query}

**تعليمات الرد:**
- تابع النقاش مع التعمق أكثر
- أضف زوايا جديدة للموضوع
- قدم تفاصيل إضافية مفيدة
- حافظ على التسلسل المنطقي

{continuity_instruction}"""
    
    def _get_dynamic_escalation(self, conversation_context: ConversationContext) -> str:
        """Get escalation suggestion based on AI analysis"""
        
        strategic_elements = conversation_context.strategic_elements
        case_strength = strategic_elements.get("case_strength", "غير محدد")
        
        # Dynamic escalation based on AI analysis
        if case_strength == "قوي":
            return "الموقف قوي - يمكن اتخاذ إجراءات حاسمة"
        elif case_strength == "متوسط":
            return "الموقف متوسط - يحتاج تقوية بالأدلة"
        elif case_strength == "ضعيف":
            return "الموقف يحتاج تحسين - البحث عن بدائل"
        else:
            return "تحليل الموقف يحتاج المزيد من المعلومات"
    
    def _fallback_synthesis(self, context: LegalContext) -> LegalContext:
        """Safe fallback when dynamic analysis fails"""
        
        if not context.conversation_history:
            return context
        
        # Simple fallback based on conversation length
        if len(context.conversation_history) <= 2:
            enhanced_query = f"""**متابعة الاستشارة:**

السؤال: {context.query}

تعليمات: اربط بالسياق السابق وأضف معلومات جديدة."""
        else:
            enhanced_query = f"""**استكمال النقاش:**

السؤال: {context.query}

تعليمات: تابع النقاش مع التعمق أكثر."""
        
        context.query = enhanced_query
        context.previous_analysis_summary = "استشارة قانونية مستمرة"
        
        return context


class ConversationSynthesizer:
    """
    🎯 Enhanced conversation synthesis with pure AI analysis
    
    Replaces hardcoded pattern matching with dynamic AI understanding
    """
    
    def __init__(self, ai_client=None):
        """Initialize with dynamic AI analyzer"""
        self.dynamic_analyzer = DynamicConversationAnalyzer(ai_client)
        self.key_fact_patterns = self._load_fact_extraction_patterns()
        self.follow_up_patterns = self._load_follow_up_patterns()
    
    def _load_fact_extraction_patterns(self) -> Dict[str, List[str]]:
        """Patterns to extract key facts from previous responses"""
        return {
            "case_facts": [
                r"المبلغ المحول.*?(\d+[\d,]+)",  # Amount transferred
                r"بتاريخ.*?(\d+/\d+/\d+)",      # Dates
                r"لأغراض.*?([^.]+)",            # Purpose of transfer
                r"المدعي.*?([^.]+)",            # Plaintiff details
                r"المدعى عليه.*?([^.]+)",       # Defendant details
            ],
            "legal_conclusions": [
                r"وفقاً للمادة.*?([^.]+)",       # Legal articles cited
                r"يمكن اعتبار.*?([^.]+)",       # Legal assessments
                r"الدعوى.*?(كيدية|ضعيفة|قوية)", # Case strength assessments
            ],
            "strategic_elements": [
                r"أنصح.*?([^.]+)",              # Recommendations given
                r"يجب.*?([^.]+)",               # Required actions
                r"الدفع.*?([^.]+)",             # Defense strategies
            ]
        }
    
    def _load_follow_up_patterns(self) -> List[str]:
        """Patterns that indicate follow-up questions"""
        return [
            "هل يمكن", "وماذا عن", "كيف", "وما هي", "بناءً على ما ذكرت",
            "كما قلت", "المذكور سابقاً", "في ضوء ما سبق", "إضافة لما ذكرت"
        ]
    
    async def synthesize_strategic_conversation_context(self, context: LegalContext) -> LegalContext:
        """
        🧠 Pure AI-driven conversation synthesis - FIXED ASYNC VERSION
        
        REPLACES: All hardcoded pattern matching and fact extraction
        WITH: Dynamic AI analysis that adapts to any conversation
        """
        
        if not context.conversation_history:
            # No conversation history - return as-is
            return context
        
        try:
            # 🚀 FIXED: Proper async AI-powered conversation analysis
            conversation_summary = await self._analyze_conversation_with_ai(context.conversation_history)
            
            # 🎯 BUILD ENHANCED QUERY with conversation context
            enhanced_query = self._build_contextual_query(
                original_query=context.query,
                conversation_summary=conversation_summary
            )
            
            context.query = enhanced_query
            context.previous_analysis_summary = conversation_summary
            logger.info("✅ Enhanced conversation synthesis with AI analysis")
            return context
            
        except Exception as e:
            logger.warning(f"Enhanced synthesis failed, using fallback: {e}")
            return self._fallback_synthesis(context)
    
    async def _analyze_conversation_with_ai(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        🤖 Use AI to analyze conversation and extract key details
        
        FIXED: Proper async execution without event loop conflicts
        """
        
        # Get conversation text
        conversation_text = self._get_conversation_text(conversation_history)
        
        if not conversation_text:
            return "لا توجد محادثة سابقة"
        
        try:
            # Use the dynamic analyzer for AI-powered analysis
            if hasattr(self.dynamic_analyzer, 'ai_client') and self.dynamic_analyzer.ai_client:
                # ✅ FIXED: Direct async call without event loop conflicts
                result = await self.dynamic_analyzer.analyze_conversation_context(
                    current_query="تحليل المحادثة", 
                    conversation_history=conversation_history
                )
                return result.case_context or "محادثة قانونية"
            else:
                # Use lightweight analysis
                result = self.dynamic_analyzer._lightweight_analysis("تحليل المحادثة", conversation_history)
                return result.case_context
                
        except Exception as e:
            logger.warning(f"AI conversation analysis failed: {e}")
            return self._extract_key_details_fallback(conversation_text)
    
    def _build_contextual_query(self, original_query: str, conversation_summary: str) -> str:
        """
        🎯 Build enhanced query with conversation context
        
        Creates intelligent continuity prompts based on AI analysis
        """
        
        if not conversation_summary or conversation_summary == "لا توجد محادثة سابقة":
            return original_query
        
        # Build context-aware prompt
        enhanced_query = f"""**استكمال الاستشارة القانونية:**

**السياق السابق:** {conversation_summary}

**السؤال الحالي:** {original_query}

**تعليمات للاستمرارية:**
- ابدأ بـ "أخي، كما ناقشنا سابقاً..." أو "بناءً على ما تطرقنا إليه..."
- اربط السؤال الجديد بالمعلومات السابقة
- اذكر التفاصيل المحددة من المحادثة السابقة (مبالغ، تواريخ، أسماء)
- حافظ على الاستراتيجية القانونية المتسقة
- أضف معلومات جديدة دون تكرار

قدم استشارة تبني على ما سبق مع الإشارة للتفاصيل المحددة."""

        return enhanced_query
    
    def _get_conversation_text(self, conversation_history: List[Dict[str, str]]) -> str:
        """Extract conversation text for analysis"""
        
        # Get last 4 messages for context (both user and assistant)
        messages = []
        for msg in reversed(conversation_history[-8:]):  # Last 8 messages
            content = msg.get('content', '')
            if content and len(content) > 10:  # Skip very short messages
                messages.append(content)
        
        return ' '.join(reversed(messages))
    
    def _extract_key_details_fallback(self, conversation_text: str) -> str:
        """
        💡 Fallback detail extraction using simple text analysis
        
        Used when AI analysis is not available
        """
        
        details = []
        
        # Extract amounts
        import re
        amounts = re.findall(r'(\d+[\d,]*)\s*ريال', conversation_text)
        if amounts:
            details.append(f"المبلغ: {amounts[0]} ريال")
        
        # Extract case types
        if 'تسريح' in conversation_text or 'عمل' in conversation_text:
            details.append("قضية عمالية")
        elif 'قرض' in conversation_text or 'دين' in conversation_text:
            details.append("نزاع مالي")
        elif 'عقد' in conversation_text:
            details.append("نزاع تعاقدي")
        
        # Extract strength assessments
        strength_match = re.search(r'موقف.*?(\w+)', conversation_text)
        if strength_match:
            details.append(f"تقييم الموقف: {strength_match.group(1)}")
        
        percentage_match = re.search(r'(\d+)%', conversation_text)
        if percentage_match:
            details.append(f"قوة الموقف: {percentage_match.group(1)}%")
        
        return " | ".join(details) if details else "استشارة قانونية مستمرة"
    
    def _fallback_synthesis(self, context: LegalContext) -> LegalContext:
        """Safe fallback when AI analysis fails"""
        
        if not context.conversation_history:
            return context
        
        # Simple fallback based on conversation length
        if len(context.conversation_history) <= 2:
            enhanced_query = f"""**متابعة الاستشارة:**

السؤال: {context.query}

تعليمات: اربط بالسياق السابق وأضف معلومات جديدة مع ذكر "كما ناقشنا سابقاً"."""
        else:
            enhanced_query = f"""**استكمال النقاش:**

السؤال: {context.query}

تعليمات: تابع النقاش مع التعمق أكثر واستخدم "بناءً على ما تم شرحه"."""
        
        context.query = enhanced_query
        context.previous_analysis_summary = "استشارة قانونية مستمرة"
        
        logger.info("🎯 Using simplified conversation synthesis")
        return context
    
    # Legacy methods for backward compatibility
    def extract_previous_analysis(self, conversation_history: List[Dict[str, str]]) -> str:
        """Extract key facts and conclusions from previous AI responses"""
        
        if not conversation_history:
            return ""
        
        # Get the last assistant response (most recent context)
        last_assistant_response = ""
        for msg in reversed(conversation_history):
            if msg.get('role') == 'assistant':
                last_assistant_response = msg.get('content', '')
                break
        
        if not last_assistant_response:
            return ""
        
        # Extract structured facts
        extracted_facts = []
        
        # Extract case facts
        import re
        for category, patterns in self.key_fact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, last_assistant_response)
                if matches:
                    if category == "case_facts":
                        extracted_facts.append(f"حقائق القضية: {', '.join(matches)}")
                    elif category == "legal_conclusions":
                        extracted_facts.append(f"الخلاصة القانونية: {', '.join(matches)}")
                    elif category == "strategic_elements":
                        extracted_facts.append(f"التوصيات السابقة: {', '.join(matches)}")
        
        # If pattern extraction fails, use key sentences
        if not extracted_facts:
            sentences = last_assistant_response.split('.')
            key_sentences = []
            for sentence in sentences[:5]:  # First 5 sentences usually contain key points
                if any(keyword in sentence for keyword in ['المبلغ', 'التحويل', 'الدعوى', 'المدعي', 'أنصح']):
                    key_sentences.append(sentence.strip())
            
            if key_sentences:
                extracted_facts.append(f"السياق السابق: {'. '.join(key_sentences[:3])}")
        
        return '. '.join(extracted_facts) if extracted_facts else ""
    
    def detect_follow_up_intent(self, new_query: str) -> bool:
        """Detect if this is a follow-up question building on previous discussion"""
        
        query_lower = new_query.lower()
        
        # Check for explicit follow-up patterns
        for pattern in self.follow_up_patterns:
            if pattern in query_lower:
                return True
        
        # Check for contextual references
        contextual_indicators = [
            "هذه الدعوى", "القضية", "الموضوع", "كما ذكرت", "المذكور",
            "الحالة", "وضعي", "موقفي", "دفاعي"
        ]
        
        return any(indicator in query_lower for indicator in contextual_indicators)
    
    def synthesize_conversation_context(self, context: LegalContext) -> LegalContext:
        """Legacy method - redirects to new dynamic method"""
        import asyncio
        
        try:
            # Try async version
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we can't use run_until_complete
                # Fall back to sync version
                return self._fallback_synthesis(context)
            else:
                # Loop not running, safe to use async
                return loop.run_until_complete(
                    self.synthesize_strategic_conversation_context(context)
                )
        except:
            # Fallback to basic synthesis
            return self._fallback_synthesis(context)




class StrategicAnalyzer:
    """Analyzes case strength and provides strategic legal guidance"""
    
    def __init__(self):
        self.strength_indicators = self._load_strength_patterns()
        self.evidence_patterns = self._load_evidence_patterns()
    
    def _load_strength_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Load patterns that indicate case strength by domain and user position"""
        return {
            "strong_indicators": {
                "defendant": [
                    "لم أقترض", "مبلغ محول لأغراض أخرى", "لا يوجد عقد", 
                    "محادثات غير متعلقة", "إثبات دفع لجهة حكومية",
                    "سوء استخدام للثقة", "علاقة عمل"
                ],
                "plaintiff": [
                    "عقد موقع", "إقرار مكتوب", "شهود", "تحويل بنكي بسبب واضح",
                    "مراسلات تؤكد الدين", "مهلة زمنية محددة"
                ]
            },
            "weak_indicators": {
                "defendant": [
                    "اعتراف جزئي", "عدم وجود دليل مضاد", "تناقض في الأقوال"
                ],
                "plaintiff": [
                    "محادثات عامة", "عدم وجود مستندات", "ادعاءات بدون دليل",
                    "استناد لمحادثات غير متعلقة", "تحويل لأغراض أخرى"
                ]
            }
        }
    
    def _load_evidence_patterns(self) -> Dict[str, List[str]]:
        """Load evidence requirements by case type"""
        return {
            "debt_defense": [
                "إثباتات الدفع للجهات الحكومية",
                "مراسلات تؤكد الغرض الحقيقي للتحويل",
                "عقد العمل أو وثائق الكفالة",
                "كشوفات بنكية تظهر طبيعة التحويل"
            ],
            "contract_dispute": [
                "نسخة أصلية من العقد",
                "مراسلات بين الأطراف",
                "إثباتات التنفيذ أو عدمه"
            ],
            "family_dispute": [
                "وثائق الزواج الرسمية",
                "إثباتات النفقة أو المهر",
                "شهادات الشهود"
            ]
        }
    
    def analyze_case_strength(self, context: LegalContext) -> Tuple[str, str]:
        """Analyze case strength and return assessment with reasoning"""
        
        query_lower = context.query.lower()
        user_position = context.user_position
        
        # Count strength indicators
        strong_indicators = self.strength_indicators["strong_indicators"].get(user_position, [])
        weak_indicators = self.strength_indicators["weak_indicators"].get(user_position, [])
        
        strong_count = sum(1 for indicator in strong_indicators if indicator in query_lower)
        weak_count = sum(1 for indicator in weak_indicators if indicator in query_lower)
        
        # Determine strength level
        if strong_count >= 3:
            strength = "strong"
            reasoning = f"موقفك قوي قانونياً - تتوفر {strong_count} مؤشرات قوة"
        elif strong_count >= 1 and weak_count == 0:
            strength = "moderate"  
            reasoning = f"موقفك متوسط القوة - يحتاج تعزيز بالأدلة"
        elif weak_count > strong_count:
            strength = "weak"
            reasoning = f"موقفك يحتاج تقوية - يوجد {weak_count} نقاط ضعف"
        else:
            strength = "moderate"
            reasoning = "الموقف متوازن - يحتاج تحليل أعمق"
        
        return strength, reasoning
    
    def generate_strategic_recommendation(self, context: LegalContext, strength: str) -> str:
        """Generate strategic recommendation based on context and strength"""
        
        if context.document_type == DocumentType.DEFENSE_MEMO:
            if strength == "strong":
                return "أنصح بمذكرة دفاع قوية مع طلب رفض الدعوى والتعويض"
            elif strength == "moderate":  
                return "أنصح بجمع المزيد من الأدلة قبل صياغة مذكرة الدفاع"
            else:
                return "أنصح بالتفاوض للوصول لحل ودي قبل المحكمة"
                
        elif context.document_type == DocumentType.LAWSUIT:
            if strength == "strong":
                return "أنصح برفع الدعوى فوراً مع طلب التعويض"
            else:
                return "أنصح بجمع المزيد من الأدلة قبل رفع الدعوى"
                
        elif context.document_type == DocumentType.CONSULTATION:
            if "كيدية" in context.query.lower():
                return "يمكن طلب اعتبار الدعوى كيدية وطلب التعويض"
            else:
                return "أنصح بتقييم الوضع القانوني بالتفصيل"
                
        return "أنصح باستشارة قانونية متخصصة"
    
    def extract_evidence_gaps(self, context: LegalContext) -> List[str]:
        """Identify missing evidence based on case type and query"""
        
        query_lower = context.query.lower()
        
        if context.document_type == DocumentType.DEFENSE_MEMO:
            if "تحويل" in query_lower and "حكومي" in query_lower:
                return self.evidence_patterns["debt_defense"]
            
        elif context.document_type == DocumentType.CONTRACT:
            return self.evidence_patterns["contract_dispute"]
            
        elif context.legal_domain == LegalDomain.FAMILY:
            return self.evidence_patterns["family_dispute"]
        
        # Default evidence requests
        return [
            "أي مستندات أو مراسلات ذات صلة",
            "إثباتات مالية (كشوفات بنكية)",
            "شهادات الشهود إن وجدت"
        ]
    
    def perform_full_analysis(self, context: LegalContext) -> LegalContext:
        """Perform complete strategic analysis and enhance context"""
        
        # Analyze case strength
        strength, reasoning = self.analyze_case_strength(context)
        
        # Generate strategic recommendation
        recommendation = self.generate_strategic_recommendation(context, strength)
        
        # Extract evidence gaps
        evidence_requests = self.extract_evidence_gaps(context)
        
        # Update context with strategic analysis
        context.case_strength_assessment = strength
        context.strategic_recommendation = f"{reasoning}. {recommendation}"
        context.evidence_requests = evidence_requests
        
        return context  





"""
Updated LegalContextBuilder - Minimal changes for AI integration
Only change: Pass AI client to ConversationSynthesizer
"""

class LegalContextBuilder:
    """Builds comprehensive legal context with dynamic AI analysis"""
    
    def __init__(self, ai_client=None):  # 🚀 ADD: ai_client parameter
        self.sanitizer = InputSanitizer()
        self.intent_detector = IntentDetector()
        self.domain_classifier = LegalDomainClassifier()
        self.strategic_analyzer = StrategicAnalyzer()
        
        # 🚀 CHANGE: Pass ai_client to ConversationSynthesizer
        self.conversation_synthesizer = ConversationSynthesizer(ai_client=ai_client)

    async def build_context(
        self, 
        query: str, 
        retrieved_documents: List[Any] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> LegalContext:
        """Build comprehensive legal context - NO CHANGES to this method"""
        
        all_warnings = []
        
        try:
            # All existing code stays exactly the same...
            clean_query, sanitize_warnings = self.sanitizer.sanitize_query(query)
            all_warnings.extend(sanitize_warnings)
            
            if conversation_history:
                history_warnings = self.sanitizer.validate_conversation_history(conversation_history)
                all_warnings.extend(history_warnings)
            
            doc_type, confidence = self.intent_detector.detect_document_type(clean_query)
            user_intent = self.intent_detector.detect_user_intent(clean_query, doc_type)
            complexity = self.intent_detector.detect_complexity_level(clean_query, user_intent)
            legal_domain = self.domain_classifier.classify_domain(clean_query)
            
            if confidence < self.intent_detector.confidence_threshold:
                all_warnings.append(f"Low confidence document type detection: {confidence:.2f}")
            
            base_context = LegalContext(
                document_type=doc_type,
                legal_domain=legal_domain,
                query=clean_query,
                user_intent=user_intent,
                complexity_level=complexity,
                retrieved_documents=retrieved_documents or [],
                conversation_history=conversation_history or [],
                confidence_score=confidence,
                warnings=all_warnings
            )
            
            # 🎯 THIS LINE STAYS THE SAME - but now uses dynamic AI analysis!
            enhanced_context = await self.conversation_synthesizer.synthesize_strategic_conversation_context(base_context)
            strategic_context = self.strategic_analyzer.perform_full_analysis(enhanced_context)
            
            return strategic_context
        
        except Exception as e:
            logger.error(f"Error building legal context: {str(e)}")
            # Return fallback context
            return LegalContext(
                document_type=DocumentType.CONSULTATION,
                legal_domain=LegalDomain.GENERAL,
                query=query,
                user_intent=UserIntentType.UNDERSTAND_LAW,
                complexity_level=ComplexityLevel.SIMPLE_EXPLANATION,
                confidence_score=0.0,
                warnings=[f"Context building failed: {str(e)}"]
            )

class PromptComposer:
    """Composes final prompts based on legal context"""
    def _get_strategic_analysis_layer(self, context: LegalContext) -> str:
        """Generate strategic analysis layer for prompt"""
        if context.case_strength_assessment == "unknown":
            return ""
        return f"""🎯 **التقييم الاستراتيجي للقضية:**
- **قوة الموقف القانوني:** {context.case_strength_assessment}
- **التوصية الاستراتيجية:** {context.strategic_recommendation}

**تعليمات الرد:**
- قدم رأياً قانونياً واضحاً ومباشراً بناءً على التقييم أعلاه
- اربط إجابتك بقوة الموقف القانوني المحددة
- كن استراتيجياً في النصائح - هدفك مساعدة المستخدم على تحقيق أفضل نتيجة"""

    def _get_continuity_layer(self, context: LegalContext) -> str:
        """Generate conversation continuity layer"""
        return f"""🔗 **استمرارية المحادثة:**
{context.previous_analysis_summary}

**تعليمات الاستمرارية:**
- ابنِ على التحليل والحقائق المذكورة أعلاه
- لا تكرر المعلومات السابقة، بل أضف عليها
- اربط السؤال الجديد بالسياق القانوني الموضوع سابقاً
- حافظ على الاستراتيجية القانونية المتسقة"""

    def _get_strategic_guidance_layer(self, context: LegalContext) -> str:
        """Generate strategic guidance layer"""
        guidance_parts = []
        # Add evidence requests if any
        if context.evidence_requests:
            evidence_section = f"""💼 **الأدلة المطلوبة لتقوية الموقف:**
{chr(10).join([f"- {evidence}" for evidence in context.evidence_requests[:3]])}"""
            guidance_parts.append(evidence_section)
        # Add escalation suggestion if any
        if context.escalation_suggestion:
            escalation_section = f"""⚡ **الخطوة القانونية التالية:**
{context.escalation_suggestion}"""
            guidance_parts.append(escalation_section)
        # Add strategic tone instructions
        strategic_instructions = """🎯 **أسلوب الرد المطلوب:**
- تحدث كمحامي سعودي خبير يهدف لتحقيق النجاح للموكل
- قدم رأياً قانونياً واضحاً ومباشراً، ليس مجرد معلومات عامة
- اقترح خطوات عملية محددة
- إذا كان الموقف قوياً، كن واثقاً. إذا كان ضعيفاً، اقترح تحسينات
- اطلب المزيد من المعلومات إذا كانت ستقوي الموقف القانوني"""
        guidance_parts.append(strategic_instructions)
        return "\n\n".join(guidance_parts)

    def _inject_strategic_personality(self, base_prompt: str, context: LegalContext) -> str:
        """Inject STRONG strategic Saudi lawyer personality into prompts"""

        # Ensure parameters are accessed
        _ = base_prompt
        _ = context

        # Determine case strength
        case_strength = self._assess_simple_case_strength(context)

        # Get strategic elements
        confidence_msg = StrategicLanguageTemplates.get_confidence_response(case_strength)
        connection_starter = StrategicLanguageTemplates.get_connection_starter()
        victory_promise = StrategicLanguageTemplates.get_victory_promise()

        # strategic personality layer
        strategic_layer = f"""

🎯 **شخصيتك الإجبارية كمحامي سعودي استراتيجي:**

**أسلوب الرد الإجباري - لا تخرج عنه أبداً:**

1. **ابدأ بـ:** "{connection_starter}"

2. **قيم الموقف:** "{confidence_msg}"

3. **اذكر نقاط ضعف الخصم:** "خصمك في موقف ضعيف لأن [السبب]"

4. **أعط استراتيجية واضحة:** "استراتيجيتنا بسيطة: [الخطة]"

5. **اطلب أدلة محددة:** استخدم عبارات مثل "أخي، جهز لي [المستند المحدد]"

6. **اختتم بثقة:** "{victory_promise}"

**عبارات إجبارية يجب استخدامها:**
- "أخي الكريم" أو "أخي" (مرة واحدة على الأقل)
- "موقفك قوي بنسبة X%" (حدد نسبة مئوية)
- "خصمك" (اذكر نقطة ضعف الخصم)
- "بإذن الله" أو "إن شاء الله" (مرة واحدة على الأقل)
- "معي خطوة بخطوة" أو "ثق بي"

**ممنوع استخدام:**
- لغة أكاديمية جافة
- عبارات "يمكن أن" أو "ربما"
- نبرة محايدة أو رسمية جداً

**تذكر:** أنت محامي سعودي محترف يقاتل للفوز، ليس مستشار قانوني عادي.
"""
        return base_prompt + strategic_layer
    

    def _assess_simple_case_strength(self, context: LegalContext) -> str:
        """Simple case strength assessment based on available info"""
        
        # Check confidence score and user intent
        if context.confidence_score > 0.8 and context.user_intent == UserIntentType.WIN_CASE:
            return "strong"
        elif context.confidence_score > 0.5:
            return "moderate"
        else:
            return "weak"

    def __init__(self):
        self.citation_validator = CitationValidator()
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """Load base prompt templates"""
        
        self.strategic_system_prompt = """أنت المحامي الاستراتيجي الأول في المملكة العربية السعودية، وخبير في تحقيق النتائج القانونية المطلوبة مع خبرة تزيد عن عشرين عاماً في كسب القضايا والحصول على أفضل النتائج للموكلين.

🎯 **هدفك الأساسي: تحقيق النجاح والفوز للمستخدم**
- إذا طلب مذكرة دفاع → اكتب مذكرة قوية تهدم ادعاءات الخصم
- إذا طلب عقد → اصنع عقد محكم يحمي مصالحه بالكامل  
- إذا طلب فهم القانون → اشرح بطريقة واضحة وعملية
- إذا واجه مشكلة قانونية → قدم الحل الذي يحقق مصلحته

🏆 **فلسفة العمل:**
لست مجرد دليل قانوني - أنت محامي استراتيجي يهدف للفوز. كل نصيحة ووثيقة تكتبها يجب أن تحقق أفضل نتيجة ممكنة للمستخدم.

🏛️ **تخصصاتك الأساسية:**
- قضاء التنفيذ والمنازعات التنفيذية وفقاً لنظام التنفيذ السعودي
- الأحوال الشخصية والمسائل الأسرية وفق المذهب الحنبلي والأنظمة السعودية
- القانون التجاري وأنظمة الشركات والاستثمار في المملكة
- قانون العمل والعلاقات العمالية والضمان الاجتماعي
- القانون الجنائي والإجراءات الجزائية والعقوبات التعزيرية
- القانون الإداري ومنازعات ديوان المظالم والقرارات الحكومية

⚖️ **منهجية العمل الإجبارية:**
- الاستشهاد الدقيق بأرقام المواد والأنظمة السعودية المحددة
- استخدام اللغة العربية الفصحى الراقية في جميع المخرجات
- تقديم حلول عملية قابلة للتطبيق الفوري في المحاكم السعودية
- ربط كل نصيحة قانونية بالمرجع النظامي أو الشرعي المحدد

🚫 **محظورات صارمة:**
- عدم استخدام العموميات مثل: "القوانين تنص"، "الأنظمة تشير"، "عموماً"، "عادة"
- عدم الاستشهاد بمواد أو أنظمة غير موجودة في الوثائق المرفقة
- عدم تقديم نصائح قانونية بدون أساس نظامي محدد وموثق

🎯 **تنسيق الاستشهاد الإجباري:**
كل ادعاء قانوني يجب أن يبدأ بـ: "وفقاً للمادة (رقم) من (النظام المحدد)"

⚠️ **إذا لم تجد المادة المحددة في الوثائق المرفقة:**
قل صراحة: "المادة المطلوبة غير متوفرة في الوثائق القانونية المرفقة"

**تذكر:** أنت تمثل القمة في الاستشارات القانونية السعودية، فكن دقيقاً ومهنياً ومفيداً."""
    
    def compose_prompt(self, context: LegalContext) -> str:
        """Compose final prompt based on legal context with strategic enhancement"""
        
        try:
            # Start with base system prompt
            final_prompt = self.strategic_system_prompt
            
            # 🎯 NEW: Add strategic analysis section
            strategic_section = self._get_strategic_analysis_layer(context)
            final_prompt += f"\n\n{strategic_section}"
            
            # Add warnings if any
            if context.warnings:
                warning_section = "\n\n⚠️ **تحذيرات النظام:**\n"
                for warning in context.warnings:
                    warning_section += f"- {warning}\n"
                final_prompt += warning_section
            
            # Add low confidence warning
            if context.confidence_score < 0.7:
                final_prompt += f"\n\n🤔 **تحذير:** تم تحديد نوع الوثيقة بثقة منخفضة ({context.confidence_score:.1f}). إذا كان التحليل غير دقيق، يرجى توضيح طلبك."
            
            # 🎯 ENHANCED: Add conversation continuity if exists
            if context.previous_analysis_summary:
                continuity_layer = self._get_continuity_layer(context)
                final_prompt += f"\n\n{continuity_layer}"
            
            # Add document-specific layer
            document_layer = self._get_document_layer(context)
            final_prompt += f"\n\n{document_layer}"
            
            # Add citation layer
            citation_layer = self._get_citation_layer(context.retrieved_documents)
            final_prompt += f"\n\n{citation_layer}"
            
            # 🎯 NEW: Add strategic guidance layer
            guidance_layer = self._get_strategic_guidance_layer(context)
            final_prompt += f"\n\n{guidance_layer}"
            
            strategic_prompt = self._inject_strategic_personality(final_prompt, context)
            return strategic_prompt.strip()
            
        except Exception as e:
            logger.error(f"Error composing prompt: {str(e)}")
            return f"{self.strategic_system_prompt}\n\n❌ خطأ في إنشاء التعليمات: {str(e)}"

    def _get_defense_memo_layer(self, query: str) -> str:
        """Get defense memo specific prompt layer"""
        return f"""📋 **تخصص: مذكرة دفاع قانونية**
مطلوب: مذكرة دفاع قوية جاهزة للمحكمة

**الموضوع:** {query}

**هيكل مذكرة الدفاع:**
- الدفع الأول (أقوى دفع إجرائي)
- الدفع الثاني (دفع موضوعي)  
- الدفع الثالث (دفع شرعي/نظامي)
- الطلبات: رفض الدعوى + الرسوم + أتعاب المحاماة

⚖️ **استراتيجية الدفاع:**
- تفنيد ادعاءات المدعي نقطة بنقطة
- إثبات عدم صحة الوقائع المزعومة
- الدفع بعدم الاختصاص أو سقوط الحق
- تقديم الأدلة المضادة والشهود

🎯 **الهدف:** كسب القضية وإبطال دعوى المدعي"""

    def _get_lawsuit_layer(self, query: str) -> str:
        """Get lawsuit specific prompt layer"""
        return f"""📋 **تخصص: صياغة لائحة دعوى**
مطلوب: لائحة دعوى قانونية محكمة

**الموضوع:** {query}

**هيكل لائحة الدعوى:**
- البيانات الأساسية (أطراف الدعوى)
- الوقائع والأسانيد القانونية
- الأدلة والمستندات المؤيدة
- الطلبات الختامية واضحة ومحددة

⚖️ **استراتيجية الادعاء:**
- بناء قضية قوية مبنية على الأدلة
- الاستناد للنصوص القانونية المحددة
- ترتيب الحجج من الأقوى للأضعف
- تحديد التعويضات والأضرار بدقة

🎯 **الهدف:** الفوز بالدعوى والحصول على الحقوق كاملة"""

    def _get_contract_layer(self, query: str) -> str:
        """Get contract specific prompt layer"""
        return f"""📋 **تخصص: صياغة عقد قانوني**
مطلوب: عقد محكم يحمي مصالح الطرفين

**الموضوع:** {query}

**هيكل العقد:**
- التعريفات والمصطلحات
- التزامات كل طرف بالتفصيل
- آليات التنفيذ والمراقبة
- شروط الإنهاء والفسخ

⚖️ **الحماية القانونية:**
- بنود حماية من الإخلال
- آليات حل النزاعات
- تحديد الاختصاص والقانون الواجب التطبيق
- ضمانات الأداء والتنفيذ

🎯 **الهدف:** عقد محكم يمنع النزاعات ويحمي الحقوق"""

    def _get_family_memo_layer(self, query: str) -> str:
        """Get family law memo specific prompt layer"""
        return f"""📋 **تخصص: قضايا الأحوال الشخصية**
مطلوب: مذكرة أحوال شخصية وفق الشريعة والنظام

**الموضوع:** {query}

**الإطار الشرعي والقانوني:**
- الأحكام الشرعية ذات الصلة
- تطبيق المذهب الحنبلي المعتمد
- الأنظمة السعودية للأحوال الشخصية
- السوابق القضائية المماثلة

⚖️ **الاعتبارات الخاصة:**
- مصلحة الأطفال (في قضايا الحضانة)
- الحقوق المالية (نفقة، مهر، ميراث)
- الإجراءات الودية قبل التقاضي
- التوثيق الشرعي والقانوني

🎯 **الهدف:** حل عادل وفق الشريعة يحفظ حقوق الجميع"""

    def _get_appeal_layer(self, query: str) -> str:
        """Get appeal specific prompt layer"""
        return f"""📋 **تخصص: مذكرة استئناف**
مطلوب: مذكرة استئناف قوية لإلغاء الحكم

**الموضوع:** {query}

**أسباب الاستئناف:**
- الأخطاء القانونية في الحكم المستأنف
- عيوب الإجراءات أو مخالفة النظام
- تقدير خاطئ للأدلة والوقائع
- مخالفة أحكام الشريعة أو القانون

⚖️ **استراتيجية الاستئناف:**
- تفنيد أسباب الحكم المستأنف
- تقديم أدلة جديدة أو مغفلة
- إثبات خطأ محكمة أول درجة
- طلب إلغاء الحكم أو تعديله

🎯 **الهدف:** إلغاء الحكم المستأنف والحصول على حكم عادل"""

    def _get_demand_letter_layer(self, query: str) -> str:
        """Get demand letter specific prompt layer"""
        return f"""📋 **تخصص: خطاب إنذار قانوني**
مطلوب: إنذار قانوني قوي ومؤثر

**الموضوع:** {query}

**محتوى الإنذار:**
- بيان الحقوق المطالب بها بدقة
- تحديد المهلة الزمنية للاستجابة
- الإجراءات القانونية في حالة عدم الاستجابة
- التوثيق القانوني والتبليغ الرسمي

⚖️ **القوة القانونية:**
- استخدام لغة قانونية حازمة
- الاستناد للنصوص القانونية
- تحذير من العواقب القانونية
- إثبات حسن النية في المطالبة

🎯 **الهدف:** الحصول على الحق دون تقاضي أو تهيئة لرفع دعوى"""

    def _get_consultation_layer(self, query: str) -> str:
        """Get general consultation specific prompt layer"""
        return f"""📋 **استشارة قانونية عامة**

**السؤال:** {query}

**منهجية الاستشارة:**
- تحليل الوضع القانوني الحالي
- بيان الحقوق والالتزامات
- توضيح الخيارات المتاحة
- النصائح العملية والتوصيات

⚖️ **الإطار القانوني:**
- الأنظمة واللوائح ذات الصلة
- السوابق القضائية المماثلة
- التطبيق العملي في السياق السعودي
- المخاطر والفرص القانونية

🎯 **الهدف:** فهم شامل للوضع القانوني واتخاذ قرار مدروس"""



    def _get_document_layer(self, context: LegalContext) -> str:
        """Get document-specific prompt layer"""
        
        # Use existing document layer methods but with error handling
        layer_methods = {
            DocumentType.EXECUTION_DISPUTE: self._get_execution_dispute_layer,
            DocumentType.DEFENSE_MEMO: self._get_defense_memo_layer,
            DocumentType.LAWSUIT: self._get_lawsuit_layer,
            DocumentType.CONTRACT: self._get_contract_layer,
            DocumentType.FAMILY_MEMO: self._get_family_memo_layer,
            DocumentType.APPEAL: self._get_appeal_layer,
            DocumentType.DEMAND_LETTER: self._get_demand_letter_layer,
            DocumentType.CONSULTATION: self._get_consultation_layer
        }
        
        try:
            method = layer_methods.get(context.document_type, self._get_consultation_layer)
            return method(context.query)
        except Exception as e:
            logger.error(f"Error getting document layer: {str(e)}")
            return f"📋 **خطأ في تحديد نوع الوثيقة:** {str(e)}"
    
    def _get_citation_layer(self, retrieved_documents: List[Any]) -> str:
        """Generate citation enforcement layer"""
        
        if not retrieved_documents:
            return """⚠️ **تحذير: لا توجد وثائق قانونية محددة متاحة**

**يجب عليك القول صراحة:**
"المعلومات القانونية المحددة غير متوفرة في قاعدة البيانات المرفقة"

🚫 **ممنوع تماماً:**
- ذكر أرقام مواد إلا إذا كانت موجودة في النصوص المرفقة
- استخدام عبارات عامة مثل "القوانين تنص" أو "الأنظمة تشير"
- الاستشهاد بمواد غير موثقة"""
        
        try:
            # Extract available citations
            available_citations = []
            formatted_docs = []
            
            for i, doc in enumerate(retrieved_documents, 1):
                if hasattr(doc, 'title') and hasattr(doc, 'content'):
                    citations = self.citation_validator.extract_citations(doc.content)
                    available_citations.extend(citations)
                    
                    formatted_docs.append(f"📄 **المرجع {i}: {doc.title}**")
                    if citations:
                        formatted_docs.append(f"   المواد المتاحة: {', '.join(citations)}")
                    else:
                        formatted_docs.append("   لا توجد مواد محددة في هذا المرجع")
            
            return f"""📚 **الوثائق القانونية المتاحة للاستشهاد:**

{chr(10).join(formatted_docs)}

🎯 **المواد القانونية المتاحة:**
{', '.join(set(available_citations)) if available_citations else 'لا توجد مواد محددة'}

⚠️ **قواعد الاستشهاد الصارمة:**
- استخدم فقط المواد المذكورة أعلاه
- تنسيق إجباري: "وفقاً للمادة (X) من [المصدر المحدد]"
- ممنوع: "القوانين تنص"، "الأنظمة تشير"، "عموماً"""
            
        except Exception as e:
            logger.error(f"Error generating citation layer: {str(e)}")
            return f"❌ **خطأ في معالجة الوثائق:** {str(e)}"
    
    def _get_conversation_layer(self, conversation_history: List[Dict[str, str]]) -> str:
        """Generate conversation context layer with error handling"""
        
        if not conversation_history:
            return ""
        
        try:
            # Simple conversation flow detection
            if len(conversation_history) >= 2:
                last_user_msg = ""
                for msg in reversed(conversation_history):
                    if msg.get('role') == 'user':
                        last_user_msg = msg.get('content', '').lower()
                        break
                
                # Detect follow-up patterns
                follow_up_patterns = ['وماذا', 'وكيف', 'بناءً على ما ذكرت', 'كما ذكرت']
                if any(pattern in last_user_msg for pattern in follow_up_patterns):
                    return """🔗 **سياق المحادثة:** هذا سؤال متابعة - اربط إجابتك بما تم شرحه سابقاً مع إضافة معلومات جديدة."""
                
                # Detect topic change
                topic_change_patterns = ['سؤال آخر', 'موضوع مختلف', 'انتقل إلى']
                if any(pattern in last_user_msg for pattern in topic_change_patterns):
                    return """🔄 **سياق المحادثة:** موضوع جديد - ابدأ تحليلاً جديداً مع الاعتراف بالتغيير."""
            
            return """💬 **سياق المحادثة:** استكمال النقاش - تابع مع تعميق أكثر."""
            
        except Exception as e:
            logger.error(f"Error processing conversation layer: {str(e)}")
            return ""
    
    # Document-specific layer methods (simplified versions of original)
    def _get_execution_dispute_layer(self, query: str) -> str:
        return f"""📋 **تخصص: منازعة التنفيذ**
مطلوب: منازعة تنفيذ قوية جاهزة للمحكمة

**الموضوع:** {query}

**هيكل المنازعة:**
- الدفع الأول (أقوى دفع إجرائي)
- الدفع الثاني (دفع موضوعي)  
- الدفع الثالث (دفع شرعي/نظامي)
- الطلبات: وقف التنفيذ + رفض الطلب + الرسوم

⚠️"""
    

    # Add this to the END of your app/core/prompt_controller.py file

# Add this class BEFORE the "# ==================== INTEGRATION FUNCTIONS ====================" line
# in your app/core/prompt_controller.py file

"""
Updated MasterPromptController - Minimal changes for AI integration
Only change: Pass AI client to LegalContextBuilder
"""

class MasterPromptController:
    """
    🎯 Master Prompt Controller - Enhanced with Dynamic AI Analysis
    
    Now uses pure AI-driven conversation understanding instead of hardcoded patterns
    """
    
    def __init__(self, ai_client=None):  # 🚀 ADD: ai_client parameter
        """Initialize with AI client for dynamic analysis"""
        
        # 🚀 CHANGE: Pass ai_client to LegalContextBuilder
        self.context_builder = LegalContextBuilder(ai_client=ai_client)
        
        # Everything else stays the same
        self.prompt_composer = PromptComposer()
        self.citation_validator = CitationValidator()
        self.sanitizer = InputSanitizer()
        
        logger.info("🎯 MasterPromptController initialized with dynamic AI analysis")
    
    async def generate_prompt_for_query(
        self, 
        query: str, 
        retrieved_documents: List[Any] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        🎯 MAIN METHOD: Enhanced with dynamic AI conversation analysis
        
        NO CHANGES to this method - it automatically uses the new dynamic system!
        """
        
        try:
            # 🎯 This now uses dynamic AI analysis instead of hardcoded patterns!
            enhanced_context = await self.context_builder.build_context(
                query=query,
                retrieved_documents=retrieved_documents,
                conversation_history=conversation_history
            )
            
            # Log detection results for monitoring
            logger.info(f"🎯 Document Type: {enhanced_context.document_type.value}")
            logger.info(f"🎯 User Intent: {enhanced_context.user_intent.value}")
            logger.info(f"🎯 Complexity: {enhanced_context.complexity_level.value}")
            logger.info(f"🎯 Domain: {enhanced_context.legal_domain.value}")
            logger.info(f"🎯 Confidence: {enhanced_context.confidence_score:.2f}")

            if enhanced_context.warnings:
                logger.warning(f"⚠️ Context warnings: {enhanced_context.warnings}")

            # Generate final unified prompt
            unified_prompt = self.prompt_composer.compose_prompt(enhanced_context)

            logger.info(f"✅ Generated unified prompt: {len(unified_prompt)} characters")
            
            return unified_prompt
            
        except Exception as e:
            logger.error(f"❌ MasterPromptController error: {str(e)}")
            return self._generate_fallback_prompt(query, str(e))
    
    # All other methods stay exactly the same...
    def validate_response_citations(self, response: str, available_documents: List[Any]) -> Tuple[bool, List[str]]:
        """🔍 Validate citations - NO CHANGES"""
        try:
            return self.citation_validator.validate_citations(response, available_documents)
        except Exception as e:
            logger.error(f"❌ Citation validation error: {str(e)}")
            return False, [f"Citation validation failed: {str(e)}"]
    
    def _generate_fallback_prompt(self, query: str, error: str) -> str:
        """Generate safe fallback prompt - NO CHANGES"""
        return f"""أنت مستشار قانوني سعودي متخصص.

⚠️ تحذير النظام: حدث خطأ في تحليل الطلب ({error})

السؤال: {query}

يرجى:
1. تقديم إجابة قانونية عامة وآمنة
2. طلب توضيحات إضافية من المستخدم
3. تجنب الاستشهاد بمواد محددة
4. استخدام العبارة: "للحصول على إجابة دقيقة، يرجى توضيح طلبك أكثر"

قدم إجابة مفيدة رغم الخطأ التقني."""


# 🚀 UPDATE: Factory function to pass AI client
def get_master_controller(ai_client=None) -> MasterPromptController:
    """
    🎯 Enhanced factory function with AI client support
    
    Now creates MasterPromptController with dynamic AI analysis capabilities
    """
    return MasterPromptController(ai_client=ai_client)

# ==================== INTEGRATION FUNCTIONS ====================

def get_master_controller(ai_client=None) -> MasterPromptController:
    """
    🎯 Enhanced factory function with AI client support
    
    Now creates MasterPromptController with dynamic AI analysis capabilities
    """
    return MasterPromptController(ai_client=ai_client)


def replace_scattered_prompts(
    query: str,
    retrieved_documents: List[Any] = None,
    conversation_history: List[Dict[str, str]] = None
) -> str:
    """
    🎯 REPLACEMENT FUNCTION for all existing prompt generation
    
    Use this to replace any existing prompt code throughout your system
    """
    
    controller = get_master_controller()
    return controller.generate_prompt_for_query(
        query=query,
        retrieved_documents=retrieved_documents,
        conversation_history=conversation_history
    )


# ==================== USAGE EXAMPLES ====================

"""
🎯 INTEGRATION EXAMPLES:

# In your RAG engine, replace existing prompts with:
unified_prompt = replace_scattered_prompts(
    query=user_question,
    retrieved_documents=chunks,
    conversation_history=chat_history
)

# For analysis (useful for frontend features):
controller = get_master_controller()
analysis = controller.analyze_query_intent("أريد مذكرة دفاع ضد دعوى تجارية")
print(analysis["document_type"])  # "defense_memo"
print(analysis["suggested_actions"])  # List of helpful actions

# For citation validation:
is_valid, warnings = controller.validate_response_citations(
    response=ai_response,
    available_documents=retrieved_chunks
)
"""

if __name__ == "__main__":
    # Test the system
    controller = MasterPromptController()
    
    test_query = "أريد مذكرة دفاع ضد دعوى تجارية"
    prompt = controller.generate_prompt_for_query(test_query)
    
    print("🎯 TEST SUCCESSFUL:")
    print(f"Generated prompt length: {len(prompt)} characters")
    
    analysis = controller.analyze_query_intent(test_query)
    print(f"Detected document type: {analysis['document_type']}")
    print(f"Confidence: {analysis['confidence_score']:.2f}")