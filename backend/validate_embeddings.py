import asyncio
import numpy as np
import sqlite3
import json
from typing import List, Any

async def validate_embedding_storage():
    """Comprehensive embedding validation system"""
    
    print("🔍 EMBEDDING VALIDATION SYSTEM")
    print("=" * 50)
    
    # Check database structure
    conn = sqlite3.connect('data/vectors.db')
    cursor = conn.cursor()
    
    # Get sample embeddings
    cursor.execute('SELECT id, embedding FROM chunks LIMIT 3')
    results = cursor.fetchall()
    
    validation_results = {
        'total_chunks': 0,
        'valid_embeddings': 0,
        'invalid_embeddings': 0,
        'embedding_type': None,
        'embedding_dimensions': None,
        'issues': []
    }
    
    for chunk_id, embedding_data in results:
        validation_results['total_chunks'] += 1
        
        try:
            # Test 1: Check if it's a string
            if isinstance(embedding_data, str):
                validation_results['issues'].append(f"❌ {chunk_id}: Embedding is string, should be binary")
                validation_results['invalid_embeddings'] += 1
                
                # Try to parse as JSON array
                try:
                    parsed = json.loads(embedding_data)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        validation_results['embedding_dimensions'] = len(parsed)
                        print(f"🔧 {chunk_id}: Fixable - JSON array with {len(parsed)} dimensions")
                except:
                    validation_results['issues'].append(f"❌ {chunk_id}: Invalid JSON format")
                    
            # Test 2: Check if it's proper binary
            elif isinstance(embedding_data, (bytes, bytearray)):
                try:
                    # Try to deserialize as numpy array
                    embedding_array = np.frombuffer(embedding_data, dtype=np.float32)
                    validation_results['valid_embeddings'] += 1
                    validation_results['embedding_dimensions'] = len(embedding_array)
                    validation_results['embedding_type'] = 'binary_numpy'
                    print(f"✅ {chunk_id}: Valid binary embedding ({len(embedding_array)} dims)")
                except:
                    validation_results['issues'].append(f"❌ {chunk_id}: Invalid binary format")
                    validation_results['invalid_embeddings'] += 1
            else:
                validation_results['issues'].append(f"❌ {chunk_id}: Unknown embedding type: {type(embedding_data)}")
                validation_results['invalid_embeddings'] += 1
                
        except Exception as e:
            validation_results['issues'].append(f"❌ {chunk_id}: Validation error - {e}")
            validation_results['invalid_embeddings'] += 1
    
    conn.close()
    
    # Print validation report
    print(f"\n📊 VALIDATION REPORT:")
    print(f"   Total chunks: {validation_results['total_chunks']}")
    print(f"   ✅ Valid embeddings: {validation_results['valid_embeddings']}")
    print(f"   ❌ Invalid embeddings: {validation_results['invalid_embeddings']}")
    print(f"   📐 Embedding dimensions: {validation_results['embedding_dimensions']}")
    print(f"   🔧 Embedding type: {validation_results['embedding_type']}")
    
    if validation_results['issues']:
        print(f"\n🚨 ISSUES FOUND:")
        for issue in validation_results['issues']:
            print(f"   {issue}")
    
    # Recommendation
    if validation_results['invalid_embeddings'] > 0:
        print(f"\n💡 RECOMMENDATION:")
        print(f"   🧹 Clean database and re-embed with fixed storage")
        print(f"   💰 Cost: ~${validation_results['total_chunks'] * 0.0001:.4f}")
        return False
    else:
        print(f"\n✅ EMBEDDINGS ARE VALID!")
        return True

# Run validation
asyncio.run(validate_embedding_storage())
