class EliteLegalClassifier:
    """Elite classifier for Saudi legal content"""
    
    def __init__(self):
        self.legislation_patterns = [
            r'نظام\s+[المحاماة|العمل|الإجراءات|الإثبات|التكاليف]',
            r'المرسوم\s+الملكي\s+رقم',
            r'الباب\s+[الأول|الثاني|الثالث|\d+]',
            r'المادة\s+[الأولى|الثانية|الثالثة|\d+]',
            r'اللائحة\s+التنفيذية'
        ]
        
        self.court_patterns = [
            r'محكمة\s+[الرياض|جدة|الدمام|مكة]',
            r'قرار\s+رقم\s+\d+',
            r'الحكم\s+الصادر',
            r'محكمة\s+[التمييز|الاستئناف|البداية]',
            r'القضية\s+رقم\s+\d+',
            r'تاريخ\s+\d+/\d+/\d+'
        ]
        
        self.legal_domains = {
            'attorney': ['محاماة', 'محامي', 'وكالة', 'توكيل'],
            'criminal': ['جزائية', 'جريمة', 'متهم', 'سجن', 'موقوف'],
            'civil': ['مدنية', 'دعوى', 'خصومة', 'تبليغ'],
            'commercial': ['تجارية', 'شركة', 'تجارة', 'مال'],
            'labor': ['عمل', 'عامل', 'موظف', 'راتب', 'إجازة'],
            'evidence': ['إثبات', 'شاهد', 'دليل', 'خبير']
        }
    
    def classify_content(self, title: str, content: str) -> Dict[str, Any]:
        """Classify legal content with elite precision"""
        
        combined_text = f"{title} {content}"
        
        # Determine content type
        content_type = self._classify_content_type(combined_text)
        
        # Determine legal domain
        legal_domain = self._classify_legal_domain(combined_text)
        
        # Determine hierarchical level
        hierarchy_level = self._classify_hierarchy_level(combined_text)
        
        # Calculate authority score
        authority_score = self._calculate_authority_score(content_type, hierarchy_level)
        
        return {
            'content_type': content_type,      # 'legislation' or 'court_ruling'
            'legal_domain': legal_domain,      # 'attorney', 'criminal', etc.
            'hierarchy_level': hierarchy_level, # 'article', 'chapter', 'law', 'ruling'
            'authority_score': authority_score, # 0.0 - 1.0
            'search_priority': self._calculate_search_priority(content_type, legal_domain, hierarchy_level)
        }
    
    def _classify_content_type(self, text: str) -> str:
        """Distinguish legislation from court rulings"""
        
        legislation_score = sum(1 for pattern in self.legislation_patterns 
                              if re.search(pattern, text))
        
        court_score = sum(1 for pattern in self.court_patterns 
                         if re.search(pattern, text))
        
        if legislation_score > court_score:
            return 'legislation'
        elif court_score > 0:
            return 'court_ruling'
        else:
            return 'unknown'
    
    def _classify_legal_domain(self, text: str) -> str:
        """Identify specific legal domain"""
        
        domain_scores = {}
        for domain, keywords in self.legal_domains.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                domain_scores[domain] = score
        
        return max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general'
    
    def _classify_hierarchy_level(self, text: str) -> str:
        """Determine hierarchical level in legal structure"""
        
        if re.search(r'المادة\s+\d+', text):
            return 'article'
        elif re.search(r'الفصل\s+\d+', text):
            return 'section' 
        elif re.search(r'الباب\s+\d+', text):
            return 'chapter'
        elif re.search(r'نظام\s+', text):
            return 'law'
        elif re.search(r'قرار\s+رقم', text):
            return 'court_decision'
        elif re.search(r'حكم\s+', text):
            return 'court_judgment'
        else:
            return 'general'
    
    def _calculate_authority_score(self, content_type: str, hierarchy_level: str) -> float:
        """Calculate authority/precedence score"""
        
        authority_weights = {
            'legislation': {
                'law': 1.0,
                'chapter': 0.9, 
                'section': 0.8,
                'article': 0.95,  # Articles are very authoritative
                'general': 0.7
            },
            'court_ruling': {
                'court_decision': 0.6,
                'court_judgment': 0.65,
                'general': 0.5
            }
        }
        
        return authority_weights.get(content_type, {}).get(hierarchy_level, 0.5)
    
    def _calculate_search_priority(self, content_type: str, domain: str, hierarchy_level: str) -> float:
        """Calculate search priority for ranking"""
        
        # Legislation gets higher priority for legal questions
        type_weight = 0.8 if content_type == 'legislation' else 0.6
        
        # Articles get highest priority
        hierarchy_weight = {
            'article': 1.0,
            'section': 0.8, 
            'chapter': 0.7,
            'law': 0.9,
            'court_decision': 0.6,
            'court_judgment': 0.65
        }.get(hierarchy_level, 0.5)
        
        return (type_weight + hierarchy_weight) / 2
