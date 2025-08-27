# Find and replace the chunk loading section (around lines 166-176)

# New clean loading logic:
new_logic = '''
                        # Parse embedding (handle both JSON and binary)
                        chunk_embedding = None
                        if embedding_blob:
                            if isinstance(embedding_blob, str):
                                # Old JSON format
                                chunk_embedding = json.loads(embedding_blob)
                            else:
                                # New binary format
                                chunk_embedding = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
                        
                        if not chunk_embedding or len(chunk_embedding) != 1536:
                            continue
'''

print("Ready to apply fix...")
