#!/usr/bin/env python3
"""
Document Loading Script
Loads initial Saudi legal documents into the database
Reads from your existing manual_chunks.py and populates database
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment
load_dotenv(project_root / ".env")

# Import our services
from app.storage.sqlite_store import SqliteVectorStore
from app.services.document_service import DocumentService

# Import your existing chunks from the correct path
try:
    # Add rag_test directory to path
    sys.path.append(str(project_root / "rag_test"))
    from manual_chunks import chunks as SAUDI_LEGAL_CHUNKS
    print(f"✅ Successfully imported {len(SAUDI_LEGAL_CHUNKS)} chunks from rag_test/manual_chunks.py")
except ImportError:
    print("❌ Could not import from rag_test/manual_chunks.py")
    print("📍 Make sure manual_chunks.py is in the backend/rag_test/ directory")
    print("📍 Current working directory:", os.getcwd())
    print("📍 Looking for file at:", project_root / "rag_test" / "manual_chunks.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error importing chunks: {e}")
    sys.exit(1)


async def initialize_storage_and_service():
    """Initialize storage and document service"""
    print("🔧 Initializing storage and services...")
    
    # Create storage (SQLite)
    storage = SqliteVectorStore("data/vectors.db")
    await storage.initialize()
    
    # Create AI client
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("❌ OPENAI_API_KEY not found in environment")
    
    ai_client = AsyncOpenAI(api_key=openai_key)
    
    # Create document service
    doc_service = DocumentService(storage, ai_client)
    
    print("✅ Storage and services initialized")
    return storage, doc_service


async def check_existing_documents(doc_service):
    """Check if documents already exist"""
    print("🔍 Checking existing documents...")
    
    health_info = await doc_service.get_storage_health()
    
    if health_info.get("total_documents", 0) > 0:
        print(f"📄 Found {health_info['total_documents']} existing documents")
        return True
    else:
        print("📄 Database is empty - ready to load documents")
        return False


async def load_documents(doc_service):
    """Load the 3 Saudi legal chunks into database"""
    print(f"📚 Loading {len(SAUDI_LEGAL_CHUNKS)} Saudi legal documents...")
    
    # Load documents in batch
    result = await doc_service.add_documents_batch(SAUDI_LEGAL_CHUNKS)
    
    if result["success"]:
        print(f"✅ Successfully loaded {result['successful']} documents")
        if result.get("errors", 0) > 0:
            print(f"⚠️ {result['errors']} documents had errors:")
            for error in result.get("error_details", []):
                print(f"   ❌ {error}")
    else:
        print(f"❌ Failed to load documents: {result['message']}")
        return False
    
    return True


async def verify_documents(doc_service):
    """Verify documents were loaded correctly"""
    print("🧪 Verifying loaded documents...")
    
    # Check each document
    for chunk in SAUDI_LEGAL_CHUNKS:
        doc = await doc_service.get_document(chunk["id"])
        if doc:
            print(f"✅ Verified: {doc['title'][:40]}...")
        else:
            print(f"❌ Missing: {chunk['id']}")
            return False
    
    # Get final statistics
    health_info = await doc_service.get_storage_health()
    print(f"📊 Final count: {health_info['total_documents']} documents in database")
    print(f"💾 Storage size: {health_info['storage_size_mb']:.2f} MB")
    
    return True


async def test_retrieval(storage):
    """Test document retrieval from database"""
    print("🧪 Testing document retrieval...")
    
    try:
        # Create AI client for query
        ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test query
        test_query = "ما هي التكاليف القضائية؟"
        print(f"🔍 Test query: {test_query}")
        
        # Generate query embedding
        response = await ai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=test_query
        )
        query_embedding = response.data[0].embedding
        
        # Search database
        search_results = await storage.search_similar(
            query_vector=query_embedding,
            top_k=2
        )
        
        if search_results:
            print(f"✅ Found {len(search_results)} relevant documents:")
            for i, result in enumerate(search_results):
                chunk = result.chunk
                similarity = result.similarity_score
                print(f"   📋 {i+1}. {chunk.title[:50]}... (similarity: {similarity:.3f})")
            return True
        else:
            print("❌ No documents found in retrieval test")
            return False
            
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")
        return False


async def main():
    """Main execution function"""
    print("🚀 Saudi Legal Document Loader")
    print("="*50)
    
    try:
        # Initialize
        storage, doc_service = await initialize_storage_and_service()
        
        # Check existing documents
        has_documents = await check_existing_documents(doc_service)
        
        if has_documents:
            print("\n🤔 Documents already exist. Options:")
            print("1. Skip loading (keep existing)")
            print("2. Clear and reload")
            
            choice = input("Enter choice (1 or 2): ").strip()
            
            if choice == "2":
                print("🗑️ Clearing existing documents...")
                cleared = await doc_service.clear_all_documents()
                if not cleared:
                    print("❌ Failed to clear documents")
                    return
                print("✅ Documents cleared")
            elif choice == "1":
                print("✅ Keeping existing documents")
                await verify_documents(doc_service)
                await test_retrieval(storage)
                return
            else:
                print("❌ Invalid choice")
                return
        
        # Load documents
        success = await load_documents(doc_service)
        if not success:
            return
        
        # Verify loading
        success = await verify_documents(doc_service)
        if not success:
            return
        
        # Test retrieval
        success = await test_retrieval(storage)
        if not success:
            return
        
        print("\n🎉 SUCCESS! Database is ready with Saudi legal documents")
        print("✅ Your RAG system can now retrieve documents from database")
        print("✅ Test your system with: 'ما هي التكاليف القضائية؟'")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())