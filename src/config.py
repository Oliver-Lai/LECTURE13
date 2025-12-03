"""Configuration module for loading environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

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
    # First try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'CWA_API_KEY' in st.secrets:
            return st.secrets['CWA_API_KEY']
    except Exception:
        pass
    
    # Fallback to environment variable (for local development)
    api_key = os.getenv("CWA_API_KEY")
    if not api_key:
        raise ValueError(
            "CWA_API_KEY environment variable is not set. "
            "Please create a .env file with your API key or add it to Streamlit secrets."
        )
    return api_key


# CWA OpenData API configuration
CWA_API_BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"

# Default map configuration
DEFAULT_MAP_CENTER = [23.5, 121.0]  # Taiwan center coordinates
DEFAULT_MAP_ZOOM = 7
