"""
AI Style Classifier for Legal Documents
Uses GPT to intelligently classify writing styles - no hard coding
"""

import json
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIStyleClassifier:
    """AI-powered style classifier for legal documents"""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
        
    async def classify_document_style(self, content: str, title: str = "") -> Dict[str, any]:
        """
        Classify the writing style of a legal document using AI
        
        Args:
            content: Document content
            title: Document title (optional context)
            
        Returns:
            Dict with style, confidence, and characteristics
        """
        try:
            # Smart prompt - let AI understand styles naturally
            classification_prompt = f"""أنت خبير في تحليل أساليب الكتابة القانونية السعودية.

حلل أسلوب الكتابة في هذا المستند القانوني:

العنوان: {title}
المحتوى: {content[:1500]}

صنف الأسلوب إلى واحد من هذه الفئات:

📋 MEMO_AGGRESSIVE: مذكرات دفاع هجومية
- حجج مفصلة ومرقمة
- تفنيد ادعاءات الخصم نقطة بنقطة
- لهجة قوية وتحليل عميق
- استراتيجيات قانونية متقدمة

📋 MEMO_DEFENSIVE: مذكرات دفاع دفاعية
- دفوع منظمة وواضحة
- تركيز على الإجراءات والقوانين
- أسلوب محافظ ومتزن

📋 COURT_FORMAL: وثائق المحكمة الرسمية
- لغة رسمية وإجرائية
- معلومات قصيرة ومحددة
- تركيز على الحقائق

📋 LEGAL_ANALYSIS: تحليل قانوني أكاديمي
- شرح نظري للقوانين
- مناقشة أكاديمية
- استشهادات قانونية متعمقة

📋 GENERAL_LEGAL: محتوى قانوني عام
- معلومات قانونية بسيطة
- إرشادات عامة

أجب بصيغة JSON فقط:
{{
    "style": "MEMO_AGGRESSIVE",
    "confidence": 0.95,
    "characteristics": ["detailed_arguments", "numbered_points", "aggressive_tone"],
    "reasoning": "المستند يحتوي على حجج مفصلة ولهجة هجومية"
}}"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            classification = json.loads(result_text)
            
            # Validate and ensure we have a valid style
            valid_styles = ["MEMO_AGGRESSIVE", "MEMO_DEFENSIVE", "COURT_FORMAL", "LEGAL_ANALYSIS", "GENERAL_LEGAL"]
            if classification.get("style") not in valid_styles:
                classification["style"] = "GENERAL_LEGAL"
                classification["confidence"] = 0.5
            
            logger.info(f"Style classified as {classification['style']} (confidence: {classification['confidence']:.2f})")
            return classification
            
        except Exception as e:
            logger.error(f"Style classification error: {e}")
            return {
                "style": "GENERAL_LEGAL",
                "confidence": 0.3,
                "characteristics": [],
                "reasoning": f"Classification failed: {str(e)}"
            }
    
    async def filter_documents_by_style(
        self, 
        documents: List[any], 
        target_style: str, 
        min_confidence: float = 0.7
    ) -> List[Dict[str, any]]:
        """
        Filter documents by writing style
        
        Args:
            documents: List of document chunks
            target_style: Desired style (e.g., "MEMO_AGGRESSIVE")
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of documents with style information
        """
        styled_documents = []
        
        for doc in documents:
            try:
                # Classify document style
                style_info = await self.classify_document_style(doc.content, doc.title)
                
                # Add style information to document
                doc_with_style = {
                    "document": doc,
                    "style": style_info["style"],
                    "style_confidence": style_info["confidence"],
                    "characteristics": style_info.get("characteristics", []),
                    "style_match": style_info["style"] == target_style and style_info["confidence"] >= min_confidence
                }
                
                styled_documents.append(doc_with_style)
                
            except Exception as e:
                logger.error(f"Error processing document {doc.title}: {e}")
                # Add document with unknown style
                styled_documents.append({
                    "document": doc,
                    "style": "UNKNOWN",
                    "style_confidence": 0.0,
                    "characteristics": [],
                    "style_match": False
                })
        
        return styled_documents
    
    def get_style_for_intent(self, intent: str) -> str:
        """
        Map user intent to desired document style
        
        Args:
            intent: User intent (e.g., "ACTIVE_DISPUTE")
            
        Returns:
            Target style for document retrieval
        """
        intent_to_style = {
            "ACTIVE_DISPUTE": "MEMO_AGGRESSIVE",
            "PLANNING_ACTION": "MEMO_DEFENSIVE", 
            "GENERAL_QUESTION": "LEGAL_ANALYSIS"
        }
        
        return intent_to_style.get(intent, "GENERAL_LEGAL")