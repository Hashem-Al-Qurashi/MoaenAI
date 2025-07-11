import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from app.storage.sqlite_store import SqliteVectorStore
from app.services.document_service import DocumentService

async def test_current_document_service():
    load_dotenv()
    
    try:
        storage = SqliteVectorStore("data/vectors.db")
        await storage.initialize()
        
        ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        doc_service = DocumentService(storage, ai_client)
        
        # Test with REALISTIC large content (not repetitive)
        realistic_content = """
        الباب الأول: التعريفات والأحكام العامة
        
        المادة الأولى: يُقصد بالمصطلحات الواردة في هذا النظام المعاني المبينة أمام كل منها:
        1. النظام: نظام المرافعات الشرعية الصادر بالمرسوم الملكي رقم (م/1) وتاريخ 22/1/1435هـ.
        2. اللائحة: اللائحة التنفيذية لنظام المرافعات الشرعية.
        3. المحكمة: أي محكمة من محاكم المملكة العربية السعودية.
        
        المادة الثانية: تطبق أحكام هذه اللائحة على جميع الدعاوى والإجراءات المنصوص عليها في النظام.
        
        الباب الثاني: إجراءات التقاضي
        
        المادة الثالثة: يجب على المدعي تقديم صحيفة الدعوى مشتملة على البيانات التالية:
        1. اسم المحكمة المرفوعة إليها الدعوى.
        2. اسم المدعي ولقبه ومهنته ومحل إقامته.
        3. اسم المدعى عليه ولقبه ومهنته ومحل إقامته.
        4. تاريخ تقديم صحيفة الدعوى.
        5. وقائع الدعوى وأسانيدها.
        6. طلبات المدعي.
        """
        
        large_doc = [{
            "title": "اختبار نظام واقعي",
            "content": realistic_content,
            "metadata": {"test_type": "realistic", "source": "test"}
        }]
        
        print(f"📄 Document: {large_doc[0]['title']}")
        print(f"📏 Content length: {len(large_doc[0]['content']):,} chars")
        print(f"🔢 Estimated tokens: {len(large_doc[0]['content']) // 2:,}")
        
        result = await doc_service.add_documents_batch(large_doc)
        print(f"✅ Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_current_document_service())
