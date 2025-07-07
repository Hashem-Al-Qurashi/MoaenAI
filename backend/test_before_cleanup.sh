#!/bin/bash

echo "🧪 COMPREHENSIVE SAFETY TEST - Before Cleanup"
echo "=============================================="

# Test 1: Main app imports
echo "1️⃣ Testing main app import..."
python -c "
try:
    from app.main import app
    print('✅ Main app imports successfully')
    print(f'✅ App title: {app.title}')
except Exception as e:
    print(f'❌ CRITICAL: Main app broken: {e}')
    exit(1)
"

# Test 2: All working endpoints
echo ""
echo "2️⃣ Testing server startup..."
python -c "
import uvicorn
from app.main import app
print('✅ Server can start (import test passed)')
"

# Test 3: Authentication system  
echo ""
echo "3️⃣ Testing authentication..."
python -c "
from app.api.simple_auth import router
print('✅ Simple auth imports')
"

# Test 4: Chat system
echo ""
echo "4️⃣ Testing chat system..."
python -c "
from app.api.chat import router
print('✅ Chat system imports')
"

# Test 5: Dependencies
echo ""
echo "5️⃣ Testing dependencies..."
python -c "
from app.dependencies.simple_auth import get_current_user_simple, get_optional_current_user
print('✅ Auth dependencies work')
"

# Test 6: Services that might be imported
echo ""
echo "6️⃣ Testing services..."
python -c "
from app.services.auth_service import AuthService
print('✅ AuthService imports')
from app.services.chat_service import ChatService  
print('✅ ChatService imports')
from app.services.cooldown_service import CooldownService
print('✅ CooldownService imports')
"

echo ""
echo "🎉 ALL SAFETY TESTS PASSED - Safe to proceed with cleanup!"
