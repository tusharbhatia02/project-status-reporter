# config/settings.py
import os
import logging
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import ClassVar


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Required environment variables
    TRELLO_API_KEY: str
    TRELLO_TOKEN: str
    TRELLO_BOARD_ID: str
    SLACK_BOT_TOKEN: str
    SLACK_CHANNEL_ID: str
    GOOGLE_API_KEY: str
    PICA_SECRET: str

    # Application specific settings
    API_V1_STR: ClassVar[str] = "/api/v1" 
    PROJECT_NAME: str = "Project Status Reporter API"
    PROJECT_VERSION: str = "1.6.0" 
    LOG_LEVEL: str = "INFO"

    # Credentials paths relative to BASE_DIR (backend/)
    GMAIL_CREDENTIALS_PATH: str = os.path.join(BASE_DIR, 'credentials.json')
    GMAIL_TOKEN_PATH: str = os.path.join(BASE_DIR, 'token.json')

    # Gemini Model Name
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash-latest"

    # Pica Options
    PICA_BASE_URL: str = "https://api.picaos.com"

    class Config:
        
        case_sensitive = False
        
        env_file = dotenv_path
        env_file_encoding = 'utf-8'

# Create a single instance to be imported by other modules
try:
    settings = Settings()
    
    logging.getLogger().setLevel(settings.LOG_LEVEL.upper())
    logger.info(f"Settings loaded successfully. Project: {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    
    if not os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
        logger.warning(f"Gmail credentials file not found at: {settings.GMAIL_CREDENTIALS_PATH}")
    if not os.path.exists(settings.GMAIL_TOKEN_PATH):
        logger.warning(f"Gmail token file not found at: {settings.GMAIL_TOKEN_PATH}. Run scripts/gmail_auth.py.")

except Exception as e:
    logger.error(f"CRITICAL ERROR: Failed to load settings. Environment variables missing or invalid? Error: {e}", exc_info=True)
    settings = None