# backend/app/main.py - Clean Architecture, No Legacy

"""
Ultimate Arabic Legal Assistant - Unified Chat System
Single chat API for all users (guests + authenticated)
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from app.models import User, Consultation, Conversation, Message
# Import routers
from app.api.simple_auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.export import router as export_router

# Initialize database tables
from app.database import engine, Base
from app.core.config import settings
Base.metadata.create_all(bind=engine)
print("✅ Database tables created!")



# Create FastAPI application
app = FastAPI(
    title="Arabic Legal AI Assistant 🇸🇦",
    description="""
    🇸🇦 استشارة قانونية ومالية وإدارية ذكية مبنية على القانون السعودي
    
    Unified Arabic Legal Assistant with:
    - JWT-based user authentication and management
    - Guest access with session-based conversation memory
    - AI-powered legal consultations with full context awareness
    - Persistent conversations for authenticated users
    - Document export capabilities with perfect Arabic support
    """,
    version="3.0.0"
)

# Add CORS middleware
# In your main.py, make sure you have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"🌐 CORS Origins configured: {settings.allowed_origins}")

# Global OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle CORS preflight requests for all routes"""
    return JSONResponse(
        content={"detail": "OK"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# 🔥 Include routers - ONLY MODERN APIS
app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")
app.include_router(export_router, prefix="/export")

# 🔥 LEGACY API REDIRECT - Graceful transition
@app.post("/api/ask")
async def legacy_api_redirect():
    """
    🚨 DEPRECATED: This endpoint has been replaced by the unified chat API
    All users should now use /api/chat/message for the best experience
    """
    raise HTTPException(
        status_code=410,  # Gone
        detail={
            "error": "Legacy API deprecated",
            "message": "This endpoint has been replaced by the unified chat system",
            "new_endpoint": "/api/chat/message",
            "migration_guide": {
                "old": "POST /api/ask with form data",
                "new": "POST /api/chat/message with form data",
                "benefits": [
                    "Conversation memory for all users",
                    "Better context awareness",
                    "Session-based memory for guests",
                    "Unified experience"
                ]
            }
        }
    )

@app.get("/")
async def root():
    """API root with system information"""
    return {
        "service": "Arabic Legal Assistant - Unified Edition",
        "version": "3.0.0",
        "status": "active",
        "features": {
            "unified_chat": "Single chat API for guests and authenticated users",
            "conversation_memory": "Context-aware responses for all users",
            "guest_sessions": "Session-based memory for guests",
            "persistent_storage": "Database conversations for authenticated users",
            "jwt_auth": "Secure authentication system",
            "arabic_support": "Native Arabic language support",
            "export": "Enhanced DOCX export with Arabic support"
        },
        "endpoints": {
            "auth": "/api/auth/*",
            "chat": "/api/chat/*",
            "export": "/export/*",
            "status": "/api/chat/status",
            "guest_session": "/api/chat/guest/session"
        },
        "architecture": {
            "type": "Unified Chat System",
            "legacy_apis": "Deprecated and removed",
            "tech_debt": "Zero - Single codebase",
            "memory_system": "Context-aware for all user types"
        },
        "cors_origins": settings.allowed_origins,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "Arabic Legal Assistant - Unified Edition",
        "version": "3.0.0",
        "features": [
            "unified_chat", 
            "guest_sessions", 
            "conversation_memory", 
            "jwt_auth", 
            "arabic_support",
            "docx_export"
        ]
    }

# 🚨 Remove all legacy imports and endpoints
# - No more simple_consultations router
# - No more dual API system
# - Single source of truth: chat API

print("🚀 Arabic Legal Assistant Unified Edition started!")
print("✅ Features: Unified Chat + Guest Sessions + Context Memory + Zero Tech Debt")
print(f"🌐 CORS configured for: {settings.allowed_origins}")
print("🔥 Legacy APIs removed - Single chat system for all users!")
print("📊 Architecture: Zero tech debt, maximum maintainability")