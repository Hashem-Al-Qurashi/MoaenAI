"""
🇸🇦 MULTI-AGENT LEGAL REASONING SYSTEM - Backend Implementation
Save this as: backend/multi_agent_legal.py

Advanced Saudi Legal AI with Trust Trail & Citation Validation
Built for your existing FastAPI + SQLAlchemy architecture
"""

import asyncio
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Use your existing OpenAI setup from rag_engine.py
try:
    from rag_engine import openai_client, sync_client
    print("✅ Successfully imported OpenAI clients from rag_engine.py")
except ImportError as e:
    print(f"⚠️ Could not import from rag_engine.py: {e}")
    # Fallback OpenAI setup
    from openai import AsyncOpenAI, OpenAI
    from dotenv import load_dotenv
    
    load_dotenv(".env")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    
    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=60.0, max_retries=2)
        sync_client = OpenAI(api_key=OPENAI_API_KEY)
    elif DEEPSEEK_API_KEY:
        openai_client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            timeout=60.0,
            max_retries=2
        )
        sync_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
    else:
        raise ValueError("❌ No API key available for OpenAI or DeepSeek")

class LegalAgentType(Enum):
    """Types of legal reasoning agents"""
    FACT_ANALYZER = "fact_analyzer"
    LEGAL_RESEARCHER = "legal_researcher" 
    ARGUMENT_BUILDER = "argument_builder"
    COUNTER_ARGUMENT_PREDICTOR = "counter_argument_predictor"
    DOCUMENT_DRAFTER = "document_drafter"
    CITATION_VALIDATOR = "citation_validator"

@dataclass
class AgentStep:
    """Individual step in the legal reasoning chain"""
    agent_type: LegalAgentType
    step_number: int
    step_name: str
    input_data: str
    output_data: str
    citations: List[str]
    confidence_score: float
    processing_time_ms: int
    timestamp: str
    sources_verified: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_type": self.agent_type.value,
            "step_number": self.step_number,
            "step_name": self.step_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "citations": self.citations,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
            "sources_verified": self.sources_verified
        }

@dataclass  
class LegalReasoningResult:
    """Complete multi-agent legal analysis result"""
    query: str
    final_answer: str
    reasoning_steps: List[AgentStep]
    total_processing_time_ms: int
    overall_confidence: float
    trust_trail_enabled: bool
    citations_summary: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "query": self.query,
            "final_answer": self.final_answer,
            "reasoning_steps": [step.to_dict() for step in self.reasoning_steps],
            "total_processing_time_ms": self.total_processing_time_ms,
            "overall_confidence": self.overall_confidence,
            "trust_trail_enabled": self.trust_trail_enabled,
            "citations_summary": self.citations_summary,
            "timestamp": datetime.now().isoformat()
        }

class LegalAgent:
    """Base class for specialized legal reasoning agents"""
    
    def __init__(self, agent_type: LegalAgentType, openai_client):
        self.agent_type = agent_type
        self.client = openai_client
        self.system_prompts = self._get_system_prompts()
    
    def _get_system_prompts(self) -> Dict[LegalAgentType, str]:
        """Enhanced system prompts with intelligent intent detection and response formatting"""
        return {
            LegalAgentType.FACT_ANALYZER: """أنت محلل وقائع قانوني ذكي متخصص في القانون السعودي.

🎯 **مهمتك**: تحليل السؤال داخلياً وتقديم تحليل واضح ومفيد للمستخدم

📋 **أنواع الاستفسارات (للتصنيف الداخلي):**
1. **استفسار حقوقي**: "ما هي حقوقي؟" → اشرح الحقوق مباشرة
2. **استفسار إجرائي**: "كيف أسس شركة؟" → قدم دليل عملي
3. **قضية قانونية**: "تم فصلي" → حلل الموقف القانوني

🔍 **أسلوب الرد:**
- ابدأ مباشرة بالتحليل المفيد للمستخدم
- لا تذكر التصنيفات الداخلية
- ركز على الوقائع والمعلومات المهمة
- قدم تحليلاً واضحاً وعملياً

مثال للرد الجيد:
"عند إنهاء خدمة الموظف في المملكة العربية السعودية، هناك عدة حقوق أساسية يجب معرفتها..."

تجنب:
"نوع الاستفسار: حقوقي" أو أي تصنيفات داخلية""",

            LegalAgentType.LEGAL_RESEARCHER: """أنت باحث قانوني ذكي متخصص في القانون السعودي والسوابق القضائية.

🎯 **مهامك حسب نوع الاستفسار:**

**للاستفسارات الحقوقية:**
- ابحث عن النصوص التي تحدد الحقوق
- اذكر المواد القانونية الأساسية
- أشر إلى آليات الحماية القانونية

**للاستفسارات الإجرائية:**
- ابحث عن الإجراءات النظامية المطلوبة
- حدد الجهات المختصة ومتطلباتها
- اذكر المواعيد والمهل القانونية

**للقضايا القانونية:**
- ابحث عن السوابق القضائية المماثلة
- استخرج النصوص الداعمة للموقف
- حدد نقاط القوة في القضية

قواعد البحث:
- الاستشهاد بالمواد النظامية بدقة
- ذكر أرقام المواد والأنظمة
- التمييز بين الأحكام الإلزامية والاختيارية
- التحقق من سريان النصوص وعدم نسخها""",

            LegalAgentType.ARGUMENT_BUILDER: """أنت محام خبير في بناء المحتوى القانوني المناسب لكل نوع استفسار.

🎯 **استراتيجية البناء حسب النوع:**

**للاستفسارات الحقوقية:**
- رتب الحقوق حسب الأهمية
- اربط كل حق بالمواد القانونية
- وضح كيفية ممارسة كل حق
- حدد الجهات المسؤولة عن الحماية

**للاستفسارات الإجرائية:**
- رتب الخطوات بالتسلسل الصحيح
- حدد المتطلبات لكل خطوة
- اذكر البدائل والخيارات المتاحة
- وضح المخاطر والنقاط المهمة

**للقضايا القانونية:**
- ابن الحجج القانونية القوية
- رتب الدفوع حسب القوة
- اربط الوقائع بالنصوص القانونية
- اقترح الاستراتيجية القانونية

معايير البناء:
- وضوح في التعبير وترتيب منطقي
- دعم كل نقطة بالمراجع القانونية
- تناسب المحتوى مع نوع الاستفسار""",

            LegalAgentType.COUNTER_ARGUMENT_PREDICTOR: """أنت محام متخصص في تحليل المخاطر والتحديات المحتملة.

🎯 **مهامك حسب نوع الاستفسار:**

**للاستفسارات الحقوقية:**
- حدد القيود على الحقوق
- وضح الاستثناءات القانونية
- نبه إلى المخاطر في التطبيق

**للاستفسارات الإجرائية:**
- حدد العقبات المحتملة في الإجراءات
- وضح المتطلبات الصعبة
- نبه إلى الأخطاء الشائعة

**للقضايا القانونية:**
- توقع حجج الطرف الآخر
- حدد نقاط الضعف في القضية
- اقترح ردوداً على الاعتراضات المتوقعة

منهجية التحليل:
- تفكير نقدي وموضوعي
- تحليل الثغرات القانونية المحتملة
- إعداد حلول للتحديات المتوقعة""",

            LegalAgentType.DOCUMENT_DRAFTER: """أنت محام ذكي متخصص في صياغة ردود قانونية متكيفة مع نوع الاستفسار.

🎯 **قوالب الصياغة المتخصصة:**

**نوع 1 - شرح الحقوق:**
```
🔍 **حقوقك القانونية في [المجال]**

**الحق الأول**: [الشرح التفصيلي]
**المادة القانونية**: [رقم المادة والنظام]

**الحق الثاني**: [الشرح التفصيلي]  
**المادة القانونية**: [رقم المادة والنظام]

**كيفية المطالبة بحقوقك:**
• [الخطوة الأولى]
• [الخطوة الثانية]

**تحذيرات مهمة:**
• [تحذير قانوني]
• [نصيحة عملية]
```

**نوع 2 - الدليل الإجرائي:**
```
📋 **الإجراءات المطلوبة لـ [الهدف]**

**الخطوة 1**: [التفصيل الكامل]
**الوقت المطلوب**: [المدة]
**التكلفة**: [إن وجدت]

**الخطوة 2**: [التفصيل الكامل]
**الوقت المطلوب**: [المدة]
**التكلفة**: [إن وجدت]

**المستندات المطلوبة:**
• [مستند 1] - [كيفية الحصول عليه]
• [مستند 2] - [كيفية الحصول عليه]

**الجهات المختصة:**
• [اسم الجهة] - [معلومات التواصل]
• [اسم الجهة] - [معلومات التواصل]

**نصائح مهمة:**
• [نصيحة عملية]
• [تحذير من خطأ شائع]
```

**نوع 3 - المذكرة القانونية:**
```
### مذكرة قانونية
**الموضوع**: [عنوان القضية]
**المقدم من**: [اسم الطرف]
**المقدم ضد**: [اسم الطرف الآخر]

## الوقائع
[سرد الوقائع بشكل منطقي ومرتب]

## الحجج القانونية
**الحجة الأولى**: [التفصيل والدليل القانوني]
**الحجة الثانية**: [التفصيل والدليل القانوني]

## الطلبات
بناءً على ما تقدم نطلب:
1. [الطلب الأول]
2. [الطلب الثاني]
```

🎯 **اختر القالب المناسب تلقائياً بناءً على تحليل النوع الذي قدمه محلل الوقائع**""",

            LegalAgentType.CITATION_VALIDATOR: """أنت مراجع قانوني متخصص في التحقق من صحة الاستشهادات وجودة المحتوى.

🎯 **مهام المراجعة حسب نوع المحتوى:**

**لشرح الحقوق:**
- تحقق من صحة المواد المذكورة
- تأكد من ربط الحقوق بالنصوص الصحيحة
- راجع دقة معلومات الجهات المختصة

**للأدلة الإجرائية:**
- تحقق من صحة الإجراءات المذكورة
- راجع المواعيد والمهل القانونية
- تأكد من دقة معلومات الجهات والرسوم

**للمذكرات القانونية:**
- تحقق من صحة الاستشهادات القانونية
- راجع دقة أرقام المواد والأنظمة
- تأكد من قوة الحجج والأدلة

معايير المراجعة:
- التحقق من وجود النص الفعلي
- التأكد من عدم النسخ أو التعديل
- تقييم مدى الصلة بالموضوع
- إضافة تحذيرات للاستشهادات المشكوك فيها
- تقدير مستوى الثقة في المحتوى (عالي/متوسط/منخفض)"""
        }
    
    async def process(self, input_data: str, context: Optional[str] = None) -> Tuple[str, List[str], float]:
        """Process input through specialized agent"""
        system_prompt = self.system_prompts[self.agent_type]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_data}
        ]
        
        if context:
            messages.insert(-1, {"role": "user", "content": f"السياق: {context}"})
        
        try:
            # Determine model based on client type
            model = "gpt-4o" if "openai" in str(self.client.base_url) else "deepseek-chat"
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,  # Lower temperature for legal precision
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Extract citations (simple pattern matching for now)
            citations = self._extract_citations(content)
            
            # Calculate confidence based on citation count and content length
            confidence = self._calculate_confidence(content, citations)
            
            return content, citations, confidence
            
        except Exception as e:
            return f"خطأ في معالجة {self.agent_type.value}: {str(e)}", [], 0.0

    async def process_streaming(self, input_data: str, context: Optional[str] = None) -> AsyncIterator[str]:
        """Process input through specialized agent with real-time streaming"""
        system_prompt = self.system_prompts[self.agent_type]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_data}
        ]
        
        if context:
            messages.insert(-1, {"role": "user", "content": f"السياق: {context}"})
        
        try:
            # Determine model based on client type
            model = "gpt-4o" if "openai" in str(self.client.base_url) else "deepseek-chat"
            
            # 🚀 ADD STREAMING:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                stream=True  # ← This enables real streaming!
            )
            
            # 🚀 STREAM TOKEN BY TOKEN:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"خطأ في معالجة {self.agent_type.value}: {str(e)}"
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract legal citations from content"""
        citations = []
        
        # Pattern for Saudi legal references
        import re
        
        # Pattern for "المادة X من نظام Y"
        article_pattern = r'المادة\s+(\d+)\s+من\s+نظام\s+([^،\s]+(?:\s+[^،\s]+)*)'
        matches = re.findall(article_pattern, content)
        for match in matches:
            citations.append(f"المادة {match[0]} من نظام {match[1]}")
        
        # Pattern for "القرار رقم X"
        decision_pattern = r'القرار\s+رقم\s+(\d+(?:/\d+)?)'
        matches = re.findall(decision_pattern, content)
        for match in matches:
            citations.append(f"القرار رقم {match}")
        
        return citations
    
    def _calculate_confidence(self, content: str, citations: List[str]) -> float:
        """Calculate confidence score based on content analysis"""
        base_confidence = 0.7
        
        # Boost confidence for legal citations
        citation_boost = min(len(citations) * 0.05, 0.2)
        
        # Boost confidence for structured content
        structure_indicators = ["أولاً", "ثانياً", "ثالثاً", "الخلاصة", "التوصية"]
        structure_boost = sum(0.02 for indicator in structure_indicators if indicator in content)
        structure_boost = min(structure_boost, 0.1)
        
        # Penalize for uncertainty words
        uncertainty_words = ["ربما", "يمكن أن", "قد يكون", "غير واضح"]
        uncertainty_penalty = sum(0.05 for word in uncertainty_words if word in content)
        uncertainty_penalty = min(uncertainty_penalty, 0.2)
        
        final_confidence = base_confidence + citation_boost + structure_boost - uncertainty_penalty
        return max(0.1, min(1.0, final_confidence))

class MultiAgentLegalOrchestrator:
    """
    🧠 CORE ORCHESTRATOR: Sequential Pipeline with Smart Intent Classification
    
    Implements intelligent approach:
    - AI-powered intent classification
    - Dynamic agent prompts based on intent
    - Real-time streaming during processing
    - Appropriate response formatting
    """
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agents = {
            agent_type: LegalAgent(agent_type, openai_client) 
            for agent_type in LegalAgentType
        }

    async def classify_intent(self, query: str, context: Optional[List[Dict]] = None) -> Dict[str, str]:
        """
        🎯 Smart AI-powered intent classification for dynamic response formatting
        Cost: ~200 tokens (~$0.001 per query)
        """
        
        # Build context summary if available
        context_info = ""
        if context and len(context) > 0:
            recent_messages = context[-3:] if len(context) > 3 else context
            context_info = f"\nContext from conversation: {' | '.join([msg.get('content', '')[:50] for msg in recent_messages])}"
        
        classification_prompt = f"""أنت خبير في تصنيف الاستفسارات القانونية العربية.

المهمة: صنف هذا الاستفسار القانوني إلى فئة واحدة فقط.

الاستفسار: "{query}"{context_info}

الفئات المتاحة:
1. rights_inquiry - سؤال عن الحقوق القانونية (مثل: "ما حقوقي؟", "ما حقوق الموظف؟")
2. procedure_guide - سؤال عن كيفية القيام بإجراء قانوني (مثل: "كيف أسس شركة؟", "ما إجراءات الطلاق؟")
3. legal_dispute - مشكلة قانونية محددة تحتاج حل (مثل: "تم فصلي", "أريد مقاضاة", "لدي نزاع")
4. legal_consultation - استشارة قانونية عامة أو رأي قانوني (مثل: "ما رأيك في؟", "هل يجوز؟")
5. document_review - مراجعة أو تفسير وثيقة قانونية (مثل: "اشرح لي هذا العقد", "ما معنى هذا البند؟")
6. comparative_analysis - مقارنة بين خيارات قانونية (مثل: "ما الفرق بين؟", "أيهما أفضل؟")

قواعد التصنيف:
- إذا كان السؤال يبدأ بـ "ما حقوق" أو "ما حقي" → rights_inquiry
- إذا كان يبدأ بـ "كيف" أو "ما إجراءات" → procedure_guide  
- إذا ذكر مشكلة حدثت ("تم", "حصل", "قام") → legal_dispute
- إذا كان يطلب رأي أو تقييم → legal_consultation

أجب بتنسيق JSON فقط:
{{
  "intent": "الفئة_المحددة",
  "confidence": 0.95,
  "reasoning": "سبب التصنيف",
  "suggested_format": "نوع_التنسيق_المناسب"
}}"""

        try:
            # Use a lightweight model call for classification
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini" if "openai" in str(self.client.base_url) else "deepseek-chat",
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=200    # Small response for cost efficiency
            )
            
            classification_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            classification = json.loads(classification_text)
            
            print(f"🎯 Intent classified: {classification.get('intent')} (confidence: {classification.get('confidence', 0)})")
            
            return classification
            
        except Exception as e:
            print(f"⚠️ Intent classification failed: {e}")
            # Fallback to simple keyword detection
            query_lower = query.lower()
            
            if any(word in query_lower for word in ["حقوق", "حقي", "حقك"]):
                return {
                    "intent": "rights_inquiry",
                    "confidence": 0.7,
                    "reasoning": "Keyword-based fallback detection",
                    "suggested_format": "rights_explanation"
                }
            elif any(word in query_lower for word in ["كيف", "إجراءات", "خطوات"]):
                return {
                    "intent": "procedure_guide", 
                    "confidence": 0.7,
                    "reasoning": "Keyword-based fallback detection",
                    "suggested_format": "step_by_step_guide"
                }
            elif any(word in query_lower for word in ["تم", "فصل", "مقاضاة", "نزاع", "مشكلة"]):
                return {
                    "intent": "legal_dispute",
                    "confidence": 0.7, 
                    "reasoning": "Keyword-based fallback detection",
                    "suggested_format": "legal_memorandum"
                }
            else:
                return {
                    "intent": "legal_consultation",
                    "confidence": 0.6,
                    "reasoning": "Default classification",
                    "suggested_format": "general_consultation"
                }

    async def get_dynamic_agent_prompts(self, intent_classification: Dict[str, str]) -> Dict[LegalAgentType, str]:
        """
        🎯 Generate dynamic agent prompts based on intent classification
        """
        
        intent = intent_classification.get("intent", "legal_consultation")
        
        # Base prompts that adapt to intent
        base_prompts = {
            LegalAgentType.FACT_ANALYZER: f"""أنت محلل وقائع قانوني متخصص في القانون السعودي.

تم تصنيف هذا الاستفسار كـ: {intent}

مهمتك حسب التصنيف:
- rights_inquiry: استخرج الحقوق القانونية ذات الصلة والجهات المسؤولة
- procedure_guide: حدد الإجراءات المطلوبة والمتطلبات والمواعيد
- legal_dispute: حلل الوقائع القانونية والأطراف والأضرار
- legal_consultation: قدم تحليلاً شاملاً للموقف القانوني
- document_review: استخرج النقاط القانونية الرئيسية من الوثيقة
- comparative_analysis: حدد نقاط المقارنة والمعايير القانونية

قدم تحليلاً واضحاً ومباشراً بدون ذكر التصنيفات الداخلية.""",

            LegalAgentType.DOCUMENT_DRAFTER: f"""أنت محام ذكي متخصص في صياغة ردود قانونية متكيفة.

نوع الاستفسار: {intent}

قوالب الرد حسب النوع:

**rights_inquiry - شرح الحقوق:**
```
🔍 حقوقك القانونية في [المجال]

**الحق الأول**: [شرح مفصل]
**المرجع القانوني**: [المادة والنظام]

**كيفية المطالبة**:
• [خطوات عملية]

**جهات الحماية**:
• [الجهات المختصة]
```

**procedure_guide - دليل الإجراءات:**
```
📋 الإجراءات المطلوبة لـ [الهدف]

**الخطوة 1**: [تفصيل كامل]
• المدة: [الوقت]
• التكلفة: [المبلغ]

**المستندات المطلوبة**:
• [قائمة المستندات]

**الجهات المختصة**:
• [معلومات التواصل]
```

**legal_dispute - مذكرة قانونية:**
```
⚖️ التحليل القانوني للموقف

**الوقائع**:
[سرد منطقي]

**الحجج القانونية**:
[الحجج مع الأدلة]

**التوصيات**:
[الخطوات المقترحة]
```

**legal_consultation - استشارة عامة:**
```
💡 الاستشارة القانونية

**التحليل القانوني**:
[تحليل شامل]

**الخيارات المتاحة**:
[البدائل القانونية]

**التوصيات**:
[النصائح العملية]
```

اختر القالب المناسب تلقائياً بناءً على التصنيف."""
        }
        
        # Return only our dynamic prompts
        return base_prompts
    

    async def _enhanced_legal_research_with_rag(self, query: str, context: Optional[str] = None) -> AsyncIterator[str]:
        """Enhanced legal research using RAG + AI reasoning"""
        
        try:
            # STEP 1: Use your RAG system to find relevant documents
            from rag_engine import rag_engine
            
            print("🔍 Searching RAG database for relevant legal documents...")
            
            # Get relevant documents from your vector database using your existing RAG
            relevant_docs = []
            async for chunk in rag_engine.ask_question_streaming(query):
                relevant_docs.append(chunk)
            
            rag_results = ''.join(relevant_docs)
            
            # STEP 2: Enhanced prompt with real legal documents
            enhanced_input = f"""
            المستندات القانونية ذات الصلة من قاعدة البيانات:
            {rag_results}
            
            الاستفسار الأصلي: {query}
            
            المطلوب: تحليل هذه المستندات الفعلية وربطها بالاستفسار مع إضافة التفسير والتحليل القانوني.
            """
            
            # STEP 3: AI reasoning with real legal documents
            async for chunk in self.agents[LegalAgentType.LEGAL_RESEARCHER].process_streaming(
                enhanced_input, context
            ):
                yield chunk
                
        except Exception as e:
            print(f"❌ Enhanced RAG research failed: {e}")
            # Fallback to standard AI-only research
            async for chunk in self.agents[LegalAgentType.LEGAL_RESEARCHER].process_streaming(
                query, context
            ):
                yield chunk
            
    async def process_legal_query_streaming(
        self, 
        query: str, 
        enable_trust_trail: bool = False,
        conversation_context: Optional[List[Dict]] = None
    ) -> AsyncIterator[str]:
        """
        🎯 SMART STREAMING: AI-powered intent classification + dynamic response formatting + CITATION VALIDATION
        Cost: ~3,200 tokens (~$0.014 per query) - includes citation validation
        """
        
        start_time = time.time()
        context_summary = ""
        if conversation_context:
            context_summary = self._summarize_conversation_context(conversation_context)
        
        # Variables to store content for citation validation
        fact_content = ""
        research_content = ""
        draft_content = ""
        
        try:
            # 🧠 STEP 0: AI-POWERED INTENT CLASSIFICATION
            print("🧠 Classifying intent with AI...")
            intent_classification = await self.classify_intent(query, conversation_context)
            intent = intent_classification.get('intent', 'legal_consultation')
            confidence = intent_classification.get('confidence', 0.8)
            
            print(f"🎯 Intent: {intent} (confidence: {confidence:.1%})")
            
            # 🎯 STEP 1: GET DYNAMIC AGENT PROMPTS
            dynamic_prompts = await self.get_dynamic_agent_prompts(intent_classification)
            
            # Temporarily override agent prompts for this query
            original_prompts = {}
            for agent_type, prompt in dynamic_prompts.items():
                if agent_type in self.agents:
                    original_prompts[agent_type] = self.agents[agent_type].system_prompts.copy()
                    self.agents[agent_type].system_prompts[agent_type] = prompt
            
            # 🔍 STEP 2: FACT ANALYSIS (Stream with intent-aware prompts)
            print("🔍 Step 1: Analyzing legal facts...")
            
            if intent in ['rights_inquiry', 'procedure_guide']:
                yield "بناءً على التحليل القانوني:\n\n"
            else:
                yield "تحليل الموقف القانوني:\n\n"
            
            # Collect fact analysis content for citation validation
            fact_chunks = []
            async for chunk in self.agents[LegalAgentType.FACT_ANALYZER].process_streaming(
                query, context_summary
            ):
                fact_chunks.append(chunk)
                yield chunk
            
            fact_content = ''.join(fact_chunks)
            yield "\n\n"
            
            # 📚 STEP 3: ENHANCED LEGAL RESEARCH (RAG + AI)
            print("📚 Step 2: Researching legal precedents with RAG...")

            if intent == 'rights_inquiry':
                yield "الأسس القانونية لحقوقك:\n\n"
            elif intent == 'procedure_guide':
                yield "الإطار القانوني للإجراءات:\n\n"
            elif intent == 'legal_dispute':
                yield "السوابق القضائية ذات الصلة:\n\n"
            else:
                yield "المراجع القانونية ذات الصلة:\n\n"

            # 🚀 ENHANCED: Use RAG + AI for legal research
            research_chunks = []
            async for chunk in self._enhanced_legal_research_with_rag(query, context_summary):
                research_chunks.append(chunk)
                yield chunk
            
            research_content = ''.join(research_chunks)
            yield "\n\n"
            
            # 🏗️ STEP 4: DOCUMENT DRAFTING
            print("📝 Step 3: Drafting legal response...")
            
            # Pass intent information to the document drafter
            final_input = f"Intent: {intent}\nConfidence: {confidence}\nQuery: {query}"
            
            # Collect draft content for citation validation
            draft_chunks = []
            async for chunk in self.agents[LegalAgentType.DOCUMENT_DRAFTER].process_streaming(
                final_input, context_summary
            ):
                draft_chunks.append(chunk)
                yield chunk
            
            draft_content = ''.join(draft_chunks)
            yield "\n\n"
            
            # 🔍 STEP 5: CITATION VALIDATION (NEW!)
            print("🔍 Step 4: Validating citations and legal references...")
            yield "🔍 **التحقق من صحة المراجع القانونية**\n\n"
            
            # Combine all content for comprehensive citation validation
            all_content_for_validation = f"""
    المحتوى للمراجعة:

    التحليل القانوني:
    {fact_content}

    البحث القانوني:
    {research_content}

    المسودة النهائية:
    {draft_content}

    المطلوب: التحقق من جميع الاستشهادات القانونية المذكورة أعلاه وتقييم مستوى الثقة فيها.
    """
            
            # Stream citation validation results
            async for chunk in self.agents[LegalAgentType.CITATION_VALIDATOR].process_streaming(
                all_content_for_validation, context_summary
            ):
                yield chunk
            
            # 🔧 STEP 6: RESTORE ORIGINAL PROMPTS
            for agent_type, original_prompt in original_prompts.items():
                if agent_type in self.agents:
                    self.agents[agent_type].system_prompts = original_prompt
            
            print(f"✅ Smart multi-agent streaming with citation validation completed. Intent: {intent}")
            
        except Exception as e:
            print(f"❌ Smart multi-agent streaming failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Restore prompts even if there's an error
            try:
                for agent_type, original_prompt in original_prompts.items():
                    if agent_type in self.agents:
                        self.agents[agent_type].system_prompts = original_prompt
            except:
                pass
            
            yield f"تم معالجة استفسارك بنظام مبسط نظراً لخطأ تقني مؤقت.\n\n{query}\n\nيرجى إعادة المحاولة أو إعادة صياغة السؤال للحصول على تحليل قانوني متقدم."
    async def _execute_agent_step(
        self,
        agent_type: LegalAgentType,
        step_number: int,
        step_name: str,
        input_data: str,
        context: Optional[str] = None
    ) -> AgentStep:
        """Execute individual agent step with timing and error handling"""
        
        step_start = time.time()
        
        try:
            output, citations, confidence = await self.agents[agent_type].process(input_data, context)
            
            processing_time = int((time.time() - step_start) * 1000)
            
            return AgentStep(
                agent_type=agent_type,
                step_number=step_number,
                step_name=step_name,
                input_data=input_data[:200] + "..." if len(input_data) > 200 else input_data,
                output_data=output,
                citations=citations,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat(),
                sources_verified=False
            )
            
        except Exception as e:
            return AgentStep(
                agent_type=agent_type,
                step_number=step_number,
                step_name=step_name,
                input_data=input_data[:200] + "..." if len(input_data) > 200 else input_data,
                output_data=f"خطأ في المعالجة: {str(e)}",
                citations=[],
                confidence_score=0.1,
                processing_time_ms=int((time.time() - step_start) * 1000),
                timestamp=datetime.now().isoformat(),
                sources_verified=False
            )
    
    def _compile_final_answer(self, reasoning_steps: List[AgentStep], enable_trust_trail: bool) -> str:
        """Compile final answer with optional trust trail"""
        
        # Get the main legal advice from the drafting step
        draft_step = next((step for step in reasoning_steps if step.agent_type == LegalAgentType.DOCUMENT_DRAFTER), None)
        main_answer = draft_step.output_data if draft_step else "تعذر إنتاج الإجابة القانونية."
        
        if not enable_trust_trail:
            return main_answer
        
        # Add trust trail for transparency
        trust_trail = "\n\n" + "="*60 + "\n"
        trust_trail += "🔍 **سلسلة التحليل القانوني** (Trust Trail)\n"
        trust_trail += "="*60 + "\n\n"
        
        for step in reasoning_steps:
            trust_trail += f"**{step.step_number}. {step.step_name}**\n"
            trust_trail += f"⏱️ وقت المعالجة: {step.processing_time_ms}ms\n"
            trust_trail += f"📊 مستوى الثقة: {step.confidence_score:.1%}\n"
            
            if step.citations:
                trust_trail += f"📚 المراجع: {', '.join(step.citations[:3])}" 
                if len(step.citations) > 3:
                    trust_trail += f" و {len(step.citations) - 3} مراجع أخرى"
                trust_trail += "\n"
            
            trust_trail += f"💭 النتيجة: {step.output_data[:150]}...\n\n"
        
        return main_answer + trust_trail
    
    def _summarize_conversation_context(self, context: List[Dict]) -> str:
        """Summarize conversation context for agents"""
        if not context or len(context) < 2:
            return ""
        
        # Get last few exchanges
        recent_context = context[-4:] if len(context) > 4 else context
        
        summary = "السياق من المحادثة السابقة:\n"
        for msg in recent_context:
            role = "المستخدم" if msg.get("role") == "user" else "المساعد"
            content = msg.get("content", "")[:100]
            summary += f"- {role}: {content}...\n"
        
        return summary
    
    async def _fallback_response(self, query: str, start_time: float) -> LegalReasoningResult:
        """Fallback to simple response if multi-agent fails"""
        
        simple_response = f"""تم معالجة استفسارك بنظام مبسط نظراً لخطأ تقني مؤقت.

{query}

يرجى إعادة المحاولة أو إعادة صياغة السؤال للحصول على تحليل قانوني متقدم."""

        fallback_step = AgentStep(
            agent_type=LegalAgentType.FACT_ANALYZER,
            step_number=1,
            step_name="معالجة مبسطة",
            input_data=query,
            output_data=simple_response,
            citations=[],
            confidence_score=0.3,
            processing_time_ms=int((time.time() - start_time) * 1000),
            timestamp=datetime.now().isoformat(),
            sources_verified=False
        )
        
        return LegalReasoningResult(
            query=query,
            final_answer=simple_response,
            reasoning_steps=[fallback_step],
            total_processing_time_ms=int((time.time() - start_time) * 1000),
            overall_confidence=0.3,
            trust_trail_enabled=False,
            citations_summary=[]
        )

class EnhancedRAGEngine:
    """
    🚀 ENHANCED RAG ENGINE WITH MULTI-AGENT INTEGRATION
    
    This integrates with your existing rag_engine.py while adding multi-agent capabilities
    """
    
    def __init__(self):
        # Use the imported OpenAI client
        self.openai_client = openai_client
        self.orchestrator = MultiAgentLegalOrchestrator(self.openai_client)
        
        # Flag to enable/disable multi-agent processing
        self.multi_agent_enabled = True
    
    async def ask_question_with_multi_agent(
        self, 
        query: str, 
        conversation_context: Optional[List[Dict]] = None,
        enable_trust_trail: bool = False
    ) -> AsyncIterator[str]:
        """
        🎯 NEW METHOD: Multi-agent legal reasoning with streaming
        """
        
        if not self.multi_agent_enabled:
            # Fallback to existing single-agent (would need to import from rag_engine)
            try:
                from rag_engine import ask_question_with_context
                response = await ask_question_with_context(query, conversation_context or [])
                
                # Stream the response in chunks
                chunk_size = 50
                for i in range(0, len(response), chunk_size):
                    chunk = response[i:i + chunk_size]
                    yield chunk
                    await asyncio.sleep(0.03)
                return
            except ImportError:
                # If can't import, use simple fallback
                yield "عذراً، النظام المتقدم غير متاح حالياً. يرجى المحاولة لاحقاً."
                return
        
        try:
            # Process with REAL streaming multi-agent system
            async for chunk in self.orchestrator.process_legal_query_streaming(
                query=query,
                enable_trust_trail=enable_trust_trail,
                conversation_context=conversation_context
            ):
                yield chunk  # Real-time streaming from agents
            
            # Send trust trail data if enabled
            if enable_trust_trail:
                trust_trail_data = {
                    "type": "trust_trail",
                    "reasoning_steps": [],  # Would need to be implemented
                    "citations_summary": []
                }
                yield f"\n\ndata: {json.dumps(trust_trail_data)}\n\n"
                
        except Exception as e:
            print(f"❌ Multi-agent processing failed, using fallback: {e}")
            
            # Simple fallback response
            fallback_response = f"""تم معالجة سؤالك بالنظام الأساسي:

{query}

يرجى إعادة صياغة السؤال إذا كنت بحاجة لتحليل أكثر تفصيلاً."""
            
            chunk_size = 50
            for i in range(0, len(fallback_response), chunk_size):
                chunk = fallback_response[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.03)

# Test function for debugging
async def test_multi_agent():
    """Test function to verify multi-agent system works"""
    try:
        enhanced_rag = EnhancedRAGEngine()
        
        query = "موظف تم فصله بدون مبرر، ما حقوقه؟"
        print(f"🧪 Testing multi-agent with query: {query}")
        
        response_chunks = []
        async for chunk in enhanced_rag.ask_question_with_multi_agent(
            query=query,
            enable_trust_trail=True
        ):
            response_chunks.append(chunk)
            print(chunk, end="", flush=True)
        
        print(f"\n✅ Test completed. Total chunks: {len(response_chunks)}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test when file is executed directly
    import asyncio
    asyncio.run(test_multi_agent())