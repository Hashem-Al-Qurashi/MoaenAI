"""
Strategic Language Templates for Elite Legal Advocacy
Transforms technical analysis into warm, confident Saudi lawyer responses
"""

class StrategicLanguageTemplates:
    """Templates for injecting strategic lawyer personality"""
    
    # Confidence builders based on case strength
    CONFIDENCE_BUILDERS = {
        "strong": [
            "أخي الكريم، موقفك قوي جداً بنسبة {percentage}% والحمد لله",
            "لا تقلق أبداً، قضيتك في غاية القوة لأن {strength_reason}",
            "بشرى سارة، موقفك ممتاز وخصمك في وضع ضعيف جداً"
        ],
        "moderate": [
            "أخي، موقفك جيد بنسبة {percentage}% لكن نحتاج نقوي بعض النقاط",
            "الوضع مطمئن، وبإذن الله سنحوله لموقف قوي جداً",
            "عندك أساس ممتاز، ومع الأدلة الإضافية ستكون في موقف لا يُقهر"
        ],
        "weak": [
            "أخي لا تقلق، رغم التحديات لدينا استراتيجيات قوية",
            "الوضع يحتاج تقوية، لكن ثق بي - لدينا خيارات ممتازة",
            "موقفك أفضل مما تتصور، ومع الخطة الصحيحة سنحقق نتيجة ممتازة"
        ]
    }
    
    # Strategic framing
    STRATEGIC_FRAMES = {
        "opponent_weak": [
            "خصمك في موقف ضعيف جداً لأن {weakness_reason}",
            "الطرف الآخر يعتمد على {weak_evidence} وهذا لصالحك",
            "خصمك يحاول تضليل المحكمة بـ {false_claim} لكن سنفضحه"
        ],
        "evidence_strong": [
            "الأدلة التي معك {evidence_type} كافية لحسم القضية",
            "إثباتاتك ممتازة وخاصة {key_evidence}",
            "مع هذه الأدلة، خصمك لن يستطيع المجادلة"
        ],
        "next_action": [
            "استراتيجيتنا الآن بسيطة: {strategic_plan}",
            "الخطة واضحة - {action_steps} وبإذن الله ننتهي بالفوز",
            "معي خطوة بخطوة: {detailed_plan}"
        ]
    }
    
    # Emotional connection starters
    CONNECTION_STARTERS = [
        "أهلاً وسهلاً أخي، أنا هنا لحمايتك قانونياً",
        "حياك الله أخي، لا تقلق - سنحل هذا الموضوع بإذن الله",
        "مرحباً بك أخي الكريم، إن شاء الله نقف معك حتى النهاية"
    ]
    
    # Evidence requests (warm but strategic)
    EVIDENCE_REQUESTS = {
        "bank_transfer": "أخي، جهز لي كشف التحويل البنكي - هذا سيكون سلاحنا الأقوى",
        "contracts": "لو سمحت أرسل لي صورة من العقد - هذا سيدمر حجة خصمك",
        "messages": "شاركني رسائل الواتساب كاملة - حتى لو تبدو عادية، قد تكون مفيدة",
        "government_docs": "احضر لي الأوراق الحكومية - هذا سيثبت صدقك بشكل قاطع"
    }
    
    # Victory promises (confidence building)
    VICTORY_PROMISES = [
        "مع هذه الأدلة، بإذن الله سنفوز بسهولة",
        "ثق بي، خصمك سيندم على رفع هذه الدعوى",
        "إن شاء الله ستخرج من هذا منتصراً ومعوضاً",
        "بالأدلة اللي معنا، المحكمة ستكون في صالحك"
    ]

    @classmethod
    def get_confidence_response(cls, strength_level: str, percentage: int = None, reason: str = "") -> str:
        """Get confidence building response based on case strength"""
        import random
        templates = cls.CONFIDENCE_BUILDERS.get(strength_level, cls.CONFIDENCE_BUILDERS["moderate"])
        template = random.choice(templates)
        
        return template.format(
            percentage=percentage or (85 if strength_level == "strong" else 70 if strength_level == "moderate" else 60),
            strength_reason=reason
        )
    
    @classmethod  
    def get_strategic_frame(cls, frame_type: str, **kwargs) -> str:
        """Get strategic framing language"""
        import random
        templates = cls.STRATEGIC_FRAMES.get(frame_type, [])
        if not templates:
            return ""
        
        template = random.choice(templates)
        return template.format(**kwargs)
    
    @classmethod
    def get_connection_starter(cls) -> str:
        """Get warm connection starter"""
        import random
        return random.choice(cls.CONNECTION_STARTERS)
    
    @classmethod
    def get_evidence_request(cls, evidence_type: str) -> str:
        """Get strategic evidence request"""
        return cls.EVIDENCE_REQUESTS.get(evidence_type, 
            "أخي، لو تقدر تشاركني هذا المستند، سيقوي موقفنا كثيراً")
    
    @classmethod
    def get_victory_promise(cls) -> str:
        """Get confidence-building victory promise"""
        import random
        return random.choice(cls.VICTORY_PROMISES)