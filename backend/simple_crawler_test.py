#!/usr/bin/env python3
"""
Simple Crawler Test - Debug the initialization issue
"""

import asyncio
import sys
import os

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_storage_initialization():
    """Test storage initialization step by step"""
    print("🔧 Testing storage initialization...")
    
    try:
        # Step 1: Import storage
        print("Step 1: Importing storage...")
        from app.storage.sqlite_store import SqliteVectorStore
        print("✅ Storage imported")
        
        # Step 2: Create vector store
        print("Step 2: Creating vector store...")
        vector_store = SqliteVectorStore("data/vectors.db")
        print("✅ Vector store created")
        
        # Step 3: Initialize
        print("Step 3: Initializing vector store...")
        await vector_store.initialize()
        print("✅ Vector store initialized")
        
        # Step 4: Health check
        print("Step 4: Running health check...")
        health = await vector_store.health_check()
        print(f"Health check result type: {type(health)}")
        print(f"Health check result: {health}")
        
        # Step 5: Import DocumentService
        print("Step 5: Importing DocumentService...")
        from app.services.document_service import DocumentService
        print("✅ DocumentService imported")
        
        # Step 6: Import OpenAI and config
        print("Step 6: Importing OpenAI and config...")
        from openai import OpenAI
        from app.core.config import settings
        print("✅ OpenAI and config imported")
        
        # Step 7: Create AI client
        print("Step 7: Creating AI client...")
        ai_client = OpenAI(api_key=settings.openai_api_key)
        print("✅ AI client created")
        
        # Step 8: Create DocumentService
        print("Step 8: Creating DocumentService...")
        document_service = DocumentService(vector_store, ai_client)
        print("✅ DocumentService created")
        
        # Step 9: Test document service
        print("Step 9: Testing document service...")
        docs = await document_service.list_documents()
        print(f"✅ Found {len(docs)} existing documents")
        
        print("\n🎉 ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR at step: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🇸🇦 Simple Crawler Storage Test")
    print("=" * 40)
    
    success = await test_storage_initialization()
    
    if success:
        print("\n✅ Ready to run full crawler!")
    else:
        print("\n❌ Fix the errors above before running crawler")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)