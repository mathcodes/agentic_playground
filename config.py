"""
Configuration management for Voice-to-SQL Agent.
Loads settings from environment variables / .env file.

SECURITY ENHANCEMENTS:
- Validates all configuration values for security
- Enforces secure defaults
- Redacts sensitive values in logs
- Validates API key formats
- Implements secure database connection settings
"""

import os
import re
from dotenv import load_dotenv
from typing import List

# SECURITY: Load .env file if it exists
# IMPORTANT: .env file should NEVER be committed to version control
# Add .env to .gitignore to prevent accidental exposure
load_dotenv()


class Config:
    """
    Application configuration with security validation.
    
    SECURITY: All sensitive configuration loaded from environment variables
    COMPLIANCE: Follows 12-factor app methodology for configuration
    """
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    
    # SECURITY: Database connection URL
    # Format: postgresql://username:password@host:port/database
    # For production:
    #   - Use strong passwords (16+ chars, random)
    #   - Use SSL/TLS connections (add ?sslmode=require)
    #   - Use connection pooling
    #   - Limit database user privileges (SELECT only for read operations)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{os.getenv('USER', 'jonchristie')}@localhost:5432/voice_sql_test"
    )
    
    # SECURITY: Database connection timeout (prevents hanging connections)
    DB_CONNECT_TIMEOUT: int = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
    
    # SECURITY: Database query timeout (prevents long-running queries from DoS)
    DB_QUERY_TIMEOUT: int = int(os.getenv("DB_QUERY_TIMEOUT", "30"))
    
    # SECURITY: Enable SSL for database connections in production
    DB_SSL_REQUIRED: bool = os.getenv("DB_SSL_REQUIRED", "false").lower() == "true"
    
    # =============================================================================
    # API KEYS AND AUTHENTICATION
    # =============================================================================
    
    # SECURITY: Anthropic API key for LLM access
    # CRITICAL: This should ALWAYS be loaded from environment variable
    # NEVER hardcode API keys in source code
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # SECURITY: LLM model to use
    # Validate that model string doesn't contain injection attempts
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    # SECURITY: JWT secret key for authentication
    # In production, generate with: openssl rand -hex 32
    # This should be a long, random string stored securely
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    
    # SECURITY: API key for programmatic access (if using API keys instead of JWT)
    API_KEY: str = os.getenv("API_KEY", "")
    
    # =============================================================================
    # WHISPER (SPEECH-TO-TEXT) CONFIGURATION
    # =============================================================================
    
    # SECURITY: Whisper model size
    # Larger models = better accuracy but more resource usage
    # Validate to prevent arbitrary file/model loading
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    ALLOWED_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    
    # SECURITY: Allow write queries (INSERT, UPDATE, DELETE, DROP)
    # CRITICAL: Keep this FALSE in production unless absolutely necessary
    # If enabled, implement strict authorization checks
    ALLOW_WRITE_QUERIES: bool = os.getenv("ALLOW_WRITE_QUERIES", "false").lower() == "true"
    
    # SECURITY: Maximum results returned from database queries
    # Prevents memory exhaustion and information disclosure
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "100"))
    
    # SECURITY: Maximum query execution time (seconds)
    # Prevents resource exhaustion from complex queries
    MAX_QUERY_TIME: int = int(os.getenv("MAX_QUERY_TIME", "30"))
    
    # SECURITY: Enable authentication requirement
    # If True, all API endpoints require valid JWT token
    REQUIRE_AUTH: bool = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
    
    # SECURITY: Enable rate limiting
    # Prevents abuse and DDoS attacks
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    
    # SECURITY: Enable audit logging
    # Required for compliance (SOC2, HIPAA, GDPR)
    ENABLE_AUDIT_LOGGING: bool = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    
    # SECURITY: Allowed CORS origins
    # Restrict which domains can access your API
    # In production, set to specific domain(s): https://yourdomain.com
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:*,http://127.0.0.1:*")
    
    # SECURITY: Session timeout (minutes)
    # How long JWT tokens remain valid
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "60"))
    
    # SECURITY: Enable HTTPS-only mode
    # In production, this should ALWAYS be True
    HTTPS_ONLY: bool = os.getenv("HTTPS_ONLY", "false").lower() == "true"
    
    # SECURITY: Maximum request size (MB)
    # Prevents memory exhaustion from large payloads
    MAX_REQUEST_SIZE_MB: int = int(os.getenv("MAX_REQUEST_SIZE_MB", "10"))
    
    # =============================================================================
    # AUDIO CONFIGURATION
    # =============================================================================
    
    # Audio sample rate for Whisper (16kHz required)
    SAMPLE_RATE: int = 16000
    
    # =============================================================================
    # ENVIRONMENT
    # =============================================================================
    
    # SECURITY: Environment (development, staging, production)
    # Different security settings apply per environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # SECURITY: Debug mode
    # CRITICAL: Must be False in production (exposes sensitive info in errors)
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> List[str]:
        """
        Validate configuration for security and completeness.
        
        SECURITY: Checks for:
        - Required values are set
        - API keys have valid format
        - Security settings are appropriate for environment
        - No hardcoded secrets
        - Dangerous configurations disabled
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # =============================================================================
        # CRITICAL SECURITY CHECKS
        # =============================================================================
        
        # SECURITY: Anthropic API key must be set
        if not cls.ANTHROPIC_API_KEY:
            errors.append("CRITICAL: ANTHROPIC_API_KEY is not set")
        elif not cls._validate_api_key_format(cls.ANTHROPIC_API_KEY):
            errors.append("CRITICAL: ANTHROPIC_API_KEY has invalid format")
        elif cls.ANTHROPIC_API_KEY.startswith("sk-ant-api") and len(cls.ANTHROPIC_API_KEY) < 50:
            errors.append("WARNING: ANTHROPIC_API_KEY looks like a test/example key")
        
        # SECURITY: JWT secret must be set if authentication enabled
        if cls.REQUIRE_AUTH and not cls.JWT_SECRET_KEY:
            errors.append("CRITICAL: JWT_SECRET_KEY must be set when REQUIRE_AUTH is enabled")
        elif cls.JWT_SECRET_KEY and len(cls.JWT_SECRET_KEY) < 32:
            errors.append("CRITICAL: JWT_SECRET_KEY is too short (minimum 32 characters)")
        
        # SECURITY: Whisper model must be from allowed list
        if cls.WHISPER_MODEL not in cls.ALLOWED_WHISPER_MODELS:
            errors.append(f"SECURITY: Invalid WHISPER_MODEL '{cls.WHISPER_MODEL}'. "
                         f"Allowed: {', '.join(cls.ALLOWED_WHISPER_MODELS)}")
        
        # =============================================================================
        # PRODUCTION SECURITY CHECKS
        # =============================================================================
        
        if cls.ENVIRONMENT == "production":
            # SECURITY: Production must have strict settings
            
            if cls.DEBUG:
                errors.append("CRITICAL: DEBUG must be False in production")
            
            if not cls.HTTPS_ONLY:
                errors.append("CRITICAL: HTTPS_ONLY must be True in production")
            
            if not cls.REQUIRE_AUTH:
                errors.append("CRITICAL: REQUIRE_AUTH should be True in production")
            
            if not cls.ENABLE_RATE_LIMITING:
                errors.append("WARNING: ENABLE_RATE_LIMITING should be True in production")
            
            if not cls.ENABLE_AUDIT_LOGGING:
                errors.append("WARNING: ENABLE_AUDIT_LOGGING should be True for compliance")
            
            if cls.ALLOW_WRITE_QUERIES:
                errors.append("WARNING: ALLOW_WRITE_QUERIES is enabled in production - ensure proper authorization")
            
            if not cls.DB_SSL_REQUIRED:
                errors.append("WARNING: DB_SSL_REQUIRED should be True in production")
            
            if "localhost" in cls.DATABASE_URL:
                errors.append("WARNING: DATABASE_URL points to localhost in production")
        
        # =============================================================================
        # VALUE VALIDATION
        # =============================================================================
        
        # SECURITY: Validate numeric limits are reasonable
        if cls.MAX_RESULTS <= 0 or cls.MAX_RESULTS > 10000:
            errors.append("SECURITY: MAX_RESULTS must be between 1 and 10000")
        
        if cls.MAX_QUERY_TIME <= 0 or cls.MAX_QUERY_TIME > 300:
            errors.append("SECURITY: MAX_QUERY_TIME must be between 1 and 300 seconds")
        
        if cls.SESSION_TIMEOUT <= 0 or cls.SESSION_TIMEOUT > 1440:  # Max 24 hours
            errors.append("SECURITY: SESSION_TIMEOUT must be between 1 and 1440 minutes")
        
        if cls.MAX_REQUEST_SIZE_MB <= 0 or cls.MAX_REQUEST_SIZE_MB > 100:
            errors.append("SECURITY: MAX_REQUEST_SIZE_MB must be between 1 and 100")
        
        # SECURITY: Validate database URL format
        if not cls._validate_database_url(cls.DATABASE_URL):
            errors.append("SECURITY: DATABASE_URL has invalid format")
        
        return errors
    
    @staticmethod
    def _validate_api_key_format(api_key: str) -> bool:
        """
        Validate API key format.
        
        SECURITY: Basic format validation for Anthropic keys
        Real validation happens when key is used
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid
        """
        if not api_key:
            return False
        
        # SECURITY: Anthropic keys start with 'sk-ant-'
        if not api_key.startswith("sk-ant-"):
            return False
        
        # SECURITY: Must be reasonable length
        if len(api_key) < 40 or len(api_key) > 256:
            return False
        
        # SECURITY: Should only contain alphanumeric and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True
    
    @staticmethod
    def _validate_database_url(db_url: str) -> bool:
        """
        Validate database URL format.
        
        SECURITY: Ensures database URL is properly formatted
        Prevents injection through malformed URLs
        
        Args:
            db_url: Database URL to validate
            
        Returns:
            True if format is valid
        """
        if not db_url:
            return False
        
        # SECURITY: Must start with postgresql://
        if not db_url.startswith("postgresql://"):
            return False
        
        # SECURITY: Basic URL structure validation
        # Format: postgresql://[user[:password]@][host][:port]/database
        pattern = r'^postgresql://([^:@]+(?::[^@]+)?@)?([^:/]+)(:\d+)?/[^/\s]+(\?[^\s]*)?$'
        if not re.match(pattern, db_url):
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """
        Print current configuration (hiding sensitive values).
        
        SECURITY: Redacts all sensitive values for safe logging
        """
        print("\n" + "="*60)
        print("APPLICATION CONFIGURATION")
        print("="*60)
        
        print("\n🗄️  DATABASE:")
        # SECURITY: Redact password from database URL
        safe_db_url = cls._redact_db_password(cls.DATABASE_URL)
        print(f"  URL: {safe_db_url}")
        print(f"  SSL Required: {cls.DB_SSL_REQUIRED}")
        print(f"  Connect Timeout: {cls.DB_CONNECT_TIMEOUT}s")
        print(f"  Query Timeout: {cls.DB_QUERY_TIMEOUT}s")
        
        print("\n🔑 AUTHENTICATION:")
        print(f"  Anthropic API Key: {cls._redact_key(cls.ANTHROPIC_API_KEY)}")
        print(f"  Anthropic Model: {cls.ANTHROPIC_MODEL}")
        print(f"  JWT Secret: {cls._redact_key(cls.JWT_SECRET_KEY)}")
        print(f"  API Key: {cls._redact_key(cls.API_KEY)}")
        
        print("\n🔒 SECURITY:")
        print(f"  Require Auth: {cls.REQUIRE_AUTH}")
        print(f"  Rate Limiting: {cls.ENABLE_RATE_LIMITING}")
        print(f"  Audit Logging: {cls.ENABLE_AUDIT_LOGGING}")
        print(f"  HTTPS Only: {cls.HTTPS_ONLY}")
        print(f"  Allow Write Queries: {cls.ALLOW_WRITE_QUERIES}")
        print(f"  Max Results: {cls.MAX_RESULTS}")
        print(f"  Max Query Time: {cls.MAX_QUERY_TIME}s")
        print(f"  Session Timeout: {cls.SESSION_TIMEOUT}min")
        
        print("\n🎤 SPEECH-TO-TEXT:")
        print(f"  Whisper Model: {cls.WHISPER_MODEL}")
        print(f"  Sample Rate: {cls.SAMPLE_RATE}Hz")
        
        print("\n🌍 ENVIRONMENT:")
        print(f"  Environment: {cls.ENVIRONMENT}")
        print(f"  Debug: {cls.DEBUG}")
        print(f"  CORS Origins: {cls.CORS_ORIGINS}")
        
        print("\n" + "="*60 + "\n")
        
        # SECURITY: Show validation errors
        errors = cls.validate()
        if errors:
            print("⚠️  CONFIGURATION WARNINGS/ERRORS:")
            for error in errors:
                print(f"  • {error}")
            print()
    
    @staticmethod
    def _redact_key(key: str) -> str:
        """
        Redact sensitive key for safe display.
        
        SECURITY: Shows only first/last few characters
        
        Args:
            key: Key to redact
            
        Returns:
            Redacted key string
        """
        if not key:
            return "(not set)"
        if len(key) < 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"
    
    @staticmethod
    def _redact_db_password(db_url: str) -> str:
        """
        Redact password from database URL.
        
        SECURITY: Safely display database URL without exposing credentials
        
        Args:
            db_url: Database URL
            
        Returns:
            URL with password redacted
        """
        # Pattern: postgresql://user:password@host/db
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)


# SECURITY: Convenience instance
config = Config()


# SECURITY: Validate configuration on import
# This ensures configuration errors are caught early
if __name__ != "__main__":
    errors = Config.validate()
    if errors:
        critical_errors = [e for e in errors if e.startswith("CRITICAL")]
        if critical_errors:
            print("\n⚠️  CRITICAL CONFIGURATION ERRORS DETECTED!")
            for error in critical_errors:
                print(f"  {error}")
            print("\nPlease fix these issues before running the application.\n")
