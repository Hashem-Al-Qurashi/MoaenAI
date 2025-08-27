#!/usr/bin/env python3
"""
🔧 Saudi Legal Crawler Environment Setup
Bulletproof environment preparation for safe crawling
"""

import os
import sys
from pathlib import Path
import subprocess
import asyncio
import json
from datetime import datetime


class CrawlerEnvironmentSetup:
    """Setup and validate crawler environment"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent  # Go up one level from backend/
        self.backend_dir = Path(__file__).parent  # Current backend/ directory
        self.data_dir = self.backend_dir / "data"  # backend/data/
        self.logs_dir = self.data_dir / "logs"
        self.crawler_runs_dir = self.data_dir / "crawler_runs"
        
    def create_directory_structure(self):
        """Create required directory structure"""
        print("📁 Creating directory structure...")
        
        directories = [
            self.data_dir,
            self.logs_dir,
            self.crawler_runs_dir,
            self.data_dir / "checkpoints",
            self.data_dir / "reports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directory}")
        
        print("✅ Directory structure created")
    
    def check_python_dependencies(self):
        """Check and install required Python dependencies"""
        print("🐍 Checking Python dependencies...")
        
        required_packages = [
            'aiohttp',
            'beautifulsoup4',
            'aiosqlite',
            'numpy',
            'openai',
            'python-dotenv',
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'alembic'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"   ❌ {package} - MISSING")
        
        if missing_packages:
            print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            print("📦 Install with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All Python dependencies satisfied")
        return True
    
    def check_environment_variables(self):
        """Check required environment variables"""
        print("🔑 Checking environment variables...")
        
        required_vars = {
            'OPENAI_API_KEY': 'OpenAI API key for embeddings',
            'DEEPSEEK_API_KEY': 'DeepSeek API key for RAG (optional)'
        }
        
        missing_vars = []
        
        for var, description in required_vars.items():
            if os.getenv(var):
                print(f"   ✅ {var}")
            else:
                missing_vars.append((var, description))
                print(f"   ❌ {var} - MISSING")
        
        if missing_vars:
            print("\n⚠️ Missing environment variables:")
            for var, desc in missing_vars:
                print(f"   {var}: {desc}")
            
            print("\n📝 Create .env file in backend/ directory with:")
            for var, _ in missing_vars:
                print(f"   {var}=your_key_here")
            
            return False
        
        print("✅ All environment variables present")
        return True
    
    async def test_database_connectivity(self):
        """Test database connectivity and setup"""
        print("🗄️ Testing database connectivity...")
        
        try:
            # Import here to avoid circular imports
            sys.path.append(str(self.backend_dir))
            from app.storage.sqlite_store import SqliteVectorStore
            
            # Test vector store
            vector_store = SqliteVectorStore(str(self.data_dir / "vectors.db"))
            await vector_store.initialize()
            
            health = await vector_store.health_check()
            
            # Handle both boolean and dict responses for compatibility
            if isinstance(health, bool):
                if health:
                    print("   ✅ Vector store healthy (basic check)")
                    return True
                else:
                    print("   ❌ Vector store unhealthy")
                    return False
            elif isinstance(health, dict):
                if health.get('healthy', False):
                    print(f"   ✅ Vector store healthy: {health.get('stats', 'No stats')}")
                    return True
                else:
                    print(f"   ❌ Vector store unhealthy: {health}")
                    return False
            else:
                print("   ✅ Vector store health check completed")
                return True
                
        except Exception as e:
            print(f"   ❌ Database connectivity failed: {e}")
            return False
    
    def test_network_connectivity(self):
        """Test network connectivity to target websites"""
        print("🌐 Testing network connectivity...")
        
        test_urls = [
            "https://laws.moj.gov.sa",
            "https://api.openai.com",
            "https://api.deepseek.com"
        ]
        
        import urllib.request
        import urllib.error
        
        all_connected = True
        
        for url in test_urls:
            try:
                response = urllib.request.urlopen(url, timeout=10)
                print(f"   ✅ {url} - Status: {response.getcode()}")
            except urllib.error.URLError as e:
                print(f"   ❌ {url} - Error: {e}")
                all_connected = False
            except Exception as e:
                print(f"   ❌ {url} - Error: {e}")
                all_connected = False
        
        if all_connected:
            print("✅ All network connectivity tests passed")
        else:
            print("⚠️ Some network connectivity issues detected")
        
        return all_connected
    
    def create_example_env_file(self):
        """Create example .env file"""
        env_example_content = """# Saudi Legal Crawler Environment Configuration
# Copy this file to .env and fill in your actual API keys

# Required: OpenAI API key for embeddings
OPENAI_API_KEY=sk-proj-your_openai_key_here

# Optional: DeepSeek API key for enhanced RAG responses
DEEPSEEK_API_KEY=sk-your_deepseek_key_here

# Storage Configuration
VECTOR_STORAGE_TYPE=sqlite
SQLITE_DB_PATH=data/vectors.db

# Crawler Configuration
MAX_DOCUMENTS=50
BATCH_SIZE=10
REQUEST_DELAY=2.0
MIN_QUALITY_SCORE=7.5

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=data/logs/crawler.log

# CORS Configuration (for API)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
"""
        
        env_example_file = self.backend_dir / ".env.example"
        
        with open(env_example_file, 'w', encoding='utf-8') as f:
            f.write(env_example_content)
        
        print(f"📝 Example .env file created: {env_example_file}")
        
        # Check if .env already exists
        env_file = self.backend_dir / ".env"
        if not env_file.exists():
            print("⚠️ .env file not found - copy .env.example to .env and configure")
            return False
        
        return True
    
    def create_crawler_config_file(self):
        """Create crawler configuration file"""
        config = {
            "production_configs": {
                "phase_1_validation": {
                    "max_documents": 50,
                    "batch_size": 10,
                    "request_delay": 2.0,
                    "min_content_length": 300,
                    "min_arabic_ratio": 0.65,
                    "min_quality_score": 7.5,
                    "description": "Conservative settings for initial validation"
                },
                "phase_2_scaling": {
                    "max_documents": 150,
                    "batch_size": 15,
                    "request_delay": 1.5,
                    "min_content_length": 250,
                    "min_arabic_ratio": 0.6,
                    "min_quality_score": 7.0,
                    "description": "Moderate scaling after successful validation"
                },
                "phase_3_production": {
                    "max_documents": 500,
                    "batch_size": 20,
                    "request_delay": 1.0,
                    "min_content_length": 200,
                    "min_arabic_ratio": 0.6,
                    "min_quality_score": 6.5,
                    "description": "Full production settings for large-scale crawling"
                }
            },
            "target_websites": [
                {
                    "name": "Ministry of Justice",
                    "base_url": "https://laws.moj.gov.sa",
                    "discovery_paths": [
                        "/ar/legislations-regulations",
                        "/ar/Laws/Pages/default.aspx",
                        "/ar/LawsAndRegulations"
                    ],
                    "expected_documents": 1500,
                    "priority": 1
                }
            ],
            "quality_controls": {
                "content_validation": {
                    "legal_keywords": [
                        "المادة", "الفصل", "الباب", "البند", "الفقرة", 
                        "النظام", "اللائحة", "المرسوم", "الملكي", "وزارة", 
                        "العدل", "المحكمة", "القضاء", "الدعوى", "الحكم"
                    ],
                    "article_patterns": [
                        "المادة\\s+[الأولى|الثانية|الثالثة|\\d+]",
                        "الفصل\\s+[الأول|الثاني|الثالث|\\d+]",
                        "الباب\\s+[الأول|الثاني|الثالث|\\d+]"
                    ]
                },
                "duplicate_detection": {
                    "similarity_threshold": 0.8,
                    "title_normalization": True,
                    "content_hash_comparison": True
                }
            },
            "safety_measures": {
                "respectful_crawling": {
                    "robots_txt_compliance": True,
                    "rate_limiting": True,
                    "user_agent": "SaudiLegalBot/1.0 (Legal Research Tool)",
                    "max_concurrent_requests": 1
                },
                "error_handling": {
                    "max_retries": 3,
                    "timeout_seconds": 45,
                    "checkpoint_frequency": 10,
                    "progress_backup": True
                }
            }
        }
        
        config_file = self.data_dir / "crawler_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"⚙️ Crawler configuration created: {config_file}")
        return True
    
    def create_run_scripts(self):
        """Create convenient run scripts"""
        
        # Windows batch script
        windows_script = """@echo off
echo 🇸🇦 Saudi Legal Crawler - Windows Runner
echo ======================================

cd /d "%~dp0backend"

echo 🔧 Activating virtual environment (if exists)...
if exist venv\\Scripts\\activate.bat (
    call venv\\Scripts\\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️ No virtual environment found - using system Python
)

echo 🚀 Starting crawler...
python run_saudi_legal_crawler.py

pause
"""
        
        # Linux/Mac shell script
        unix_script = """#!/bin/bash
echo "🇸🇦 Saudi Legal Crawler - Unix Runner"
echo "===================================="

cd "$(dirname "$0")/backend"

echo "🔧 Activating virtual environment (if exists)..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ No virtual environment found - using system Python"
fi

echo "🚀 Starting crawler..."
python run_saudi_legal_crawler.py

echo "✅ Crawler execution completed"
read -p "Press Enter to continue..."
"""
        
        # Create scripts
        windows_file = self.project_root / "run_crawler.bat"
        unix_file = self.project_root / "run_crawler.sh"
        
        with open(windows_file, 'w', encoding='utf-8') as f:
            f.write(windows_script)
        
        with open(unix_file, 'w', encoding='utf-8') as f:
            f.write(unix_script)
        
        # Make Unix script executable
        try:
            os.chmod(unix_file, 0o755)
        except:
            pass  # Windows doesn't support chmod
        
        print(f"📜 Run scripts created:")
        print(f"   Windows: {windows_file}")
        print(f"   Unix/Mac: {unix_file}")
        
        return True
    
    def create_monitoring_dashboard_config(self):
        """Create configuration for monitoring dashboard"""
        dashboard_config = {
            "monitoring": {
                "real_time_metrics": [
                    "documents_processed",
                    "quality_acceptance_rate", 
                    "current_batch_progress",
                    "errors_per_minute",
                    "storage_success_rate"
                ],
                "alerts": {
                    "quality_rate_below": 60,
                    "error_rate_above": 20,
                    "storage_failure_above": 5
                },
                "reporting_intervals": {
                    "progress_update_seconds": 30,
                    "batch_completion_report": True,
                    "final_summary_report": True
                }
            },
            "performance_targets": {
                "phase_1": {
                    "target_documents": 30,
                    "minimum_quality_rate": 70,
                    "maximum_error_rate": 15,
                    "target_completion_hours": 2
                },
                "phase_2": {
                    "target_documents": 100,
                    "minimum_quality_rate": 75,
                    "maximum_error_rate": 10,
                    "target_completion_hours": 6
                },
                "phase_3": {
                    "target_documents": 400,
                    "minimum_quality_rate": 80,
                    "maximum_error_rate": 8,
                    "target_completion_hours": 24
                }
            }
        }
        
        dashboard_file = self.data_dir / "monitoring_config.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_config, f, ensure_ascii=False, indent=2)
        
        print(f"📊 Monitoring dashboard config created: {dashboard_file}")
        return True
    
    async def run_comprehensive_setup(self):
        """Run complete environment setup"""
        print("🇸🇦 Saudi Legal Crawler - Environment Setup")
        print("=" * 50)
        print(f"📅 Setup started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        setup_steps = [
            ("Directory Structure", self.create_directory_structure),
            ("Python Dependencies", self.check_python_dependencies),
            ("Environment Variables", self.check_environment_variables),
            ("Example .env File", self.create_example_env_file),
            ("Crawler Configuration", self.create_crawler_config_file),
            ("Run Scripts", self.create_run_scripts),
            ("Monitoring Config", self.create_monitoring_dashboard_config),
            ("Database Connectivity", self.test_database_connectivity),
            ("Network Connectivity", self.test_network_connectivity)
        ]
        
        results = {}
        
        for step_name, step_func in setup_steps:
            print(f"\n📋 {step_name}:")
            print("-" * 30)
            
            try:
                if asyncio.iscoroutinefunction(step_func):
                    result = await step_func()
                else:
                    result = step_func()
                
                results[step_name] = result
                status = "✅ PASSED" if result else "⚠️ WARNING"
                print(f"   {status}")
                
            except Exception as e:
                results[step_name] = False
                print(f"   ❌ FAILED: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 SETUP SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for step, result in results.items():
            status = "✅" if result else "❌"
            print(f"{status} {step}")
        
        print(f"\n📈 Success Rate: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("🚀 Ready to run crawler with: python run_saudi_legal_crawler.py")
            print("📜 Or use convenience scripts: ./run_crawler.sh or run_crawler.bat")
        elif passed >= total * 0.8:
            print("\n⚠️ SETUP MOSTLY COMPLETE - Minor issues detected")
            print("🔧 Review warnings above and fix if needed")
            print("🚀 Crawler may still work with current setup")
        else:
            print("\n❌ SETUP INCOMPLETE - Critical issues detected")
            print("🔧 Fix the failed steps before running crawler")
            print("📝 Check .env file and install missing dependencies")
        
        # Save setup report
        setup_report = {
            "setup_timestamp": datetime.now().isoformat(),
            "results": results,
            "success_rate": (passed/total)*100,
            "ready_for_crawling": passed >= total * 0.8
        }
        
        report_file = self.data_dir / "setup_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(setup_report, f, indent=2)
        
        print(f"\n📄 Setup report saved: {report_file}")
        
        return setup_report


async def main():
    """Main setup entry point"""
    try:
        setup = CrawlerEnvironmentSetup()
        report = await setup.run_comprehensive_setup()
        
        return report
        
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        return {"success": False, "error": "Interrupted"}
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("🔧 Starting environment setup...")
    report = asyncio.run(main())
    
    success = report.get("ready_for_crawling", False)
    exit(0 if success else 1)