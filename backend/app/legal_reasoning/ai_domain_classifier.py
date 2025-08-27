"""
AI-Powered Domain Classifier using Mini GPT
Uses OpenAI to intelligently classify legal queries into domains
"""

import json
import logging
from enum import Enum
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LegalDomain(Enum):
    CONSTRUCTION = "construction"
    COMMERCIAL = "commercial" 
    EMPLOYMENT = "employment"
    SHARIA_COURTS = "sharia_courts"
    TAX = "tax"
    CIVIL = "civil"
    CRIMINAL = "criminal"
    BANKRUPTCY = "bankruptcy"
    FAMILY = "family"
    GENERAL = "general"

class AIDomainClassifier:
    """AI-powered domain classifier for Arabic legal queries"""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
        
        # Domain descriptions in Arabic for better classification
        self.domain_descriptions = {
            "construction": "قضايا البناء والإنشاء والمقاولات والمشاريع والهندسة",
            "commercial": "القضايا التجارية والشركات والأعمال والاستثمار والتوريد",
            "employment": "قضايا العمل والموظفين والرواتب والفصل والاستقالة",
            "sharia_courts": "قضايا المحاكم الشرعية والأحوال الشخصية والزواج والطلاق",
            "tax": "القضايا الضريبية والزكاة والرسوم الجمركية والمالية",
            "civil": "القضايا المدنية والحقوق والالتزامات والتعويضات",
            "criminal": "القضايا الجنائية والجرائم والعقوبات",
            "bankruptcy": "قضايا الإفلاس والتصفية والإعسار المالي",
            "family": "قضايا الأسرة والنفقة والحضانة والميراث",
            "general": "استفسارات قانونية عامة لا تندرج تحت تصنيف محدد"
        }
    
    async def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Enhanced classify method with contextual examples for better accuracy
        """
        try:
            # Enhanced classification prompt with examples
            classification_prompt = f"""أنت خبير قانوني سعودي متخصص في تصنيف الاستفسارات القانونية.

    صنف الاستفسار إلى المجال الأنسب بناءً على هذه الأمثلة:

    📋 المجالات والأمثلة:

    • CIVIL (مدني): دعاوى، مذكرات قانونية، ردود على الدعاوى، نزاعات مدنية عامة
    مثال: "الرد القانوني على دعوى"، "مذكرة دفاع في قضية"، "دعوى مدنية ضد شخص"

    • COMMERCIAL (تجاري): عقود تجارية، شركات، استثمار، نزاعات تجارية
    مثال: "عقد مع مقاول"، "نزاع تجاري"، "مشكلة في الشركة"

    • EMPLOYMENT (عمالي): قضايا العمل، الموظفين، الرواتب، إنهاء الخدمة
    مثال: "مشكلة مع الموظف"، "إنهاء عقد العمل"، "نزاع عمالي"

    • FAMILY (أسرة): زواج، طلاق، حضانة، ميراث، أحوال شخصية
    مثال: "قضية طلاق"، "مشكلة ميراث"، "حضانة الأطفال"

    • CRIMINAL (جنائي): جرائم، عقوبات، قضايا جزائية
    مثال: "جريمة سرقة"، "قضية جنائية"، "عقوبة الاعتداء"

    • TAX (ضريبي): ضرائب، زكاة، جمارك، مالية حكومية
    مثال: "مشكلة ضريبية"، "دفع الزكاة"، "نزاع مع هيئة الزكاة"

    • BANKRUPTCY (إفلاس): صعوبات مالية، إفلاس الشركات، مديونية
    مثال: "إعلان الإفلاس"، "صعوبات مالية للشركة"

    • CONSTRUCTION (إنشاء): مقاولات، بناء، مشاريع إنشائية
    مثال: "عقد مع مقاول بناء"، "مشروع إنشائي"، "نزاع مقاولات"

    • SHARIA_COURTS (محاكم شرعية): قضايا الأحوال الشخصية في المحاكم الشرعية
    مثال: "دفع شرعي"، "قضية في المحكمة الشرعية"

    • GENERAL (عام): استفسارات قانونية عامة لا تندرج تحت مجال محدد
    مثال: "استشارة قانونية عامة"، "سؤال عن القانون"

    🎯 قواعد التصنيف:
    1. ركز على الموضوع الأساسي للاستفسار
    2. "دعوى" أو "مذكرة" بدون تخصص = CIVIL
    3. إذا ذُكر نوع العقد أو النشاط، صنف حسب النشاط (تجاري، عمالي، إلخ)
    4. في حالة الشك، اختر المجال الأكثر تخصصاً

    الاستفسار: "{query}"

    أجب بتنسيق JSON فقط:
    {{
        "domain": "المجال_المناسب",
        "confidence": 0.95,
        "reasoning": "سبب التصنيف باختصار",
        "keywords": ["الكلمات", "المفتاحية", "المكتشفة"]
    }}"""

            # Get AI classification
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse response (rest of method remains same)
            ai_response = response.choices[0].message.content.strip()
            
            # Clean response
            if ai_response.startswith("```json"):
                ai_response = ai_response.replace("```json", "").replace("```", "").strip()
            
            classification_result = json.loads(ai_response)
            
            # Validate and return
            classified_domain = classification_result.get("domain", "general")
            
            # Convert to LegalDomain enum
            try:
                domain_enum = LegalDomain(classified_domain.lower())
            except ValueError:
                logger.warning(f"Invalid domain: {classified_domain}, defaulting to GENERAL")
                domain_enum = LegalDomain.GENERAL
            
            return {
                "domain": domain_enum,
                "confidence": classification_result.get("confidence", 0.5),
                "reasoning": classification_result.get("reasoning", ""),
                "keywords": classification_result.get("keywords", [])
            }
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self._fallback_classification(query)
    
    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """Fallback classification using simple keyword matching"""
        query_lower = query.lower()
        
        # Simple keyword-based fallback
        if any(word in query_lower for word in ['مقاول', 'بناء', 'إنشاء', 'مشروع']):
            domain = LegalDomain.CONSTRUCTION
        elif any(word in query_lower for word in ['تجاري', 'شركة', 'أعمال']):
            domain = LegalDomain.COMMERCIAL
        elif any(word in query_lower for word in ['عمل', 'موظف', 'فصل', 'راتب']):
            domain = LegalDomain.EMPLOYMENT
        elif any(word in query_lower for word in ['ضريبة', 'زكاة']):
            domain = LegalDomain.TAX
        elif any(word in query_lower for word in ['دفع شرعي', 'شرعي', 'طلاق', 'زواج']):
            domain = LegalDomain.SHARIA_COURTS
        elif any(word in query_lower for word in ['إفلاس', 'إعسار', 'تصفية']):
            domain = LegalDomain.BANKRUPTCY
        else:
            domain = LegalDomain.GENERAL
        
        return {
            "domain": domain,
            "confidence": 0.6,
            "reasoning": "تصنيف احتياطي بناءً على الكلمات المفتاحية",
            "keywords": [],
            "fallback": True
        }
    
    def get_domain_filter_sql(self, domain: LegalDomain) -> str:
        """
        Get SQL filter condition for a specific domain
        
        Args:
            domain: The classified legal domain
            
        Returns:
            str: SQL WHERE condition to filter documents by domain
        """
        if domain == LegalDomain.CONSTRUCTION:
            return "(title LIKE '%مقاول%' OR title LIKE '%بناء%' OR title LIKE '%إنشاء%' OR content LIKE '%مقاول%' OR content LIKE '%بناء%' OR content LIKE '%إنشاء%' OR content LIKE '%مشروع%')"
        
        elif domain == LegalDomain.COMMERCIAL:
            return "(title LIKE '%تجاري%' OR title LIKE '%شركة%' OR title LIKE '%تجارة%' OR content LIKE '%تجاري%' OR content LIKE '%شركة%' OR content LIKE '%أعمال%')"
        
        elif domain == LegalDomain.EMPLOYMENT:
            return "(title LIKE '%عمل%' OR title LIKE '%موظف%' OR title LIKE '%عمال%' OR content LIKE '%عمل%' OR content LIKE '%موظف%' OR content LIKE '%راتب%')"
        
        elif domain == LegalDomain.SHARIA_COURTS:
            return "(title LIKE '%دفع شرعي%' OR title LIKE '%شرعي%' OR title LIKE '%family%' OR content LIKE '%شرعي%' OR content LIKE '%أحوال%' OR content LIKE '%زواج%')"
        
        elif domain == LegalDomain.TAX:
            return "(title LIKE '%ضريبة%' OR title LIKE '%زكاة%' OR content LIKE '%ضريبة%' OR content LIKE '%زكاة%' OR content LIKE '%مالي%')"
        
        elif domain == LegalDomain.CIVIL:
            return "(title LIKE '%مدني%' OR title LIKE '%civil%' OR content LIKE '%مدني%' OR content LIKE '%حقوق%' OR content LIKE '%تعويض%')"
        
        elif domain == LegalDomain.CRIMINAL:
            return "(title LIKE '%جنائي%' OR title LIKE '%criminal%' OR title LIKE '%جريمة%' OR content LIKE '%جنائي%' OR content LIKE '%عقوبة%')"
        
        elif domain == LegalDomain.BANKRUPTCY:
            return "(title LIKE '%إفلاس%' OR content LIKE '%إفلاس%' OR content LIKE '%إعسار%' OR content LIKE '%مدين%')"
        
        elif domain == LegalDomain.FAMILY:
            return "(title LIKE '%family%' OR content LIKE '%أسرة%' OR content LIKE '%نفقة%' OR content LIKE '%حضانة%')"
        
        else:
            # General - no filter, search all documents
            return "1=1"