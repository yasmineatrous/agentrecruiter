

import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


class Settings:
    """Application configuration settings"""
    
    # API Keys
    LLAMA_PARSE_API_KEY: Optional[str] = os.getenv("LLAMA_PARSE_API_KEY")
    MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
    
    # Model configurations
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    
    # Application settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: set = {'.pdf', '.docx', '.txt'}
    
    # Vector store settings
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
    
    # Text processing settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# Create global settings instance
settings = Settings()

# Print configuration on startup
def print_config():
    """Print current configuration"""
    print("=== Application Configuration ===")
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"Mistral Model: {settings.MISTRAL_MODEL}")
    print(f"Max File Size: {settings.MAX_FILE_SIZE} bytes")
    print(f"LlamaParser API Key: {'✓' if settings.LLAMA_PARSE_API_KEY else '✗'}")
    print(f"Mistral API Key: {'✓' if settings.MISTRAL_API_KEY else '✗'}")
    print("=" * 35)

if __name__ == "__main__":
    print_config()
