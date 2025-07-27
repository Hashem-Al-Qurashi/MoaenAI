from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json

class ComplexityLevel(Enum):
    """Complexity levels for legal analysis"""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate" 
    COMPLEX = "complex"
    EXPERT = "expert"

class LegalContext(Enum):
    """Legal context types for specialized prompting"""
    INDIVIDUAL_RIGHTS = "individual_rights"
    BUSINESS_LEGAL = "business_legal"
    CRIMINAL_MATTER = "criminal_matter"
    CIVIL_DISPUTE = "civil_dispute"
    ADMINISTRATIVE_LAW = "administrative_law"
    TAX_COMPLIANCE = "tax_compliance"

@dataclass
class PromptConfiguration:
    """Configuration for dynamic prompt generation"""
    complexity_level: ComplexityLevel
    legal_context: LegalContext
    intent_type: str
    user_sophistication: str  # novice, intermediate, expert
    urgency_level: str  # low, medium, high, critical
    citation_depth: str  # basic, detailed, comprehensive
    format_style: str  # explanation, memo, brief, motion

class ComplexityAwareAgentSystem:
    """
    🎯 INDUSTRIAL-STRENGTH COMPLEXITY-AWARE AGENT SYSTEM
    
    Dynamically adjusts agent behavior based on:
    - Query complexity level (simple → expert)
    - Legal context and domain
    - User sophistication level
    - Urgency and risk factors
    - Required citation depth
    - Output format requirements
    """
    
    def __init__(self):
        self.prompt_templates = self._initialize_prompt_templates()
        self.complexity_indicators = self._initialize_complexity_indicators()
        self.sophistication_markers = self._initialize_sophistication_markers()
    
    def generate_adaptive_prompt(
        self,
        agent_type: str,  # Changed from LegalAgentType to avoid circular import
        base_query: str,
        validation_result: Dict,
        conversation_context: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate sophisticated, adaptive prompts based on multiple factors
        """
        
        # Analyze query characteristics
        config = self._analyze_prompt_requirements(
            base_query, validation_result, conversation_context
        )
        
        # Generate prompt based on agent type and configuration
        if agent_type == "fact_analyzer":
            return self._generate_fact_analyzer_prompt(config, base_query)
        elif agent_type == "legal_researcher":
            return self._generate_legal_researcher_prompt(config, base_query)
        elif agent_type == "argument_builder":
            return self._generate_argument_builder_prompt(config, base_query)
        elif agent_type == "document_drafter":
            return self._generate_document_drafter_prompt(config, base_query)
        elif agent_type == "citation_validator":
            return self._generate_citation_validator_prompt(config, base_query)
        else:
            return self._generate_generic_prompt(config, base_query, agent_type)
    
    def _analyze_prompt_requirements(
        self,
        query: str,
        validation_result: Dict,
        context: Optional[List[Dict]] = None
    ) -> PromptConfiguration:
        """Analyze query to determine optimal prompt configuration"""
        
        # Extract complexity from validation result
        complexity_level = ComplexityLevel(validation_result.get('complexity_level', 'simple'))
        
        # Determine legal context
        legal_context = self._detect_legal_context(query, validation_result)
        
        # Assess user sophistication from conversation patterns
        user_sophistication = self._assess_user_sophistication(query, context)
        
        # Detect urgency indicators
        urgency_level = self._detect_urgency_level(query, context)
        
        # Determine required citation depth
        citation_depth = self._determine_citation_depth(complexity_level, user_sophistication)
        
        # Choose optimal format style
        format_style = self._choose_format_style(
            validation_result.get('recommended_intents', []),
            complexity_level
        )
        
        return PromptConfiguration(
            complexity_level=complexity_level,
            legal_context=legal_context,
            intent_type=validation_result.get('recommended_intents', ['legal_consultation'])[0],
            user_sophistication=user_sophistication,
            urgency_level=urgency_level,
            citation_depth=citation_depth,
            format_style=format_style
        )
    
    def _generate_fact_analyzer_prompt(self, config: PromptConfiguration, query: str) -> str:
        """Generate sophisticated fact analyzer prompts"""
        
        base_template = self.prompt_templates['fact_analyzer'][config.complexity_level]
        
        # Customize based on legal context
        context_instructions = self._get_context_specific_instructions(
            'fact_analyzer', config.legal_context
        )
        
        # Customize based on user sophistication
        sophistication_adjustments = self._get_sophistication_adjustments(
            'fact_analyzer', config.user_sophistication
        )
        
        # Add urgency-specific guidance
        urgency_instructions = self._get_urgency_instructions(config.urgency_level)
        
        return f"""{base_template}

{context_instructions}

{sophistication_adjustments}

{urgency_instructions}

**الاستفسار المطلوب تحليله:**
{query}

**متطلبات الأداء حسب مستوى التعقيد ({config.complexity_level.value}):**
{self._get_performance_requirements('fact_analyzer', config.complexity_level)}

**تعليمات الصياغة:**
{self._get_formatting_instructions(config.format_style, config.user_sophistication)}"""
    
    def _generate_legal_researcher_prompt(self, config: PromptConfiguration, query: str) -> str:
        """Generate sophisticated legal researcher prompts"""
        
        base_template = self.prompt_templates['legal_researcher'][config.complexity_level]
        
        # Advanced research instructions based on complexity
        research_depth = {
            ComplexityLevel.SIMPLE: "التركيز على الأحكام الأساسية والمواد الرئيسية",
            ComplexityLevel.INTERMEDIATE: "البحث في السوابق القضائية والتفسيرات الرسمية",
            ComplexityLevel.COMPLEX: "تحليل متقدم للسوابق + اللوائح التنفيذية + التطبيقات العملية",
            ComplexityLevel.EXPERT: "بحث شامل يتضمن الفقه القانوني + المذكرات التفسيرية + القرارات الإدارية"
        }
        
        citation_requirements = {
            'basic': "ذكر أرقام المواد الأساسية فقط",
            'detailed': "استشهاد كامل بالمواد + أرقام القرارات + التواريخ",
            'comprehensive': "مراجع شاملة تتضمن النصوص الأصلية + التفسيرات + السوابق"
        }
        
        return f"""{base_template}

**عمق البحث المطلوب:**
{research_depth[config.complexity_level]}

**متطلبات الاستشهاد:**
{citation_requirements[config.citation_depth]}

**السياق القانوني المتخصص:**
{self._get_context_specific_instructions('legal_researcher', config.legal_context)}

**الاستفسار:**
{query}

**معايير جودة البحث:**
- دقة المراجع: 95%+ للمواد الأساسية
- حداثة المعلومات: آخر التعديلات النظامية
- شمولية التغطية: {self._get_coverage_requirements(config.complexity_level)}
- عمق التحليل: {config.complexity_level.value}

**تحذيرات خاصة:**
{self._get_research_warnings(config.legal_context)}"""
    
    def _generate_argument_builder_prompt(self, config: PromptConfiguration, query: str) -> str:
        """Generate sophisticated argument builder prompts"""
        
        argument_strategies = {
            ComplexityLevel.SIMPLE: "بناء حجة واحدة قوية مع دليل واضح",
            ComplexityLevel.INTERMEDIATE: "تطوير 2-3 حجج متدرجة القوة مع الأدلة الداعمة",
            ComplexityLevel.COMPLEX: "بناء استراتيجية قانونية متعددة المستويات مع حجج أساسية ومساندة",
            ComplexityLevel.EXPERT: "تطوير نظرية قانونية شاملة مع حجج متشابكة ودفوع متقدمة"
        }
        
        risk_analysis_depth = {
            'low': "تحليل المخاطر الأساسية",
            'medium': "تقييم المخاطر + خطط التخفيف",
            'high': "تحليل شامل للمخاطر + استراتيجيات متعددة",
            'critical': "تحليل متقدم للمخاطر + خطط طوارئ + بدائل متعددة"
        }
        
        return f"""أنت محام خبير في بناء الحجج القانونية المتقدمة.

**استراتيجية البناء حسب التعقيد:**
{argument_strategies[config.complexity_level]}

**تحليل المخاطر المطلوب:**
{risk_analysis_depth[config.urgency_level]}

**السياق القانوني:**
{config.legal_context.value}

**نوع الاستفسار:**
{config.intent_type}

**الاستفسار:**
{query}

**معايير بناء الحجج:**
1. **القوة القانونية:** كل حجة يجب أن تكون مدعومة بنص صريح
2. **التسلسل المنطقي:** ترتيب الحجج من الأقوى للأضعف
3. **الأدلة الداعمة:** ربط كل حجة بسوابق أو نصوص محددة
4. **التنبؤ بالاعتراضات:** توقع نقاط الضعف المحتملة

**مستوى التعقيد المطلوب:**
{self._get_argument_complexity_requirements(config.complexity_level)}

**تنسيق المخرجات:**
{self._get_argument_formatting_requirements(config.format_style)}

**معايير الجودة:**
- وضوح الحجج: 95%+
- قوة الأدلة: {self._get_evidence_strength_requirement(config.complexity_level)}
- اكتمال التحليل: شامل لجميع الجوانب ذات الصلة"""
    
    def _generate_document_drafter_prompt(self, config: PromptConfiguration, query: str) -> str:
        """Generate sophisticated document drafter prompts"""
        
        format_specifications = {
            'explanation': {
                ComplexityLevel.SIMPLE: "شرح مبسط بلغة واضحة للمواطن العادي",
                ComplexityLevel.INTERMEDIATE: "تحليل متوسط يوازن بين الوضوح والدقة القانونية",
                ComplexityLevel.COMPLEX: "تحليل قانوني متقدم بمصطلحات مهنية دقيقة",
                ComplexityLevel.EXPERT: "تحليل خبير يستخدم الفقه القانوني والنظريات المتقدمة"
            },
            'memo': {
                ComplexityLevel.SIMPLE: "مذكرة قصيرة تركز على النقاط الأساسية",
                ComplexityLevel.INTERMEDIATE: "مذكرة متوسطة تغطي الجوانب الرئيسية مع أدلة داعمة",
                ComplexityLevel.COMPLEX: "مذكرة قانونية شاملة بتنظيم هرمي ومراجع متقدمة",
                ComplexityLevel.EXPERT: "مذكرة متخصصة بمستوى محكمة التمييز مع فقه قانوني"
            },
            'brief': {
                ComplexityLevel.SIMPLE: "ملخص تنفيذي بنقاط واضحة",
                ComplexityLevel.COMPLEX: "مذكرة إجرائية متقدمة للمحكمة"
            },
            'motion': {
                ComplexityLevel.COMPLEX: "لائحة دعوى مفصلة مع طلبات محددة",
                ComplexityLevel.EXPERT: "مذكرة إجرائية متخصصة بمستوى محكمة عليا"
            }
        }

        user_language_levels = {
            'novice': "استخدم لغة بسيطة وتجنب المصطلحات المعقدة",
            'intermediate': "استخدم مصطلحات قانونية أساسية مع الشرح",
            'expert': "استخدم المصطلحات القانونية الدقيقة والتقنية"
        }

        return f"""أنت محام خبير في صياغة الوثائق القانونية المتقدمة.

**مواصفات التنسيق:**
{format_specifications.get(config.format_style, {}).get(config.complexity_level, "تنسيق قانوني احترافي")}

**مستوى اللغة المطلوب:**
{user_language_levels[config.user_sophistication]}

**السياق القانوني المتخصص:**
{self._get_context_specific_instructions('document_drafter', config.legal_context)}

**نوع الوثيقة المطلوبة:**
{config.format_style}

**الاستفسار:**
{query}

**معايير الصياغة حسب التعقيد:**
{self._get_drafting_standards(config.complexity_level)}

**متطلبات الهيكل:**
{self._get_structure_requirements(config.format_style, config.complexity_level)}

**معايير الجودة:**
- دقة قانونية: 98%+
- وضوح التعبير: مناسب للمستوى المحدد
- اكتمال المحتوى: شامل لجميع الجوانب المطلوبة
- احترافية الصياغة: مستوى {config.complexity_level.value}

**تعليمات خاصة بالسياق:**
{self._get_context_specific_drafting_rules(config.legal_context)}"""

    def _generate_citation_validator_prompt(self, config: PromptConfiguration, query: str) -> str:
        """Generate sophisticated citation validator prompts"""
        
        validation_standards = {
            ComplexityLevel.SIMPLE: "التحقق من صحة المواد الأساسية المذكورة",
            ComplexityLevel.INTERMEDIATE: "التحقق من المواد + التأكد من التواريخ والأرقام",
            ComplexityLevel.COMPLEX: "فحص شامل للمراجع + التحقق من السوابق + مطابقة النصوص",
            ComplexityLevel.EXPERT: "تدقيق خبير يشمل الفقه القانوني + المذكرات التفسيرية + التحليل النقدي"
        }
        
        return f"""أنت خبير في تدقيق وتحليل المراجع القانونية.

**معايير التحقق حسب التعقيد:**
{validation_standards[config.complexity_level]}

**عمق التحقق المطلوب:**
{config.citation_depth}

**السياق القانوني:**
{config.legal_context.value}

**الاستفسار الأصلي:**
{query}

**معايير التدقيق الصارمة:**
1. **صحة النصوص:** التأكد من وجود المواد المذكورة فعلياً
2. **دقة الأرقام:** مطابقة أرقام المواد والقرارات
3. **حداثة المراجع:** التأكد من عدم نسخ أو تعديل النصوص
4. **مدى الصلة:** تقييم ارتباط كل مرجع بالموضوع

**نظام التقييم:**
- صحيح تماماً: 🟢
- صحيح مع ملاحظات: 🟡
- مشكوك فيه: 🟠
- خطأ: 🔴

**تقرير التحقق يجب أن يشمل:**
{self._get_validation_report_requirements(config.complexity_level)}

**تحذيرات خاصة بالسياق:**
{self._get_validation_warnings(config.legal_context)}"""

    # Initialization methods
    def _initialize_prompt_templates(self) -> Dict:
        """Initialize base prompt templates for each agent type and complexity level"""
        return {
            'fact_analyzer': {
                ComplexityLevel.SIMPLE: """أنت محلل وقائع قانوني يركز على الأساسيات.
مهمتك: استخراج الوقائع الرئيسية بلغة واضحة ومباشرة.""",
                
                ComplexityLevel.INTERMEDIATE: """أنت محلل وقائع قانوني متمرس.
مهمتك: تحليل متعمق للوقائع مع ربطها بالسياق القانوني والنظامي.""",
                
                ComplexityLevel.COMPLEX: """أنت محلل وقائع قانوني خبير متخصص في القضايا المعقدة.
مهمتك: تحليل شامل ومتطور للوقائع مع التركيز على التعقيدات القانونية والنظامية.""",
                
                ComplexityLevel.EXPERT: """أنت خبير تحليل وقائع بمستوى أكاديمي قانوني متقدم.
مهمتك: تحليل نقدي متطور للوقائع مع تطبيق النظريات القانونية المتقدمة."""
            },
            'legal_researcher': {
                ComplexityLevel.SIMPLE: """أنت باحث قانوني يركز على المراجع الأساسية.
مهمتك: العثور على النصوص القانونية الواضحة والمباشرة.""",
                
                ComplexityLevel.INTERMEDIATE: """أنت باحث قانوني متمرس في الأنظمة السعودية.
مهمتك: بحث متعمق في النصوص والسوابق ذات الصلة.""",
                
                ComplexityLevel.COMPLEX: """أنت باحث قانوني خبير متخصص في البحث المتقدم.
مهمتك: بحث شامل يتضمن السوابق واللوائح التنفيذية والتفسيرات الرسمية.""",
                
                ComplexityLevel.EXPERT: """أنت خبير بحث قانوني بمستوى أكاديمي متقدم.
مهمتك: بحث متطور يشمل الفقه القانوني والدراسات المقارنة."""
            }
        }
    
    def _initialize_complexity_indicators(self) -> Dict:
        """Initialize indicators that help determine complexity level"""
        return {
            'simple_indicators': [
                'ما هي', 'ما هو', 'كيف', 'هل يمكن', 'هل يجوز'
            ],
            'intermediate_indicators': [
                'ما الإجراءات', 'ما المطلوب', 'كيفية التعامل', 'ما العواقب'
            ],
            'complex_indicators': [
                'نزاع', 'دعوى', 'مقاضاة', 'استئناف', 'تحكيم', 'خلاف قانوني'
            ],
            'expert_indicators': [
                'تفسير دستوري', 'فقه قانوني', 'نظرية قانونية', 'تحليل مقارن'
            ]
        }
    
    def _initialize_sophistication_markers(self) -> Dict:
        """Initialize markers that indicate user sophistication level"""
        return {
            'novice_markers': [
                'لا أفهم', 'ما معنى', 'اشرح لي', 'بلغة بسيطة'
            ],
            'intermediate_markers': [
                'المادة', 'النظام', 'القانون', 'اللائحة'
            ],
            'expert_markers': [
                'الفقه', 'السابقة القضائية', 'التفسير', 'الاجتهاد'
            ]
        }

    # Analysis methods
    def _detect_legal_context(self, query: str, validation_result: Dict) -> LegalContext:
        """Detect the specific legal context"""
        query_lower = query.lower()
        
        # Tax and administrative law
        if any(word in query_lower for word in ['ضريبة', 'زكاة', 'جمارك', 'هيئة']):
            return LegalContext.TAX_COMPLIANCE
        
        # Criminal matters
        if any(word in query_lower for word in ['جريمة', 'عقوبة', 'سجن', 'غرامة']):
            return LegalContext.CRIMINAL_MATTER
        
        # Business legal
        if any(word in query_lower for word in ['شركة', 'تجاري', 'استثمار', 'عقد']):
            return LegalContext.BUSINESS_LEGAL
        
        # Individual rights
        if any(word in query_lower for word in ['حقوق', 'موظف', 'عامل', 'مستهلك']):
            return LegalContext.INDIVIDUAL_RIGHTS
        
        # Civil disputes
        if any(word in query_lower for word in ['نزاع', 'دعوى', 'خلاف', 'مقاضاة']):
            return LegalContext.CIVIL_DISPUTE
        
        return LegalContext.ADMINISTRATIVE_LAW  # Default
    
    def _assess_user_sophistication(self, query: str, context: Optional[List[Dict]]) -> str:
        """Assess user's legal sophistication level"""
        query_lower = query.lower()
        
        # Check for expert markers
        if any(marker in query_lower for marker in self.sophistication_markers['expert_markers']):
            return 'expert'
        
        # Check for intermediate markers
        if any(marker in query_lower for marker in self.sophistication_markers['intermediate_markers']):
            return 'intermediate'
        
        # Check conversation context
        if context:
            combined_context = ' '.join([msg.get('content', '') for msg in context])
            if any(marker in combined_context.lower() for marker in self.sophistication_markers['expert_markers']):
                return 'expert'
        
        return 'novice'  # Default to novice for safety
    
    def _detect_urgency_level(self, query: str, context: Optional[List[Dict]]) -> str:
        """Detect urgency level from query and context"""
        query_lower = query.lower()
        
        critical_indicators = ['عاجل', 'فوري', 'طارئ', 'خلال ساعات']
        high_indicators = ['سريع', 'بسرعة', 'قريباً', 'خلال أيام']
        medium_indicators = ['قريب', 'خلال أسبوع', 'قبل الموعد']
        
        if any(indicator in query_lower for indicator in critical_indicators):
            return 'critical'
        elif any(indicator in query_lower for indicator in high_indicators):
            return 'high'
        elif any(indicator in query_lower for indicator in medium_indicators):
            return 'medium'
        else:
            return 'low'
    
    def _determine_citation_depth(self, complexity_level: ComplexityLevel, user_sophistication: str) -> str:
        """Determine required citation depth"""
        if complexity_level == ComplexityLevel.EXPERT or user_sophistication == 'expert':
            return 'comprehensive'
        elif complexity_level == ComplexityLevel.COMPLEX or user_sophistication == 'intermediate':
            return 'detailed'
        else:
            return 'basic'
    
    def _choose_format_style(self, intents: List[str], complexity_level: ComplexityLevel) -> str:
        """Choose optimal format style"""
        if complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT]:
            if 'legal_dispute' in intents:
                return 'memo'
            elif 'procedure_guide' in intents:
                return 'brief'
        
        return 'explanation'  # Default
    
    # Helper methods for generating specific instruction sections
    def _get_context_specific_instructions(self, agent_type: str, legal_context: LegalContext) -> str:
        """Get context-specific instructions for each agent type"""
        instructions = {
            'fact_analyzer': {
                LegalContext.TAX_COMPLIANCE: "ركز على الالتزامات الضريبية والمهل الزمنية والجهات المختصة",
                LegalContext.CRIMINAL_MATTER: "حدد العناصر الإجرامية والأطراف والأدلة المحتملة",
                LegalContext.BUSINESS_LEGAL: "اهتم بالجوانب التجارية والتنظيمية والمخاطر القانونية",
                LegalContext.INDIVIDUAL_RIGHTS: "ركز على الحقوق الشخصية وآليات الحماية والجهات المختصة",
                LegalContext.CIVIL_DISPUTE: "حدد الأطراف والخلاف والأضرار المحتملة والأدلة",
                LegalContext.ADMINISTRATIVE_LAW: "اهتم بالإجراءات الإدارية والجهات الحكومية والقرارات"
            }
        }
        
        return instructions.get(agent_type, {}).get(legal_context, "اتبع المعايير القانونية العامة")
    
    def _get_sophistication_adjustments(self, agent_type: str, user_sophistication: str) -> str:
        """Get adjustments based on user sophistication"""
        if user_sophistication == 'expert':
            return "استخدم المصطلحات القانونية الدقيقة والتحليل المتطور"
        elif user_sophistication == 'intermediate':
            return "استخدم مصطلحات قانونية أساسية مع شرح موجز"
        else:
            return "استخدم لغة واضحة وتجنب المصطلحات المعقدة"
    
    def _get_urgency_instructions(self, urgency_level: str) -> str:
        """Get urgency-specific instructions"""
        if urgency_level == 'critical':
            return "⚡ **عاجل:** ركز على الإجراءات الفورية والمواعيد الحرجة"
        elif urgency_level == 'high':
            return "🔥 **مستعجل:** أعط أولوية للخطوات العاجلة والمهل القريبة"
        elif urgency_level == 'medium':
            return "⏰ **متوسط الأولوية:** اذكر المواعيد والإجراءات المطلوبة"
        else:
            return "📋 **معلومات عامة:** قدم تحليلاً شاملاً ومتوازناً"
    
    def _get_performance_requirements(self, agent_type: str, complexity_level: ComplexityLevel) -> str:
        """Get performance requirements based on complexity"""
        requirements = {
            ComplexityLevel.SIMPLE: "تحليل أساسي يركز على النقاط الواضحة",
            ComplexityLevel.INTERMEDIATE: "تحليل متوسط يغطي الجوانب الرئيسية",
            ComplexityLevel.COMPLEX: "تحليل شامل يتضمن التعقيدات والاستثناءات",
            ComplexityLevel.EXPERT: "تحليل متطور بمستوى أكاديمي ومهني عالي"
        }
        return requirements[complexity_level]
    
    def _get_formatting_instructions(self, format_style: str, user_sophistication: str) -> str:
        """Get formatting instructions"""
        if format_style == 'memo':
            return "استخدم تنسيق المذكرة القانونية المهنية مع العناوين والترقيم"
        elif format_style == 'brief':
            return "اتبع تنسيق الملخص التنفيذي بنقاط واضحة ومحددة"
        else:
            return "استخدم تنسيق الشرح التدريجي بفقرات منظمة"