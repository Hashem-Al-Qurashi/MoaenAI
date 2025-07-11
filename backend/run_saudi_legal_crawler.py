#!/usr/bin/env python3
"""
🚀 Saudi Legal Document Crawler Runner
Bulletproof orchestration script for safe, high-quality document extraction

SAFETY FIRST APPROACH:
- Phase 1: 50 documents (validation & learning)
- Phase 2: Scale to 200+ based on results
- Phase 3: Full corpus 500+ documents

Built for Production: Zero tolerance for incomplete files or low quality
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import our enterprise crawler and services
from saudi_legal_crawler import (
    SaudiLegalCrawler, 
    CrawlerConfig, 
    ContentValidator,
    DuplicateDetector,
    ProgressTracker
)
from app.services.document_service import DocumentService
from app.storage.sqlite_store import SqliteVectorStore


class CrawlerOrchestrator:
    """Bulletproof crawler orchestration with enterprise safety"""
    
    def __init__(self):
        self.setup_logging()
        self.config = self.create_production_config()
        self.document_service = None
        self.crawler = None
        
        # Execution tracking
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = Path(f"data/crawler_runs/{self.execution_id}")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 Crawler Orchestrator initialized - Run ID: {self.execution_id}")
    
    def setup_logging(self):
        """Configure enterprise-grade logging"""
        # Create logs directory
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set specific loggers
        logging.getLogger('playwright').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        global logger
        logger = logging.getLogger('CrawlerOrchestrator')
        
        logger.info(f"📝 Logging configured - Log file: {log_file}")
    
    def create_production_config(self) -> CrawlerConfig:
        """Create production-ready crawler configuration for Saudi laws"""
        # Optimized for Saudi legal documents (all 63 laws)
        config = CrawlerConfig(
            max_documents=70,           # Allow for all Saudi laws (~63) plus buffer
            batch_size=15,              # Larger batches for efficiency  
            request_delay=1.5,          # Faster processing, still respectful
            min_content_length=200,     # Slightly lower for legal documents
            min_arabic_ratio=0.60,      # Accommodate mixed legal content
            min_quality_score=4.5,      # Balanced quality threshold
            max_retries=3,              # Robust error handling
            timeout=60                  # Longer timeout for government sites
        )
        
        logger.info(f"📋 Production config for Saudi laws: {config}")
        return config
    
    async def initialize_services(self):
        """Initialize document service with vector storage"""
        try:
            logger.info("🔧 Initializing document storage services...")
            
            # Initialize vector store
            vector_store = SqliteVectorStore("data/vectors.db")
            await vector_store.initialize()
            
            # Test vector store health (simplified)
            try:
                health = await vector_store.health_check()
                logger.info(f"✅ Vector store health check: {health}")
            except Exception as health_error:
                logger.warning(f"⚠️ Health check failed but continuing: {health_error}")
            
            # Initialize AI client
            from openai import AsyncOpenAI
            from app.core.config import settings
            
            ai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("✅ OpenAI client initialized")
            
            # Initialize document service
            self.document_service = DocumentService(vector_store, ai_client)
            logger.info("✅ Document service initialized")
            
            # Get current document count
            try:
                existing_docs = await self.document_service.list_documents()
                logger.info(f"📊 Current database: {len(existing_docs)} documents")
            except Exception as list_error:
                logger.warning(f"⚠️ Could not list documents but continuing: {list_error}")
            
            # Initialize crawler
            self.crawler = SaudiLegalCrawler(self.config, self.document_service)
            logger.info("✅ Crawler initialized")
            
            logger.info("✅ All services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    async def validate_prerequisites(self) -> bool:
        """Validate system prerequisites before crawling"""
        try:
            logger.info("🔍 Validating system prerequisites...")
            
            # Check API keys using the same config system as your app
            try:
                from app.core.config import settings
                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key not configured in settings")
                logger.info("✅ OpenAI API key found in settings")
            except Exception as e:
                logger.error(f"❌ API key validation failed: {e}")
                return False
            
            # Check data directory
            data_dir = Path("data")
            if not data_dir.exists():
                data_dir.mkdir(parents=True)
                logger.info("📁 Created data directory")
            
            # Check database connectivity
            if self.document_service:
                test_result = await self.document_service.list_documents()
                logger.info(f"🗄️ Database connectivity confirmed: {len(test_result)} existing documents")
            
            # Check network connectivity
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("https://laws.moj.gov.sa") as response:
                    if response.status != 200:
                        raise Exception(f"Target website not accessible: {response.status}")
            
            logger.info("✅ All prerequisites validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Prerequisites validation failed: {e}")
            return False
    
    def save_pre_crawl_snapshot(self):
        """Save system state before crawling"""
        try:
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'execution_id': self.execution_id,
                'config': {
                    'max_documents': self.config.max_documents,
                    'batch_size': self.config.batch_size,
                    'quality_threshold': self.config.min_quality_score,
                    'min_arabic_ratio': self.config.min_arabic_ratio
                },
                'system_info': {
                    'python_version': sys.version,
                    'working_directory': str(Path.cwd()),
                    'data_directory': str(Path("data").absolute())
                }
            }
            
            snapshot_file = self.results_dir / "pre_crawl_snapshot.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📸 Pre-crawl snapshot saved: {snapshot_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save pre-crawl snapshot: {e}")
    
    async def execute_crawling_phase(self) -> Dict[str, Any]:
        """Execute main crawling with comprehensive monitoring"""
        try:
            logger.info("🚀 Starting main crawling phase...")
            logger.info(f"🎯 Target: {self.config.max_documents} high-quality Saudi legal documents")
            logger.info(f"📊 Quality threshold: {self.config.min_quality_score}/10")
            logger.info(f"🇸🇦 Arabic ratio minimum: {self.config.min_arabic_ratio * 100}%")
            
            # Execute crawling with the crawler
            async with self.crawler:
                results = await self.crawler.crawl_documents()
            
            logger.info("✅ Crawling phase completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Crawling phase failed: {e}")
            raise
    
    def analyze_crawl_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and validate crawling results"""
        try:
            logger.info("📊 Analyzing crawl results...")
            
            # Extract key metrics
            summary = results.get('crawler_summary', {})
            quality = results.get('quality_metrics', {})
            storage = results.get('storage_results', {})
            
            # Calculate success rates
            analysis = {
                'execution_summary': {
                    'execution_id': self.execution_id,
                    'duration_minutes': summary.get('duration_minutes', 0),
                    'total_urls_found': summary.get('total_urls_discovered', 0),
                    'documents_processed': summary.get('documents_processed', 0),
                    'overall_success_rate': summary.get('success_rate', 0)
                },
                'quality_analysis': {
                    'successful_extractions': quality.get('successful_extractions', 0),
                    'quality_rejections': quality.get('quality_rejections', 0),
                    'duplicates_found': quality.get('duplicates_found', 0),
                    'errors_encountered': quality.get('errors', 0),
                    'quality_acceptance_rate': quality.get('quality_acceptance_rate', 0)
                },
                'storage_analysis': {
                    'documents_stored': storage.get('successful', 0),
                    'storage_errors': storage.get('errors', 0),
                    'storage_success_rate': (storage.get('successful', 0) / max(storage.get('total', 1), 1)) * 100
                },
                'next_phase_recommendation': self.generate_next_phase_recommendation(results)
            }
            
            # Quality assessment
            if analysis['storage_analysis']['documents_stored'] >= 30:
                analysis['phase_result'] = "EXCELLENT"
            elif analysis['storage_analysis']['documents_stored'] >= 20:
                analysis['phase_result'] = "GOOD"
            elif analysis['storage_analysis']['documents_stored'] >= 10:
                analysis['phase_result'] = "ACCEPTABLE"
            else:
                analysis['phase_result'] = "NEEDS_IMPROVEMENT"
            
            logger.info(f"📈 Analysis complete - Phase result: {analysis['phase_result']}")
            logger.info(f"📚 Documents stored: {analysis['storage_analysis']['documents_stored']}")
            logger.info(f"⭐ Quality rate: {analysis['quality_analysis']['quality_acceptance_rate']:.1f}%")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Results analysis failed: {e}")
            return {'phase_result': 'ERROR', 'error': str(e)}
    
    def generate_next_phase_recommendation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for next crawling phase"""
        storage_successful = results.get('storage_results', {}).get('successful', 0)
        quality_rate = results.get('quality_metrics', {}).get('quality_acceptance_rate', 0)
        
        if storage_successful >= 40 and quality_rate >= 80:
            return {
                'recommendation': 'SCALE_AGGRESSIVELY',
                'next_batch_size': 100,
                'confidence': 'HIGH',
                'rationale': 'Excellent results - ready for aggressive scaling'
            }
        elif storage_successful >= 25 and quality_rate >= 70:
            return {
                'recommendation': 'SCALE_MODERATELY',
                'next_batch_size': 75,
                'confidence': 'MEDIUM',
                'rationale': 'Good results - moderate scaling recommended'
            }
        elif storage_successful >= 15:
            return {
                'recommendation': 'SCALE_CAUTIOUSLY',
                'next_batch_size': 60,
                'confidence': 'LOW',
                'rationale': 'Acceptable results - cautious scaling'
            }
        else:
            return {
                'recommendation': 'INVESTIGATE_ISSUES',
                'next_batch_size': 30,
                'confidence': 'VERY_LOW',
                'rationale': 'Poor results - investigate quality issues before scaling'
            }
    
    def save_comprehensive_report(self, results: Dict[str, Any], analysis: Dict[str, Any]):
        """Save comprehensive crawling report"""
        try:
            # Create comprehensive report
            comprehensive_report = {
                'execution_metadata': {
                    'execution_id': self.execution_id,
                    'timestamp': datetime.now().isoformat(),
                    'configuration': {
                        'max_documents': self.config.max_documents,
                        'batch_size': self.config.batch_size,
                        'quality_threshold': self.config.min_quality_score,
                        'arabic_ratio_min': self.config.min_arabic_ratio
                    }
                },
                'raw_results': results,
                'analysis': analysis,
                'recommendations': {
                    'immediate_actions': self.get_immediate_actions(analysis),
                    'next_phase': analysis.get('next_phase_recommendation', {}),
                    'quality_improvements': self.get_quality_improvement_suggestions(results)
                },
                'technical_details': {
                    'log_files': f"data/logs/crawler_{self.execution_id}.log",
                    'checkpoint_files': "data/crawler_progress.json",
                    'vector_database': "data/vectors.db"
                }
            }
            
            # Save main report
            report_file = self.results_dir / "comprehensive_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
            
            # Save human-readable summary
            self.save_human_readable_summary(comprehensive_report)
            
            logger.info(f"📄 Comprehensive report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save comprehensive report: {e}")
    
    def save_human_readable_summary(self, report: Dict[str, Any]):
        """Save human-readable summary"""
        try:
            analysis = report['analysis']
            recommendations = report['recommendations']
            
            summary_text = f"""
🚀 SAUDI LEGAL CRAWLER - EXECUTION SUMMARY
============================================

📅 Execution ID: {self.execution_id}
⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 RESULTS OVERVIEW:
-------------------
✅ Documents Successfully Stored: {analysis['storage_analysis']['documents_stored']}
📈 Overall Success Rate: {analysis['execution_summary']['overall_success_rate']:.1f}%
⭐ Quality Acceptance Rate: {analysis['quality_analysis']['quality_acceptance_rate']:.1f}%
🚫 Quality Rejections: {analysis['quality_analysis']['quality_rejections']}
🔄 Duplicates Found: {analysis['quality_analysis']['duplicates_found']}
❌ Errors Encountered: {analysis['quality_analysis']['errors_encountered']}

🎯 PHASE ASSESSMENT: {analysis['phase_result']}

🔮 NEXT PHASE RECOMMENDATION:
----------------------------
Strategy: {recommendations['next_phase']['recommendation']}
Confidence: {recommendations['next_phase']['confidence']}
Next Batch Size: {recommendations['next_phase']['next_batch_size']}
Rationale: {recommendations['next_phase']['rationale']}

🎛️ CONFIGURATION USED:
----------------------
Max Documents: {self.config.max_documents}
Batch Size: {self.config.batch_size}
Quality Threshold: {self.config.min_quality_score}/10
Arabic Ratio Min: {self.config.min_arabic_ratio * 100}%

📂 TECHNICAL FILES:
-------------------
📊 Full Report: {self.results_dir}/comprehensive_report.json
📝 Log File: data/logs/crawler_{self.execution_id}.log
🗄️ Vector Database: data/vectors.db
💾 Progress Checkpoint: data/crawler_progress.json

{self.get_next_steps_text(analysis, recommendations)}
"""
            
            summary_file = self.results_dir / "summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            
            # Also print to console
            print("\n" + "="*60)
            print(summary_text)
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"❌ Failed to save human-readable summary: {e}")
    
    def get_immediate_actions(self, analysis: Dict[str, Any]) -> list:
        """Get immediate action recommendations"""
        actions = []
        
        if analysis['storage_analysis']['documents_stored'] < 20:
            actions.append("Review quality thresholds - may be too strict")
            actions.append("Investigate common rejection patterns")
        
        if analysis['quality_analysis']['quality_acceptance_rate'] < 60:
            actions.append("Analyze failed URLs for pattern identification")
            actions.append("Consider adjusting content extraction logic")
        
        if analysis['quality_analysis']['duplicates_found'] > 10:
            actions.append("Review duplicate detection sensitivity")
            actions.append("Consider enhanced URL filtering")
        
        if analysis['quality_analysis']['errors_encountered'] > 15:
            actions.append("Investigate common error patterns")
            actions.append("Consider increasing timeout or retry logic")
        
        if not actions:
            actions.append("Excellent results - ready for next phase scaling")
        
        return actions
    
    def get_quality_improvement_suggestions(self, results: Dict[str, Any]) -> list:
        """Get quality improvement suggestions"""
        suggestions = []
        
        quality_rate = results.get('quality_metrics', {}).get('quality_acceptance_rate', 0)
        
        if quality_rate < 70:
            suggestions.extend([
                "Consider lowering minimum Arabic ratio threshold",
                "Review content extraction selectors for MOJ website",
                "Analyze rejected documents for common patterns",
                "Consider alternative quality scoring algorithms"
            ])
        
        if quality_rate > 90:
            suggestions.extend([
                "Quality thresholds are working excellently",
                "Consider increasing batch size for efficiency",
                "Ready for more aggressive scaling"
            ])
        
        return suggestions
    
    def get_next_steps_text(self, analysis: Dict[str, Any], recommendations: Dict[str, Any]) -> str:
        """Generate next steps text"""
        result = analysis['phase_result']
        
        if result == "EXCELLENT":
            return """
🚀 NEXT STEPS:
--------------
✅ Phase 1 completed with excellent results!
✅ Ready for Phase 2: Scale to 100-200 documents
✅ Consider increasing batch size for efficiency
✅ Current quality controls are working perfectly
"""
        elif result == "GOOD":
            return """
🚀 NEXT STEPS:
--------------
✅ Phase 1 completed with good results
✅ Ready for Phase 2: Scale to 75-150 documents
🔧 Consider minor quality threshold adjustments
📊 Monitor quality metrics in next phase
"""
        elif result == "ACCEPTABLE":
            return """
🚀 NEXT STEPS:
--------------
✅ Phase 1 completed acceptably
⚠️ Investigate quality rejection patterns before scaling
🔧 Consider adjusting quality thresholds
📊 Next phase: Cautious scaling to 60-100 documents
"""
        else:
            return """
🚀 NEXT STEPS:
--------------
⚠️ Phase 1 needs improvement before scaling
🔍 Investigate technical issues and quality patterns
🔧 Adjust configuration based on error analysis
📊 Retry Phase 1 with improved settings
"""
    
    async def run_complete_crawling_cycle(self) -> Dict[str, Any]:
        """Execute complete crawling cycle with full orchestration"""
        try:
            logger.info("🎬 Starting complete crawling cycle...")
            
            # Phase 1: Initialize and validate
            await self.initialize_services()
            
            if not await self.validate_prerequisites():
                raise Exception("Prerequisites validation failed")
            
            # Phase 2: Pre-crawl preparation
            self.save_pre_crawl_snapshot()
            
            # Phase 3: Execute crawling
            crawl_results = await self.execute_crawling_phase()
            
            # Phase 4: Analyze results
            analysis = self.analyze_crawl_results(crawl_results)
            
            # Phase 5: Generate comprehensive reports
            self.save_comprehensive_report(crawl_results, analysis)
            
            logger.info("🎉 Complete crawling cycle finished successfully!")
            
            return {
                'success': True,
                'execution_id': self.execution_id,
                'results': crawl_results,
                'analysis': analysis,
                'reports_directory': str(self.results_dir)
            }
            
        except Exception as e:
            error_msg = f"Complete crawling cycle failed: {e}"
            logger.error(f"❌ {error_msg}")
            
            # Save error report
            error_report = {
                'success': False,
                'execution_id': self.execution_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            error_file = self.results_dir / "error_report.json"
            with open(error_file, 'w') as f:
                json.dump(error_report, f, indent=2)
            
            return error_report


async def main():
    """Main entry point for crawler execution"""
    print("🇸🇦 Saudi Legal Document Crawler - Production Runner")
    print("=" * 60)
    
    try:
        # Create and run orchestrator
        orchestrator = CrawlerOrchestrator()
        results = await orchestrator.run_complete_crawling_cycle()
        
        if results['success']:
            print(f"\n✅ CRAWLING COMPLETED SUCCESSFULLY!")
            print(f"📁 Results saved in: {results['reports_directory']}")
            print(f"🆔 Execution ID: {results['execution_id']}")
            
            # Quick summary
            analysis = results['analysis']
            stored = analysis['storage_analysis']['documents_stored']
            quality_rate = analysis['quality_analysis']['quality_acceptance_rate']
            
            print(f"📚 Documents stored: {stored}")
            print(f"⭐ Quality rate: {quality_rate:.1f}%")
            print(f"🎯 Phase result: {analysis['phase_result']}")
            
        else:
            print(f"\n❌ CRAWLING FAILED!")
            print(f"🆔 Execution ID: {results['execution_id']}")
            print(f"❌ Error: {results['error']}")
            
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️ Crawling interrupted by user")
        return {'success': False, 'error': 'Interrupted by user'}
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run the crawler
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit(0 if results.get('success') else 1)