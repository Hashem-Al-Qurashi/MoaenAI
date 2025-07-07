"""
Core configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    app_name: str = "Arabic Legal Assistant"
    debug: bool = False
    version: str = "2.0.0"
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./arabic_legal.db"
    
    # Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Services
    deepseek_api_key: str
    
    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    
    # CORS - Support both environment variable and fallback
    @property
    def allowed_origins(self) -> List[str]:
        """Get CORS origins from environment or use defaults"""
        cors_origins = os.getenv("CORS_ORIGINS")
        if cors_origins:
            return [origin.strip() for origin in cors_origins.split(",")]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Helper properties
    @property
    def is_postgresql(self) -> bool:
        return self.database_url.startswith("postgresql")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Debug logging for production
if settings.environment == "production":
    print(f"🔧 Config loaded:")
    print(f"   📱 App: {settings.app_name} v{settings.version}")
    print(f"   🗄️  Database: {'PostgreSQL' if settings.is_postgresql else 'SQLite'}")
    print(f"   🌍 Environment: {settings.environment}")
    print(f"   🔐 DeepSeek API: {'✅ Configured' if settings.deepseek_api_key else '❌ Missing'}")
    print(f"   🌐 CORS Origins: {settings.allowed_origins}")
