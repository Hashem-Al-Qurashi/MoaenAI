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
from app.legal_reasoning.memo_processor import LegalMemoProcessor
# Import legal reasoning components
from app.legal_reasoning.issue_analyzer import EnhancedLegalIssueAnalyzer, LegalIssue
from app.core.prompt_controller import MasterPromptController, get_master_controller
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

🎯 **قواعد الاستشهاد الإجبارية:**
- يجب ذكر رقم المادة والنظام المحدد لكل نقطة قانونية
- كل ادعاء قانوني يجب أن يبدأ بـ: "وفقاً للمادة (X) من [النظام المحدد]"
- ممنوع استخدام العبارات العامة: "القوانين تنص", "الأنظمة تشير", "عموماً", "عادة"
- إذا لم تجد المادة المحددة في الوثائق المرفقة، قل: "المادة غير متوفرة في الوثائق المرفقة"

🚫 **عبارات محظورة تماماً:**
- "تحددها القوانين عموماً"
- "تنص الأنظمة عادة"
- "القوانين السعودية تشير"
- "وفقاً للقوانين العامة"
- "حسب الأنظمة المعمول بها"

✅ **منهجية العمل الإجبارية:**
- تقديم مشورة قانونية عملية مع استشهاد دقيق
- التركيز على الحلول مع ذكر المصادر القانونية المحددة
- استخدام لغة واضحة مع الاستناد لأرقام المواد الصريحة
- تقديم استراتيجيات قانونية محددة مبنية على نصوص واضحة
- ربط كل نصيحة بالمادة القانونية المناسبة بالرقم والمصدر

🎯 **تنسيق الاستشهاد المطلوب:**
- "وفقاً للمادة (12) من اللوائح التنفيذية لنظام المرافعات الشرعية"
- "بناءً على المادة (8) من نظام الإثبات"
- "استناداً للمادة (94) من نظام الإجراءات الجزائية"

⚠️ **تحذير نهائي:**
أي إجابة تحتوي على عموميات أو عدم ذكر أرقام المواد المحددة تعتبر غير مقبولة قانونياً."""
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """Get legal system prompt"""
        return cls.LEGAL_SYSTEM_PROMPT
    
    @classmethod
    def add_anti_generalization_enforcement(cls, base_prompt: str) -> str:
        """Add final layer of anti-generalization enforcement to any prompt"""
        
        enforcement_layer = """

🚨 **تحذير نهائي - قواعد صارمة للاستشهاد:**

✅ **يجب عليك:**
- ذكر رقم المادة والمصدر لكل ادعاء قانوني
- استخدام تنسيق: "وفقاً للمادة (X) من [النظام المحدد]"
- الاعتماد فقط على النصوص المرفقة أعلاه

🚫 **ممنوع تماماً استخدام هذه العبارات:**
- "تحددها القوانين عموماً"
- "تنص الأنظمة عادة"
- "القوانين السعودية تشير"
- "وفقاً للقوانين العامة"
- "حسب الأنظمة المعمول بها"
- "القانون ينص"
- "الأنظمة توضح"
- "في المملكة العربية السعودية عموماً"

⚠️ **إذا لم تجد المادة المحددة:**
قل بوضوح: "المعلومة المطلوبة غير متوفرة في الوثائق القانونية المرفقة"

🎯 **تذكر:** كل كلمة في إجابتك يجب أن تكون مدعومة بمادة قانونية محددة أو تصريح واضح بعدم توفر المعلومة.

**أي مخالفة لهذه القواعد تعتبر خطأً قانونياً جسيماً.**"""

        return base_prompt + enforcement_layer


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
        """Format retrieved legal documents with article extraction and citation guidance"""
        if not retrieved_chunks:
            return """⚠️ **تحذير:** لا توجد وثائق قانونية محددة متاحة في قاعدة البيانات.
            
**يجب عليك:**
- أن تقول صراحة: "المعلومات القانونية المحددة غير متوفرة في قاعدة البيانات"
- تجنب تماماً الاستشهادات العامة أو غير المدعومة
- لا تذكر أرقام مواد إلا إذا كانت موجودة في النصوص المرفقة"""
        
        formatted_context = []
        article_numbers_found = []
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            # Extract article numbers from chunk content
            articles = cls._extract_article_numbers(chunk.content)
            if articles:
                article_numbers_found.extend(articles)
            
            # Format chunk with article highlighting
            formatted_chunk = f"""📄 **المرجع {i}: {chunk.title}**

📋 **المواد القانونية المتاحة في هذا المرجع:**
{cls._highlight_articles(chunk.content)}

💡 **إرشادات الاستشهاد:**
- استخدم فقط المواد المذكورة أعلاه من هذا المرجع
- اذكر رقم المادة + مصدرها ({chunk.title})
- لا تستنتج مواد غير موجودة في النص"""
            
            formatted_context.append(formatted_chunk)
        
        # Add citation summary
        if article_numbers_found:
            summary = f"""
🎯 **ملخص المواد القانونية المتاحة للاستشهاد:**
{', '.join(set(article_numbers_found))}

⚠️ **تعليمات صارمة:**
- استخدم فقط هذه المواد المذكورة أعلاه
- كل استشهاد يجب أن يتبع تنسيق: "وفقاً للمادة (X) من [المصدر المحدد]"
- ممنوع ذكر أي مواد أخرى غير موجودة في النصوص المرفقة
- إذا سألك المستخدم عن مادة غير موجودة، قل: "هذه المادة غير متوفرة في الوثائق المرفقة"
"""
            formatted_context.insert(0, summary)
        
        return "\n\n".join(formatted_context)

    @classmethod
    def _extract_article_numbers(cls, text: str) -> List[str]:
        """Extract article numbers from legal text"""
        import re
        
        # Patterns for Arabic article numbers
        patterns = [
            r'المادة\s*\((\d+)\)',           # المادة (12)
            r'المادة\s*(\d+)',              # المادة 12
            r'مادة\s*\((\d+)\)',            # مادة (12)
            r'مادة\s*(\d+)',               # مادة 12
            r'الفقرة\s*\((\d+)\)',          # الفقرة (3)
            r'الفقرة\s*(\d+)',             # الفقرة 3
            r'البند\s*\((\d+)\)',           # البند (5)
            r'البند\s*(\d+)',              # البند 5
        ]
        
        article_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                article_numbers.append(f"المادة ({match})")
        
        return list(set(article_numbers))  # Remove duplicates

    @classmethod  
    def _highlight_articles(cls, text: str) -> str:
        """Highlight article numbers in legal text for easy identification"""
        import re
        
        # Highlight article patterns
        patterns = [
            (r'(المادة\s*\(\d+\))', r'🎯 **\1**'),
            (r'(المادة\s*\d+)', r'🎯 **\1**'),
            (r'(مادة\s*\(\d+\))', r'🎯 **\1**'),
            (r'(مادة\s*\d+)', r'🎯 **\1**'),
        ]
        
        highlighted_text = text
        for pattern, replacement in patterns:
            highlighted_text = re.sub(pattern, replacement, highlighted_text)
        
        return highlighted_text


    @classmethod
    def build_conversation_aware_prompt(
        cls, 
        query: str, 
        retrieved_chunks: List[Chunk], 
        legal_issue: LegalIssue
    ) -> str:
        """Lean conversation-aware prompt with citation enforcement"""
        
        legal_context = cls._format_legal_context(retrieved_chunks)
        
        # Determine conversation prefix
        conversation_prefix = ""
        if hasattr(legal_issue, 'conversation_context'):
            context = legal_issue.conversation_context
            if context.conversation_flow == 'first_message':
                conversation_prefix = "استشارة جديدة - قدم تحليل شامل:"
            elif context.is_follow_up:
                conversation_prefix = "متابعة - ابدأ بـ 'كما ذكرت سابقاً':"
            elif context.is_repetition:
                conversation_prefix = "توضيح - اشرح بطريقة أبسط:"
            elif context.conversation_flow == 'continuation':
                conversation_prefix = "استكمال - أضف معلومات جديدة:"
            elif context.conversation_flow == 'topic_change':
                conversation_prefix = "موضوع جديد - ابدأ بـ 'انتقالاً إلى':"
        
        return f"""{conversation_prefix}

📚 {legal_context}

❓ {query}

🎯 **إجبارية:** كل نقطة تبدأ بـ "وفقاً للمادة (X) من [المصدر]"
🚫 **ممنوع:** عموميات، "القوانين تنص"، استشهادات غير موجودة

قدم استشارة عملية مع استشهاد دقيق."""
            

    @classmethod
    def _build_comprehensive_first_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
        """Build comprehensive first response prompt with citation enforcement"""
        legal_context = cls._format_legal_context(retrieved_chunks)

        # 'legal_issue' is required by signature for consistency, even if not used directly.
        return f"""هذا أول سؤال في استشارة قانونية جديدة. قدم استشارة شاملة مع استشهاد دقيق.

📚 **المراجع القانونية:**
{legal_context}

❓ **السؤال القانوني:**
{query}

🎯 **قواعد الاستشهاد الإجبارية:**
- كل نقطة قانونية يجب أن تبدأ بـ: "وفقاً للمادة (X) من [المصدر المحدد]"
- ممنوع استخدام: "القوانين تنص", "الأنظمة تشير", "عموماً", "عادة"
- استخدم فقط المواد المذكورة في المراجع أعلاه
- إذا لم تجد مادة محددة، قل: "المادة غير متوفرة في الوثائق المرفقة"

**مطلوب منك كمحامي سعودي خبير:**

⚖️ **التحليل القانوني الأساسي:**
- ابدأ كل نقطة بالاستشهاد المحدد: "وفقاً للمادة (X) من [المصدر]"
- اربط كل حق أو التزام بالمادة القانونية المناسبة
- اشرح التطبيق العملي مع ذكر المصدر القانوني

💡 **الإرشاد العملي مع المصادر:**
- "بموجب المادة (X): الخطوة الأولى هي..."
- "استناداً للمادة (Y): المستندات المطلوبة هي..."
- "وفقاً للمادة (Z): المهلة القانونية هي..."

🎯 **الاستراتيجية المقترحة مع الأساس القانوني:**
- "المادة (X) تتيح لك الخيارات التالية..."
- "بناءً على المادة (Y): المخاطر هي..."
- "المادة (Z) توضح البدائل المتاحة..."

⚠️ **تحذيرات قانونية محددة:**
- "المادة (X) تحذر من..."
- "وفقاً للمادة (Y): يجب تجنب..."
- "المادة (Z) تنص على عقوبة..."

🚫 **ممنوع تماماً:**
- أي عبارة عامة بدون رقم مادة محدد
- الاستشهاد بمواد غير موجودة في المراجع المرفقة
- استخدام عبارات: "حسب القانون", "الأنظمة تنص", "عموماً"

استخدم فقط المواد المحددة في المراجع أعلاه مع ذكر أرقامها ومصادرها بدقة."""


    @classmethod
    def _build_clarification_prompt(cls, query: str, retrieved_chunks: List[Chunk]) -> str:
        """Build clarification-focused prompt with citation enforcement"""

        legal_context = cls._format_legal_context(retrieved_chunks)

        return f"""المستخدم يطلب توضيحاً إضافياً. ركز على التوضيح مع استشهاد دقيق.

📚 **المراجع القانونية:**
{legal_context}

❓ **طلب التوضيح:**
{query}

🎯 **قواعد الاستشهاد الإجبارية:**
- كل توضيح يجب أن يبدأ بـ: "وفقاً للمادة (X) من [المصدر]"
- لا توضيحات عامة - فقط مبنية على المواد المحددة
- إذا لم تجد مادة محددة، قل: "التوضيح المطلوب غير متوفر في الوثائق المرفقة"

**مطلوب منك:**

🔍 **التوضيح المركز مع المصادر:**
- "المادة (X) توضح هذه النقطة كالتالي..."
- "بموجب المادة (Y): التفسير الصحيح هو..."
- "وفقاً للمادة (Z): المعنى المحدد يشمل..."

💭 **إعادة الصياغة بالاستشهاد:**
- "لتبسيط المادة (X): المقصود هو..."
- "المادة (Y) تعني عملياً..."
- "للتوضيح، المادة (Z) تنص على..."

✅ **خطوات واضحة مع المصادر:**
- "الخطوة الأولى وفقاً للمادة (X): ..."
- "الخطوة الثانية بموجب المادة (Y): ..."
- "الخطوة الثالثة استناداً للمادة (Z): ..."

🚫 **ممنوع تماماً:**
- أي توضيح بدون رقم مادة محدد
- العبارات التوضيحية العامة
- التشبيهات بدون أساس قانوني

قدم توضيحاً مختصراً مبنياً فقط على المواد المحددة في المراجع."""

@classmethod
def _build_follow_up_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
    """Build follow-up prompt with citation enforcement and reference to previous discussion"""
    
    legal_context = cls._format_legal_context(retrieved_chunks)
    
    return f"""هذا سؤال متابعة يبني على النقاش السابق. اربط إجابتك بما تم شرحه مع استشهاد دقيق.

📚 **المراجع القانونية الإضافية:**
{legal_context}

❓ **سؤال المتابعة:**
{query}

🎯 **قواعد الاستشهاد الإجبارية:**
- كل نقطة قانونية يجب أن تبدأ بـ: "وفقاً للمادة (X) من [المصدر المحدد]"
- استخدم فقط المواد المذكورة في المراجع أعلاه
- ممنوع الاستشهادات العامة أو غير المدعومة

**مطلوب منك:**

🔗 **الربط بالسابق مع المصادر:**
- "بناءً على ما ناقشناه سابقاً حول المادة (X)..."
- "كما ذكرت في النقطة السابقة وفقاً للمادة (Y)..."
- "لاستكمال ما تم شرحه عن المادة (Z)..."

➕ **المعلومات الإضافية مع الاستشهاد:**
- "وفقاً للمادة (X) الإضافية: المعلومة الجديدة هي..."
- "المادة (Y) توضح جانباً لم نتطرق إليه سابقاً..."
- "بموجب المادة (Z): التفصيل الإضافي يشمل..."

🎯 **التطبيق العملي مع المصادر:**
- "المادة (X) تطبق مع ما سبق بالطريقة التالية..."
- "استناداً للمادة (Y): الخطوات التالية هي..."
- "وفقاً للمادة (Z): التكامل يتم عبر..."

⚠️ **تجنب تماماً:**
- تكرار نفس الاستشهادات من المناقشة السابقة
- ذكر مواد جديدة بدون الإشارة إليها كإضافة
- العبارات العامة بدون مصادر محددة

حافظ على تسلسل منطقي مع استشهاد دقيق من المواد المتاحة."""

@classmethod
def _build_continuation_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
    """Build continuation prompt with citation enforcement"""
    
    legal_context = cls._format_legal_context(retrieved_chunks)
    
    return f"""هذا استكمال لنفس الموضوع القانوني. تابع النقاش مع استشهاد دقيق.

📚 **المراجع القانونية ذات الصلة:**
{legal_context}

❓ **استكمال الموضوع:**
{query}

🎯 **قواعد الاستشهاد الإجبارية:**
- كل معلومة جديدة يجب أن تبدأ بـ: "وفقاً للمادة (X) من [المصدر]"
- استخدم فقط المواد المذكورة في المراجع أعلاه
- لا تكرر الاستشهادات السابقة إلا للضرورة

**مطلوب منك:**

📈 **البناء على المناقشة مع مصادر جديدة:**
- "للتعمق أكثر، المادة (X) تنص على..."
- "من جانب آخر، المادة (Y) توضح..."
- "للإضافة على ما سبق، المادة (Z) تشير إلى..."

🔍 **التعمق في التفاصيل مع الاستشهاد:**
- "المادة (X) تحدد الحالات الخاصة التالية..."
- "وفقاً للمادة (Y): الاستثناءات تشمل..."
- "المادة (Z) توضح التطبيقات المختلفة..."

💼 **الجانب العملي مع المصادر:**
- "المادة (X) تطبق عملياً في هذه الحالات..."
- "بموجب المادة (Y): الممارسة القانونية تتطلب..."
- "استناداً للمادة (Z): النصائح المتقدمة تشمل..."

🚫 **ممنوع:**
- إعادة شرح المواد التي تم تناولها مسبقاً
- الاستشهاد بمواد غير موجودة في المراجع
- العموميات بدون مصادر محددة

قدم معلومات جديدة مع استشهاد دقيق من المواد المتاحة."""

@classmethod
def _build_topic_change_prompt(cls, query: str, retrieved_chunks: List[Chunk], legal_issue: LegalIssue) -> str:
    """Build prompt for topic change with fresh citation enforcement"""
    
    legal_context = cls._format_legal_context(retrieved_chunks)
    
    return f"""انتقل المستخدم لموضوع قانوني جديد. ابدأ تحليلاً جديداً مع استشهاد دقيق.

📚 **المراجع القانونية للموضوع الجديد:**
{legal_context}

❓ **الموضوع الجديد:**
{query}

🎯 **قواعد الاستشهاد للموضوع الجديد:**
- كل نقطة يجب أن تبدأ بـ: "وفقاً للمادة (X) من [المصدر]"
- تعامل مع هذا كاستشارة قانونية جديدة تماماً
- استخدم فقط المراجع المرفقة للموضوع الجديد

**مطلوب منك:**

🔄 **الاعتراف بالتغيير:**
- "انتقالاً إلى موضوع قانوني جديد..."
- "بخصوص استفسارك الجديد حول..."
- "في هذا الموضوع المختلف..."

⚖️ **التحليل الجديد مع الاستشهاد:**
- "المادة (X) تحكم هذا الموضوع الجديد..."
- "وفقاً للمادة (Y): الإطار القانوني يشمل..."
- "بموجب المادة (Z): الأحكام ذات الصلة هي..."

🎯 **التركيز على الجديد مع المصادر:**
- "المادة (X) تنص على القواعد الأساسية..."
- "استناداً للمادة (Y): المتطلبات تشمل..."
- "وفقاً للمادة (Z): الإجراءات المطلوبة هي..."

🚫 **ممنوع:**
- الربط بالمواضيع السابقة بدون مبرر قانوني
- الاستشهادات العامة أو المختلطة
- نقل المعلومات من مواضيع أخرى

تعامل مع هذا كاستشارة جديدة مع استشهاد دقيق من المراجع المتاحة."""





"""
Updated RAG Engine Integration - Minimal changes to pass AI client
Only change: Pass AI client to MasterPromptController
"""


    
class LegalReasoningRAGEngine:
    """
    Advanced Legal Reasoning RAG Engine - Enhanced with Dynamic AI Analysis
    
    Minimal changes: Now passes AI client to MasterPromptController for dynamic conversation analysis
    """
    
    def __init__(self):
        """Initialize Legal RAG engine with dynamic AI conversation analysis"""
        self.ai_client = ai_client
        self.ai_model = ai_model
        
        # Create storage backend via factory
        self.storage = StorageFactory.create_storage()
        
        # Create components
        self.retriever = DocumentRetriever(
            storage=self.storage,
            ai_client=self.ai_client
        )
        
        self.issue_analyzer = EnhancedLegalIssueAnalyzer()
        self.document_type_analyzer = LegalDocumentTypeAnalyzer()
        self.document_generator = LegalDocumentGenerator()
        
        # 🚀 ENHANCED: Pass AI client to MasterPromptController for dynamic analysis
        self.master_controller = get_master_controller(ai_client=self.ai_client)
        
        self.prompt_builder = LegalPromptBuilder()
        
        logger.info(f"LegalReasoningRAGEngine initialized with dynamic AI conversation analysis")

    # ✅ ADD THIS METHOD INSIDE THE CLASS - PROPERLY INDENTED
    async def _stream_legal_response(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream legal response from AI with rate limit handling"""
        import asyncio

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
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

                return  # Success - exit retry loop

            except Exception as e:
                error_str = str(e).lower()
                logger.error(f"AI streaming error (attempt {attempt + 1}): {e}")

                # Check if it's a rate limiting error
                if any(indicator in error_str for indicator in ["429", "rate limit", "too many requests", "quota"]):
                    if attempt < max_retries - 1:
                        retry_delay = base_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                        logger.warning(f"🔄 Rate limit detected. Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")

                        # Yield a waiting message to user
                        yield f"\n\n⏳ **انتظار:** تم تجاوز الحد المسموح مؤقتاً. جاري إعادة المحاولة خلال {retry_delay} ثانية...\n\n"

                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # Final attempt failed
                        logger.error(f"❌ Rate limit exceeded after {max_retries} attempts")
                        yield f"""

🚨 **خطأ في الاتصال بخدمة الذكاء الاصطناعي**

**السبب:** تجاوز الحد المسموح من الطلبات (Rate Limit)

**الحلول المقترحة:**
1. **انتظر دقيقة واحدة** ثم أعد المحاولة
2. **تحقق من رصيد OpenAI** في حسابك
3. **تواصل مع الدعم الفني** إذا استمر الخطأ

**رمز الخطأ:** HTTP 429 - Too Many Requests"""
                        return

                # Different error type (not rate limiting)
                elif any(indicator in error_str for indicator in ["authentication", "api key", "unauthorized"]):
                    logger.error("❌ Authentication error - API key issue")
                    yield f"""

🔑 **خطأ في المصادقة**

**السبب:** مشكلة في مفتاح API أو انتهاء صلاحيته

**الحلول:**
1. تحقق من صحة مفتاح OpenAI API
2. تأكد من وجود رصيد كافي في الحساب
3. تواصل مع المطور لتحديث المفاتيح

**رمز الخطأ:** {str(e)}"""
                    return

                else:
                    # Generic error - retry once
                    if attempt < max_retries - 1:
                        logger.warning(f"🔄 Generic error, retrying... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(base_delay)
                        continue
                    else:
                        logger.error(f"❌ Final attempt failed with generic error")
                        yield f"\n\n❌ **خطأ تقني:** {str(e)}\n\nيرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني."
                        return
    
    async def _add_request_delay(self):
        """Add small delay between requests to prevent rate limiting"""
        import asyncio
        await asyncio.sleep(0.5)

    # ... rest of your existing methods (ask_question_streaming, ask_question_with_context_streaming, etc.)
    async def ask_question_streaming(self, query: str) -> AsyncIterator[str]:
        """
        Stream legal consultation with dynamic AI conversation analysis
        
        NO CHANGES to this method - it automatically uses the enhanced system!
        """
        try:
            logger.info(f"Processing legal question: {query[:50]}...")
            
            # Stage 1: Analyze legal issue
            legal_issue = await self.issue_analyzer.analyze_issue_with_context(query, [])
            logger.info(f"Legal analysis: {legal_issue.issue_type} | {legal_issue.legal_domain} | {legal_issue.user_position}")
            
            # Stage 2: Retrieve relevant legal documents
            document_type = self.document_type_analyzer.analyze_document_type(query)
            logger.info(f"Contextual document type: {document_type.specific_type} | Category: {document_type.document_category}")
            relevant_chunks = await self.retriever.retrieve_relevant_chunks(
                query=query, 
                legal_issue=legal_issue,
                top_k=2
            )
            
            # 🎯 Stage 3: Use Enhanced Master Controller with dynamic AI analysis
            legal_prompt = self.master_controller.generate_prompt_for_query(
                query=query,
                retrieved_documents=relevant_chunks,
                conversation_history=[]
            )
            logger.info("✅ Using enhanced Master Controller with dynamic AI conversation analysis")
            
            if relevant_chunks:
                logger.info(f"Using legal reasoning with {len(relevant_chunks)} relevant documents")
            else:
                logger.info("Using general legal knowledge (no specific documents found)")
            await self._add_request_delay()
            
            # Stage 4: Generate legal advice with enhanced system
            messages = [
                {"role": "system", "content": "أنت مستشار قانوني سعودي متخصص."},
                {"role": "user", "content": legal_prompt}
            ]
            
            # Stream legal advice
            yield "⚖️ **الاستشارة القانونية**\n\n"
            
            async for chunk in await self._stream_legal_response(messages):
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
        Stream legal consultation with dynamic conversation context analysis
        
        🚀 ENHANCED: Now uses dynamic AI conversation analysis instead of hardcoded patterns!
        """
        try:
            logger.info(f"Processing contextual legal question: {query[:50]}...")
            logger.info(f"Conversation context: {len(conversation_history)} messages")
            
            # Stage 1: Analyze legal issue with conversation context
            legal_issue = await self.issue_analyzer.analyze_issue_with_context(query, conversation_history)
            logger.info(f"Legal analysis: {legal_issue.issue_type} | {legal_issue.legal_domain} | {legal_issue.user_position}")
            
            # Stage 2: Retrieve relevant legal documents
            document_type = self.document_type_analyzer.analyze_document_type(query)
            logger.info(f"Contextual document type: {document_type.specific_type} | Category: {document_type.document_category}")
            relevant_chunks = await self.retriever.retrieve_relevant_chunks(
                query=query, 
                legal_issue=legal_issue,
                top_k=2
            )
            
            # Stage 3: Build contextual messages
            messages = [
                {"role": "system", "content": "أنت مستشار قانوني سعودي متخصص."}
            ]
            
            # Add conversation history (limit to last 8 messages)
            recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # 🎯 Stage 4: Use Enhanced Master Controller with dynamic conversation analysis
            contextual_prompt = await self.master_controller.generate_prompt_for_query(
                query=query,
                retrieved_documents=relevant_chunks,
                conversation_history=recent_history
            )
            logger.info("✅ Using enhanced Master Controller with dynamic conversation context analysis")
            
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

    # All other methods stay exactly the same...
    async def _add_request_delay(self):
        """Add small delay between requests to prevent rate limiting - NO CHANGES"""
        import asyncio
        await asyncio.sleep(0.5)
    


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

# Add this method to your LegalReasoningRAGEngine class (around line 200)

async def process_legal_memo_file(self, file_path: str) -> Dict[str, Any]:
   """Process 25K legal memo file and add to storage"""
   
   try:
       processor = LegalMemoProcessor(self.storage)
       
       # Extract individual memos
       memos = await processor.extract_individual_memos(file_path)
       logger.info(f"Extracted {len(memos)} legal memos from file")
       
       # Process each memo
       all_chunks = []
       court_system_counts = {}
       
       for memo in memos:
           # Count by court system
           court_system_counts[memo.court_system] = court_system_counts.get(memo.court_system, 0) + 1
           
           # Chunk the memo
           chunks = processor.chunk_legal_memo(memo)
           all_chunks.extend(chunks)
           
           # Process in batches to avoid memory issues
           if len(all_chunks) >= 50:
               await self.storage.add_chunks(all_chunks)
               logger.info(f"Stored batch of {len(all_chunks)} chunks")
               all_chunks = []
       
       # Store remaining chunks
       if all_chunks:
           await self.storage.add_chunks(all_chunks)
           logger.info(f"Stored final batch of {len(all_chunks)} chunks")
       
       # Get final stats
       stats = await self.storage.get_stats()
       
       return {
           "success": True,
           "total_memos": len(memos),
           "total_chunks": stats.total_chunks,
           "court_system_breakdown": court_system_counts,
           "message": f"Successfully processed {len(memos)} legal memos into {stats.total_chunks} chunks"
       }
       
   except Exception as e:
       logger.error(f"Error processing legal memo file: {e}")
       return {
           "success": False,
           "error": str(e),
           "message": f"Failed to process legal memo file: {str(e)}"
       }

# System initialization message
print("🏛️ Legal Reasoning RAG Engine loaded - Production ready with zero tech debt!")
rag_engine = LegalReasoningRAGEngine()