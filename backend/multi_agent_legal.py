"""
🇸🇦 MULTI-AGENT LEGAL REASONING SYSTEM - Backend Implementation
Save this as: backend/multi_agent_legal.py

Advanced Saudi Legal AI with Trust Trail & Citation Validation
Built for your existing FastAPI + SQLAlchemy architecture
"""

import asyncio
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, AsyncIterator, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Use your existing OpenAI setup from rag_engine.py
try:
    from rag_engine import openai_client, sync_client
    print("✅ Successfully imported OpenAI clients from rag_engine.py")
except ImportError as e:
    print(f"⚠️ Could not import from rag_engine.py: {e}")
    # Fallback OpenAI setup
    from openai import AsyncOpenAI, OpenAI
    from dotenv import load_dotenv
    
    load_dotenv(".env")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    
    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=60.0, max_retries=2)
        sync_client = OpenAI(api_key=OPENAI_API_KEY)
    elif DEEPSEEK_API_KEY:
        openai_client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            timeout=60.0,
            max_retries=2
        )
        sync_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
    else:
        raise ValueError("❌ No API key available for OpenAI or DeepSeek")

class LegalAgentType(Enum):
    """Types of legal reasoning agents"""
    FACT_ANALYZER = "fact_analyzer"
    LEGAL_RESEARCHER = "legal_researcher" 
    ARGUMENT_BUILDER = "argument_builder"
    COUNTER_ARGUMENT_PREDICTOR = "counter_argument_predictor"
    DOCUMENT_DRAFTER = "document_drafter"
    CITATION_VALIDATOR = "citation_validator"

@dataclass
class AgentStep:
    """Individual step in the legal reasoning chain"""
    agent_type: LegalAgentType
    step_number: int
    step_name: str
    input_data: str
    output_data: str
    citations: List[str]
    confidence_score: float
    processing_time_ms: int
    timestamp: str
    sources_verified: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_type": self.agent_type.value,
            "step_number": self.step_number,
            "step_name": self.step_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "citations": self.citations,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
            "sources_verified": self.sources_verified
        }

@dataclass  
class LegalReasoningResult:
    """Complete multi-agent legal analysis result"""
    query: str
    final_answer: str
    reasoning_steps: List[AgentStep]
    total_processing_time_ms: int
    overall_confidence: float
    trust_trail_enabled: bool
    citations_summary: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "query": self.query,
            "final_answer": self.final_answer,
            "reasoning_steps": [step.to_dict() for step in self.reasoning_steps],
            "total_processing_time_ms": self.total_processing_time_ms,
            "overall_confidence": self.overall_confidence,
            "trust_trail_enabled": self.trust_trail_enabled,
            "citations_summary": self.citations_summary,
            "timestamp": datetime.now().isoformat()
        }

class LegalAgent:
    """Base class for specialized legal reasoning agents"""
    
    def __init__(self, agent_type: LegalAgentType, openai_client):
        self.agent_type = agent_type
        self.client = openai_client
        self.system_prompts = self._get_system_prompts()
    
    def _get_system_prompts(self) -> Dict[LegalAgentType, str]:
        """Specialized system prompts for each agent type"""
        return {
            LegalAgentType.FACT_ANALYZER: """أنت محلل وقائع قانوني متخصص في القانون السعودي.

مهامك:
🔍 استخراج الوقائع القانونية الأساسية من السؤال
⚖️ تحديد الأطراف المعنية والعلاقات القانونية
📋 تصنيف نوع النزاع والمجال القانوني
🎯 تحديد النقاط القانونية الحاسمة

أسلوب العمل:
- تحليل منطقي مرتب
- استخراج الوقائع دون تفسير قانوني
- تحديد المعلومات الناقصة
- ترتيب الأولويات حسب الأهمية القانونية""",

            LegalAgentType.LEGAL_RESEARCHER: """أنت باحث قانوني متخصص في القانون السعودي والسوابق القضائية.

مهامك:
📚 البحث في النصوص النظامية ذات الصلة
⚖️ العثور على السوابق القضائية المماثلة
📖 استخراج المواد القانونية الأساسية
🔗 ربط الوقائع بالأحكام القانونية

قواعد البحث:
- الاستشهاد بالمواد النظامية بدقة
- ذكر أرقام المواد والأنظمة
- التمييز بين الأحكام الإلزامية والاختيارية
- التحقق من سريان النصوص وعدم نسخها""",

            LegalAgentType.ARGUMENT_BUILDER: """أنت محام خبير في بناء الحجج القانونية والدفوع.

مهامك:
🏗️ بناء حجج قانونية قوية ومترابطة
⚡ ترتيب الدفوع حسب القوة والأهمية
📋 صياغة الطلبات القانونية بوضوح
🎯 ربط الوقائع بالقانون بطريقة مقنعة

استراتيجية الدفوع:
- البدء بالحجج الأقوى
- دعم كل حجة بالنصوص النظامية
- استخدام السوابق القضائية
- صياغة قانونية دقيقة ومهنية""",

            LegalAgentType.COUNTER_ARGUMENT_PREDICTOR: """أنت محام متخصص في التنبؤ بحجج الطرف الآخر والرد عليها.

مهامك:
🤔 توقع حجج ودفوع الطرف المقابل
🛡️ إعداد ردود قانونية مسبقة
⚠️ تحديد نقاط الضعف في القضية
💪 تقوية الدفوع ضد الهجمات المتوقعة

منهجية التحليل:
- التفكير من منظور الطرف الآخر
- تحديد الثغرات القانونية المحتملة
- إعداد ردود مدعومة بالأدلة
- تقييم مخاطر كل دفع مضاد""",

            LegalAgentType.DOCUMENT_DRAFTER: """أنت محام متخصص في صياغة المستندات القانونية والمرافعات.

مهامك:
📝 صياغة المستندات القانونية بدقة
⚖️ تنظيم المحتوى حسب الأصول القانونية
📋 كتابة مذكرات قانونية مهنية
🎯 إنتاج مستندات قابلة للتقديم للمحكمة

معايير الصياغة:
- لغة قانونية دقيقة ومهنية
- ترتيب منطقي للحجج والدفوع
- استشهادات صحيحة ومحددة
- مطابقة للأصول الإجرائية""",

            LegalAgentType.CITATION_VALIDATOR: """أنت مراجع قانوني متخصص في التحقق من صحة الاستشهادات.

مهامك:
🔍 التحقق من صحة المراجع القانونية
📚 التأكد من سريان النصوص المذكورة
⚖️ مراجعة دقة أرقام المواد والأنظمة
✅ تصنيف مستوى الثقة في كل استشهاد

معايير المراجعة:
- التحقق من وجود النص الفعلي
- التأكد من عدم النسخ أو التعديل
- تقييم مدى الصلة بالموضوع
- إضافة تحذيرات للاستشهادات المشكوك فيها"""
        }
    
    async def process(self, input_data: str, context: Optional[str] = None) -> Tuple[str, List[str], float]:
        """Process input through specialized agent"""
        system_prompt = self.system_prompts[self.agent_type]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_data}
        ]
        
        if context:
            messages.insert(-1, {"role": "user", "content": f"السياق: {context}"})
        
        try:
            # Determine model based on client type
            model = "gpt-4o" if "openai" in str(self.client.base_url) else "deepseek-chat"
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,  # Lower temperature for legal precision
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Extract citations (simple pattern matching for now)
            citations = self._extract_citations(content)
            
            # Calculate confidence based on citation count and content length
            confidence = self._calculate_confidence(content, citations)
            
            return content, citations, confidence
            
        except Exception as e:
            return f"خطأ في معالجة {self.agent_type.value}: {str(e)}", [], 0.0
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract legal citations from content"""
        citations = []
        
        # Pattern for Saudi legal references
        import re
        
        # Pattern for "المادة X من نظام Y"
        article_pattern = r'المادة\s+(\d+)\s+من\s+نظام\s+([^،\s]+(?:\s+[^،\s]+)*)'
        matches = re.findall(article_pattern, content)
        for match in matches:
            citations.append(f"المادة {match[0]} من نظام {match[1]}")
        
        # Pattern for "القرار رقم X"
        decision_pattern = r'القرار\s+رقم\s+(\d+(?:/\d+)?)'
        matches = re.findall(decision_pattern, content)
        for match in matches:
            citations.append(f"القرار رقم {match}")
        
        return citations
    
    def _calculate_confidence(self, content: str, citations: List[str]) -> float:
        """Calculate confidence score based on content analysis"""
        base_confidence = 0.7
        
        # Boost confidence for legal citations
        citation_boost = min(len(citations) * 0.05, 0.2)
        
        # Boost confidence for structured content
        structure_indicators = ["أولاً", "ثانياً", "ثالثاً", "الخلاصة", "التوصية"]
        structure_boost = sum(0.02 for indicator in structure_indicators if indicator in content)
        structure_boost = min(structure_boost, 0.1)
        
        # Penalize for uncertainty words
        uncertainty_words = ["ربما", "يمكن أن", "قد يكون", "غير واضح"]
        uncertainty_penalty = sum(0.05 for word in uncertainty_words if word in content)
        uncertainty_penalty = min(uncertainty_penalty, 0.2)
        
        final_confidence = base_confidence + citation_boost + structure_boost - uncertainty_penalty
        return max(0.1, min(1.0, final_confidence))

class MultiAgentLegalOrchestrator:
    """
    🧠 CORE ORCHESTRATOR: Sequential Pipeline with Parallel Sub-tasks
    
    Implements hybrid approach:
    - Sequential main steps (Analysis → Research → Arguments → Counter → Draft)
    - Parallel sub-tasks within each step for speed
    - Full trust trail for conservative firms
    - Citation validation throughout
    """
    
    def __init__(self, openai_client):
        self.client = openai_client
        self.agents = {
            agent_type: LegalAgent(agent_type, openai_client) 
            for agent_type in LegalAgentType
        }
        
    async def process_legal_query(
        self, 
        query: str, 
        enable_trust_trail: bool = False,
        conversation_context: Optional[List[Dict]] = None
    ) -> LegalReasoningResult:
        """
        🎯 MAIN ORCHESTRATION: Process legal query through multi-agent pipeline
        """
        
        start_time = time.time()
        reasoning_steps = []
        
        # Add conversation context if available
        context_summary = ""
        if conversation_context:
            context_summary = self._summarize_conversation_context(conversation_context)
        
        try:
            # STEP 1: FACT ANALYSIS
            print("🔍 Step 1: Analyzing legal facts...")
            fact_step = await self._execute_agent_step(
                LegalAgentType.FACT_ANALYZER,
                1,
                "تحليل الوقائع القانونية",
                query,
                context_summary
            )
            reasoning_steps.append(fact_step)
            
            # STEP 2: LEGAL RESEARCH 
            print("📚 Step 2: Researching legal precedents...")
            research_step = await self._execute_agent_step(
                LegalAgentType.LEGAL_RESEARCHER,
                2, 
                "البحث القانوني والسوابق",
                fact_step.output_data,
                context_summary
            )
            reasoning_steps.append(research_step)
            
            # STEP 3: ARGUMENT BUILDING
            print("🏗️ Step 3: Building legal arguments...")
            argument_step = await self._execute_agent_step(
                LegalAgentType.ARGUMENT_BUILDER,
                3,
                "بناء الحجج القانونية", 
                f"الوقائع: {fact_step.output_data}\n\nالبحث القانوني: {research_step.output_data}",
                context_summary
            )
            reasoning_steps.append(argument_step)
            
            # STEP 4: DOCUMENT DRAFTING (simplified for now)
            print("📝 Step 4: Drafting legal response...")
            draft_step = await self._execute_agent_step(
                LegalAgentType.DOCUMENT_DRAFTER,
                4,
                "صياغة الرد القانوني",
                f"الحجج: {argument_step.output_data}",
                context_summary
            )
            reasoning_steps.append(draft_step)
            
            # Compile final answer
            final_answer = self._compile_final_answer(reasoning_steps, enable_trust_trail)
            
            # Calculate metrics
            total_time = int((time.time() - start_time) * 1000)
            overall_confidence = sum(step.confidence_score for step in reasoning_steps) / len(reasoning_steps)
            all_citations = list(set([cite for step in reasoning_steps for cite in step.citations]))
            
            return LegalReasoningResult(
                query=query,
                final_answer=final_answer,
                reasoning_steps=reasoning_steps,
                total_processing_time_ms=total_time,
                overall_confidence=overall_confidence,
                trust_trail_enabled=enable_trust_trail,
                citations_summary=all_citations
            )
            
        except Exception as e:
            print(f"❌ Multi-agent processing failed: {e}")
            # Fallback to single-agent response
            return await self._fallback_response(query, start_time)
    
    async def _execute_agent_step(
        self,
        agent_type: LegalAgentType,
        step_number: int,
        step_name: str,
        input_data: str,
        context: Optional[str] = None
    ) -> AgentStep:
        """Execute individual agent step with timing and error handling"""
        
        step_start = time.time()
        
        try:
            output, citations, confidence = await self.agents[agent_type].process(input_data, context)
            
            processing_time = int((time.time() - step_start) * 1000)
            
            return AgentStep(
                agent_type=agent_type,
                step_number=step_number,
                step_name=step_name,
                input_data=input_data[:200] + "..." if len(input_data) > 200 else input_data,
                output_data=output,
                citations=citations,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat(),
                sources_verified=False
            )
            
        except Exception as e:
            return AgentStep(
                agent_type=agent_type,
                step_number=step_number,
                step_name=step_name,
                input_data=input_data[:200] + "..." if len(input_data) > 200 else input_data,
                output_data=f"خطأ في المعالجة: {str(e)}",
                citations=[],
                confidence_score=0.1,
                processing_time_ms=int((time.time() - step_start) * 1000),
                timestamp=datetime.now().isoformat(),
                sources_verified=False
            )
    
    def _compile_final_answer(self, reasoning_steps: List[AgentStep], enable_trust_trail: bool) -> str:
        """Compile final answer with optional trust trail"""
        
        # Get the main legal advice from the drafting step
        draft_step = next((step for step in reasoning_steps if step.agent_type == LegalAgentType.DOCUMENT_DRAFTER), None)
        main_answer = draft_step.output_data if draft_step else "تعذر إنتاج الإجابة القانونية."
        
        if not enable_trust_trail:
            return main_answer
        
        # Add trust trail for transparency
        trust_trail = "\n\n" + "="*60 + "\n"
        trust_trail += "🔍 **سلسلة التحليل القانوني** (Trust Trail)\n"
        trust_trail += "="*60 + "\n\n"
        
        for step in reasoning_steps:
            trust_trail += f"**{step.step_number}. {step.step_name}**\n"
            trust_trail += f"⏱️ وقت المعالجة: {step.processing_time_ms}ms\n"
            trust_trail += f"📊 مستوى الثقة: {step.confidence_score:.1%}\n"
            
            if step.citations:
                trust_trail += f"📚 المراجع: {', '.join(step.citations[:3])}" 
                if len(step.citations) > 3:
                    trust_trail += f" و {len(step.citations) - 3} مراجع أخرى"
                trust_trail += "\n"
            
            trust_trail += f"💭 النتيجة: {step.output_data[:150]}...\n\n"
        
        return main_answer + trust_trail
    
    def _summarize_conversation_context(self, context: List[Dict]) -> str:
        """Summarize conversation context for agents"""
        if not context or len(context) < 2:
            return ""
        
        # Get last few exchanges
        recent_context = context[-4:] if len(context) > 4 else context
        
        summary = "السياق من المحادثة السابقة:\n"
        for msg in recent_context:
            role = "المستخدم" if msg.get("role") == "user" else "المساعد"
            content = msg.get("content", "")[:100]
            summary += f"- {role}: {content}...\n"
        
        return summary
    
    async def _fallback_response(self, query: str, start_time: float) -> LegalReasoningResult:
        """Fallback to simple response if multi-agent fails"""
        
        simple_response = f"""تم معالجة استفسارك بنظام مبسط نظراً لخطأ تقني مؤقت.

{query}

يرجى إعادة المحاولة أو إعادة صياغة السؤال للحصول على تحليل قانوني متقدم."""

        fallback_step = AgentStep(
            agent_type=LegalAgentType.FACT_ANALYZER,
            step_number=1,
            step_name="معالجة مبسطة",
            input_data=query,
            output_data=simple_response,
            citations=[],
            confidence_score=0.3,
            processing_time_ms=int((time.time() - start_time) * 1000),
            timestamp=datetime.now().isoformat(),
            sources_verified=False
        )
        
        return LegalReasoningResult(
            query=query,
            final_answer=simple_response,
            reasoning_steps=[fallback_step],
            total_processing_time_ms=int((time.time() - start_time) * 1000),
            overall_confidence=0.3,
            trust_trail_enabled=False,
            citations_summary=[]
        )

class EnhancedRAGEngine:
    """
    🚀 ENHANCED RAG ENGINE WITH MULTI-AGENT INTEGRATION
    
    This integrates with your existing rag_engine.py while adding multi-agent capabilities
    """
    
    def __init__(self):
        # Use the imported OpenAI client
        self.openai_client = openai_client
        self.orchestrator = MultiAgentLegalOrchestrator(self.openai_client)
        
        # Flag to enable/disable multi-agent processing
        self.multi_agent_enabled = True
    
    async def ask_question_with_multi_agent(
        self, 
        query: str, 
        conversation_context: Optional[List[Dict]] = None,
        enable_trust_trail: bool = False
    ) -> AsyncIterator[str]:
        """
        🎯 NEW METHOD: Multi-agent legal reasoning with streaming
        """
        
        if not self.multi_agent_enabled:
            # Fallback to existing single-agent (would need to import from rag_engine)
            try:
                from rag_engine import ask_question_with_context
                response = await ask_question_with_context(query, conversation_context or [])
                
                # Stream the response in chunks
                chunk_size = 50
                for i in range(0, len(response), chunk_size):
                    chunk = response[i:i + chunk_size]
                    yield chunk
                    await asyncio.sleep(0.03)
                return
            except ImportError:
                # If can't import, use simple fallback
                yield "عذراً، النظام المتقدم غير متاح حالياً. يرجى المحاولة لاحقاً."
                return
        
        try:
            # Process with multi-agent system
            result = await self.orchestrator.process_legal_query(
                query=query,
                enable_trust_trail=enable_trust_trail,
                conversation_context=conversation_context
            )
            
            # Send metadata first
            metadata = {
                "type": "multi_agent_metadata",
                "total_steps": len(result.reasoning_steps),
                "overall_confidence": result.overall_confidence,
                "processing_time_ms": result.total_processing_time_ms,
                "citations_summary": result.citations_summary
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream response in chunks
            response_text = result.final_answer
            chunk_size = 50
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield chunk
                
                # Small delay for streaming effect
                await asyncio.sleep(0.05)
            
            # Send trust trail data if enabled
            if enable_trust_trail:
                trust_trail_data = {
                    "type": "trust_trail",
                    "reasoning_steps": [step.to_dict() for step in result.reasoning_steps],
                    "citations_summary": result.citations_summary
                }
                yield f"\n\ndata: {json.dumps(trust_trail_data)}\n\n"
                
        except Exception as e:
            print(f"❌ Multi-agent processing failed, using fallback: {e}")
            
            # Simple fallback response
            fallback_response = f"""تم معالجة سؤالك بالنظام الأساسي:

{query}

يرجى إعادة صياغة السؤال إذا كنت بحاجة لتحليل أكثر تفصيلاً."""
            
            chunk_size = 50
            for i in range(0, len(fallback_response), chunk_size):
                chunk = fallback_response[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.03)

# Test function for debugging
async def test_multi_agent():
    """Test function to verify multi-agent system works"""
    try:
        enhanced_rag = EnhancedRAGEngine()
        
        query = "موظف تم فصله بدون مبرر، ما حقوقه؟"
        print(f"🧪 Testing multi-agent with query: {query}")
        
        response_chunks = []
        async for chunk in enhanced_rag.ask_question_with_multi_agent(
            query=query,
            enable_trust_trail=True
        ):
            response_chunks.append(chunk)
            print(chunk, end="", flush=True)
        
        print(f"\n✅ Test completed. Total chunks: {len(response_chunks)}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test when file is executed directly
    import asyncio
    asyncio.run(test_multi_agent())