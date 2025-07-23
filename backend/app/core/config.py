"""
Core configuration settings with best practices.
Supports multiple AI providers with proper validation and security.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import List, Optional, Literal
from enum import Enum
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"

class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Follows 12-factor app methodology with secure defaults.
    """
    
    # ==================== APP SETTINGS ====================
    app_name: str = Field(
        default="Arabic Legal Assistant",
        description="Application name"
    )
    
    version: str = Field(
        default="2.0.0",
        description="Application version"
    )
    
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode (never True in production)"
    )
    
    # ==================== DATABASE SETTINGS ====================
    database_url: str = Field(
        default="sqlite:///./arabic_legal.db",
        description="Database connection URL"
    )
    
    # ==================== AUTHENTICATION SETTINGS ====================
    secret_key: str = Field(
        ...,  # Required field
        min_length=32,
        description="JWT secret key - must be at least 32 characters"
    )
    
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,  # At least 5 minutes
        le=1440,  # At most 24 hours
        description="Access token expiration time in minutes"
    )
    
    # ==================== AI PROVIDER SETTINGS ====================
    ai_provider: AIProvider = Field(
        default=AIProvider.OPENAI,
        description="Primary AI provider to use"
    )
    
    # Optional API keys - at least one must be provided
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    deepseek_api_key: Optional[str] = Field(
        default=None,
        description="DeepSeek API key"
    )
    
    # AI Configuration
    ai_max_tokens: int = Field(
        default=6000,
        ge=100,
        le=8000,
        description="Maximum tokens for AI responses"
    )
    
    ai_temperature: float = Field(
        default=0.15,
        ge=0.0,
        le=2.0,
        description="AI response temperature"
    )
    
    ai_timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        description="AI request timeout in seconds"
    )
    
    # ==================== STORAGE SETTINGS ====================
    chroma_persist_dir: str = Field(
        default="./chroma_db",
        description="ChromaDB persistence directory"
    )
    
    # ==================== CORS SETTINGS ====================
    cors_origins: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed CORS origins"
    )
    
    # ==================== SECURITY SETTINGS ====================
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="List of allowed hosts"
    )
    
    # ==================== VALIDATORS ====================

    @field_validator('debug')
    @classmethod
    def validate_debug_in_production(cls, v, values):
        """Ensure debug is never True in production"""
        return v

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key_strength(cls, v):
        """Validate secret key meets security requirements"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        weak_keys = ['your-secret-key', 'change-me', 'default-key']
        if v.lower() in weak_keys:
            raise ValueError("Please use a strong, unique secret key")
        
        return v

    @model_validator(mode='after')
    def validate_configuration(self):
        """Validate complete configuration after all fields are set"""
        
        # Validate debug mode in production
        if self.environment == Environment.PRODUCTION and self.debug:
            raise ValueError("Debug mode cannot be enabled in production")
        
        # Validate AI provider configuration
        ai_provider = self.ai_provider
        openai_key = self.openai_api_key
        deepseek_key = self.deepseek_api_key
        
        # Ensure at least one API key is provided
        if not openai_key and not deepseek_key:
            raise ValueError(
                "At least one AI provider API key must be configured. "
                "Set OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable."
            )
        
        # Validate primary provider has corresponding key
        if ai_provider == AIProvider.OPENAI and not openai_key:
            if deepseek_key:
                logger.warning("OpenAI provider selected but no OpenAI key found. Falling back to DeepSeek.")
                self.ai_provider = AIProvider.DEEPSEEK
            else:
                raise ValueError("OpenAI provider selected but OPENAI_API_KEY not found")
        
        if ai_provider == AIProvider.DEEPSEEK and not deepseek_key:
            if openai_key:
                logger.warning("DeepSeek provider selected but no DeepSeek key found. Falling back to OpenAI.")
                self.ai_provider = AIProvider.OPENAI
            else:
                raise ValueError("DeepSeek provider selected but DEEPSEEK_API_KEY not found")
        
        return self
        
    # ==================== HELPER PROPERTIES ====================
    @property
    def allowed_origins(self) -> List[str]:
        """Get CORS origins from environment or use defaults"""
        if self.cors_origins:
            origins = [origin.strip() for origin in self.cors_origins.split(",")]
            return [origin for origin in origins if origin]  # Filter empty strings
        
        # Default origins based on environment
        if self.environment == Environment.DEVELOPMENT:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",  # Vite dev server
                "https://*.ngrok.io",
                # Local network access for mobile testing
                "http://192.168.1.10:3000",      # Your specific local IP
                "http://192.168.1.*:3000",       # Your network range (if supported)
                "http://10.0.3.1:3000",          # Your virtual interface
                "http://172.18.0.1:3000",        # Docker bridge
                "http://172.17.0.1:3000",        # Docker bridge
            ]
        elif self.environment == Environment.STAGING:
            return [
                "https://staging.yourdomain.com",
                "http://localhost:3000",  # Allow local testing
                "https://*.ngrok.io",
                # Add local network for staging testing if needed
                "http://192.168.1.10:3000",
            ]
        else:  # Production
            # For production, require explicit configuration but provide CloudFront fallback
            return [
                "https://d10drat4g0606g.cloudfront.net",
                "https://d2c979d13bkvf4.cloudfront.net"
            ]
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database"""
        return self.database_url.startswith("postgresql")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def active_ai_provider(self) -> str:
        """Get the active AI provider name"""
        return self.ai_provider.value
    
    @property
    def active_ai_key(self) -> str:
        """Get the API key for the active AI provider"""
        if self.ai_provider == AIProvider.OPENAI:
            return self.openai_api_key
        else:
            return self.deepseek_api_key
    
    # ==================== CONFIGURATION ====================
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
# ==================== SETTINGS INSTANCE ====================

def create_settings() -> Settings:
    """Create settings instance with proper error handling"""
    try:
        return Settings()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

# Global settings instance
settings = create_settings()

# ==================== STARTUP LOGGING ====================

def log_startup_info():
    """Log application startup information"""
    logger.info("🚀 Arabic Legal Assistant - Configuration Loaded")
    logger.info(f"📱 App: {settings.app_name} v{settings.version}")
    logger.info(f"🌍 Environment: {settings.environment.value}")
    logger.info(f"🗄️ Database: {'PostgreSQL' if settings.is_postgresql else 'SQLite'}")
    logger.info(f"🤖 AI Provider: {settings.active_ai_provider}")
    
    # Security-conscious logging
    if settings.openai_api_key:
        logger.info("🔐 OpenAI API: ✅ Configured")
    if settings.deepseek_api_key:
        logger.info("🔐 DeepSeek API: ✅ Configured")
    
    logger.info(f"🌐 CORS Origins: {len(settings.allowed_origins)} configured")
    
    if settings.is_development:
        logger.info("🔧 Debug mode: Enabled")
        logger.debug(f"🌐 CORS Origins: {settings.allowed_origins}")
    
    # Production warnings
    if settings.is_production:
        if not settings.allowed_origins:
            logger.warning("⚠️ No CORS origins configured for production!")
        if settings.database_url.startswith("sqlite"):
            logger.warning("⚠️ Using SQLite in production - consider PostgreSQL for better performance")

# Log startup info when module is imported
log_startup_info()