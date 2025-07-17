"""
Export Router - Document generation and download
Handles all export functionality with proper Arabic support
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
import io
import re
from typing import Optional

# Import dependencies for potential authentication
from app.dependencies.auth import get_current_user_optional
from app.models.user import User

router = APIRouter(tags=["Export"])

def create_enhanced_docx_stream(question: str, answer: str, user: Optional[User] = None) -> io.BytesIO:
    """
    Create enhanced DOCX with perfect Arabic support
    Includes user attribution if authenticated
    """
    buffer = io.BytesIO()
    
    try:
        from docx import Document
        from docx.shared import Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # Create Word document
        doc = Document()
        
        # Clean HTML tags from content
        clean_question = re.sub('<[^<]+?>', '', question)
        clean_answer = re.sub('<[^<]+?>', '', answer)
        clean_answer = clean_answer.replace('&nbsp;', ' ')
        
        # Document title
        title = doc.add_heading('المساعد القانوني الذكي 🇸🇦', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Subtitle
        subtitle = doc.add_paragraph('استشارة قانونية ذكية مبنية على القانون السعودي')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add user attribution if authenticated
        if user:
            user_info = doc.add_paragraph(f'المستخدم: {user.full_name}')
            user_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in user_info.runs:
                run.font.size = Pt(10)
                run.italic = True
        
        # Add separator line
        doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()
        
        # Question section
        question_heading = doc.add_heading('📋 السؤال:', level=1)
        question_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        question_para = doc.add_paragraph(clean_question)
        question_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for run in question_para.runs:
            run.font.size = Pt(12)
        
        doc.add_paragraph()
        
        # Answer section
        answer_heading = doc.add_heading('✅ الإجابة:', level=1)
        answer_heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        answer_para = doc.add_paragraph(clean_answer)
        answer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for run in answer_para.runs:
            run.font.size = Pt(11)
        
        # Footer
        doc.add_paragraph()
        doc.add_paragraph()
        
        footer_line = doc.add_paragraph('─' * 50)
        footer_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        timestamp_text = f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d الساعة %H:%M')}"
        footer_para = doc.add_paragraph(timestamp_text)
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add disclaimer
        disclaimer = doc.add_paragraph()
        disclaimer_run = disclaimer.add_run(
            'تنبيه: هذه الاستشارة القانونية مبنية على الذكاء الاصطناعي وتهدف للإرشاد العام. '
            'للحصول على استشارة قانونية دقيقة، يُنصح بالتواصل مع محامٍ مختص.'
        )
        disclaimer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        disclaimer_run.font.size = Pt(9)
        disclaimer_run.italic = True
        
        # Save to buffer
        doc.save(buffer)
        
    except Exception as e:
        print(f"DOCX creation error: {e}")
        # Create simple fallback document
        from docx import Document
        doc = Document()
        doc.add_heading('خطأ في إنشاء المستند', 0)
        doc.add_paragraph('حدث خطأ أثناء إنشاء المستند. يرجى المحاولة مرة أخرى.')
        doc.add_paragraph(f'تفاصيل الخطأ: {str(e)}')
        doc.save(buffer)
    
    buffer.seek(0)
    return buffer

@router.get("/docx")
async def export_docx(
    question: str = Query(..., description="The legal question asked"),
    answer: str = Query(..., description="The AI assistant's response"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Export legal consultation as DOCX with perfect Arabic support
    Works for both authenticated users and guests
    """
    try:
        print(f"📝 Generating DOCX export...")
        print(f"📝 User: {current_user.full_name if current_user else 'Guest'}")
        print(f"📝 Question length: {len(question)} chars")
        print(f"📝 Answer length: {len(answer)} chars")
        
        # Create enhanced DOCX
        docx_buffer = create_enhanced_docx_stream(question, answer, current_user)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_prefix = f"{current_user.full_name.replace(' ', '_')}_" if current_user else "guest_"
        filename = f"{user_prefix}legal_consultation_{timestamp}.docx"
        
        print(f"✅ DOCX export generated: {filename}")
        
        return StreamingResponse(
            io.BytesIO(docx_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        print(f"❌ DOCX export error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"خطأ في إنشاء ملف Word: {str(e)}"
        )

@router.get("/conversation/docx")
async def export_conversation_docx(
    conversation_id: str = Query(..., description="The conversation ID to export"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Export entire conversation as DOCX
    Future enhancement for full conversation export
    """
    # TODO: Implement conversation export
    # This is a placeholder for future enhancement
    raise HTTPException(
        status_code=501,
        detail="تصدير المحادثة الكاملة غير متوفر حالياً"
    )