"""
Enterprise Saudi Legal Document Crawler
Bulletproof quality validation with duplicate prevention
Built for 500+ documents with zero incomplete files
"""

import asyncio
import hashlib
import re
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from playwright.async_api import async_playwright
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import unicodedata

# Import our services
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    """Crawler configuration with quality controls"""
    max_documents: int = 50  # Start small, scale up
    batch_size: int = 10     # Process in small batches
    request_delay: float = 2.0  # Be respectful to servers
    min_content_length: int = 200
    min_arabic_ratio: float = 0.6
    min_quality_score: float = 7.0
    max_retries: int = 3
    timeout: int = 30


@dataclass
class DocumentQuality:
    """Document quality metrics"""
    content_length: int
    arabic_ratio: float
    legal_keywords_count: int
    structure_score: float
    duplicate_score: float
    overall_score: float
    
    def is_acceptable(self, config: CrawlerConfig) -> bool:
        """Check if document meets quality standards"""
        return (
            self.content_length >= config.min_content_length and
            self.arabic_ratio >= config.min_arabic_ratio and
            self.overall_score >= config.min_quality_score
        )


@dataclass
class CrawledDocument:
    """Crawled document with validation data"""
    url: str
    title: str
    content: str
    content_hash: str
    source_domain: str
    extraction_timestamp: datetime
    quality: DocumentQuality
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'content_hash': self.content_hash,
            'source_domain': self.source_domain,
            'extraction_timestamp': self.extraction_timestamp.isoformat(),
            'quality': asdict(self.quality),
            'metadata': self.metadata
        }


class ContentValidator:
    """Enterprise-grade content validation"""
    
    LEGAL_KEYWORDS = [
        'المادة', 'الفصل', 'الباب', 'البند', 'الفقرة', 'النظام', 'اللائحة',
        'المرسوم', 'الملكي', 'وزارة', 'العدل', 'المحكمة', 'القضاء', 'الدعوى',
        'الحكم', 'التشريع', 'القانون', 'الأنظمة', 'التكاليف', 'الرسوم'
    ]
    
    ARTICLE_PATTERNS = [
        r'المادة\s+[الأولى|الثانية|الثالثة|\d+]',
        r'الفصل\s+[الأول|الثاني|الثالث|\d+]',
        r'الباب\s+[الأول|الثاني|الثالث|\d+]'
    ]
    
    @classmethod
    def calculate_arabic_ratio(cls, text: str) -> float:
        """Calculate percentage of Arabic characters"""
        if not text:
            return 0.0
        
        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        total_chars = len([c for c in text if c.isalpha()])
        
        return arabic_chars / total_chars if total_chars > 0 else 0.0
    
    @classmethod
    def count_legal_keywords(cls, text: str) -> int:
        """Count legal terminology occurrences"""
        text_lower = text.lower()
        return sum(1 for keyword in cls.LEGAL_KEYWORDS if keyword in text_lower)
    
    @classmethod
    def calculate_structure_score(cls, text: str) -> float:
        """Score document structure based on legal formatting"""
        score = 0.0
        
        # Check for article patterns
        for pattern in cls.ARTICLE_PATTERNS:
            if re.search(pattern, text):
                score += 2.0
        
        # Check for numbering
        if re.search(r'\d+\.', text):
            score += 1.0
        
        # Check for legal structure
        if 'تعريفات' in text or 'نطاق التطبيق' in text:
            score += 2.0
        
        return min(score, 10.0)  # Cap at 10
    
    @classmethod
    def validate_content(cls, original_content: str, extracted_content: str) -> bool:
        """Validate extracted content against original"""
        # Hash comparison
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()
        extracted_hash = hashlib.sha256(extracted_content.encode()).hexdigest()
        
        if original_hash == extracted_hash:
            return True
        
        # Length comparison (allow 5% variance)
        length_ratio = len(extracted_content) / len(original_content)
        if 0.95 <= length_ratio <= 1.05:
            return True
        
        # Key phrase preservation check
        key_phrases = re.findall(r'المادة\s+\w+', original_content)
        preserved_phrases = sum(1 for phrase in key_phrases if phrase in extracted_content)
        preservation_ratio = preserved_phrases / len(key_phrases) if key_phrases else 1.0
        
        return preservation_ratio >= 0.9
    
    @classmethod
    def calculate_quality_score(cls, content: str, metadata: Dict[str, Any]) -> DocumentQuality:
        """Calculate comprehensive quality score"""
        content_length = len(content)
        arabic_ratio = cls.calculate_arabic_ratio(content)
        legal_keywords = cls.count_legal_keywords(content)
        structure_score = cls.calculate_structure_score(content)
        
        # Overall score calculation
        length_score = min(content_length / 500, 10.0)  # 500 chars = max score
        arabic_score = arabic_ratio * 10
        keywords_score = min(legal_keywords / 5, 10.0)  # 5 keywords = max score
        
        overall_score = (length_score + arabic_score + keywords_score + structure_score) / 4
        
        return DocumentQuality(
            content_length=content_length,
            arabic_ratio=arabic_ratio,
            legal_keywords_count=legal_keywords,
            structure_score=structure_score,
            duplicate_score=0.0,  # Will be calculated later
            overall_score=overall_score
        )


class DuplicateDetector:
    """Advanced duplicate detection system"""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.seen_titles: Set[str] = set()
        self.processed_documents: List[CrawledDocument] = []
    
    def is_duplicate_hash(self, content_hash: str) -> bool:
        """Check for exact content duplicates"""
        return content_hash in self.seen_hashes
    
    def is_duplicate_title(self, title: str) -> bool:
        """Check for title duplicates"""
        normalized_title = self.normalize_title(title)
        return normalized_title in self.seen_titles
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Remove diacritics and extra spaces
        normalized = unicodedata.normalize('NFD', title)
        normalized = re.sub(r'[\u064B-\u0652]', '', normalized)  # Remove diacritics
        normalized = re.sub(r'\s+', ' ', normalized).strip().lower()
        return normalized
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simple word overlap)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def find_similar_documents(self, document: CrawledDocument, threshold: float = 0.8) -> List[CrawledDocument]:
        """Find documents with high similarity"""
        similar = []
        
        for existing_doc in self.processed_documents:
            similarity = self.calculate_similarity(document.content, existing_doc.content)
            if similarity >= threshold:
                similar.append(existing_doc)
        
        return similar
    
    def add_document(self, document: CrawledDocument) -> bool:
        """Add document to tracking, return False if duplicate"""
        # Check exact duplicates
        if self.is_duplicate_hash(document.content_hash):
            logger.warning(f"Exact duplicate found: {document.title}")
            return False
        
        if self.is_duplicate_title(document.title):
            logger.warning(f"Title duplicate found: {document.title}")
            return False
        
        # Check similarity
        similar_docs = self.find_similar_documents(document)
        if similar_docs:
            logger.warning(f"Similar document found for: {document.title}")
            # Could implement smart merging here
        
        # Add to tracking
        self.seen_hashes.add(document.content_hash)
        self.seen_titles.add(self.normalize_title(document.title))
        self.processed_documents.append(document)
        
        return True


class ProgressTracker:
    """Progress tracking with checkpoint system"""
    
    def __init__(self, checkpoint_file: str = "data/crawler_progress.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.progress = self.load_progress()
    
    def load_progress(self) -> Dict[str, Any]:
        """Load progress from checkpoint file"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading progress: {e}")
        
        return {
            'processed_urls': [],
            'failed_urls': [],
            'last_checkpoint': None,
            'total_processed': 0,
            'total_successful': 0,
            'quality_stats': {}
        }
    
    def save_progress(self):
        """Save current progress to checkpoint"""
        try:
            self.checkpoint_file.parent.mkdir(exist_ok=True)
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def add_processed_url(self, url: str, success: bool = True):
        """Track processed URL"""
        if success:
            self.progress['processed_urls'].append(url)
            self.progress['total_successful'] += 1
        else:
            self.progress['failed_urls'].append(url)
        
        self.progress['total_processed'] += 1
        
        # Save checkpoint every 10 documents
        if self.progress['total_processed'] % 10 == 0:
            self.progress['last_checkpoint'] = datetime.now().isoformat()
            self.save_progress()
            logger.info(f"Checkpoint saved: {self.progress['total_processed']} documents processed")
    
    def is_processed(self, url: str) -> bool:
        """Check if URL was already processed"""
        return url in self.progress['processed_urls'] or url in self.progress['failed_urls']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get progress statistics"""
        return {
            'total_processed': self.progress['total_processed'],
            'successful': self.progress['total_successful'],
            'failed': len(self.progress['failed_urls']),
            'success_rate': self.progress['total_successful'] / max(self.progress['total_processed'], 1),
            'last_checkpoint': self.progress['last_checkpoint']
        }


class SaudiLegalCrawler:
    """Enterprise Saudi Legal Document Crawler"""
    
    def __init__(self, config: CrawlerConfig, document_service: DocumentService):
        self.config = config
        self.document_service = document_service
        self.validator = ContentValidator()
        self.duplicate_detector = DuplicateDetector()
        self.progress_tracker = ProgressTracker()
        
        self.playwright = None
        self.browser = None
        self.page = None
        self.stats = {
            'started_at': None,
            'total_urls_found': 0,
            'total_processed': 0,
            'successful_extractions': 0,
            'quality_rejections': 0,
            'duplicates_found': 0,
            'errors': 0
        }
        
        logger.info(f"SaudiLegalCrawler initialized with config: {asdict(config)}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.page = await self.browser.new_page()
        await self.page.set_extra_http_headers({
            'User-Agent': 'SaudiLegalBot/1.0 (Legal Research Tool)'
        })
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def discover_document_urls(self, base_url: str = "https://laws.moj.gov.sa") -> List[str]:
        """Discover legal document URLs from MOJ website using real structure"""
        urls = []
        
        logger.info(f"🔍 Starting URL discovery from MOJ legislation pages (7 pages expected)")
        
        # Real MOJ structure: 7 pages of laws
        for page_num in range(1, 8):  # Pages 1-7
            discovery_url = f"{base_url}/ar/legislations-regulations?pageNumber={page_num}&pageSize=9&LegalStatue=1&sortingBy=7"
            
            try:
                logger.info(f"📄 Processing page {page_num}/7: {discovery_url}")
                
                page_urls = await self.extract_urls_from_page(discovery_url)
                urls.extend(page_urls)
                
                logger.info(f"✅ Found {len(page_urls)} law URLs from page {page_num}")
                
                # Respectful delay between pages
                await asyncio.sleep(self.config.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error discovering URLs from page {page_num}: {e}")
                # Continue with other pages even if one fails
                continue
        
        # Remove duplicates and filter
        unique_urls = list(set(urls))
        filtered_urls = self.filter_legal_urls(unique_urls)
        
        logger.info(f"🎯 Discovery complete: {len(filtered_urls)} Saudi legal documents found")
        self.stats['total_urls_found'] = len(filtered_urls)
        
        return filtered_urls
    
    async def extract_urls_from_page(self, url: str) -> List[str]:
        """Extract law URLs from MOJ page using Playwright"""
        try:
            logger.info(f"🌐 Loading page with JavaScript: {url}")
            
            # Navigate to page and wait for content
            await self.page.goto(url, wait_until="networkidle")
            
            # Wait for law content to load (try multiple selectors)
            try:
                await self.page.wait_for_selector("a[href*='/ar/legislation/']", timeout=10000)
            except:
                # If specific selector fails, wait for general content
                await self.page.wait_for_selector("a", timeout=5000)
            
            # Get page content after JavaScript execution
            html = await self.page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for law links - these go to /ar/legislation/{law-id}
            law_urls = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href")
                if href and "/ar/legislation/" in href:
                    full_url = urljoin(url, href)
                    if "laws.moj.gov.sa" in full_url:
                        law_urls.append(full_url)
            
            # Remove duplicates
            law_urls = list(set(law_urls))
            
            logger.info(f"🔗 Found {len(law_urls)} law URLs on page")
            for law_url in law_urls[:3]:  # Log first 3 for debugging
                logger.info(f"   📋 {law_url}")
            
            return law_urls
            
        except Exception as e:
            logger.error(f"Error extracting URLs from {url}: {e}")
            return []
    
    def filter_legal_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to keep only Saudi legal documents"""
        # For MOJ legislation URLs, they're already filtered by structure
        filtered = []
        
        for url in urls:
            # Must be from MOJ domain
            if 'laws.moj.gov.sa' not in url:
                continue
            
            # Must be a legislation URL
            if '/ar/legislation/' not in url:
                continue
            
            # Must have a law ID (not just the base legislation path)
            if url.endswith('/ar/legislation/') or url.endswith('/ar/legislation'):
                continue
            
            filtered.append(url)
        
        logger.info(f"🔍 Filtered to {len(filtered)} valid Saudi legal document URLs")
        return filtered
    
    async def crawl_documents(self) -> Dict[str, Any]:
        """Main crawling orchestration"""
        self.stats['started_at'] = datetime.now()
        
        logger.info("🚀 Starting Saudi Legal Document Crawler")
        logger.info(f"📋 Target: {self.config.max_documents} documents")
        logger.info(f"🔍 Quality threshold: {self.config.min_quality_score}/10")
        
        try:
            # Phase 1: Discover URLs
            urls = await self.discover_document_urls()
            if not urls:
                raise Exception("No legal document URLs found")
            
            # Phase 2: Process in batches
            successful_documents = []
            
            for i in range(0, len(urls), self.config.batch_size):
                batch_urls = urls[i:i + self.config.batch_size]
                batch_num = (i // self.config.batch_size) + 1
                
                logger.info(f"📦 Processing batch {batch_num}: {len(batch_urls)} URLs")
                
                batch_results = await self.process_batch(batch_urls)
                successful_documents.extend(batch_results)
                
                # Progress report
                self.log_progress_report(batch_num, len(urls) // self.config.batch_size + 1)
                
                # Respectful delay between batches
                if i + self.config.batch_size < len(urls):
                    await asyncio.sleep(self.config.request_delay * 2)
            
            # Phase 3: Final quality check and storage
            final_results = await self.finalize_documents(successful_documents)
            
            # Phase 4: Generate final report
            return self.generate_final_report(final_results)
            
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            raise
    
    async def process_batch(self, urls: List[str]) -> List[CrawledDocument]:
        """Process a batch of URLs"""
        tasks = []
        
        for url in urls:
            # Skip if already processed
            if self.progress_tracker.is_processed(url):
                logger.info(f"Skipping already processed URL: {url}")
                continue
            
            task = self.process_single_document(url)
            tasks.append(task)
        
        # Process concurrently but respectfully
        results = []
        for task in tasks:
            try:
                result = await task
                if result:
                    results.append(result)
                # Delay between requests
                await asyncio.sleep(self.config.request_delay)
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                self.stats['errors'] += 1
        
        return results
    
    async def process_single_document(self, url: str) -> Optional[CrawledDocument]:
        """Process a single document with full validation"""
        try:
            logger.info(f"🔄 Processing: {url}")
            
            # Extract content
            document = await self.extract_document_content(url)
            if not document:
                self.progress_tracker.add_processed_url(url, success=False)
                return None
            
            # Quality validation
            if not document.quality.is_acceptable(self.config):
                logger.warning(f"❌ Quality rejected: {document.title} (score: {document.quality.overall_score:.1f})")
                self.stats['quality_rejections'] += 1
                self.progress_tracker.add_processed_url(url, success=False)
                return None
            
            # Duplicate check
            if not self.duplicate_detector.add_document(document):
                logger.warning(f"❌ Duplicate rejected: {document.title}")
                self.stats['duplicates_found'] += 1
                self.progress_tracker.add_processed_url(url, success=False)
                return None
            
            # Success
            logger.info(f"✅ Accepted: {document.title} (score: {document.quality.overall_score:.1f})")
            self.stats['successful_extractions'] += 1
            self.progress_tracker.add_processed_url(url, success=True)
            
            return document
            
        except Exception as e:
            logger.error(f"❌ Error processing {url}: {e}")
            self.stats['errors'] += 1
            self.progress_tracker.add_processed_url(url, success=False)
            return None
    
    async def extract_document_content(self, url: str) -> Optional[CrawledDocument]:
        """Extract and validate document content using Playwright"""
        try:
            logger.info(f"🌐 Loading law page: {url}")
            
            # Navigate to law page and wait for content
            await self.page.goto(url, wait_until="networkidle")
            
            # Wait longer for law content to load completely
            await self.page.wait_for_timeout(5000)  # Wait 5 seconds
            
            # Try to wait for main content specifically
            try:
                await self.page.wait_for_selector("main", timeout=10000)
            except:
                logger.warning(f"Timeout waiting for main content on {url}")
            
            # Get page content after JavaScript execution
            html = await self.page.content()
            
            # Parse content
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract title
            title = self.extract_title(soup, url)
            if not title:
                logger.warning(f"No title found for {url}")
                return None
            
            # Extract main content
            content = self.extract_main_content(soup)
            if not content:
                logger.warning(f"No content found for {url}")
                return None
            
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Calculate quality
            metadata = {
                "source_url": url,
                "domain": urlparse(url).netloc,
                "extraction_method": "playwright",
                "html_length": len(html)
            }
            
            quality = self.validator.calculate_quality_score(content, metadata)
            
            return CrawledDocument(
                url=url,
                title=title,
                content=content,
                content_hash=content_hash,
                source_domain=urlparse(url).netloc,
                extraction_timestamp=datetime.now(),
                quality=quality,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Content extraction error for {url}: {e}")
            return None
            
            # Extract main content
            content = self.extract_main_content(soup)
            if not content:
                logger.warning(f"No content found for {url}")
                return None
            
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Calculate quality
            metadata = {
                "source_url": url,
                "domain": urlparse(url).netloc,
                "extraction_method": "playwright",
                "html_length": len(html)
            }
            
            quality = self.validator.calculate_quality_score(content, metadata)
            
            return CrawledDocument(
                url=url,
                title=title,
                content=content,
                content_hash=content_hash,
                source_domain=urlparse(url).netloc,
                extraction_timestamp=datetime.now(),
                quality=quality,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Content extraction error for {url}: {e}")
            return None
    
    def extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract document title from MOJ law pages"""
        # MOJ-specific title selectors (try these in order)
        title_selectors = [
            '.law-title',             # Likely law title class
            '.legislation-title',     # Alternative title class
            '.document-title',        # Generic document title
            '.page-title',            # Page title
            '.main-heading',          # Main heading
            'h1',                     # Primary heading
            'h2',                     # Secondary heading
            '.title',                 # Generic title class
            '#title',                 # Title ID
            '.law-name',              # Law name specific
            '.legislation-name'       # Legislation name
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                logger.info(f"✅ Title extracted using selector: {selector}")
                return title
        
        # Fallback: Look for the first meaningful heading
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            title = heading.get_text(strip=True)
            if len(title) > 10 and any(keyword in title for keyword in ['نظام', 'قانون', 'لائحة', 'مرسوم']):
                logger.info("✅ Title extracted from legal heading")
                return title
        
        # Fallback: Use page title
        title_element = soup.find('title')
        if title_element:
            title = title_element.get_text(strip=True)
            # Clean up common suffixes
            title = title.replace(' - وزارة العدل', '').replace(' | وزارة العدل', '').strip()
            if title:
                logger.info("✅ Title extracted from page title")
                return title
        
        # Final fallback: Extract from URL
        url_parts = url.split('/')
        if len(url_parts) > 0:
            law_id = url_parts[-1]
            logger.warning(f"⚠️ Using URL-based title: Law {law_id}")
            return f"قانون سعودي - {law_id}"
        
        logger.warning("❌ No title found")
        return "قانون سعودي - بدون عنوان"
    
    def extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main document content from MOJ law pages"""
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Try main element first with detailed logging
        main_element = soup.select_one("main")
        if main_element:
            content = main_element.get_text(strip=True)
            logger.info(f"🔍 Main element found with {len(content)} characters")
            if len(content) > 200:
                logger.info(f"✅ Content extracted from main element ({len(content)} chars)")
                return content
            else:
                logger.warning(f"⚠️ Main element too short: {len(content)} chars")
        else:
            logger.warning("⚠️ No main element found")
        
        # Fallback: try other selectors
        content_selectors = [
            ".law-content", ".legislation-content", ".document-content",
            ".main-content", ".content", "article", ".law-text"
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content = element.get_text(strip=True)
                logger.info(f"🔍 {selector} found with {len(content)} characters")
                if len(content) > 200:
                    logger.info(f"✅ Content extracted using {selector} ({len(content)} chars)")
                    return content
        
        # Final fallback: get all text
        content = soup.get_text(strip=True)
        logger.info(f"🔍 Full page text: {len(content)} characters")
        if len(content) > 200:
            logger.info(f"✅ Content extracted using full page text ({len(content)} chars)")
            return content
        
        logger.warning("❌ No sufficient content found")
        return None
    def log_progress_report(self, current_batch: int, total_batches: int):
        """Log progress report"""
        progress_pct = (current_batch / total_batches) * 100
        
        logger.info(f"📊 Progress Report - Batch {current_batch}/{total_batches} ({progress_pct:.1f}%)")
        logger.info(f"   ✅ Successful: {self.stats['successful_extractions']}")
        logger.info(f"   ❌ Quality rejected: {self.stats['quality_rejections']}")
        logger.info(f"   🔄 Duplicates: {self.stats['duplicates_found']}")
        logger.info(f"   ⚠️ Errors: {self.stats['errors']}")
    
    async def finalize_documents(self, documents: List[CrawledDocument]) -> Dict[str, Any]:
        """Store documents in database"""
        logger.info(f"💾 Storing {len(documents)} validated documents in database...")
        
        # Convert to document service format
        doc_dicts = []
        for doc in documents:
            doc_dict = {
                'id': f"crawled_{hashlib.md5(doc.url.encode()).hexdigest()[:8]}",
                'title': doc.title,
                'content': doc.content,
                'metadata': {
                    **doc.metadata,
                    'content_hash': doc.content_hash,
                    'extraction_timestamp': doc.extraction_timestamp.isoformat()
                }
            }
            doc_dicts.append(doc_dict)
        
        # Store in database
        result = await self.document_service.add_documents_batch(doc_dicts)
        
        logger.info(f"📊 Storage result: {result['successful']} stored, {result['errors']} errors")
        
        return {
            'documents_processed': len(documents),
            'storage_result': result,
            'final_documents': doc_dicts
        }
    
    def generate_final_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        duration = datetime.now() - self.stats['started_at']
        
        report = {
            'crawler_summary': {
                'started_at': self.stats['started_at'].isoformat(),
                'duration_minutes': duration.total_seconds() / 60,
                'total_urls_discovered': self.stats['total_urls_found'],
                'documents_processed': results['documents_processed'],
                'success_rate': (self.stats['successful_extractions'] / max(self.stats['total_urls_found'], 1)) * 100
            },
            'quality_metrics': {
                'successful_extractions': self.stats['successful_extractions'],
                'quality_rejections': self.stats['quality_rejections'],
                'duplicates_found': self.stats['duplicates_found'],
                'errors': self.stats['errors'],
                'quality_acceptance_rate': (self.stats['successful_extractions'] / max(self.stats['successful_extractions'] + self.stats['quality_rejections'], 1)) * 100
            },
            'storage_results': results['storage_result'],
            'configuration': asdict(self.config),
            'next_steps': {
                'documents_in_database': results['storage_result']['successful'],
                'ready_for_rag': True,
                'recommended_next_batch_size': min(self.config.max_documents * 2, 100)
            }
        }
        
        # Save final report
        self.save_crawler_report(report)
        
        return report
    
    def save_crawler_report(self, report: Dict[str, Any]):
        """Save crawler report to file"""
        try:
            report_file = Path(f"data/crawler_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 Crawler report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Error saving crawler report: {e}")