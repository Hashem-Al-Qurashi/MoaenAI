"""
Fixed Main FastAPI application with REAL JWT authentication and CORS fix
"""
from app.api.chat import router as chat_router
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import io
import os

# Import routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router

# Initialize database tables
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
print("✅ Database tables created!")

# ✅ FIXED: CORS using environment variable with fallback
def get_cors_origins():
    """Get CORS origins from environment or use defaults"""
    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins:
        return [origin.strip() for origin in cors_origins.split(",")]
    return ["http://localhost:3000", "http://127.0.0.1:3000"]

# Create FastAPI application
app = FastAPI(
    title="Arabic Legal Assistant",
    description="""
    🇸🇦 استشارة قانونية ومالية وإدارية ذكية مبنية على القانون السعودي
    
    Professional Arabic Legal Assistant with:
    - JWT-based user authentication and management  
    - AI-powered legal consultations
    - Document export capabilities
    - Multi-domain consultation support
    """,
    version="2.0.0"
)

# ✅ FIXED: Add CORS middleware using environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),  # ✅ FIXED: Use environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug log CORS configuration
cors_origins = get_cors_origins()
print(f"🌐 CORS Origins configured: {cors_origins}")

# ✅ FIXED: Include REAL JWT authentication routers
# Include routers with proper prefixes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["User Management"])
app.include_router(chat_router, prefix="/api")

# Health check endpoint
@app.get("/")
async def root():
    """API health check with CORS debug info"""
    return {
        "status": "healthy",
        "message": "🇸🇦 Arabic Legal Assistant API",
        "version": "2.0.0",
        "auth_system": "JWT",
        "cors_origins": get_cors_origins(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

# Document export endpoint
@app.get("/export/docx")
async def export_docx(question: str = Query(...), answer: str = Query(...)):
    """Export legal response as DOCX with perfect Arabic support"""
    try:
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        import re
        
        print(f"📝 Generating DOCX export...")
        
        # Create new document
        doc = Document()
        
        # Add header
        header = doc.add_heading('الاستشارة القانونية', 0)
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add question section
        question_heading = doc.add_heading('السؤال:', level=1)
        question_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        question_para = doc.add_paragraph(question)
        question_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Add answer section
        answer_heading = doc.add_heading('الإجابة:', level=1)
        answer_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Clean HTML tags from answer
        clean_answer = re.sub('<[^<]+?>', '', answer)
        clean_answer = clean_answer.replace('&nbsp;', ' ')
        
        answer_para = doc.add_paragraph(clean_answer)
        answer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Add footer
        footer_para = doc.add_paragraph('\n\nتم إنشاء هذه الوثيقة بواسطة المساعد القانوني العربي')
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Save to BytesIO
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"legal_consultation_{timestamp}.docx"
        
        print(f"✅ DOCX export generated: {filename}")
        
        return StreamingResponse(
            io.BytesIO(file_stream.read()),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"❌ DOCX export error: {e}")
        raise HTTPException(500, f"Export failed: {str(e)}")

print("🚀 Arabic Legal Assistant API started with REAL JWT authentication and CORS fix!")