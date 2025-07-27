"""
Intelligent RAG Engine with AI-Powered Intent Classification
No hard-coding - AI handles all classification and prompt selection
Natural conversations + Smart document retrieval + Dynamic prompt selection
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
    print("✅ Using OpenAI for intelligent legal AI with classification")
elif DEEPSEEK_API_KEY:
    ai_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
    ai_model = "deepseek-chat"
    classification_model = "deepseek-chat"
    print("✅ Using DeepSeek for intelligent legal AI with classification")
else:
    raise ValueError("❌ Either OPENAI_API_KEY or DEEPSEEK_API_KEY must be provided")


# DYNAMIC PROMPTS - NO HARD-CODING OF CATEGORIES
CLASSIFICATION_PROMPT = """أنت خبير في تحليل الاستفسارات القانونية. حلل هذا السؤال وحدد نوع الاستشارة المطلوبة.

السؤال: {query}

ردك يجب أن يكون JSON فقط بهذا التنسيق:
{{
    "category": "GENERAL_QUESTION | ACTIVE_DISPUTE | PLANNING_ACTION",
    "confidence": 0.95,
    "reasoning": "سبب التصنيف"
}}

التصنيفات:
- GENERAL_QUESTION: سؤال عام للمعرفة ("ما هي", "كيف", "هل يجوز")
- ACTIVE_DISPUTE: مشكلة قانونية نشطة تحتاج دفاع ("رفع علي دعوى", "خصمي يدعي", "كيف أرد")
- PLANNING_ACTION: يخطط لاتخاذ إجراء قانوني ("أريد مقاضاة", "هل أرفع دعوى", "كيف أرفع قضية")

ردك JSON فقط، لا نص إضافي."""

# DYNAMIC PROMPT TEMPLATES - AI CHOOSES THE RIGHT PERSONALITY
PROMPT_TEMPLATES = {
    "GENERAL_QUESTION": """أنت مستشار قانوني سعودي ودود ومفيد.

🎯 مهمتك:
- مساعدة المستخدمين بوضوح وبساطة
- شرح الحقوق والقوانين بطريقة مفهومة  
- إعطاء نصائح عملية قابلة للتطبيق
- طرح أسئلة للفهم أكثر عند الحاجة

⚖️ منهجك:
- ابدأ بإجابة مباشرة على السؤال
- اذكر المصدر القانوني بطبيعية: "حسب نظام العمل، المادة 12 , لابد من ذكر المصدر اذا وجد"
- قدم خطوات عملية واضحة
- لا تعقد الأمور بلا داع

🔥 النهاية الذكية:
- اقترح الخطوة التالية المنطقية للمستخدم
- كن محدداً بناءً على حالته

🚫 تجنب:
- اللغة المعقدة والمصطلحات الصعبة
- الرموز التعبيرية المفرطة  
- القوالب الجاهزة
- الإطالة بلا فائدة

تحدث كمستشار محترف يهتم بمساعدة الناس فهم حقوقهم.""",

    "ACTIVE_DISPUTE": """

# ACTIVE_DISPUTE - Reasoning Model

## Core Legal Identity
أنت محامٍ سعودي محترف، متمرس في الدفاع المدني، تمتلك قدرة استثنائية على تحليل الدعاوى وكشف نقاط ضعفها. تتعامل مع كل قضية كطبيب جراح - بدقة ولا مجال للخطأ.

## Legal Philosophy
- الأدلة تتحدث، ليس العواطف
- كل ادعاء يحتاج إثبات قاطع
- القانون أداة للعدالة، ليس للاستغلال
- الخصم بريء حتى يثبت براءة ادعائه

## Reasoning Framework

### Primary Analysis Mode
اسأل نفسك دائماً: "ما هو أضعف عنصر في هذه الدعوى؟" ثم ابني تحليلك حول هذا العنصر.

### Legal Investigation Process
1. **حلل الأدلة**: ما المفقود؟ ما المشكوك فيه؟ ما المتناقض؟
2. **اختبر المنطق القانوني**: هل الادعاء منطقي قانونياً؟
3. **فحص السوابق**: كيف ينظر القضاء لحالات مماثلة؟
4. **تقييم النتائج**: ما هي أقوى استراتيجية دفاع؟

## Prohibited Approaches
🚫 **ممنوع نهائياً:**
- التبع الأعمى لقوالب جاهزة
- افتراض حسن نية الخصم
- الاعتماد على الاحتمالات ("ربما"، "قد يكون")
- اقتراح اليمين الحاسمة
- النبرة العاطفية أو الهجومية غير المبررة
- نسخ مواد القانون دون ربطها بالواقع

## Dynamic Response Strategy

### Natural Flow Principle
دع كل قضية تحدد طريقة تحليلها:
- قضية ضعيفة الأدلة؟ ابدأ بتفكيك الأدلة
- قضية متناقضة؟ ابدأ بكشف التناقضات  
- قضية مفتقرة للسند القانوني؟ ابدأ بالقانون
- قضية واضحة الكيدية؟ ابدأ بكشف سوء النية

### Adaptive Structure
لا تلتزم بهيكل ثابت. استخدم ما يناسب القضية:
- تحليل مباشر للأدلة
- مناقشة قانونية متعمقة  
- استراتيجية إجرائية
- تحليل نفسي لدوافع المدعي

## Professional Standards

### Tone Guidelines
- **حازم دون عدوانية**: كن واثقاً، ليس متنمراً
- **ذكي دون تعالي**: أظهر خبرتك، لا غرورك
- **ساخر بلباقة**: الذكاء يتحدث بهدوء

### Credibility Markers
- استشهد بالقانون عند الحاجة، لا للإعجاب
- اربط كل نقطة قانونية بالواقع مباشرة
- قدم حلول عملية، ليس فلسفة قانونية

## Closing Strategy
اختتم بطريقة طبيعية تناسب السياق:
- اقتراح عملي محدد
- سؤال استراتيجي
- ملخص قوي للموقف
- خطوة تالية واضحة

## The Ultimate Test
بعد كتابة تحليلك، اسأل نفسك:
"هل يبدو هذا وكأنني أحلل قضية حقيقية لموكل حقيقي، أم وكأنني أملأ استمارة؟"

إذا كان الجواب الثاني، أعد الكتابة.
""",

    "PLANNING_ACTION": """أنت مستشار قانوني استراتيجي متخصص في التخطيط للإجراءات القانونية.

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

🔥 التركيز:
- خطة عمل واضحة وقابلة للتطبيق
- توقعات واقعية للنتائج
- بدائل إذا فشل المسار الأساسي

تحدث كمستشار استراتيجي يساعد في اتخاذ القرارات الذكية."""
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


class DocumentRetriever:
    """Smart document retriever - gets relevant Saudi legal documents from database"""
    
    def __init__(self, storage: VectorStore, ai_client: AsyncOpenAI):
        self.storage = storage
        self.ai_client = ai_client
        self.initialized = False
        logger.info(f"DocumentRetriever initialized with {type(storage).__name__}")
    
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
    
    async def get_relevant_documents(self, query: str, top_k: int = 3, user_intent: str = "GENERAL_QUESTION") -> List[Chunk]:
        """
        Enhanced document retrieval with dual-stage filtering:
        Stage 1: Content-based retrieval (existing system)  
        Stage 2: Style-based filtering using AI
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            stats = await self.storage.get_stats()
            if stats.total_chunks == 0:
                logger.info("No documents found in storage - using general knowledge")
                return []
            
            logger.info(f"🔍 Enhanced search in {stats.total_chunks} documents for: '{query[:50]}...'")
            logger.info(f"📋 User intent: {user_intent}")
            
            # Get query embedding
            response = await self.ai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # STAGE 1: Content-based retrieval (your existing system)
            logger.info("🚀 Stage 1: Content-based document retrieval")
            
            # Get more candidates for style filtering (4x the requested amount)
            expanded_top_k = min(top_k * 4, 15)  # Get more candidates but cap at 15
            search_results = await self.storage.search_similar(
                query_embedding, 
                top_k=expanded_top_k, 
                query_text=query, 
                openai_client=self.ai_client
            )
            content_candidates = [result.chunk for result in search_results]
            
            if not content_candidates:
                logger.info("No relevant documents found - using general knowledge")
                return []
            
            logger.info(f"📊 Stage 1: Found {len(content_candidates)} content matches")
            
            # STAGE 2: Style-based filtering (only if we have multiple candidates)
            if len(content_candidates) > top_k and user_intent == "ACTIVE_DISPUTE":
                try:
                    logger.info("🎨 Stage 2: AI-powered style filtering")
                    
                    # Import style classifier
                    from app.legal_reasoning.ai_style_classifier import AIStyleClassifier
                    style_classifier = AIStyleClassifier(self.ai_client)
                    
                    # Get target style for this intent
                    target_style = style_classifier.get_style_for_intent(user_intent)
                    logger.info(f"🎯 Target style: {target_style}")
                    
                    # Classify documents by style
                    styled_documents = await style_classifier.filter_documents_by_style(
                        content_candidates, 
                        target_style=target_style,
                        min_confidence=0.6  # Lower threshold for more matches
                    )
                    
                    # Separate style matches from others
                    style_matches = [doc for doc in styled_documents if doc["style_match"]]
                    all_styled = styled_documents
                    
                    logger.info(f"✨ Style matches: {len(style_matches)}")
                    
                    # Smart selection: prioritize style matches
                    final_documents = []
                    
                    if style_matches:
                        # Add style matches first
                        style_docs = [doc["document"] for doc in style_matches[:top_k]]
                        final_documents.extend(style_docs)
                        
                        # Fill remaining with best content matches
                        remaining = top_k - len(style_docs)
                        if remaining > 0:
                            other_docs = [doc["document"] for doc in all_styled 
                                        if not doc["style_match"]][:remaining]
                            final_documents.extend(other_docs)
                        
                        logger.info(f"🎯 Selected: {len([d for d in styled_documents[:len(final_documents)] if d['style_match']])} style + {len(final_documents) - len([d for d in styled_documents[:len(final_documents)] if d['style_match']])} content")
                    else:
                        # No style matches - use best content
                        final_documents = [doc["document"] for doc in all_styled[:top_k]]
                        logger.info(f"📊 No style matches - using top {len(final_documents)} content matches")
                    
                    relevant_chunks = final_documents[:top_k]
                    
                except Exception as style_error:
                    logger.warning(f"Style filtering failed: {style_error}, using content-only")
                    relevant_chunks = content_candidates[:top_k]
            else:
                # Use original content-based results for non-dispute queries or limited candidates
                relevant_chunks = content_candidates[:top_k]
                logger.info(f"📊 Using content-based retrieval ({user_intent})")
            
            # Log final results (keeping your original format)
            if relevant_chunks:
                logger.info(f"Found {len(relevant_chunks)} relevant documents:")
                for i, chunk in enumerate(relevant_chunks):
                    # Find similarity score from original search results
                    similarity = 0.0
                    for result in search_results:
                        if result.chunk.id == chunk.id:
                            similarity = result.similarity_score
                            break
                    logger.info(f"  {i+1}. {chunk.title[:50]}... (similarity: {similarity:.3f})")
            else:
                logger.info("No relevant documents found - using general knowledge")
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


class IntentClassifier:
    """AI-powered intent classifier - no hard-coding"""
    
    def __init__(self, ai_client: AsyncOpenAI, model: str):
        self.ai_client = ai_client
        self.model = model
        logger.info("🧠 AI Intent Classifier initialized - zero hard-coding")
    
    async def classify_intent(self, query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, any]:
        """Use AI to classify user intent dynamically"""
        try:
            # Build context for better classification
            context = ""
            if conversation_history:
                recent_context = conversation_history[-3:]  # Last 3 messages for context
                context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_context])
                context = f"\n\nسياق المحادثة:\n{context}\n"
            
            classification_prompt = CLASSIFICATION_PROMPT.format(query=query) + context
            
            logger.info(f"🧠 Classifying intent for: {query[:30]}...")
            
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=200,
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
            
            logger.info(f"🎯 Intent classified: {classification['category']} (confidence: {classification['confidence']:.2f})")
            
            # Validate classification
            valid_categories = ["GENERAL_QUESTION", "ACTIVE_DISPUTE", "PLANNING_ACTION"]
            if classification["category"] not in valid_categories:
                logger.warning(f"Invalid category: {classification['category']}, defaulting to GENERAL_QUESTION")
                classification["category"] = "GENERAL_QUESTION"
                classification["confidence"] = 0.5
            
            return classification
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            # Safe fallback
            return {
                "category": "GENERAL_QUESTION",
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}"
            }


def format_legal_context_naturally(retrieved_chunks: List[Chunk]) -> str:
    """Format legal documents in a natural way"""
    if not retrieved_chunks:
        return ""
    
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        formatted_chunk = f"""
**مرجع {i}: {chunk.title}**
{chunk.content}
"""
        context_parts.append(formatted_chunk)
    
    context = f"""لديك هذه المراجع القانونية السعودية ذات الصلة:

{chr(10).join(context_parts)}

استخدم هذه المراجع للمساعدة في إجابتك، ولكن لا تجعل ردك يبدو كآلة قانونية. تحدث بطريقة طبيعية واستشهد بالمراجع عند الحاجة فقط."""
    
    return context


class IntelligentLegalRAG:
    """
    Intelligent Legal RAG with AI-Powered Intent Classification
    No hard-coding - AI handles classification and prompt selection
    """
    
    def __init__(self):
        """Initialize intelligent RAG with AI classification"""
        self.ai_client = ai_client
        self.ai_model = ai_model
        
        # Add smart document retrieval
        self.storage = StorageFactory.create_storage()
        self.retriever = DocumentRetriever(
            storage=self.storage,
            ai_client=self.ai_client
        )
        
        # Add AI-powered intent classifier
        self.classifier = IntentClassifier(
            ai_client=self.ai_client,
            model=classification_model
        )
        
        logger.info("🚀 Intelligent Legal RAG initialized - AI-powered classification + Smart retrieval!")
    
    async def ask_question_streaming(self, query: str) -> AsyncIterator[str]:
        """
        Intelligent legal consultation with AI-powered intent classification
        """
        try:
            logger.info(f"Processing intelligent legal question: {query[:50]}...")
            
            # Stage 1: AI-powered intent classification
            classification = await self.classifier.classify_intent(query)
            category = classification["category"]
            confidence = classification["confidence"]
            
            # Stage 2: Get relevant documents from database
            relevant_docs = await self.retriever.get_relevant_documents(query, top_k=3)
            
            # Stage 3: Select appropriate prompt based on AI classification
            system_prompt = PROMPT_TEMPLATES[category]
            
            # Stage 4: Build intelligent prompt with documents
            if relevant_docs:
                legal_context = format_legal_context_naturally(relevant_docs)
                full_prompt = f"""{legal_context}

السؤال: {query}"""
                logger.info(f"Using {len(relevant_docs)} relevant legal documents with {category} approach")
            else:
                full_prompt = query
                logger.info(f"No relevant documents found - using {category} approach with general knowledge")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ]
            
            # Stage 5: Stream intelligent response
            async for chunk in self._stream_ai_response(messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Intelligent legal AI error: {e}")
            yield f"عذراً، حدث خطأ في معالجة سؤالك: {str(e)}"
    
    async def ask_question_with_context_streaming(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """
        Intelligent context-aware legal consultation with AI classification
        """
        try:
            logger.info(f"Processing intelligent contextual legal question: {query[:50]}...")
            logger.info(f"Conversation context: {len(conversation_history)} messages")
            
            # Stage 1: AI-powered intent classification with context
            classification = await self.classifier.classify_intent(query, conversation_history)
            category = classification["category"]
            confidence = classification["confidence"]
            
            # Stage 2: Get relevant documents
            relevant_docs = await self.retriever.get_relevant_documents(query, top_k=3)
            
            # Stage 3: Select appropriate prompt
            system_prompt = PROMPT_TEMPLATES[category]
            
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
            
            # Stage 5: Add current question with legal context if available
            if relevant_docs:
                legal_context = format_legal_context_naturally(relevant_docs)
                contextual_prompt = f"""{legal_context}

السؤال: {query}"""
                logger.info(f"Using {len(relevant_docs)} relevant legal documents with {category} approach (contextual)")
            else:
                contextual_prompt = query
                logger.info(f"No relevant documents found - using {category} approach with contextual general knowledge")
            
            messages.append({
                "role": "user", 
                "content": contextual_prompt
            })
            
            # Stage 6: Stream intelligent contextual response
            async for chunk in self._stream_ai_response(messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Intelligent contextual legal AI error: {e}")
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
        """Intelligent conversation title generation"""
        try:
            title_prompt = f"اقترح عنواناً مختصراً (أقل من 30 حرف) لهذه الاستشارة القانونية: {first_message[:100]}"
            
            response = await self.ai_client.chat.completions.create(
                model=classification_model,  # Use small model for title generation
                messages=[{"role": "user", "content": title_prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            title = title.strip('"').strip("'").strip()
            
            # Remove common prefixes
            prefixes = ["العنوان:", "المقترح:", "عنوان:"]
            for prefix in prefixes:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            
            return title[:30] if len(title) > 30 else title
            
        except Exception as e:
            logger.error(f"Title generation error: {e}")
            return first_message[:25] + "..." if len(first_message) > 25 else first_message


# Global instance - maintains compatibility with existing code
rag_engine = IntelligentLegalRAG()

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
async def test_intelligent_rag():
    """Test the intelligent RAG system with classification"""
    print("🧪 Testing intelligent RAG engine with AI classification...")
    
    test_queries = [
        "ما هي عقوبات التهرب الضريبي؟",  # Should be GENERAL_QUESTION
        "رفع علي خصم دعوى كيدية كيف أرد عليه؟",  # Should be ACTIVE_DISPUTE
        "أريد مقاضاة شركتي هل الأمر يستحق؟"  # Should be PLANNING_ACTION
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
print("🏛️ Intelligent Legal RAG Engine loaded - AI-powered classification + Smart document retrieval!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_intelligent_rag())