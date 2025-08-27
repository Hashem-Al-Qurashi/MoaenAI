"""
Script to process 25K legal memo lines
Run this to import all your legal memos into the system
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.legal_reasoning.memo_processor import LegalMemoProcessor
from app.storage.sqlite_store import SqliteVectorStore

async def process_legal_memos(file_path: str):
    """Process 25K legal memo lines"""
    
    print("🏛️ Starting legal memo processing...")
    
    # Initialize storage
    storage = SqliteVectorStore("data/vectors.db")
    await storage.initialize()
    
    # Initialize processor
    processor = LegalMemoProcessor(storage)
    
    # Step 1: Extract individual memos
    print("📄 Extracting individual memos...")
    memos = await processor.extract_individual_memos(file_path)
    print(f"✅ Found {len(memos)} legal memos")
    
    # Step 2: Process each memo
    print("🔍 Processing and chunking memos...")
    all_chunks = []
    
    for i, memo in enumerate(memos):
        print(f"Processing memo {i+1}/{len(memos)} - {memo.court_system} - {memo.complexity_level}")
        
        # Chunk the memo
        chunks = processor.chunk_legal_memo(memo)
        all_chunks.extend(chunks)
        
        # Process in batches to avoid memory issues
        if len(all_chunks) >= 100:
            await storage.add_chunks(all_chunks)
            print(f"✅ Stored batch of {len(all_chunks)} chunks")
            all_chunks = []
    
    # Store remaining chunks
    if all_chunks:
        await storage.add_chunks(all_chunks)
        print(f"✅ Stored final batch of {len(all_chunks)} chunks")
    
    # Get final stats
    stats = await storage.get_stats()
    print(f"🎉 Processing complete! Total chunks: {stats.total_chunks}")
    
    return stats

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_25k_memos.py <path_to_25k_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    # Run the processing
    asyncio.run(process_legal_memos(file_path))