import asyncio
import os
from dotenv import load_dotenv  # Add this import
from openai import AsyncOpenAI
from app.storage.sqlite_store import SqliteVectorStore
from app.services.document_service import DocumentService

async def test_current_document_service():
    """Test current DocumentService with small and large documents"""
    
    print("🧪 Testing Current DocumentService")
    print("=" * 50)
    
    # Load environment variables from .env file
    load_dotenv()
    print("📁 Loaded .env file")
    
    try:
        # Initialize your real DocumentService (same as crawler uses)
        print("🔧 Initializing DocumentService...")
        storage = SqliteVectorStore("data/vectors.db")
        await storage.initialize()
        
        # Get OpenAI key from environment
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("❌ OPENAI_API_KEY not found in environment")
            print(f"🔍 Available env vars: {list(os.environ.keys())[:5]}...")
            return
        
        print(f"🔑 OpenAI key found: {openai_key[:10]}...")
        
        ai_client = AsyncOpenAI(api_key=openai_key)
        doc_service = DocumentService(storage, ai_client)
        
        print("✅ DocumentService initialized successfully")
        print()
        
        # Test 1: Small document (should work perfectly)
        print("🧪 TEST 1: Small Document (Should Work)")
        print("-" * 30)
        
        small_doc = [{
            "title": "اختبار وثيقة صغيرة",
            "content": "هذا اختبار بسيط للوثيقة الصغيرة. يحتوي على نص قصير لا يتجاوز حد الرموز المسموح به.",
            "metadata": {"test_type": "small", "source": "test"}
        }]
        
        print(f"📄 Document: {small_doc[0]['title']}")
        print(f"📏 Content length: {len(small_doc[0]['content'])} chars")
        print(f"🔢 Estimated tokens: {len(small_doc[0]['content']) // 2}")
        
        result = await doc_service.add_documents_batch(small_doc)
        print(f"✅ Result: {result}")
        print()
        
        # Test 2: Large document (should fail with token error)  
        print("🧪 TEST 2: Large Document (Should Fail)")
        print("-" * 30)
        
        # Create a realistically large document (simulate Saudi legal doc)
        large_content = """
        الباب الأول: الأحكام العامة
        """ + """
        المادة الأولى: تعريفات وأحكام عامة في القانون السعودي تشمل جميع الجوانب القانونية والإدارية والتنظيمية.
        المادة الثانية: نطاق التطبيق والاختصاص القضائي في المملكة العربية السعودية.
        """ * 2000  # Repeat to make it large
        
        large_doc = [{
            "title": "نظام اختبار كبير",
            "content": large_content,
            "metadata": {"test_type": "large", "source": "test"}
        }]
        
        print(f"📄 Document: {large_doc[0]['title']}")
        print(f"📏 Content length: {len(large_doc[0]['content']):,} chars")
        print(f"🔢 Estimated tokens: {len(large_doc[0]['content']) // 2:,}")
        
        result = await doc_service.add_documents_batch(large_doc)
        print(f"📊 Result: {result}")
        print()
        
        # Test 3: Check storage status
        print("🧪 TEST 3: Storage Health Check")
        print("-" * 30)
        
        health = await doc_service.get_storage_health()
        print(f"🏥 Storage Health: {health}")
        
        docs_list = await doc_service.list_documents()
        print(f"📋 Documents List: {docs_list}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_current_document_service())
