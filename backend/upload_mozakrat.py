"""
Upload mozakrat.txt to the system
"""

import asyncio
import os
import sys

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from rag_engine import rag_engine
from app.legal_reasoning.memo_processor import LegalMemoProcessor

async def upload_mozakrat():
    """Upload mozakrat.txt file"""
    
    file_path = "/home/sakr_quraish/Documents/myNewWebsite/ocr/mozakrat.txt"
    
    print(f"🏛️ Processing: {file_path}")
    print(f"📁 Size: 1.8MB")
    
    try:
        processor = LegalMemoProcessor(rag_engine.storage)
        
        print("📄 Reading and extracting memos...")
        memos = await processor.extract_individual_memos(file_path)
        print(f"✅ Found {len(memos)} legal memos")
        
        # Process in batches
        print("🔍 Processing memos...")
        all_chunks = []
        
        for i, memo in enumerate(memos):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(memos)}")
            
            chunks = processor.chunk_legal_memo(memo)
            all_chunks.extend(chunks)
            
            # Store every 50 chunks
            if len(all_chunks) >= 50:
                await rag_engine.storage.store_chunks(all_chunks)
                print(f"  ✅ Stored {len(all_chunks)} chunks")
                all_chunks = []
        
        # Store remaining
        if all_chunks:
            await rag_engine.storage.store_chunks(all_chunks)
            print(f"  ✅ Final batch: {len(all_chunks)} chunks")
        
        # Final stats
        stats = await rag_engine.get_system_stats()
        print(f"\n🎉 Complete!")
        print(f"📊 Total documents: {stats['total_documents']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(upload_mozakrat())