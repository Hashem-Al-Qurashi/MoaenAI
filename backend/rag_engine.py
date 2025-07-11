"""
Legal Reasoning RAG Engine - Production Ready
Zero tech debt, clean architecture, smart legal reasoning
Built for Saudi legal AI with proper issue analysis and contextual prompting
"""
from app.legal_reasoning.document_type_analyzer import LegalDocumentTypeAnalyzer, DocumentType
from app.legal_reasoning.document_generator import LegalDocumentGenerator
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
import markdown
from typing import List, Dict, Optional, Any, AsyncIterator
import re
import logging

# Import legal reasoning components
from app.legal_reasoning.issue_analyzer import LegalIssueAnalyzer, LegalIssue

# Import clean architecture components
from app.storage.vector_store import VectorStore, Chunk
from app.storage.sqlite_store import SqliteVectorStore

# Load environment variables
try:
    load_dotenv(".env")
except:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API key configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize AI clients - prioritize OpenAI, fallback to DeepSeek
if OPENAI_API_KEY:
    ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    ai_model = "gpt-4o"
    print("✅ Using OpenAI for async AI and embeddings")
elif DEEPSEEK_API_KEY:
    ai_client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
    ai_model = "deepseek-chat"
    print("✅ Using DeepSeek for async AI and embeddings")
else:
    raise ValueError("❌ Either OPENAI_API_KEY or DEEPSEEK_API_KEY must be provided in environment")


class StorageFactory:
    """Factory for creating storage backends based on configuration"""
    
    @staticmethod
    def create_storage() -> VectorStore:
        """Create storage backend based on environment configuration"""
        storage_type = os.getenv("VECTOR_STORAGE_TYPE", "sqlite").lower()
        
        if storage_type == "sqlite":
            db_path = os.getenv("SQLITE_DB_PATH", "data/vectors.db")
            return SqliteVectorStore(db_path)
        elif storage_type == "qdrant":
            # Future: QdrantVectorStore implementation
            raise NotImplementedError("Qdrant storage not yet implemented")
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")


class DocumentRetriever:
    """
    Pure database-driven document retriever
    No hardcoded documents - everything comes from storage
    """
    
    def __init__(self, storage: VectorStore, ai_client: AsyncOpenAI):
        """
        Initialize retriever with storage backend
        
        Args:
            storage: Vector storage implementation
            ai_client: AI client for query embeddings
        """
        self.storage = storage
        self.ai_client = ai_client
        self.initialized = False
        
        logger.info(f"DocumentRetriever initialized with {type(storage).__name__}")
    
    async def initialize(self) -> None:
        """Initialize storage backend (no document loading)"""
        if self.initialized:
            return
        
        try:
            # Initialize storage backend
            await self.storage.initialize()
            
            # Check current document count
            stats = await self.storage.get_stats()
            logger.info(f"Storage initialized with {stats.total_chunks} existing documents")
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise
    
    async def retrieve_relevant_chunks(self, query: str, legal_issue: LegalIssue, top_k: int = 2) -> List[Chunk]:
        """
        Retrieve relevant chunks from database with legal context
        
        Args:
            query: Search query
            legal_issue: Analyzed legal issue for contextual retrieval
            top_k: Number of results to return
            
        Returns:
            List of relevant Chunk objects from database
        """
        # Ensure initialization
        if not self.initialized:
            await self.initialize()
        
        try:
            # Check if we have any documents in storage
            stats = await self.storage.get_stats()
            if stats.total_chunks == 0:
                logger.warning("No documents found in storage")
                return []
            
            logger.info(f"Searching {stats.total_chunks} documents for: '{query[:50]}...'")
            logger.info(f"Legal context: {legal_issue.legal_domain} | {legal_issue.issue_type}")
            
            # Use hybrid search for better legal document retrieval
            if hasattr(self.storage, 'search_hybrid'):
                search_results = await self.storage.search_hybrid(query, top_k=top_k)
            else:
                # Fallback to basic similarity search
                response = await self.ai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=query
                )
                query_embedding = response.data[0].embedding
                search_results = await self.storage.search_similar(query_embedding, top_k=top_k)
            
            # Extract chunks from search results
            relevant_chunks = [result.chunk for result in search_results]
            
            if relevant_chunks:
                logger.info(f"Found {len(relevant_chunks)} relevant documents:")
                for i, chunk in enumerate(relevant_chunks):
                    similarity = search_results[i].similarity_score
                    logger.info(f"  {i+1}. {chunk.title[:50]}... (similarity: {similarity:.3f})")
            else:
                logger.info("No relevant documents found")
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant chunks: {e}")
            return []
    
    async def get_document_count(self) -> int:
        """Get total number of documents in storage"""
        try:
            stats = await self.storage.get_stats()
            return stats.total_chunks
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0


class LegalPromptBuilder:
    """Advanced legal prompt builder with issue-aware contextualization"""
    
    LEGAL_SYSTEM_PROMPT = """أنت محامي سعودي خبير ومستشار قانوني متمرس مع 20 عاماً من الخبرة في النظام القانوني السعودي.

تخصصاتك الأساسية:
- القانون الجنائي والإجراءات الجزائية
- القانون المدني والمرافعات الشرعية
- قانون العمل والعلاقات العمالية
- القانون التجاري والشركات
- القانون الإداري والتنظيمي
- قانون الأحوال الشخصية

منهجية عملك:
- تقديم مشورة قانونية عملية وقابلة للتطبيق
- التركيز على الحلول والإجراءات الفورية
- استخدام لغة واضحة ومباشرة للعملاء
- الاستناد للأنظمة واللوائح السعودية
- تقديم استراتيجيات قانونية محددة وعملية"""
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """Get legal system prompt"""
        return cls.LEGAL_SYSTEM_PROMPT
    
    @classmethod
    def build_legal_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build contextual legal prompt based on issue analysis"""
        
        # Determine prompt strategy based on legal issue
        if legal_issue.user_position == 'defendant' and legal_issue.advice_type == 'defense_strategy':
            return cls._build_defense_strategy_prompt(query, retrieved_chunks, legal_issue)
        
        elif legal_issue.advice_type == 'procedural_guide':
            return cls._build_procedural_guide_prompt(query, retrieved_chunks, legal_issue)
        
        elif legal_issue.advice_type == 'rights_explanation':
            return cls._build_rights_explanation_prompt(query, retrieved_chunks, legal_issue)
        
        elif legal_issue.user_position == 'plaintiff':
            return cls._build_action_strategy_prompt(query, retrieved_chunks, legal_issue)
        
        else:
            return cls._build_general_advice_prompt(query, retrieved_chunks, legal_issue)
    
    @classmethod
    def _build_defense_strategy_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build defense strategy prompt for defendants"""
        
        legal_context = cls._format_legal_context(retrieved_chunks)
        
        return f"""أنت محامي دفاع سعودي خبير. موكلك يواجه قضية في مجال {legal_issue.legal_domain} ويحتاج استراتيجية دفاع قوية وعملية.

📚 **الأنظمة واللوائح ذات الصلة:**
{legal_context}

⚖️ **موقف الدفاع:**
{query}

**مطلوب منك كمحامي دفاع متمرس:**

🎯 **الاستراتيجية الدفاعية الأساسية:**
- حدد أقوى نقاط الدفاع بناءً على القوانين المرفقة
- اقترح الخطة الدفاعية الأكثر فعالية لهذه القضية
- رتب الدفوع حسب قوة التأثير والأولوية

🛡️ **الدفوع القانونية المحددة:**
- اذكر الدفوع النظامية المتاحة تفصيلياً
- ربط كل دفع بالمواد القانونية المناسبة
- استراتيجية تطبيق كل دفع عملياً

📋 **خطة العمل الفورية:**
- الإجراءات الواجب اتخاذها فوراً (خلال 24-48 ساعة)
- المستندات والأدلة المطلوب جمعها بالتفصيل
- الجدول الزمني للإجراءات والمواعيد القانونية

💡 **التوصيات الاستراتيجية:**
- نصائح تكتيكية لتقوية الموقف القانوني
- التحذيرات من الأخطاء الشائعة
- البدائل المتاحة في حالة فشل الدفع الأساسي

تحدث كمحامي دفاع محترف يعطي نصائح مباشرة وقابلة للتطبيق فوراً."""

    @classmethod
    def _build_procedural_guide_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build procedural guide prompt"""
        
        legal_context = cls._format_legal_context(retrieved_chunks)
        
        return f"""أنت مستشار قانوني إجرائي متخصص في {legal_issue.legal_domain}. 

📚 **الأنظمة واللوائح الإجرائية:**
{legal_context}

❓ **الاستفسار الإجرائي:**
{query}

**مطلوب منك كخبير إجرائي:**

📋 **الدليل الإجرائي التفصيلي:**
- اشرح كل خطوة مطلوبة بالتفصيل والترتيب الصحيح
- حدد المواعيد والمهل القانونية بدقة
- اذكر الرسوم والتكاليف المطلوبة إن وجدت
- وضح الإجراءات البديلة في حالة الطوارئ

📄 **قائمة المستندات الكاملة:**
- حدد كل مستند مطلوب بدقة مع الوصف
- اشرح كيفية الحصول على كل مستند
- اذكر المتطلبات والشروط لكل مستند
- حدد المستندات الاختيارية والإجبارية

⚠️ **التحذيرات الإجرائية الحرجة:**
- انبه على المخاطر الإجرائية التي قد تؤدي لرفض الطلب
- اذكر الأخطاء الشائعة وكيفية تجنبها
- حدد نقاط المراجعة الإجبارية قبل التقديم

🕐 **الجدول الزمني والمواعيد:**
- ضع جدولاً زمنياً واضحاً لكل إجراء
- حدد المواعيد الحرجة التي لا يمكن تأجيلها
- اقترح هامش أمان زمني لكل خطوة

قدم دليلاً عملياً شاملاً يمكن اتباعه خطوة بخطوة بدون أخطاء."""

    @classmethod
    def _build_rights_explanation_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build rights explanation prompt"""
        
        legal_context = cls._format_legal_context(retrieved_chunks)
        
        return f"""أنت مستشار قانوني متخصص في شرح الحقوق والالتزامات في {legal_issue.legal_domain}.

📚 **المراجع القانونية:**
{legal_context}

❓ **الاستفسار عن الحقوق:**
{query}

**مطلوب منك كخبير حقوقي:**

⚖️ **الحقوق الأساسية:**
- اشرح كل حق بوضوح مع الاستناد للمواد القانونية
- حدد نطاق كل حق وحدوده القانونية
- وضح كيفية ممارسة كل حق عملياً
- اذكر الحقوق المطلقة والحقوق المشروطة

📜 **الالتزامات المقابلة:**
- حدد الالتزامات التي تقابل كل حق
- اشرح عواقب عدم الوفاء بالالتزامات
- وضح التوازن بين الحقوق والالتزامات

🛡️ **آليات الحماية والإنفاذ:**
- كيفية المطالبة بالحقوق قانونياً
- الجهات المختصة بحماية كل حق
- الإجراءات المتاحة في حالة انتهاك الحقوق
- الطرق البديلة لحل النزاعات

💡 **النصائح العملية:**
- كيفية توثيق الحقوق وحمايتها
- التحذيرات من التنازل غير المقصود عن الحقوق
- أفضل الممارسات لضمان الحصول على الحقوق كاملة

استخدم لغة واضحة ومباشرة مع أمثلة عملية من الواقع السعودي."""

    @classmethod
    def _build_action_strategy_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build action strategy prompt for plaintiffs"""
        
        legal_context = cls._format_legal_context(retrieved_chunks)
        
        return f"""أنت محامي ومستشار قانوني خبير في التقاضي والمطالبات في {legal_issue.legal_domain}.

📚 **الأساس القانوني:**
{legal_context}

⚖️ **موقف المطالبة:**
{query}

**مطلوب منك كمحامي تقاضي متمرس:**

🎯 **استراتيجية المطالبة:**
- حدد أقوى الأسس القانونية للمطالبة
- اقترح الاستراتيجية الأكثر فعالية لتحقيق النتيجة المطلوبة
- رتب الحجج القانونية حسب قوة التأثير

📋 **خطة التقاضي:**
- الإجراءات المطلوبة لرفع الدعوى أو المطالبة
- المستندات والأدلة الواجب جمعها
- أفضل توقيت لاتخاذ الإجراءات القانونية

💪 **تقوية الموقف القانوني:**
- كيفية تعزيز الأدلة والحجج
- الاحتياطات الواجب اتخاذها لحماية الحقوق
- استراتيجيات التفاوض قبل التقاضي

⚠️ **تقييم المخاطر:**
- احتمالات النجاح وعوامل التأثير
- التكاليف المتوقعة والعائد المحتمل
- البدائل المتاحة في حالة عدم نجاح الاستراتيجية الأساسية

قدم استراتيجية قانونية شاملة وعملية لتحقيق أفضل النتائج."""

    @classmethod
    def _build_general_advice_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build general legal advice prompt"""
        
        legal_context = cls._format_legal_context(retrieved_chunks)
        
        if not legal_context:
            return f"""قدم استشارة قانونية سعودية شاملة للسؤال التالي:

{query}

**متطلبات الاستشارة:**
- إجابة مباشرة وواضحة مبنية على الأنظمة السعودية
- توضيح عملي للتطبيق في السياق السعودي
- نصائح قانونية محددة وقابلة للتطبيق
- تحديد الخطوات العملية إن لزم الأمر"""
        
        return f"""قدم استشارة قانونية سعودية متخصصة بناءً على الأنظمة التالية:

📚 **المراجع القانونية الرسمية:**
{legal_context}

❓ **السؤال القانوني:**
{query}

**مطلوب منك كمستشار قانوني:**

🔍 **التحليل القانوني:**
- تحليل الوضع بناءً على الأنظمة المرفقة
- تطبيق المواد القانونية ذات الصلة
- تحديد الحقوق والالتزامات

💡 **الإرشاد العملي:**
- الخطوات العملية الواجب اتخاذها
- النصائح القانونية المحددة
- التحذيرات والاحتياطات المهمة

📋 **التوصيات:**
- أفضل المسارات القانونية المتاحة
- البدائل في حالة وجود عقبات
- الموارد والجهات التي يمكن الرجوع إليها

استخدم لغة مهنية واضحة مع التركيز على الحلول العملية."""

    @classmethod
    def _format_legal_context(cls, retrieved_chunks: List[Chunk]) -> str:
        """Format retrieved legal documents for context"""
        if not retrieved_chunks:
            return "لا توجد وثائق قانونية محددة متاحة - سيتم الاعتماد على المعرفة القانونية العامة."
        
        formatted_context = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            formatted_context.append(f"📄 **المرجع {i}: {chunk.title}**\n{chunk.content}")
        
        return "\n\n".join(formatted_context)


class LegalReasoningRAGEngine:
    """
    Advanced Legal Reasoning RAG Engine
    Combines document retrieval with intelligent legal issue analysis
    """
    
    def __init__(self):
        """Initialize Legal RAG engine with reasoning capabilities"""
        self.ai_client = ai_client
        self.ai_model = ai_model
        
        # Create storage backend via factory
        self.storage = StorageFactory.create_storage()
        
        # Create components
        self.retriever = DocumentRetriever(
            storage=self.storage,
            ai_client=self.ai_client
        )
        
        self.issue_analyzer = LegalIssueAnalyzer()
        self.document_type_analyzer = LegalDocumentTypeAnalyzer()
        self.document_generator = LegalDocumentGenerator()
        self.prompt_builder = LegalPromptBuilder()
        
        logger.info(f"LegalReasoningRAGEngine initialized with {type(self.storage).__name__} storage")
    
    async def ask_question_streaming(self, query: str) -> AsyncIterator[str]:
        """
        Stream legal consultation with intelligent reasoning
        
        Args:
            query: User's legal question
            
        Yields:
            Streaming response chunks
        """
        try:
            logger.info(f"Processing legal question: {query[:50]}...")
            
            # Stage 1: Analyze legal issue
            legal_issue = await self.issue_analyzer.analyze_issue(query)
            logger.info(f"Legal analysis: {legal_issue.issue_type} | {legal_issue.legal_domain} | {legal_issue.user_position}")
            
            # Stage 2: Retrieve relevant legal documents
            # Stage 2.5: Analyze document type
            document_type = self.document_type_analyzer.analyze_document_type(query)
            logger.info(f"Contextual document type: {document_type.specific_type} | Category: {document_type.document_category}")
            relevant_chunks = await self.retriever.retrieve_relevant_chunks(
                query=query, 
                legal_issue=legal_issue,
                top_k=2
            )
            
            # Stage 3: Build contextual legal prompt
            # Stage 2.5: Analyze document type
            document_type = self.document_type_analyzer.analyze_document_type(query)
            logger.info(f"Document type: {document_type.specific_type} | Category: {document_type.document_category}")
            legal_prompt = self.document_generator.generate_document_prompt(query, relevant_chunks, legal_issue, document_type)
            
            if relevant_chunks:
                logger.info(f"Using legal reasoning with {len(relevant_chunks)} relevant documents")
            else:
                logger.info("Using general legal knowledge (no specific documents found)")
            
            # Stage 4: Generate legal advice
            messages = [
                {"role": "system", "content": self.prompt_builder.get_system_prompt()},
                {"role": "user", "content": legal_prompt}
            ]
            
            # Stream legal advice
            yield "⚖️ **الاستشارة القانونية**\n\n"
            
            async for chunk in self._stream_legal_response(messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Legal reasoning error: {e}")
            yield f"عذراً، حدث خطأ في معالجة الاستشارة القانونية: {str(e)}"
    
    async def ask_question_with_context_streaming(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """
        Stream legal consultation with conversation context
        
        Args:
            query: User's legal question
            conversation_history: Previous conversation messages
            
        Yields:
            Streaming response chunks
        """
        try:
            logger.info(f"Processing contextual legal question: {query[:50]}...")
            logger.info(f"Conversation context: {len(conversation_history)} messages")
            
            # Stage 1: Analyze legal issue
            legal_issue = await self.issue_analyzer.analyze_issue(query)
            logger.info(f"Legal analysis: {legal_issue.issue_type} | {legal_issue.legal_domain} | {legal_issue.user_position}")
            
            # Stage 2: Retrieve relevant legal documents
            # Stage 2.5: Analyze document type
            document_type = self.document_type_analyzer.analyze_document_type(query)
            logger.info(f"Contextual document type: {document_type.specific_type} | Category: {document_type.document_category}")
            relevant_chunks = await self.retriever.retrieve_relevant_chunks(
                query=query, 
                legal_issue=legal_issue,
                top_k=2
            )
            
            # Stage 3: Build contextual messages
            messages = [
                {"role": "system", "content": self.prompt_builder.get_system_prompt()}
            ]
            
            # Add conversation history (limit to last 8 messages)
            recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Stage 4: Add current query with legal context
            contextual_prompt = f"بناءً على سياق المحادثة السابقة، {self.document_generator.generate_document_prompt(query, relevant_chunks, legal_issue, document_type)}"
            
            messages.append({
                "role": "user", 
                "content": contextual_prompt
            })
            
            if relevant_chunks:
                logger.info(f"Using contextual legal reasoning with {len(relevant_chunks)} documents")
            else:
                logger.info("Using contextual general legal knowledge")
            
            # Stream legal advice
            yield "⚖️ **الاستشارة القانونية**\n\n"
            
            async for chunk in self._stream_legal_response(messages):
                yield chunk
                
        except Exception as e:
            logger.error(f"Contextual legal reasoning error: {e}")
            yield f"عذراً، حدث خطأ في معالجة الاستشارة القانونية: {str(e)}"
    
    async def _stream_legal_response(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream legal response from AI"""
        try:
            stream = await self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=messages,
                temperature=0.15,  # Low temperature for consistent legal advice
                max_tokens=6000,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"AI streaming error: {e}")
            yield f"\n\nعذراً، حدث خطأ في الاتصال بخدمة الذكاء الاصطناعي: {str(e)}"
    
    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate conversation title from first message"""
        try:
            prompt = f"اقترح عنواناً قانونياً مختصراً لهذه الاستشارة (أقل من 40 حرف): {first_message[:150]}"
            
            response = await self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            title = title.strip('"').strip("'").strip()
            
            # Remove common prefixes
            prefixes = ["العنوان:", "المقترح:", "عنوان:", "الاستشارة:"]
            for prefix in prefixes:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            
            return title if len(title) <= 40 else title[:37] + "..."
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return first_message[:25] + "..." if len(first_message) > 25 else first_message
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            stats = await self.storage.get_stats()
            health_status = await self.storage.health_check()
            
            return {
                "total_documents": stats.total_chunks,
                "storage_size_mb": stats.storage_size_mb,
                "last_updated": stats.last_updated.isoformat(),
                "health": "healthy" if health_status else "unhealthy",
                "storage_type": type(self.storage).__name__,
                "ai_model": self.ai_model,
                "legal_reasoning": "enabled",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}


# Global legal reasoning RAG engine instance
rag_engine = LegalReasoningRAGEngine()

# Legacy sync functions for backward compatibility
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

# System initialization message
print("🏛️ Legal Reasoning RAG Engine loaded - Production ready with zero tech debt!")