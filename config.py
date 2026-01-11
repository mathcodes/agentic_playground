"""
Configuration management for Voice-to-SQL Agent.
Loads settings from environment variables / .env file.
"""

import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Application configuration."""
    
    # Database  
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"postgresql://{os.getenv('USER', 'jonchristie')}@localhost:5432/voice_sql_test"
    )
    
    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    
    # Safety
    ALLOW_WRITE_QUERIES: bool = os.getenv("ALLOW_WRITE_QUERIES", "false").lower() == "true"
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "100"))
    
    # Audio
    SAMPLE_RATE: int = 16000  # Whisper expects 16kHz
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration. Returns list of errors."""
        errors = []
        
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive values)."""
        print("Current Configuration:")
        print(f"  DATABASE_URL: {cls.DATABASE_URL}")
        print(f"  ANTHROPIC_API_KEY: {'*' * 8 if cls.ANTHROPIC_API_KEY else '(not set)'}")
        print(f"  ANTHROPIC_MODEL: {cls.ANTHROPIC_MODEL}")
        print(f"  WHISPER_MODEL: {cls.WHISPER_MODEL}")
        print(f"  ALLOW_WRITE_QUERIES: {cls.ALLOW_WRITE_QUERIES}")
        print(f"  MAX_RESULTS: {cls.MAX_RESULTS}")


# Convenience instance
config = Config()
