"""Configuration module for loading environment variables."""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_cwa_api_key() -> str:
    """Get CWA API key from environment variables or Streamlit secrets.
    
    Returns:
        str: The CWA API key.
        
    Raises:
        ValueError: If CWA_API_KEY is not set.
    """
    api_key = None
    
    # First try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            # Try different possible key names
            for key_name in ['CWA_API_KEY', 'cwa_api_key']:
                if key_name in st.secrets:
                    api_key = st.secrets[key_name]
                    logger.info(f"API key loaded from Streamlit secrets ({key_name})")
                    break
    except Exception as e:
        logger.warning(f"Could not load from Streamlit secrets: {e}")
    
    # Fallback to environment variable (for local development)
    if not api_key:
        api_key = os.getenv("CWA_API_KEY")
        if api_key:
            logger.info("API key loaded from environment variable")
    
    if not api_key:
        raise ValueError(
            "CWA_API_KEY is not set. "
            "Please add it to Streamlit secrets (Settings -> Secrets) with format:\n"
            'CWA_API_KEY = "your-api-key-here"'
        )
    
    # Clean up the API key (remove quotes and whitespace)
    api_key = api_key.strip().strip('"').strip("'")
    
    return api_key


# CWA OpenData API configuration
CWA_API_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

# Default map configuration
DEFAULT_MAP_CENTER = [23.5, 121.0]  # Taiwan center coordinates
DEFAULT_MAP_ZOOM = 7
