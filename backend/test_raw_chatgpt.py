"""
Test script to verify raw ChatGPT responses
"""
import requests
import json

def test_direct_chatgpt():
    """Test the direct ChatGPT endpoint"""
    
    # Backend URL
    url = "http://localhost:8000/api/direct-chatgpt"
    
    # Test message - same as the one you provided
    test_message = "كيفية تأسيس شركة استثمار أجنبي؟"
    
    payload = {
        "message": test_message,
        "history": []  # Empty history for fresh conversation
    }
    
    print("🚀 Testing Direct ChatGPT Endpoint")
    print(f"📝 Question: {test_message}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Raw ChatGPT Response:")
            print("-" * 50)
            print(result["response"])
            print("-" * 50)
            print(f"Model: {result.get('model', 'unknown')}")
            print(f"Pure ChatGPT: {result.get('pure_chatgpt', False)}")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the backend server is running on port 8000")

def test_regular_chat():
    """Test the regular chat endpoint for comparison"""
    
    url = "http://localhost:8000/api/chat/message"
    
    test_message = "كيفية تأسيس شركة استثمار أجنبي؟"
    
    # Form data for regular chat
    data = {
        "message": test_message,
        "session_id": "test_session_123"
    }
    
    headers = {
        "Accept": "application/json"
    }
    
    print("\n" + "=" * 50)
    print("📊 Testing Regular Chat Endpoint (for comparison)")
    print(f"📝 Question: {test_message}")
    print("-" * 50)
    
    try:
        response = requests.post(url, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            ai_message = result.get("ai_message", {})
            print("Regular Chat Response:")
            print("-" * 50)
            print(ai_message.get("content", "No content"))
            print("-" * 50)
            print(f"Processing mode: {result.get('processing_mode', 'unknown')}")
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    # Test direct ChatGPT first
    test_direct_chatgpt()
    
    # Then test regular chat for comparison
    test_regular_chat()