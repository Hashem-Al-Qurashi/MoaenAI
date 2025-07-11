import json
import numpy as np

# Fix for lines 100-101 (storage)
def fix_embedding_storage():
    return '''
                    # Serialize embedding as binary (proper BLOB storage)
                    embedding_blob = chunk.embedding.tobytes() if chunk.embedding is not None else None
'''

# Fix for lines 165-169 (loading)  
def fix_embedding_loading():
    return '''
                        # Parse embedding from binary
                        chunk_embedding = None
                        if embedding_json:
                            try:
                                # Handle both old JSON format and new binary format
                                if isinstance(embedding_json, str):
                                    # Old JSON format - convert
                                    chunk_embedding = json.loads(embedding_json)
                                else:
                                    # New binary format - deserialize
                                    chunk_embedding = np.frombuffer(embedding_json, dtype=np.float32).tolist()
                            except:
                                # Fallback to JSON parsing
                                chunk_embedding = json.loads(embedding_json) if isinstance(embedding_json, str) else None
                        
                        if not chunk_embedding:
                            continue
'''

print("🔧 Fixes ready to apply...")
