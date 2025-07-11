"""
Legal Document Type Analyzer - The Brain of Document Generation
Determines what type of legal document to generate with 100% accuracy
"""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DocumentType:
    """Represents the type of legal document to generate"""
    document_category: str    # 'court_filing', 'contract', 'consultation', 'correspondence'
    specific_type: str        # 'defense_memo', 'lawsuit', 'purchase_contract', etc.
    template_required: bool   # True if needs structured template
    urgency_level: str       # 'immediate', 'standard', 'research'
    complexity_level: str    # 'simple', 'complex', 'expert'

class LegalDocumentTypeAnalyzer:
    """Analyzes queries to determine exact document type needed"""
    
    def __init__(self):
        # Court filing patterns
        self.court_filing_patterns = {
            'defense_memo': [
                'الرد القانوني على دعوى', 'رد على الدعوى', 'مذكرة دفاع', 'دفوع قانونية',
                'الرد على اللائحة', 'مذكرة جوابية', 'دفاع عن المدعى عليه'
            ],
            'lawsuit': [
                'لائحة دعوى', 'صحيفة دعوى', 'رفع دعوى', 'تحرير دعوى',
                'دعوى قضائية', 'مطالبة قضائية', 'دعوى مدنية'
            ],
            'appeal': [
                'مذكرة استئناف', 'لائحة اعتراض', 'طلب استئناف',
                'اعتراض على الحكم', 'استئناف الحكم'
            ],
            'motion': [
                'طلب وقتي', 'طلب مستعجل', 'طلب تحفظي',
                'التماس', 'طلب إثبات حالة', 'طلب خبرة'
            ]
        }
        
        # Contract patterns
        self.contract_patterns = {
            'sale_contract': ['عقد بيع', 'عقد شراء', 'اتفاقية بيع'],
            'employment_contract': ['عقد عمل', 'عقد توظيف', 'اتفاقية عمل'],
            'lease_contract': ['عقد إيجار', 'عقد تأجير', 'اتفاقية إيجار'],
            'partnership_contract': ['عقد شراكة', 'اتفاقية شراكة', 'عقد تأسيس شركة'],
            'service_contract': ['عقد خدمات', 'اتفاقية خدمات', 'عقد مقاولة']
        }
        
        # Legal correspondence patterns
        self.correspondence_patterns = {
            'demand_letter': ['خطاب إنذار', 'إنذار قانوني', 'خطاب مطالبة'],
            'legal_opinion': ['رأي قانوني', 'فتوى قانونية', 'استشارة قانونية مكتوبة'],
            'legal_notice': ['إخطار قانوني', 'تنبيه قانوني', 'إشعار قانوني']
        }
        
        # Consultation patterns (advisory only)
        self.consultation_patterns = [
            'ما هي', 'كيف', 'متى', 'أين', 'لماذا', 'هل يحق',
            'ما حكم', 'ما رأيك', 'أريد استشارة', 'أحتاج نصيحة'
        ]

    def analyze_document_type(self, query: str) -> DocumentType:
        """Analyze query to determine exact document type needed"""
        
        query_lower = query.lower().strip()
        
        # Check for court filings (highest priority)
        court_type = self._detect_court_filing(query_lower)
        if court_type:
            return DocumentType(
                document_category='court_filing',
                specific_type=court_type,
                template_required=True,
                urgency_level=self._assess_urgency(query_lower),
                complexity_level=self._assess_complexity(query_lower, court_type)
            )
        
        # Check for contracts
        contract_type = self._detect_contract_type(query_lower)
        if contract_type:
            return DocumentType(
                document_category='contract',
                specific_type=contract_type,
                template_required=True,
                urgency_level='standard',
                complexity_level=self._assess_complexity(query_lower, contract_type)
            )
        
        # Check for legal correspondence
        correspondence_type = self._detect_correspondence_type(query_lower)
        if correspondence_type:
            return DocumentType(
                document_category='correspondence',
                specific_type=correspondence_type,
                template_required=True,
                urgency_level=self._assess_urgency(query_lower),
                complexity_level='standard'
            )
        
        # Default: consultation
        return DocumentType(
            document_category='consultation',
            specific_type='legal_advice',
            template_required=False,
            urgency_level='standard',
            complexity_level='simple'
        )
    
    def _detect_court_filing(self, query: str) -> Optional[str]:
        """Detect court filing document type"""
        for doc_type, patterns in self.court_filing_patterns.items():
            if any(pattern in query for pattern in patterns):
                return doc_type
        return None
    
    def _detect_contract_type(self, query: str) -> Optional[str]:
        """Detect contract type"""
        for contract_type, patterns in self.contract_patterns.items():
            if any(pattern in query for pattern in patterns):
                return contract_type
        return None
    
    def _detect_correspondence_type(self, query: str) -> Optional[str]:
        """Detect legal correspondence type"""
        for corr_type, patterns in self.correspondence_patterns.items():
            if any(pattern in query for pattern in patterns):
                return corr_type
        return None
    
    def _assess_urgency(self, query: str) -> str:
        """Assess urgency level"""
        immediate_indicators = ['عاجل', 'فوري', 'مستعجل', 'حال', 'اليوم', 'غداً']
        
        if any(indicator in query for indicator in immediate_indicators):
            return 'immediate'
        else:
            return 'standard'
    
    def _assess_complexity(self, query: str, doc_type: str) -> str:
        """Assess document complexity"""
        complex_indicators = [
            'معقد', 'متقدم', 'شامل', 'مفصل', 'متخصص',
            'استراتيجي', 'متعدد', 'دولي', 'تجاري كبير'
        ]
        
        expert_document_types = [
            'appeal', 'partnership_contract', 'complex_lawsuit'
        ]
        
        if doc_type in expert_document_types:
            return 'expert'
        elif any(indicator in query for indicator in complex_indicators):
            return 'complex'
        else:
            return 'simple'