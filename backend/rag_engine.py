"""
Multi-Domain Intelligent RAG Engine
Handles Legal (قانونية), Administrative (إدارية), and Technical (تقنية) consultations
AI-powered domain classification and specialized responses
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import List, Dict, Optional, AsyncIterator
import json

# Import the smart database components from old RAG
from app.storage.vector_store import VectorStore, Chunk
from app.storage.sqlite_store import SqliteVectorStore

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple API key configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize AI client - prioritize OpenAI, fallback to DeepSeek
if OPENAI_API_KEY:
    ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    ai_model = "gpt-4o"
    classification_model = "gpt-4o-mini"  # Small model for classification
    print("✅ Using OpenAI for multi-domain intelligent AI with classification")
elif DEEPSEEK_API_KEY:
    ai_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
    ai_model = "deepseek-chat"
    classification_model = "deepseek-chat"
    print("✅ Using DeepSeek for multi-domain intelligent AI with classification")
else:
    raise ValueError("❌ Either OPENAI_API_KEY or DEEPSEEK_API_KEY must be provided")


# ENHANCED CLASSIFICATION PROMPT - MULTI-DOMAIN
DOMAIN_CLASSIFICATION_PROMPT = """أنت خبير في تحليل الاستفسارات متعددة المجالات. حلل هذا السؤال وحدد المجال والنوع.

السؤال: {query}

ردك يجب أن يكون JSON فقط بهذا التنسيق:
{{
    "domain": "LEGAL | ADMINISTRATIVE | TECHNICAL",
    "category": "GENERAL_QUESTION | ACTIVE_DISPUTE | PLANNING_ACTION | TROUBLESHOOTING | IMPLEMENTATION",
    "confidence": 0.95,
    "reasoning": "سبب التصنيف"
}}

المجالات:
- LEGAL: استشارات قانونية (قوانين، دعاوى، حقوق، التزامات)
- ADMINISTRATIVE: استشارات إدارية (إجراءات حكومية، تراخيص، وثائق، معاملات)
- TECHNICAL: استشارات تقنية (برمجة، أنظمة، تقنية معلومات، حلول تقنية)

الفئات:
- GENERAL_QUESTION: سؤال عام للمعرفة ("ما هي", "كيف", "هل يجوز")
- ACTIVE_DISPUTE: مشكلة نشطة تحتاج حل فوري ("مواجه مشكلة", "خطأ", "لا يعمل")
- PLANNING_ACTION: يخطط لاتخاذ إجراء ("أريد تنفيذ", "كيف أبدأ", "ما الخطوات")
- TROUBLESHOOTING: حل مشاكل تقنية ("خطأ في النظام", "لا يعمل البرنامج")
- IMPLEMENTATION: تنفيذ حلول ("كيف أطور", "أريد بناء نظام")

ردك JSON فقط، لا نص إضافي."""

# MULTI-DOMAIN PROMPT TEMPLATES
PROMPT_TEMPLATES = {
    # LEGAL DOMAIN
    "LEGAL_GENERAL_QUESTION": """أنت مستشار قانوني سعودي ودود ومفيد.

🎯 مهمتك:
- مساعدة المستخدمين بوضوح وبساطة في الشؤون القانونية
- شرح الحقوق والقوانين بطريقة مفهومة  
- إعطاء نصائح قانونية عملية قابلة للتطبيق
- طرح أسئلة للفهم أكثر عند الحاجة

⚖️ منهجك:
- ابدأ بإجابة مباشرة على السؤال القانوني
- اذكر المصدر القانوني بطبيعية: "حسب نظام العمل، المادة 12"
- قدم خطوات عملية واضحة
- لا تعقد الأمور بلا داع

🔥 النهاية الذكية:
- اقترح الخطوة التالية المنطقية للمستخدم
- كن محدداً بناءً على حالته القانونية

تحدث كمستشار قانوني محترف يهتم بمساعدة الناس فهم حقوقهم.""",

    "LEGAL_ACTIVE_DISPUTE": """أنت محامٍ سعودي محترف، متمرس في الدفاع المدني، تمتلك قدرة استثنائية على تحليل الدعاوى وكشف نقاط ضعفها.

🎯 منهجك في التحليل:
- حلل الأدلة: ما المفقود؟ ما المشكوك فيه؟ ما المتناقض؟
- اختبر المنطق القانوني: هل الادعاء منطقي قانونياً؟
- فحص السوابق: كيف ينظر القضاء لحالات مماثلة؟
- تقييم النتائج: ما هي أقوى استراتيجية دفاع؟

⚖️ أسلوبك:
- حازم دون عدوانية: كن واثقاً، ليس متنمراً
- ذكي دون تعالي: أظهر خبرتك، لا غرورك
- استشهد بالقانون عند الحاجة، لا للإعجاب

🚫 ممنوع نهائياً:
- اقتراح اليمين الحاسمة
- النبرة العاطفية غير المبررة
- نسخ مواد القانون دون ربطها بالواقع

تحدث كمحامٍ خبير يحلل قضية حقيقية لموكل حقيقي.""",

    "LEGAL_PLANNING_ACTION": """أنت مستشار قانوني استراتيجي متخصص في التخطيط للإجراءات القانونية.

🎯 مهمتك:
- تقييم جدوى الإجراء القانوني المطلوب
- وضع استراتيجية واضحة خطوة بخطوة
- تحليل المخاطر والعوائد بصراحة
- إرشاد المستخدم للقرار الصحيح

⚖️ منهجك:
- قيم الموقف القانوني بموضوعية
- اشرح الخيارات المتاحة بوضوح
- حدد الإجراءات المطلوبة والتكاليف المتوقعة
- انصح بأفضل مسار بناءً على الحقائق

تحدث كمستشار استراتيجي يساعد في اتخاذ القرارات القانونية الذكية.""",

    # ADMINISTRATIVE DOMAIN
    "ADMINISTRATIVE_GENERAL_QUESTION": """أنت خبير في الإجراءات الإدارية والحكومية السعودية.

🏛️ مهمتك:
- شرح الإجراءات الحكومية والإدارية بوضوح
- إرشاد المستخدمين لأفضل الطرق لإنجاز معاملاتهم
- توضيح المتطلبات والوثائق المطلوبة
- تقديم نصائح عملية لتسريع الإجراءات

📋 منهجك:
- ابدأ بالخطوات الأساسية المطلوبة
- اذكر الجهات المختصة والمنصات الإلكترونية
- حدد المدة الزمنية المتوقعة والرسوم
- قدم بدائل إذا أمكن

🌐 التركيز على:
- المنصات الرقمية (أبشر، قوى، مساند، إلخ)
- الإجراءات الإلكترونية قبل الورقية
- توفير الوقت والجهد

تحدث كخبير إداري يساعد المواطنين في تسهيل معاملاتهم.""",

    "ADMINISTRATIVE_ACTIVE_DISPUTE": """أنت خبير في حل المشاكل الإدارية والحكومية.

🚨 مهمتك:
- تحليل المشكلة الإدارية بدقة
- تحديد الجهة المسؤولة عن الحل
- وضع خطة عمل فورية للحل
- تقديم البدائل المتاحة

🔧 منهجك:
- فهم طبيعة المشكلة وسببها
- تحديد الإجراءات الصحيحة التي فُوتت
- اقتراح طرق التواصل مع الجهات المختصة
- تقديم جدول زمني واقعي للحل

📞 التركيز على:
- قنوات التواصل الفعالة (تذاكر إلكترونية، خطوط ساخنة)
- التصعيد التدريجي للشكاوى
- الاستفادة من منصة "تواصل" الحكومية

تحدث كخبير إداري يحل المشاكل بطريقة عملية وسريعة.""",

    "ADMINISTRATIVE_PLANNING_ACTION": """أنت مستشار إداري متخصص في التخطيط للإجراءات الحكومية.

📊 مهمتك:
- التخطيط الشامل للإجراءات الإدارية المطلوبة
- ترتيب الخطوات بالتسلسل الصحيح
- تحديد الزمن والتكلفة المتوقعة
- تجنب الأخطاء الشائعة

🗓️ منهجك:
- ابدأ بتحديد الهدف النهائي
- قسم العملية لمراحل واضحة
- حدد المتطلبات لكل مرحلة
- ضع جدول زمني واقعي

💡 نصائحك تشمل:
- التحضير المسبق للوثائق
- استخدام الخدمات الإلكترونية
- تجنب الأوقات المزدحمة
- الاستفادة من الخدمات المميزة

تحدث كمخطط إداري محترف يضمن إنجاز المعاملات بكفاءة.""",

    # TECHNICAL DOMAIN
    "TECHNICAL_GENERAL_QUESTION": """أنت خبير تقني متخصص في تقنية المعلومات والحلول الرقمية.

💻 مهمتك:
- شرح المفاهيم التقنية بطريقة مبسطة ومفهومة
- تقديم إجابات عملية وقابلة للتطبيق
- مساعدة المستخدمين في فهم التقنيات الحديثة
- تقديم نصائح لاختيار الحلول المناسبة

🔧 منهجك:
- ابدأ بتعريف بسيط للمفهوم
- قدم أمثلة عملية من الواقع
- اذكر الفوائد والتحديات
- اقترح خطوات للتعلم أو التطبيق

🚀 التركيز على:
- الحلول العملية والفعالة
- التقنيات المناسبة للسوق السعودي
- الأمان والحماية الرقمية
- التكلفة والعائد

تحدث كخبير تقني يجعل التكنولوجيا مفهومة ومفيدة للجميع.""",

    "TECHNICAL_TROUBLESHOOTING": """أنت خبير في حل المشاكل التقنية والأخطاء البرمجية.

🔍 مهمتك:
- تشخيص المشكلة التقنية بدقة
- تحديد الأسباب المحتملة
- تقديم حلول عملية خطوة بخطوة
- منع تكرار المشكلة مستقبلاً

🛠️ منهجك:
- ابدأ بفهم تفاصيل المشكلة
- اطرح أسئلة تشخيصية محددة
- قدم الحلول من الأبسط للأعقد
- اشرح سبب كل حل مقترح

⚡ أسلوبك:
- سريع وعملي في التشخيص
- واضح في الشرح خطوة بخطوة
- صبور مع المستخدمين غير التقنيين
- يقدم بدائل متعددة

💡 نصائحك تشمل:
- إجراءات الوقاية
- أدوات التشخيص المفيدة
- نسخ احتياطية وحماية

تحدث كخبير تقني يحل المشاكل بطريقة منهجية وفعالة.""",

    "TECHNICAL_IMPLEMENTATION": """أنت مهندس حلول تقنية متخصص في تصميم وتطوير الأنظمة.

🏗️ مهمتك:
- تصميم حلول تقنية شاملة ومتكاملة
- تحديد التقنيات والأدوات المناسبة
- وضع خطة تنفيذ مرحلية وواقعية
- مراعاة الميزانية والمهارات المتاحة

🎯 منهجك:
- ابدأ بفهم المتطلبات بعمق
- حلل الخيارات التقنية المتاحة
- قدم توصيات مبررة بالأدلة
- ضع جدول زمني ومراحل واضحة

💼 اعتباراتك تشمل:
- التكلفة الإجمالية للملكية
- قابلية التوسع والصيانة
- الأمان وحماية البيانات
- سهولة الاستخدام والصيانة

🚀 تركز على:
- الحلول المثبتة والموثوقة
- التقنيات مفتوحة المصدر عند الإمكان
- التكامل مع الأنظمة الموجودة
- تدريب المستخدمين

تحدث كمهندس حلول خبير يبني أنظمة قوية وقابلة للاستدامة."""
}


class StorageFactory:
    """Factory for creating storage backends"""
    
    @staticmethod
    def create_storage() -> VectorStore:
        """Create storage backend based on environment configuration"""
        storage_type = os.getenv("VECTOR_STORAGE_TYPE", "sqlite").lower()
        
        if storage_type == "sqlite":
            db_path = os.getenv("SQLITE_DB_PATH", "data/vectors.db")
            return SqliteVectorStore(db_path)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")


class MultiDomainDocumentRetriever:
    """Smart document retriever for multi-domain consultations"""
    
    def __init__(self, storage: VectorStore, ai_client: AsyncOpenAI):
        self.storage = storage
        self.ai_client = ai_client
        self.initialized = False
        logger.info(f"MultiDomainDocumentRetriever initialized with {type(storage).__name__}")
    
    async def initialize(self) -> None:
        """Initialize storage backend"""
        if self.initialized:
            return
        
        try:
            await self.storage.initialize()
            stats = await self.storage.get_stats()
            logger.info(f"Storage initialized with {stats.total_chunks} existing documents")
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise
    
    async def get_relevant_documents(
        self, 
        query: str, 
        domain: str, 
        category: str, 
        top_k: int = 3
    ) -> List[Chunk]:
        """Enhanced document retrieval with domain-aware filtering"""
        if not self.initialized:
            await self.initialize()
        
        try:
            stats = await self.storage.get_stats()
            if stats.total_chunks == 0:
                logger.info("No documents found in storage - using general knowledge")
                return []
            
            logger.info(f"🔍 Multi-domain search in {stats.total_chunks} documents")
            logger.info(f"📋 Domain: {domain}, Category: {category}")
            logger.info(f"🔎 Query: '{query[:50]}...'")
            
            # Get query embedding
            response = await self.ai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=f"[{domain}] {query}"  # Domain-prefixed query for better relevance
            )
            query_embedding = response.data[0].embedding
            
            # Search with domain context
            search_results = await self.storage.search_similar(
                query_embedding, 
                top_k=top_k * 2,  # Get more candidates for domain filtering
                query_text=f"[{domain}] {query}", 
                openai_client=self.ai_client
            )
            
            relevant_chunks = [result.chunk for result in search_results[:top_k]]
            
            if relevant_chunks:
                logger.info(f"Found {len(relevant_chunks)} relevant {domain.lower()} documents:")
                for i, chunk in enumerate(relevant_chunks):
                    similarity = search_results[i].similarity_score if i < len(search_results) else 0.0
                    logger.info(f"  {i+1}. {chunk.title[:50]}... (similarity: {similarity:.3f})")
            else:
                logger.info(f"No relevant {domain.lower()} documents found - using general knowledge")
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving {domain.lower()} documents: {e}")
            return []


class MultiDomainIntentClassifier:
    """Enhanced AI-powered intent classifier for multiple domains"""
    
    def __init__(self, ai_client: AsyncOpenAI, model: str):
        self.ai_client = ai_client
        self.model = model
        logger.info("🧠 Multi-Domain AI Intent Classifier initialized")
    
    async def classify_intent(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """Use AI to classify user intent across multiple domains"""
        try:
            # Build context for better classification
            context = ""
            if conversation_history:
                recent_context = conversation_history[-3:]  # Last 3 messages for context
                context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_context])
                context = f"\n\nسياق المحادثة:\n{context}\n"
            
            classification_prompt = DOMAIN_CLASSIFICATION_PROMPT.format(query=query) + context
            
            logger.info(f"🧠 Classifying multi-domain intent for: {query[:30]}...")
            
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=300,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            # Parse AI response
            result_text = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown if present)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            classification = json.loads(result_text)
            
            logger.info(f"🎯 Intent classified: {classification['domain']}.{classification['category']} (confidence: {classification['confidence']:.2f})")
            
            # Validate classification
            valid_domains = ["LEGAL", "ADMINISTRATIVE", "TECHNICAL"]
            valid_categories = ["GENERAL_QUESTION", "ACTIVE_DISPUTE", "PLANNING_ACTION", "TROUBLESHOOTING", "IMPLEMENTATION"]
            
            if classification["domain"] not in valid_domains:
                logger.warning(f"Invalid domain: {classification['domain']}, defaulting to LEGAL")
                classification["domain"] = "LEGAL"
                classification["confidence"] = 0.5
            
            if classification["category"] not in valid_categories:
                logger.warning(f"Invalid category: {classification['category']}, defaulting to GENERAL_QUESTION")
                classification["category"] = "GENERAL_QUESTION"
                classification["confidence"] = min(classification["confidence"], 0.5)
            
            return classification
            
        except Exception as e:
            logger.error(f"Multi-domain intent classification error: {e}")
            # Safe fallback
            return {
                "domain": "LEGAL",
                "category": "GENERAL_QUESTION",
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}"
            }


def format_multi_domain_context(retrieved_chunks: List[Chunk], domain: str) -> str:
    """Format documents with domain-specific context"""
    if not retrieved_chunks:
        return ""
    
    domain_names = {
        "LEGAL": "القانونية",
        "ADMINISTRATIVE": "الإدارية", 
        "TECHNICAL": "التقنية"
    }
    
    domain_name = domain_names.get(domain, "ذات الصلة")
    
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        formatted_chunk = f"""
**مرجع {i}: {chunk.title}**
{chunk.content}
"""
        context_parts.append(formatted_chunk)
    
    context = f"""لديك هذه المراجع {domain_name} ذات الصلة:

{chr(10).join(context_parts)}

استخدم هذه المراجع للمساعدة في إجابتك، ولكن لا تجعل ردك يبدو كآلة. تحدث بطريقة طبيعية واستشهد بالمراجع عند الحاجة فقط."""
    
    return context


class MultiDomainIntelligentRAG:
    """
    Multi-Domain Intelligent RAG System
    Handles Legal, Administrative, and Technical consultations
    """
    
    def __init__(self):
        """Initialize multi-domain intelligent RAG"""
        self.ai_client = ai_client
        self.ai_model = ai_model
        
        # Add smart document retrieval
        self.storage = StorageFactory.create_storage()
        self.retriever = MultiDomainDocumentRetriever(
            storage=self.storage,
            ai_client=self.ai_client
        )
        
        # Add multi-domain AI-powered intent classifier
        self.classifier = MultiDomainIntentClassifier(
            ai_client=self.ai_client,
            model=classification_model
        )
        
        logger.info("🚀 Multi-Domain Intelligent RAG initialized - Legal, Administrative & Technical!")
    
    def _get_prompt_template(self, domain: str, category: str) -> str:
        """Get appropriate prompt template for domain and category"""
        template_key = f"{domain}_{category}"
        
        if template_key in PROMPT_TEMPLATES:
            return PROMPT_TEMPLATES[template_key]
        
        # Fallback to general question for the domain
        fallback_key = f"{domain}_GENERAL_QUESTION"
        if fallback_key in PROMPT_TEMPLATES:
            return PROMPT_TEMPLATES[fallback_key]
        
        # Ultimate fallback
        return PROMPT_TEMPLATES["LEGAL_GENERAL_QUESTION"]
    
    async def ask_question_streaming(self, query: str) -> AsyncIterator[str]:
        """
        Multi-domain intelligent consultation with AI-powered classification
        """
        try:
            logger.info(f"Processing multi-domain question: {query[:50]}...")
            
            # Stage 1: Multi-domain AI-powered intent classification
            classification = await self.classifier.classify_intent(query)
            domain = classification["domain"]
            category = classification["category"]
            confidence = classification["confidence"]
            
            # Stage 2: Get relevant documents from database
            relevant_docs = await self.retriever.get_relevant_documents(
                query, domain, category, top_k=3
            )
            
            # Stage 3: Select appropriate prompt based on AI classification
            system_prompt = self._get_prompt_template(domain, category)
            
            # Stage 4: Build intelligent prompt with documents
            if relevant_docs:
                domain_context = format_multi_domain_context(relevant_docs, domain)
                full_prompt = f"""{domain_context}

السؤال: {query}"""
                logger.info(f"Using {len(relevant_docs)} relevant {domain.lower()} documents with {domain}.{category} approach")
            else:
                full_prompt = query
                logger.info(f"No relevant documents found - using {domain}.{category} approach with general knowledge")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ]
            
            # Stage 5: Stream intelligent response
            async for chunk in self._stream_ai_response(messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Multi-domain intelligent AI error: {e}")
            yield f"عذراً، حدث خطأ في معالجة سؤالك: {str(e)}"
    
    async def ask_question_with_context_streaming(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """
        Multi-domain context-aware intelligent consultation
        """
        try:
            logger.info(f"Processing multi-domain contextual question: {query[:50]}...")
            logger.info(f"Conversation context: {len(conversation_history)} messages")
            
            # Stage 1: Multi-domain AI-powered intent classification with context
            classification = await self.classifier.classify_intent(query, conversation_history)
            domain = classification["domain"]
            category = classification["category"]
            confidence = classification["confidence"]
            
            # Stage 2: Get relevant documents
            relevant_docs = await self.retriever.get_relevant_documents(
                query, domain, category, top_k=3
            )
            
            # Stage 3: Select appropriate prompt
            system_prompt = self._get_prompt_template(domain, category)
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Stage 4: Add conversation history (last 8 messages)
            recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Stage 5: Add current question with domain context if available
            if relevant_docs:
                domain_context = format_multi_domain_context(relevant_docs, domain)
                contextual_prompt = f"""{domain_context}

السؤال: {query}"""
                logger.info(f"Using {len(relevant_docs)} relevant {domain.lower()} documents with {domain}.{category} approach (contextual)")
            else:
                contextual_prompt = query
                logger.info(f"No relevant documents found - using {domain}.{category} approach with contextual general knowledge")
            
            messages.append({
                "role": "user", 
                "content": contextual_prompt
            })
            
            # Stage 6: Stream intelligent contextual response
            async for chunk in self._stream_ai_response(messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Multi-domain contextual intelligent AI error: {e}")
            yield f"عذراً، حدث خطأ في معالجة سؤالك: {str(e)}"
    
    async def _stream_ai_response(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream AI response with error handling"""
        try:
            stream = await self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=messages,
                temperature=0.3,  # Balanced creativity and consistency
                max_tokens=1500,  # Reasonable length
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"AI streaming error: {e}")
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg or "429" in error_msg:
                yield "\n\n⏳ تم تجاوز الحد المسموح مؤقتاً. يرجى الانتظار دقيقة وإعادة المحاولة."
            elif "api key" in error_msg or "authentication" in error_msg:
                yield "\n\n🔑 خطأ في مفتاح API. يرجى التواصل مع الدعم الفني."
            else:
                yield f"\n\n❌ خطأ تقني: {str(e)}"
    
    async def generate_conversation_title(self, first_message: str) -> str:
        """Intelligent conversation title generation with domain awareness"""
        try:
            # First classify the domain for better title generation
            classification = await self.classifier.classify_intent(first_message)
            domain = classification["domain"]
            
            domain_prefixes = {
                "LEGAL": "استشارة قانونية",
                "ADMINISTRATIVE": "استشارة إدارية", 
                "TECHNICAL": "استشارة تقنية"
            }
            
            domain_prefix = domain_prefixes.get(domain, "استشارة")
            
            title_prompt = f"""اقترح عنواناً مختصراً (أقل من 30 حرف) لهذه الاستشارة من مجال {domain_prefix}: {first_message[:100]}
            
العنوان يجب أن يكون:
- واضح ومحدد
- يعكس طبيعة السؤال
- مناسب لمجال {domain_prefix}"""
            
            response = await self.ai_client.chat.completions.create(
                model=classification_model,  # Use small model for title generation
                messages=[{"role": "user", "content": title_prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            title = title.strip('"').strip("'").strip()
            
            # Remove common prefixes
            prefixes = ["العنوان:", "المقترح:", "عنوان:", domain_prefix + ":"]
            for prefix in prefixes:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            
            return title[:30] if len(title) > 30 else title
            
        except Exception as e:
            logger.error(f"Title generation error: {e}")
            return first_message[:25] + "..." if len(first_message) > 25 else first_message


# Global instance - maintains compatibility with existing code
rag_engine = MultiDomainIntelligentRAG()

# Legacy compatibility functions - exactly the same interface as before
async def ask_question(query: str) -> str:
    """Legacy sync function - converts streaming to complete response"""
    chunks = []
    async for chunk in rag_engine.ask_question_streaming(query):
        chunks.append(chunk)
    return ''.join(chunks)

async def ask_question_with_context(query: str, conversation_history: List[Dict[str, str]]) -> str:
    """Legacy sync function with context - converts streaming to complete response"""
    chunks = []
    async for chunk in rag_engine.ask_question_with_context_streaming(query, conversation_history):
        chunks.append(chunk)
    return ''.join(chunks)

async def generate_conversation_title(first_message: str) -> str:
    """Legacy function for title generation"""
    return await rag_engine.generate_conversation_title(first_message)

# Test function
async def test_multi_domain_rag():
    """Test the multi-domain RAG system with classification"""
    print("🧪 Testing Multi-Domain RAG Engine with AI classification...")
    
    test_queries = [
        # Legal queries
        "ما هي عقوبات التهرب الضريبي؟",  # LEGAL_GENERAL_QUESTION
        "رفع علي خصم دعوى كيدية كيف أرد عليه؟",  # LEGAL_ACTIVE_DISPUTE
        "أريد مقاضاة شركتي هل الأمر يستحق؟",  # LEGAL_PLANNING_ACTION
        
        # Administrative queries
        "كيف أجدد رخصة القيادة؟",  # ADMINISTRATIVE_GENERAL_QUESTION
        "رفضوا طلبي في أبشر كيف أحل المشكلة؟",  # ADMINISTRATIVE_ACTIVE_DISPUTE
        "أريد فتح محل تجاري ما الخطوات؟",  # ADMINISTRATIVE_PLANNING_ACTION
        
        # Technical queries
        "ما هو التعلم الآلي؟",  # TECHNICAL_GENERAL_QUESTION
        "موقعي لا يعمل كيف أصلحه؟",  # TECHNICAL_TROUBLESHOOTING
        "أريد بناء تطبيق جوال كيف أبدأ؟"  # TECHNICAL_IMPLEMENTATION
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing: {query}")
        print("Response:")
        
        response_chunks = []
        async for chunk in rag_engine.ask_question_streaming(query):
            response_chunks.append(chunk)
            print(chunk, end="", flush=True)
        
        print(f"\n✅ Test complete for this query!\n{'-'*50}")
    
    return True

# System initialization
print("🏛️ Multi-Domain Intelligent RAG Engine loaded!")
print("📋 Domains: Legal (قانونية) | Administrative (إدارية) | Technical (تقنية)")
print("🧠 AI-powered classification + Smart document retrieval!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_multi_domain_rag())