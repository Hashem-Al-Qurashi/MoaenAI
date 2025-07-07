#!/bin/bash

echo "🌐 ENDPOINT VERIFICATION TEST"
echo "============================"

# Start server in background for testing
echo "Starting test server..."
uvicorn app.main:app --host 127.0.0.1 --port 8001 &
SERVER_PID=$!
sleep 3

echo "Testing endpoints..."

# Test 1: Root endpoint
echo "1️⃣ Testing root endpoint..."
curl -s http://127.0.0.1:8001/ > /dev/null && echo "✅ Root endpoint works" || echo "❌ Root endpoint broken"

# Test 2: Auth endpoints  
echo "2️⃣ Testing auth endpoints..."
curl -s http://127.0.0.1:8001/api/auth/register > /dev/null && echo "✅ Auth register endpoint exists" || echo "❌ Auth register broken"

# Test 3: Guest endpoint
echo "3️⃣ Testing guest endpoint..."
curl -s http://127.0.0.1:8001/api/ask > /dev/null && echo "✅ Guest ask endpoint exists" || echo "❌ Guest ask broken"

# Test 4: Chat endpoints
echo "4️⃣ Testing chat endpoints..."
curl -s http://127.0.0.1:8001/api/chat/status > /dev/null && echo "✅ Chat status endpoint exists" || echo "❌ Chat status broken"

# Test 5: Check endpoints that should NOT exist
echo "5️⃣ Testing endpoints that should NOT exist..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/api/users/me)
if [ "$RESPONSE" = "404" ]; then
    echo "✅ /api/users/me correctly returns 404 (not used)"
else
    echo "❌ /api/users/me unexpectedly works (might be used)"
fi

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/api/consultations/ask)
if [ "$RESPONSE" = "404" ]; then
    echo "✅ /api/consultations/ask correctly returns 404 (not used)"
else
    echo "❌ /api/consultations/ask unexpectedly works (might be used)"
fi

# Cleanup
kill $SERVER_PID 2>/dev/null
echo ""
echo "🎉 Endpoint verification complete!"
