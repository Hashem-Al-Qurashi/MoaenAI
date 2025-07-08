"""
Elite Legal RAG Engine - Production Ready with OpenAI Streaming
Clean architecture with domain-specific prompting and streaming support
"""

import os
import re
import asyncio
from enum import Enum
from typing import List, Dict, Optional, AsyncIterator, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI  # ← Both sync and async clients
import markdown

# Load environment variables
try:
    load_dotenv(".env")
except:
    pass

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # ADD this line
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # ADD this line


if AI_PROVIDER == "openai" and OPENAI_API_KEY:
    openai_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        timeout=60.0,
        max_retries=2
    )
    sync_client = OpenAI(api_key=OPENAI_API_KEY)
elif DEEPSEEK_API_KEY:
    openai_client = AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1",
        timeout=60.0,
        max_retries=2
    )
    sync_client = OpenAI(
        api_key=DEEPSEEK_API_KEY, 
        base_url="https://api.deepseek.com/v1"
    )
else:
    raise ValueError("❌ No API key available")

# 4. NEW CLASSES (ADD these after client initialization)
class Domain(Enum):
    """Legal domains for specialized prompting"""
    LEGAL = "legal"
    FINANCE = "finance" 
    TECH = "tech"
    GENERAL = "general"

class Complexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    DOCUMENT = "document"

@dataclass
class PromptConfig:
    """Configuration for AI prompting"""
    domain: Domain
    complexity: Complexity
    max_tokens: int
    temperature: float

class DomainDetector:
    """Enhanced domain detection for comprehensive consultation service"""
    
    # ==================== EXPANDED KEYWORDS ====================
    
    LEGAL_KEYWORDS = [
        # Core legal terms
        "قانون", "قانوني", "قانونية", "محكمة", "دعوى", "قضية", "حكم", "نظام", 
        "قاضي", "محامي", "عقد", "عقود", "اتفاقية", "دفوع", "استئناف", "تنفيذ", 
        "إجراءات", "محاكمة", "ترافع", "مرافعة",
        
        # Business legal
        "شركة", "شركات", "تأسيس", "تسجيل", "رخصة", "تراخيص", "سجل", "سجلات",
        "تجاري", "تجارية", "استثمار", "شراكة", "اندماج", "استحواذ",
        
        # Employment law
        "موظف", "موظفين", "عمل", "عمال", "وظيفة", "خدمة", "راتب", "أجر",
        "إجازة", "استقالة", "فصل", "انهاء", "تعويض", "مكافأة", "تأمينات",
        
        # Civil law
        "حقوق", "التزامات", "مسؤولية", "ضرر", "تعويض", "ضمان", "كفالة",
        "ملكية", "إيجار", "بيع", "شراء", "هبة", "وصية", "ميراث",
        
        # Criminal law
        "جريمة", "جرائم", "عقوبة", "عقوبات", "جنائي", "جنحة", "مخالفة",
        "سجن", "غرامة", "قصاص", "دية", "تعزير"
    ]
    
    FINANCE_KEYWORDS = [
        # Banking & loans
        "بنك", "بنوك", "مصرف", "مصارف", "قرض", "قروض", "تمويل", "ائتمان",
        "فوائد", "ربا", "مرابحة", "إجارة", "مشاركة", "مضاربة", "سلم",
        
        # Investments
        "استثمار", "استثمارات", "أسهم", "سهم", "سندات", "صكوك", "محفظة",
        "عوائد", "أرباح", "خسائر", "مخاطر", "تداول", "بورصة", "سوق مالي",
        
        # Insurance & savings
        "تأمين", "تأمينات", "ادخار", "توفير", "معاش", "تقاعد", "صندوق",
        
        # Accounting & tax
        "محاسبة", "ميزانية", "حسابات", "ضريبة", "ضرائب", "زكاة", "جمارك",
        "مالي", "مالية", "نقدي", "سيولة", "رأس مال", "تكلفة", "إيرادات"
    ]
    
    TECH_KEYWORDS = [
        # Software & development
        "تقني", "تقنية", "تكنولوجيا", "برمجة", "برامج", "تطبيق", "تطبيقات",
        "موقع", "مواقع", "نظام", "أنظمة", "قاعدة بيانات", "خادم", "سيرفر",
        
        # Security & infrastructure
        "أمان", "حماية", "أمن سيبراني", "اختراق", "فيروس", "تشفير",
        "شبكة", "شبكات", "انترنت", "واي فاي", "خوادم", "سحابي", "كلاود",
        
        # AI & modern tech
        "ذكي", "ذكاء اصطناعي", "آلة", "تعلم", "بيانات", "تحليل", "خوارزمية",
        "رقمي", "رقمنة", "تحول رقمي", "منصة", "منصات", "تقنيات حديثة"
    ]
    
    # Enhanced document detection
    DOCUMENT_PHRASES = [
        # Legal documents
        "الرد القانونى على دعوى", "رد على الدعوى", "دفوع قانونية", "مذكرة قانونية",
        "لائحة دعوى", "صيغة عقد", "مسودة اتفاقية", "نموذج عقد", "صياغة عقد",
        
        # Financial documents  
        "دراسة جدوى", "خطة عمل", "تقرير مالي", "تحليل مالي", "ميزانية عمومية",
        
        # Technical documents
        "مواصفات فنية", "تصميم نظام", "هيكل تقني", "خطة تطوير"
    ]
    
    @classmethod
    def detect_domain(cls, query: str) -> Domain:
        """Enhanced domain detection with fallback logic"""
        query_lower = query.lower()
        
        # Calculate scores for each domain
        legal_score = sum(1 for kw in cls.LEGAL_KEYWORDS if kw in query_lower)
        finance_score = sum(1 for kw in cls.FINANCE_KEYWORDS if kw in query_lower)
        tech_score = sum(1 for kw in cls.TECH_KEYWORDS if kw in query_lower)
        
        # Enhanced scoring with context
        total_words = len(query_lower.split())
        
        # Boost scores based on keyword density
        legal_density = legal_score / max(total_words, 1) * 100
        finance_density = finance_score / max(total_words, 1) * 100
        tech_density = tech_score / max(total_words, 1) * 100
        
        print(f"🔍 Domain Detection: Legal={legal_score}({legal_density:.1f}%), Finance={finance_score}({finance_density:.1f}%), Tech={tech_score}({tech_density:.1f}%)")
        
        # Decision logic with minimum threshold
        if legal_score > 0 and (legal_score >= finance_score and legal_score >= tech_score):
            return Domain.LEGAL
        elif finance_score > 0 and finance_score >= tech_score:
            return Domain.FINANCE
        elif tech_score > 0:
            return Domain.TECH
        
        # Fallback: If query mentions consultation/advice, default to legal
        consultation_terms = ["استشارة", "نصيحة", "مشورة", "رأي", "توجيه", "إرشاد"]
        if any(term in query_lower for term in consultation_terms):
            print("🎯 Fallback: Consultation detected → Legal domain")
            return Domain.LEGAL
            
        return Domain.GENERAL
    
    @classmethod  
    def detect_complexity(cls, query: str) -> Complexity:
        """Enhanced complexity detection"""
        query_lower = query.lower()
        
        # Check for document generation requests
        if any(phrase in query_lower for phrase in cls.DOCUMENT_PHRASES):
            return Complexity.DOCUMENT
        
        # Complex indicators
        complex_indicators = [
            "تحليل", "استراتيجية", "تفصيل", "شامل", "متقدم", "عميق", "مفصل",
            "دراسة", "بحث", "تقييم", "مقارنة", "خطة", "برنامج", "منهجية"
        ]
        
        # Length and complexity scoring
        word_count = len(query_lower.split())
        complex_terms = sum(1 for term in complex_indicators if term in query_lower)
        
        if complex_terms >= 2 or word_count > 20:
            return Complexity.COMPLEX
        elif complex_terms >= 1 or word_count > 10:
            return Complexity.COMPLEX
        
        return Complexity.SIMPLE    
    

class PromptBuilder:
    """Advanced prompt building with domain expertise"""
    
    # System prompts for different domains
    SYSTEM_PROMPTS = {
        Domain.LEGAL: """أنت مستشار قانوني سعودي متخصص ومرخص مع خبرة 20 عاماً في القانون السعودي.

تخصصاتك:
- القانون التجاري والشركات
- قانون العمل والعمال
- الأحوال الشخصية
- القانون الجنائي
- القانون الإداري
- القانون العقاري

أسلوب عملك:
- تحليل دقيق مبني على النصوص النظامية
- استشهاد بالسوابق القضائية
- لغة قانونية واضحة ومهنية
- حلول عملية قابلة للتطبيق""",

        Domain.FINANCE: """أنت مستشار مالي سعودي معتمد مع خبرة 15 عاماً في الأسواق المالية السعودية.

تخصصاتك:
- التخطيط المالي الشخصي
- الاستثمار في السوق السعودي
- التمويل والقروض
- الضرائب والزكاة
- إدارة المخاطر المالية

أسلوب عملك:
- تحليل مالي دقيق
- توصيات مبنية على البيانات
- مراعاة الأحكام الشرعية
- حلول مالية عملية""",

        Domain.TECH: """أنت مهندس تقني سعودي متخصص مع خبرة 12 عاماً في تطوير الأنظمة والحلول التقنية.

تخصصاتك:
- تطوير الأنظمة والتطبيقات
- الأمن السيبراني
- الحوسبة السحابية
- الذكاء الاصطناعي
- إدارة البيانات

أسلوب عملك:
- حلول تقنية عملية
- مراعاة معايير الأمان
- توصيات قابلة للتطبيق
- شرح تقني واضح""",

        Domain.GENERAL: """أنت مستشار عام متخصص في تقديم المشورة الشاملة مع خبرة واسعة في مختلف المجالات.

نهجك:
- تحليل شامل ومتوازن
- حلول عملية ومبتكرة
- لغة واضحة ومفهومة
- مراعاة السياق السعودي"""
    }
    
    @classmethod
    def get_system_prompt(cls, domain: Domain) -> str:
        """Get system prompt for domain"""
        return cls.SYSTEM_PROMPTS.get(domain, cls.SYSTEM_PROMPTS[Domain.GENERAL])
    
    @classmethod
    def build_user_prompt(cls, query: str, domain: Domain, complexity: Complexity) -> str:
        """Build optimized user prompt based on domain and complexity"""
        
        if complexity == Complexity.DOCUMENT and domain == Domain.LEGAL:
            return cls._build_legal_document_prompt(query)
        elif complexity == Complexity.COMPLEX:
            return cls._build_complex_analysis_prompt(query, domain)
        else:
            return cls._build_simple_prompt(query, domain)
    
    @classmethod
    def _build_legal_document_prompt(cls, query: str) -> str:
        """Build prompt for legal document generation"""
        return f"""قم بإعداد رد قانوني متقدم ومتميز:

{query}

متطلبات الرد القانوني:

🏛️ **الهيكل الاستراتيجي:**
- ترتيب الحجج هرمياً (الأقوى أولاً)
- لغة قانونية مركزة وقوية
- ربط مباشر بالنصوص النظامية

⚖️ **الأسس القانونية:**
- الاستشهاد بالمواد النظامية ذات الصلة
- ذكر السوابق القضائية المماثلة
- تحديد الأدلة والمستندات المطلوبة

🎯 **الاستراتيجية القانونية:**
- تحليل نقاط القوة والضعف
- الدفوع القانونية المتاحة
- الطلبات والتوصيات العملية

📋 **التنفيذ العملي:**
- خطوات إجرائية محددة
- جدول زمني للتنفيذ
- المستندات المطلوبة

يجب أن يكون الرد قابلاً للتقديم أمام المحكمة ومطابقاً للأصول القانونية."""
    
    @classmethod
    def _build_complex_analysis_prompt(cls, query: str, domain: Domain) -> str:
        """Build prompt for complex analysis"""
        domain_context = {
            Domain.LEGAL: "قانونية",
            Domain.FINANCE: "مالية", 
            Domain.TECH: "تقنية",
            Domain.GENERAL: "شاملة"
        }
        
        context = domain_context.get(domain, "شاملة")
        
        return f"""قدم استشارة {context} متقدمة ومفصلة:

{query}

متطلبات التحليل:

🎯 **التحليل الاستراتيجي:**
- تقييم شامل للوضع الحالي
- تحديد الفرص والتحديات
- تحليل المخاطر والبدائل

📊 **الأسس المرجعية:**
- الاستناد للمراجع والأنظمة ذات الصلة
- تحليل السوابق والتجارب المماثلة
- مراعاة السياق السعودي

💡 **التوصيات العملية:**
- حلول قابلة للتطبيق
- خطة تنفيذية مرحلية
- مؤشرات النجاح والمتابعة

🔍 **التفاصيل التنفيذية:**
- الخطوات المطلوبة
- الموارد والمتطلبات
- الجدول الزمني المقترح"""
    
    @classmethod
    def _build_simple_prompt(cls, query: str, domain: Domain) -> str:
        """Build prompt for simple queries"""
        return f"""أجب على السؤال التالي بوضوح ودقة:

{query}

متطلبات الإجابة:
- إجابة مباشرة وواضحة
- تفسير مبسط عند الحاجة  
- توصيات عملية مختصرة
- مراعاة السياق السعودي"""

class ConfigManager:
    """Manage AI configuration based on complexity"""
    
    CONFIGS = {
        Complexity.SIMPLE: PromptConfig(
            domain=Domain.GENERAL,
            complexity=Complexity.SIMPLE,
            max_tokens=2000,
            temperature=0.3
        ),
        Complexity.COMPLEX: PromptConfig(
            domain=Domain.GENERAL,
            complexity=Complexity.COMPLEX,
            max_tokens=4000,
            temperature=0.2
        ),
        Complexity.DOCUMENT: PromptConfig(
            domain=Domain.LEGAL,
            complexity=Complexity.DOCUMENT,
            max_tokens=6000,
            temperature=0.1
        )
    }
    
    @classmethod
    def get_config(cls, domain: Domain, complexity: Complexity) -> PromptConfig:
        """Get configuration for domain and complexity"""
        config = cls.CONFIGS[complexity]
        config.domain = domain
        return config

class RAGEngine:
    """Elite RAG Engine with streaming support"""
    
    def __init__(self):
        self.client = openai_client
        self.domain_detector = DomainDetector()
        self.prompt_builder = PromptBuilder()
        self.config_manager = ConfigManager()
    
    async def ask_question_streaming(self, query: str) -> AsyncIterator[str]:
        """Process question with streaming response"""
        try:
            # Detect domain and complexity
            domain = self.domain_detector.detect_domain(query)
            complexity = self.domain_detector.detect_complexity(query)
            
            print(f"🎯 Domain: {domain.value}, Complexity: {complexity.value}")
            
            # Get configuration
            config = self.config_manager.get_config(domain, complexity)
            
            # Build prompts
            system_prompt = self.prompt_builder.get_system_prompt(domain)
            user_prompt = self.prompt_builder.build_user_prompt(query, domain, complexity)
            
            # Create messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Stream response from OpenAI
            async for chunk in self._stream_openai_response(messages, config):
                yield chunk
                
        except Exception as e:
            print(f"❌ Error in streaming: {e}")
            yield f"عذراً، حدث خطأ تقني: {str(e)}"
    
    async def ask_question_with_context_streaming(
        self, 
        query: str, 
        conversation_history: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """Process question with conversation context and streaming"""
        try:
            # Detect domain and complexity
            domain = self.domain_detector.detect_domain(query)
            complexity = self.domain_detector.detect_complexity(query)
            
            print(f"🎯 Context query - Domain: {domain.value}, Complexity: {complexity.value}")
            
            # Get configuration
            config = self.config_manager.get_config(domain, complexity)
            
            # Build messages with context
            messages = [
                {"role": "system", "content": self.prompt_builder.get_system_prompt(domain)}
            ]
            
            # Add conversation history (limit to last 8 messages)
            recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current query with context awareness
            contextual_prompt = f"بناءً على سياق المحادثة السابقة، {self.prompt_builder.build_user_prompt(query, domain, complexity)}"
            messages.append({
                "role": "user", 
                "content": contextual_prompt
            })
            
            # Stream response
            async for chunk in self._stream_openai_response(messages, config):
                yield chunk
                
        except Exception as e:
            print(f"❌ Error in context streaming: {e}")
            yield f"عذراً، حدث خطأ تقني: {str(e)}"
    
    async def _stream_openai_response(
        self, 
        messages: List[Dict[str, str]], 
        config: PromptConfig
    ) -> AsyncIterator[str]:
        """Stream response from OpenAI"""
        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o",  # Best model for Arabic legal work
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"❌ OpenAI streaming error: {e}")
            raise
    
    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate conversation title"""
        try:
            prompt = f"اقترح عنواناً مختصراً لهذه الاستشارة (أقل من 40 حرف): {first_message[:150]}"
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Faster model for titles
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            title = title.strip('"').strip("'").strip()
            
            # Remove common prefixes
            prefixes = ["العنوان:", "المقترح:", "عنوان:", "الاستشارة:"]
            for prefix in prefixes:
                if title.startswith(prefix):
                    title = title[len(prefix):].strip()
            
            return title if len(title) <= 40 else title[:37] + "..."
            
        except Exception as e:
            print(f"❌ Error generating title: {e}")
            return first_message[:25] + "..." if len(first_message) > 25 else first_message

# Global instance for easy import
rag_engine = RAGEngine()

# Legacy sync functions for backward compatibility
async def ask_question(query: str) -> str:
    """Legacy sync function - converts streaming to complete response"""
    chunks = []
    async for chunk in rag_engine.ask_question_streaming(query):
        chunks.append(chunk)
    return ''.join(chunks)

async def ask_question_with_context(query: str, conversation_history: List[Dict[str, str]]) -> str:
    """Legacy sync function with context - converts streaming to complete response"""
    chunks = []
    async for chunk in rag_engine.ask_question_with_context_streaming(query, conversation_history):
        chunks.append(chunk)
    return ''.join(chunks)

async def generate_conversation_title(first_message: str) -> str:
    """Legacy function for title generation"""
    return await rag_engine.generate_conversation_title(first_message)