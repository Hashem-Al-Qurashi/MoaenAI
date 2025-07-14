"""
Upload your 25K legal memos to the system
Usage: python upload_memos.py /path/to/your/25k_file.txt
"""

import asyncio
import sys
import os

# Add current directory to Python path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from rag_engine import rag_engine

async def upload_legal_memos(file_path: str):
    """Upload legal memos to the system"""
    
    print(f"🏛️ Uploading legal memos from: {file_path}")
    print("⏳ This may take several minutes...")
    
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        # Get file size for progress indication
        file_size = os.path.getsize(file_path)
        print(f"📁 File size: {file_size / (1024*1024):.1f} MB")
        
        # Check if the method exists (if you added it to rag_engine)
        if hasattr(rag_engine, 'process_legal_memo_file'):
            result = await rag_engine.process_legal_memo_file(file_path)
            
            if result["success"]:
                print("✅ Upload successful!")
                print(f"📊 Total memos processed: {result['total_memos']}")
                print(f"📦 Total chunks created: {result['total_chunks']}")
                print("\n🏛️ Court system breakdown:")
                for court, count in result['court_system_breakdown'].items():
                    print(f"   {court}: {count} memos")
            else:
                print(f"❌ Upload failed: {result['error']}")
        else:
            print("⚠️ Memo processing method not available.")
            print("💡 Let's add it to your rag_engine.py")
            
            # Alternative: Manual processing with existing components
            from app.legal_reasoning.memo_processor import LegalMemoProcessor
            
            processor = LegalMemoProcessor(rag_engine.storage)
            
            print("📄 Extracting individual memos...")
            memos = await processor.extract_individual_memos(file_path)
            print(f"✅ Found {len(memos)} legal memos")
            
            print("🔍 Processing and chunking memos...")
            all_chunks = []
            court_counts = {}
            
            for i, memo in enumerate(memos):
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(memos)} memos")
                
                # Count by court system
                court_counts[memo.court_system] = court_counts.get(memo.court_system, 0) + 1
                
                # Chunk the memo
                chunks = processor.chunk_legal_memo(memo)
                all_chunks.extend(chunks)
                
                # Process in batches
                if len(all_chunks) >= 50:
                    await rag_engine.storage.add_chunks(all_chunks)
                    print(f"  ✅ Stored batch of {len(all_chunks)} chunks")
                    all_chunks = []
            
            # Store remaining chunks
            if all_chunks:
                await rag_engine.storage.add_chunks(all_chunks)
                print(f"  ✅ Stored final batch of {len(all_chunks)} chunks")
            
            # Get final stats
            stats = await rag_engine.get_system_stats()
            print(f"\n🎉 Processing complete!")
            print(f"📊 Total memos: {len(memos)}")
            print(f"📦 Total documents in system: {stats['total_documents']}")
            print(f"\n🏛️ Court system breakdown:")
            for court, count in court_counts.items():
                print(f"   {court}: {count} memos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("📋 Usage: python upload_memos.py <path_to_25k_file>")
        print("📋 Example: python upload_memos.py /home/user/legal_memos.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Run the upload
    asyncio.run(upload_legal_memos(file_path))