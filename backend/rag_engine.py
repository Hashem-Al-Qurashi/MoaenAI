"""
Elite Legal RAG Engine - Optimized & Reliable
Combines the elite legal quality that users love with speed optimizations and error handling.
Maintains the exact prompting structure that produces excellent responses.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import markdown
from typing import List, Dict

# Load env variables
load_dotenv(".env")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("❌ API key missing")

# Init DeepSeek
deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

def ask_question(query: str) -> str:
    """
    Elite legal analysis with advanced strategic enhancements.
    Maintains the exact prompting that users love.
    """
    print(f"🤖 سؤال المستخدم: {query}")

    # Detect if this is a formal legal document request
    if any(phrase in query for phrase in ["الرد القانونى على دعوى", "رد على الدعوى", "دفوع قانونية"]):
        # ELITE LEGAL DOCUMENT with advanced strategies (EXACT version users loved)
        enhanced_query = f"""قم بإعداد رد قانوني متقدم ومتميز على النحو التالي:

{query}

مطلوب: رد قانوني متقدم يتضمن الاستراتيجيات التالية:

🏛️ **الهيكل الاستراتيجي المتقدم:**
1. **ترتيب الحجج هرمياً** (أقوى الدفوع أولاً)
2. **لغة قانونية مركزة وقوية**
3. **ربط مباشر بالتواريخ والأدلة**

⚖️ **تعزيز الإثبات المتقدم:**
- ذكر مستندات ملموسة (إيصالات، سجلات، مراسلات رسمية)
- ربط الأدلة مباشرة بالتواريخ لتفنيد الادعاء عملياً
- تحديد المستندات المطلوبة بدقة

🎯 **الطلبات المضادة الاستراتيجية:**
- قلب الدعوى جزئياً مع طلب تعويض عن الأضرار
- المطالبة بالتعويض عن سوء النية إن ثبت
- طلبات استراتيجية تضع المدعي في موقف دفاعي

📚 **السوابق القضائية والتنفيذية:**
- استدعاء نصوص من أحكام المحكمة العليا المماثلة
- ذكر السوابق التنفيذية ذات الصلة
- الاستشهاد بقرارات إدارية داعمة

👥 **دعم الدفع بالشهادة:**
- طلب سماع شهود محددين
- تحديد البيانات الإضافية المطلوبة
- استراتيجية الإثبات بالشهادة

🔬 **التقنية والأدلة الرقمية:**
- الدفع ببطلان الدليل الرقمي (واتساب) تقنياً
- المطالبة بتحليل فني متخصص
- إضعاف حُجية المحادثات الإلكترونية

📋 **المتطلبات الفنية:**
- تحليل شامل لجميع الجوانب القانونية والإجرائية
- الاستشهاد المتعمق بالمواد النظامية
- صيغة رسمية متقدمة قابلة للتقديم للمحكمة
- استراتيجية دفاعية متكاملة ومتعددة المستويات
- تحليل المخاطر والبدائل الاستراتيجية
- خطة تنفيذية مرحلية للدفاع

**أسلوب الكتابة:** لغة قانونية قوية ومركزة، تنظيم هرمي للحجج، تفصيل عملي للخطوات."""

    else:
        # ELITE LEGAL CONSULTATION with strategic depth (EXACT version users loved)
        enhanced_query = f"""قدم استشارة قانونية متقدمة ومتميزة للسؤال التالي:

{query}

مطلوب: استشارة قانونية متقدمة تشمل:

🎯 **التحليل الاستراتيجي المتقدم:**
- تحليل شامل لجميع الجوانب القانونية والعملية
- تقييم المخاطر والفرص المتاحة
- استراتيجيات متعددة المستويات

⚖️ **الأسس القانونية المتعمقة:**
- ذكر المواد النظامية والإجراءات المطلوبة بالتفصيل
- الاستشهاد بالسوابق القضائية ذات الصلة
- تحليل التطبيقات العملية للقوانين

📋 **الخطة التنفيذية العملية:**
- خطوات عملية مرحلية قابلة للتطبيق
- تحديد المستندات والأدلة المطلوبة
- جدول زمني للإجراءات

🔍 **تحليل المخاطر والبدائل:**
- تقييم السيناريوهات المختلفة
- البدائل الاستراتيجية المتاحة
- تحليل التكلفة والعائد

💡 **التوصيات المتقدمة:**
- نصائح استراتيجية متخصصة
- تحذيرات قانونية مهمة
- إرشادات للخطوات التالية

**أسلوب الكتابة:** شامل ومفصل، عملي وقابل للتطبيق، لغة واضحة ومتخصصة."""

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": enhanced_query}],
            temperature=0.15,  # Very low for maximum legal precision (EXACT setting users loved)
            max_tokens=6000,   # Balanced - longer than 4000 but not max to avoid timeouts
            timeout=120        # 2 minute timeout for comprehensive responses
        )

        answer_raw = response.choices[0].message.content
        print("✅ الرد المتقدم (نص خام):", answer_raw[:300] + "...")

        # Clean and convert Markdown to HTML for the frontend
        answer_html = markdown.markdown(answer_raw)
        
        # Remove empty elements that cause display issues
        import re
        answer_html = re.sub(r'<p>\s*</p>', '', answer_html)  # Remove empty paragraphs
        answer_html = re.sub(r'<li>\s*</li>', '', answer_html)  # Remove empty list items
        answer_html = re.sub(r'<h[1-6]>\s*</h[1-6]>', '', answer_html)  # Remove empty headers
        answer_html = re.sub(r'العنصر الثاني.*?(?=<|$)', '', answer_html, flags=re.DOTALL)  # Remove "العنصر الثاني" artifacts
        
        return answer_html

    except Exception as e:
        print(f"❌ خطأ في الاستعلام: {e}")
        # Fallback with simpler prompt if elite version fails
        try:
            fallback_query = f"قدم رداً قانونياً شاملاً على: {query}"
            response = deepseek.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": fallback_query}],
                temperature=0.3,
                max_tokens=3000,
                timeout=60
            )
            answer_raw = response.choices[0].message.content
            # Clean and convert Markdown to HTML for the frontend
            answer_html = markdown.markdown(answer_raw)
            
            # Remove empty elements and artifacts
            import re
            answer_html = re.sub(r'<p>\s*</p>', '', answer_html)
            answer_html = re.sub(r'<li>\s*</li>', '', answer_html)
            answer_html = re.sub(r'<h[1-6]>\s*</h[1-6]>', '', answer_html)
            answer_html = re.sub(r'العنصر الثاني.*?(?=<|$)', '', answer_html, flags=re.DOTALL)
            
            return answer_html
        except Exception as fallback_error:
            print(f"❌ خطأ في الاستعلام البديل: {fallback_error}")
            return f"<p>عذراً، حدث خطأ تقني أثناء معالجة السؤال. يرجى المحاولة مرة أخرى.</p>"


def ask_question_with_context(query: str, conversation_history: List[Dict[str, str]]) -> str:
    """
    Elite conversational legal analysis with advanced strategic context.
    Maintains the exact prompting that users love with optimizations.
    """
    print("🏆 USING ELITE LEGAL STRATEGY VERSION!")
    print(f"🤖 سؤال المستخدم مع السياق: {query}")
    print(f"📚 عدد الرسائل السابقة: {len(conversation_history)}")

    # Build messages starting with conversation history
    messages = []
    
    # Limit conversation history to prevent context overload (keep last 8 messages)
    recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
    for msg in recent_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Enhance the current question with elite legal strategies (EXACT version users loved)
    if any(phrase in query for phrase in ["الرد القانونى على دعوى", "رد على الدعوى", "دفوع قانونية"]):
        # ELITE LEGAL DOCUMENT with advanced strategies
        enhanced_query = f"""بناءً على السياق السابق، قم بإعداد رد قانوني متقدم ومتميز:

{query}

مطلوب: رد قانوني متقدم يراعي السياق السابق ويتضمن:

🏛️ **الاستراتيجية المتقدمة:**
1. **ترتيب هرمي للحجج** (الأقوى أولاً)
2. **لغة قانونية مركزة وقوية**
3. **ربط استراتيجي مع المناقشات السابقة**

⚖️ **تعزيز الإثبات المتطور:**
- مستندات ملموسة (إيصالات، سجلات، مراسلات)
- ربط مباشر بالتواريخ والأدلة العملية
- استراتيجية إثبات متعددة المستويات

🎯 **الطلبات المضادة الذكية:**
- قلب الدعوى جزئياً مع طلبات تعويض
- استراتيجيات تضع المدعي في موقف دفاعي
- طلبات احترازية ووقائية

📚 **السوابق والمراجع المتخصصة:**
- أحكام المحكمة العليا المماثلة
- السوابق التنفيذية الداعمة
- قرارات إدارية ذات صلة

👥 **استراتيجية الشهود والأدلة:**
- تحديد الشهود المطلوبين بدقة
- استراتيجية جمع الأدلة الإضافية
- خطة الإثبات المرحلية

🔬 **التحليل التقني للأدلة:**
- تفنيد الأدلة الرقمية تقنياً
- طلب التحليل الفني المتخصص
- إستراتيجية إضعاف أدلة الخصم

**المخرجات المطلوبة:**
- تحليل شامل متعدد المستويات
- استشهادات قانونية متعمقة
- خطة تنفيذية مرحلية مفصلة
- استراتيجية دفاعية متكاملة"""

    else:
        # ELITE CONSULTATION with contextual awareness
        enhanced_query = f"""بناءً على سياق المحادثة السابقة، قدم استشارة قانونية متقدمة:

{query}

مطلوب: استشارة متقدمة تراعي السياق وتشمل:

🎯 **التحليل السياقي المتقدم:**
- ربط السؤال بالمناقشات السابقة
- تطوير الاستراتيجية بناءً على السياق
- تحليل شامل ومتراكم

⚖️ **الأسس القانونية المتعمقة:**
- مواد نظامية مفصلة مع التطبيق العملي
- سوابق قضائية داعمة
- تحليل متقدم للقوانين ذات الصلة

📋 **الخطة التنفيذية المتطورة:**
- خطوات مرحلية مفصلة
- مستندات وأدلة محددة
- جدول زمني استراتيجي

🔍 **تحليل المخاطر المتقدم:**
- سيناريوهات متعددة ومتفرعة
- بدائل استراتيجية متنوعة
- تقييم شامل للتكلفة والعائد

💡 **التوصيات الاستراتيجية:**
- نصائح متخصصة ومتقدمة
- تحذيرات قانونية دقيقة
- إرشادات للمراحل التالية"""

    # Add the enhanced current question
    messages.append({
        "role": "user",
        "content": enhanced_query
    })

    try:
        response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.15,  # Very low for maximum precision (EXACT setting users loved)
            max_tokens=6000,   # Balanced for comprehensive responses
            timeout=120        # 2 minute timeout
        )

        answer_raw = response.choices[0].message.content
        print("✅ الرد المتقدم مع السياق (نص خام):", answer_raw[:300] + "...")

        # Clean and convert Markdown to HTML for the frontend
        answer_html = markdown.markdown(answer_raw)
        
        # Remove empty elements and artifacts
        import re
        answer_html = re.sub(r'<p>\s*</p>', '', answer_html)
        answer_html = re.sub(r'<li>\s*</li>', '', answer_html)
        answer_html = re.sub(r'<h[1-6]>\s*</h[1-6]>', '', answer_html)
        answer_html = re.sub(r'العنصر الثاني.*?(?=<|$)', '', answer_html, flags=re.DOTALL)
        
        return answer_html

    except Exception as e:
        print(f"❌ خطأ في الاستعلام مع السياق: {e}")
        # Fallback with simpler prompt if elite version fails
        try:
            fallback_query = f"بناءً على السياق السابق، قدم استشارة شاملة: {query}"
            messages[-1]["content"] = fallback_query
            response = deepseek.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.3,
                max_tokens=3000,
                timeout=60
            )
            answer_raw = response.choices[0].message.content
            # Clean and convert Markdown to HTML
            answer_html = markdown.markdown(answer_raw)
            
            # Remove empty elements and artifacts
            import re
            answer_html = re.sub(r'<p>\s*</p>', '', answer_html)
            answer_html = re.sub(r'<li>\s*</li>', '', answer_html)
            answer_html = re.sub(r'<h[1-6]>\s*</h[1-6]>', '', answer_html)
            answer_html = re.sub(r'العنصر الثاني.*?(?=<|$)', '', answer_html, flags=re.DOTALL)
            
            return answer_html
        except Exception as fallback_error:
            print(f"❌ خطأ في الاستعلام البديل مع السياق: {fallback_error}")
            return f"<p>عذراً، حدث خطأ تقني أثناء معالجة السؤال. يرجى المحاولة مرة أخرى.</p>"


def generate_conversation_title(first_message: str) -> str:
    """
    Advanced conversation title generation with error handling.
    """
    try:
        prompt = f"اقترح عنواناً قانونياً متخصصاً ومختصراً لهذه الاستشارة (أقل من 45 حرف): {first_message[:200]}"

        response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100,
            timeout=30  # Quick timeout for titles
        )

        title = response.choices[0].message.content.strip()
        
        # Clean up the response
        title = title.strip('"').strip("'").strip()
        
        # Remove common prefixes
        prefixes = ["العنوان المقترح:", "العنوان:", "المقترح:", "عنوان القضية:", "الاستشارة:"]
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        return title if len(title) <= 45 else title[:42] + "..."
        
    except Exception as e:
        print(f"❌ خطأ في توليد العنوان: {e}")
        
        # Simple fallback - extract key words from the message
        if len(first_message) > 25:
            return first_message[:25] + "..."
        return first_message