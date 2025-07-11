"""
Streaming Vector Store Retriever
Clean architecture retriever that works with any storage backend
Maintains streaming capabilities while providing storage flexibility
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional, Any, AsyncIterator
from openai import AsyncOpenAI
import logging

# Import our storage interface and implementations
from app.storage.vector_store import VectorStore, Chunk, SearchResult

logger = logging.getLogger(__name__)


class VectorStoreRetriever:
    """
    Streaming-capable document retriever using storage interface
    
    This class replaces AsyncSaudiLegalRetriever with clean architecture:
    - Uses storage interface (SQLite, Qdrant, etc.)
    - Maintains streaming capabilities
    - Works with Chunk objects instead of dictionaries
    - Ready for crawler integration
    """
    
    def __init__(self, storage: VectorStore, ai_client: AsyncOpenAI):
        """
        Initialize retriever with storage backend and AI client
        
        Args:
            storage: Any VectorStore implementation (SQLite, Qdrant, etc.)
            ai_client: AsyncOpenAI client for embeddings
        """
        self.storage = storage
        self.ai_client = ai_client
        self.initialized = False
        
        logger.info(f"VectorStoreRetriever initialized with {type(storage).__name__}")
    
    async def initialize(self, enable_progress: bool = False) -> AsyncIterator[str]:
        """
        Initialize storage and load documents with optional streaming progress
        
        Args:
            enable_progress: Whether to yield progress messages
            
        Yields:
            Progress messages if enable_progress is True
        """
        if self.initialized:
            if enable_progress:
                yield "✅ النظام جاهز بالفعل\n\n"
            return
        
        try:
            if enable_progress:
                yield "🔄 جاري تحضير نظام التخزين...\n\n"
            
            # Initialize storage backend
            await self.storage.initialize()
            
            # Check if we have existing documents
            stats = await self.storage.get_stats()
            
            if stats.total_chunks == 0:
                if enable_progress:
                    yield "📚 جاري تحميل الوثائق القانونية الأساسية...\n\n"
                
                # Load initial Saudi legal documents
                await self._load_initial_documents(enable_progress)
            else:
                if enable_progress:
                    yield f"📄 تم العثور على {stats.total_chunks} وثيقة قانونية محفوظة\n\n"
            
            self.initialized = True
            
            if enable_progress:
                final_stats = await self.storage.get_stats()
                yield f"✅ النظام جاهز مع {final_stats.total_chunks} وثيقة قانونية سعودية\n\n"
            
            logger.info("VectorStoreRetriever initialized successfully")
            
        except Exception as e:
            error_msg = f"❌ خطأ في تحضير النظام: {str(e)}"
            if enable_progress:
                yield error_msg + "\n\n"
            logger.error(f"Failed to initialize retriever: {e}")
            raise
    
    async def _load_initial_documents(self, enable_progress: bool = False) -> None:
        """Load initial Saudi legal documents into storage"""
        
        # Same enhanced legal documents from your original system
        saudi_legal_documents = [
            {
                "id": "judicial_costs_definitions",
                "title": "نظام التكاليف القضائية - التعريفات والنطاق",
                "content": """المرسوم الملكي رقم م/16 تاريخ ٣٠ مُحرَّم ١٤٤٣هـ
نظام التكاليف القضائية - حالة التشريع: ساري

المادة الأولى - التعريفات:
- النظام: نظام التكاليف القضائية
- التكاليف القضائية: مبالغ مالية يلتزم المكلف بدفعها إلى الإدارة المختصة وفقاً لأحكام النظام واللائحة
- الدعوى: الدعوى المرفوعة أمام المحاكم
- الطلبات: كل ما يقدمه الخصوم وغيرهم من طلبات أمام المحاكم

المادة الثانية - نطاق التطبيق:
تسري أحكام النظام على جميع الدعاوى والطلبات التي تقدم إلى المحاكم، فيما عدا:
1. الدعاوى الجزائية العامة والدعاوى التأديبية
2. دعاوى الأحوال الشخصية (عدا النقض والتماس إعادة النظر)
3. دعاوى ديوان المظالم
4. دعاوى قسمة التركات""",
                "metadata": {
                    "source": "laws.moj.gov.sa",
                    "authority": "royal_decree",
                    "decree_number": "م/16",
                    "year": "1443",
                    "category": "judicial_costs"
                }
            },
            
            {
                "id": "judicial_costs_amounts",
                "title": "مقدار التكاليف القضائية والحد الأقصى",
                "content": """المادة الثالثة - مقدار التكاليف القضائية:
تفرض تكاليف قضائية على الدعوى بمبلغ لا يزيد على ما نسبته (5%) من قيمة المطالبة.

الحد الأعلى: مليون ريال سعودي

تحدد اللائحة التنفيذية:
- معايير تقدير التكاليف القضائية
- الضوابط والقواعد المنظمة لذلك
- طرق الحساب والاستثناءات

المادة الرابعة - إعفاءات خاصة:
يجوز للوزير إعفاء أو تخفيض التكاليف في الحالات التي تستدعي ذلك""",
                "metadata": {
                    "source": "laws.moj.gov.sa",
                    "authority": "royal_decree",
                    "decree_number": "م/16",
                    "calculation": "5%",
                    "max_amount": "1000000 ريال",
                    "category": "judicial_costs"
                }
            },
            
            {
                "id": "judicial_costs_payment_procedures",
                "title": "إجراءات دفع التكاليف القضائية",
                "content": """المادة الخامسة - توقيت الدفع:
تستحق التكاليف القضائية عند تقديم الدعوى أو الطلب، ويجوز تقسيطها وفقاً للائحة.

المادة السادسة - عدم الدفع:
إذا لم يتم دفع التكاليف المستحقة خلال المدة المحددة، تعتبر الدعوى أو الطلب كأن لم يكن.

المادة السابعة - استرداد التكاليف:
- ترد التكاليف للمدعي في حالة كسب الدعوى
- تحمل على المدعى عليه في حالة الحكم لصالح المدعي
- تحدد اللائحة حالات الاسترداد الأخرى""",
                "metadata": {
                    "source": "laws.moj.gov.sa",
                    "authority": "royal_decree",
                    "decree_number": "م/16",
                    "procedure": "payment_refund",
                    "category": "judicial_costs"
                }
            },
            
            {
                "id": "commercial_courts_jurisdiction",
                "title": "اختصاص المحاكم التجارية",
                "content": """نظام المحاكم التجارية الصادر بالمرسوم الملكي رقم م/93

اختصاص المحاكم التجارية:
1. المنازعات التجارية بين التجار
2. المنازعات المتعلقة بالأوراق التجارية
3. دعاوى الإفلاس والتصفية
4. منازعات الشركات التجارية
5. منازعات العلامات التجارية وبراءات الاختراع
6. المنازعات المصرفية والتأمين
7. منازعات الأسواق المالية""",
                "metadata": {
                    "source": "laws.moj.gov.sa",
                    "authority": "royal_decree",
                    "decree_number": "م/93",
                    "court_type": "commercial",
                    "category": "commercial_law"
                }
            },
            
            {
                "id": "company_establishment_procedures",
                "title": "إجراءات تأسيس الشركات التجارية",
                "content": """نظام الشركات السعودي - المرسوم الملكي رقم م/132

إجراءات تأسيس الشركة:

المادة الأولى - المتطلبات الأساسية:
1. تحديد نوع الشركة (مساهمة، محدودة، تضامن)
2. اختيار اسم الشركة والتأكد من عدم تعارضه
3. تحديد رأس المال وفقاً للحد الأدنى المطلوب
4. تحديد مقر الشركة الرئيسي

المادة الثانية - الوثائق المطلوبة:
- عقد التأسيس والنظام الأساسي
- كشف بأسماء المؤسسين والشركاء
- إثبات إيداع رأس المال
- ترخيص مزاولة النشاط من الجهة المختصة

المادة الثالثة - إجراءات التسجيل:
1. التسجيل في السجل التجاري
2. الحصول على الرقم الضريبي
3. التسجيل في الغرفة التجارية
4. فتح حساب مصرفي باسم الشركة""",
                "metadata": {
                    "source": "laws.moj.gov.sa",
                    "authority": "royal_decree",
                    "decree_number": "م/132",
                    "procedure_type": "company_establishment",
                    "category": "commercial_law"
                }
            }
        ]
        
        # Generate embeddings and create Chunk objects
        chunks_to_store = []
        
        for i, doc_data in enumerate(saudi_legal_documents):
            try:
                if enable_progress:
                    yield f"🔄 معالجة الوثيقة {i+1}/{len(saudi_legal_documents)}: {doc_data['title'][:30]}...\n"
                
                # Generate embedding
                response = await self.ai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=doc_data['content']
                )
                
                # Create Chunk object
                chunk = Chunk(
                    id=doc_data['id'],
                    content=doc_data['content'],
                    title=doc_data['title'],
                    embedding=response.data[0].embedding,
                    metadata=doc_data['metadata']
                )
                
                chunks_to_store.append(chunk)
                
                if enable_progress:
                    yield f"✅ تمت معالجة: {doc_data['title'][:40]}...\n"
                
            except Exception as e:
                error_msg = f"❌ خطأ في معالجة {doc_data['title']}: {str(e)}"
                if enable_progress:
                    yield error_msg + "\n"
                logger.error(f"Failed to process document {doc_data['id']}: {e}")
                continue
        
        # Store all chunks in storage
        if chunks_to_store:
            if enable_progress:
                yield f"💾 حفظ {len(chunks_to_store)} وثيقة في النظام...\n"
            
            success = await self.storage.store_chunks(chunks_to_store)
            
            if success:
                if enable_progress:
                    yield f"✅ تم حفظ جميع الوثائق بنجاح\n"
                logger.info(f"Successfully stored {len(chunks_to_store)} legal documents")
            else:
                error_msg = "❌ فشل في حفظ الوثائق"
                if enable_progress:
                    yield error_msg + "\n"
                logger.error("Failed to store documents in storage")
                raise Exception("Failed to store initial documents")
    
    async def retrieve_relevant_chunks(
        self, 
        query: str, 
        top_k: int = 2,
        enable_progress: bool = False
    ) -> List[Chunk]:
        """
        Retrieve relevant chunks with optional streaming progress
        
        Args:
            query: Search query
            top_k: Number of results to return
            enable_progress: Whether to yield progress messages
            
        Returns:
            List of relevant Chunk objects
        """
        # Ensure initialization
        if not self.initialized:
            async for _ in self.initialize(enable_progress=enable_progress):
                pass  # Consume initialization progress
        
        try:
            if enable_progress:
                logger.info(f"Searching for: '{query[:50]}...'")
            
            # Generate query embedding
            response = await self.ai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = response.data[0].embedding
            
            # Search using storage interface
            search_results = await self.storage.search_similar(
                query_vector=query_embedding,
                top_k=top_k
            )
            
            # Extract chunks from search results
            relevant_chunks = [result.chunk for result in search_results]
            
            if enable_progress and relevant_chunks:
                logger.info(f"Found {len(relevant_chunks)} relevant documents:")
                for i, chunk in enumerate(relevant_chunks):
                    similarity = search_results[i].similarity_score
                    logger.info(f"  {i+1}. {chunk.title[:50]}... (similarity: {similarity:.3f})")
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant chunks: {e}")
            return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add new documents to storage (for crawler integration)
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            chunks_to_store = []
            
            for doc_data in documents:
                # Generate embedding
                response = await self.ai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=doc_data['content']
                )
                
                # Create Chunk object
                chunk = Chunk(
                    id=doc_data['id'],
                    content=doc_data['content'],
                    title=doc_data['title'],
                    embedding=response.data[0].embedding,
                    metadata=doc_data.get('metadata', {})
                )
                
                chunks_to_store.append(chunk)
            
            # Store in storage
            success = await self.storage.store_chunks(chunks_to_store)
            
            if success:
                logger.info(f"Successfully added {len(chunks_to_store)} new documents")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = await self.storage.get_stats()
            return stats.to_dict()
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if retriever and storage are healthy"""
        try:
            return await self.storage.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False