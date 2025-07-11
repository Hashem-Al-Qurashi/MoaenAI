"""
Legal Issue Analyzer - Stage 1 of Legal Reasoning Engine
Analyzes user queries to understand the legal context and required advice type
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class LegalIssue:
    """Represents analyzed legal issue from user query"""
    issue_type: str          # 'criminal_procedure', 'contract_dispute', 'employment_law', etc.
    legal_domain: str        # 'criminal', 'civil', 'commercial', 'administrative'
    user_position: str       # 'defendant', 'plaintiff', 'seeking_advice', 'compliance'
    urgency_level: str       # 'emergency', 'planning', 'research'
    advice_type: str         # 'defense_strategy', 'procedural_guide', 'rights_explanation'


class LegalIssueAnalyzer:
    """
    Analyzes legal queries to understand context and required advice type
    This is the foundation for targeted legal reasoning
    """
    
    def __init__(self):
        """Initialize with legal pattern recognition"""
        
        # Criminal law indicators
        self.criminal_patterns = {
            'keywords': ['سجين', 'موقوف', 'متهم', 'جريمة', 'عقوبة', 'قصاص', 'حد', 'تعزير', 'جزائية'],
            'procedures': ['حضور', 'جلسة', 'محاكمة', 'استجواب', 'تحقيق']
        }
        
        # Civil law indicators  
        self.civil_patterns = {
            'keywords': ['دعوى', 'مرافعة', 'خصومة', 'استئناف', 'طعن', 'تبليغ', 'مدنية'],
            'procedures': ['تقديم', 'رفع', 'إجراءات', 'موعد']
        }
        
        # Contract/Commercial indicators
        self.contract_patterns = {
            'keywords': ['قرض', 'عقد', 'اتفاق', 'شركة', 'تجارة', 'استثمار', 'أعمال'],
            'disputes': ['نزاع', 'خلاف', 'مطالبة', 'رد', 'تعويض']
        }
        
        # Employment law indicators
        self.employment_patterns = {
            'keywords': ['عمل', 'عامل', 'موظف', 'راتب', 'أجر', 'إجازة', 'وظيفة', 'صاحب'],
            'issues': ['حقوق', 'التزامات', 'فصل', 'استقالة']
        }
        
        # Administrative law indicators
        self.administrative_patterns = {
            'keywords': ['ترخيص', 'تصريح', 'شروط', 'متطلبات', 'محاماة', 'مزاولة'],
            'procedures': ['تقديم', 'حصول', 'تجديد']
        }

    async def analyze_issue(self, query: str) -> LegalIssue:
        """
        Analyze user query to determine legal context
        
        Args:
            query: User's legal question
            
        Returns:
            LegalIssue object with analyzed context
        """
        
        query_lower = query.lower()
        
        # Determine issue type and domain
        issue_type, legal_domain = self._classify_issue_type(query_lower)
        
        # Determine user position
        user_position = self._determine_user_position(query_lower, issue_type)
        
        # Determine urgency level
        urgency_level = self._assess_urgency(query_lower)
        
        # Determine advice type needed
        advice_type = self._determine_advice_type(query_lower, user_position)
        
        return LegalIssue(
            issue_type=issue_type,
            legal_domain=legal_domain,
            user_position=user_position,
            urgency_level=urgency_level,
            advice_type=advice_type
        )
    
    def _classify_issue_type(self, query: str) -> tuple[str, str]:
        """Classify the type of legal issue"""
        
        # Check criminal law
        criminal_score = self._calculate_pattern_score(query, self.criminal_patterns)
        
        # Check civil law
        civil_score = self._calculate_pattern_score(query, self.civil_patterns)
        
        # Check contract law
        contract_score = self._calculate_pattern_score(query, self.contract_patterns)
        
        # Check employment law
        employment_score = self._calculate_pattern_score(query, self.employment_patterns)
        
        # Check administrative law
        admin_score = self._calculate_pattern_score(query, self.administrative_patterns)
        
        # Determine highest scoring category
        scores = {
            'criminal_procedure': (criminal_score, 'criminal'),
            'civil_procedure': (civil_score, 'civil'),
            'contract_dispute': (contract_score, 'commercial'),
            'employment_law': (employment_score, 'commercial'),
            'administrative_law': (admin_score, 'administrative')
        }
        
        best_match = max(scores.items(), key=lambda x: x[1][0])
        
        if best_match[1][0] > 0:
            return best_match[0], best_match[1][1]
        else:
            return 'general_legal', 'general'
    
    def _calculate_pattern_score(self, query: str, patterns: Dict) -> int:
        """Calculate how well query matches legal patterns"""
        score = 0
        
        for pattern_group in patterns.values():
            for pattern in pattern_group:
                if pattern in query:
                    score += 1
        
        return score
    
    def _determine_user_position(self, query: str, issue_type: str) -> str:
        """Determine user's position in legal matter"""
        
        # Defense indicators
        defense_indicators = ['مدعى عليه', 'متهم', 'رد على', 'دفاع', 'دفع']
        
        # Plaintiff indicators  
        plaintiff_indicators = ['مدعي', 'شاكي', 'رفع دعوى', 'مقاضاة']
        
        # Advice seeking indicators
        advice_indicators = ['ما هي', 'كيف', 'ماذا', 'متى', 'شروط', 'إجراءات']
        
        if any(indicator in query for indicator in defense_indicators):
            return 'defendant'
        elif any(indicator in query for indicator in plaintiff_indicators):
            return 'plaintiff'
        elif any(indicator in query for indicator in advice_indicators):
            return 'seeking_advice'
        else:
            return 'general_inquiry'
    
    def _assess_urgency(self, query: str) -> str:
        """Assess urgency level of legal matter"""
        
        # Emergency indicators
        emergency_indicators = ['عاجل', 'فوري', 'حال', 'أمس', 'غد', 'اليوم']
        
        # Planning indicators
        planning_indicators = ['أريد', 'أنوي', 'سأقوم', 'تخطيط', 'مستقبل']
        
        if any(indicator in query for indicator in emergency_indicators):
            return 'emergency'
        elif any(indicator in query for indicator in planning_indicators):
            return 'planning'
        else:
            return 'research'
    
    def _determine_advice_type(self, query: str, user_position: str) -> str:
        """Determine what type of legal advice is needed"""
        
        if user_position == 'defendant':
            return 'defense_strategy'
        elif user_position == 'plaintiff':
            return 'action_strategy'
        elif 'شروط' in query or 'متطلبات' in query:
            return 'compliance_guide'
        elif 'حقوق' in query or 'التزامات' in query:
            return 'rights_explanation'
        elif 'إجراءات' in query or 'كيف' in query:
            return 'procedural_guide'
        else:
            return 'general_advice'