import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables
    
    Returns:
        Dictionary with configuration values
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration values with defaults
    config = {
        "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
        "base_url": os.environ.get("BASE_URL", "https://erasmusintern.org/traineeships"),
        "max_pages": int(os.environ.get("MAX_PAGES", 0)),  # 0 means all pages
        "data_dir": os.environ.get("DATA_DIR", "data")
    }
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if configuration is valid, False otherwise
    """
    # Check if GROQ API key is set
    if not config["groq_api_key"]:
        print("ERROR: GROQ API key is not set. Set it in .env file or as environment variable.")
        return False
    
    # Check if base URL is set and valid
    if not config["base_url"] or not config["base_url"].startswith("https://erasmusintern.org"):
        print("ERROR: Invalid base URL. Must be a valid erasmusintern.org URL.")
        return False
    
    # Ensure data directory exists
    os.makedirs(config["data_dir"], exist_ok=True)
    
    return True


def get_most_recent_data_file(data_dir: str, file_pattern: str = "erasmusintern_traineeships_*.csv") -> Optional[str]:
    """
    Get the most recent data file matching the pattern
    
    Args:
        data_dir: Directory containing data files
        file_pattern: Pattern to match files
        
    Returns:
        Path to the most recent file, or None if no files found
    """
    import glob
    
    # Make sure data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        return None
    
    # Get all files matching the pattern
    files = glob.glob(os.path.join(data_dir, file_pattern))
    
    # If no files found, return None
    if not files:
        return None
    
    # Return the most recent file
    return sorted(files)[-1]


def create_timestamp_filename(prefix: str, extension: str, data_dir: str = "data") -> str:
    """
    Create a filename with a timestamp
    
    Args:
        prefix: Prefix for the filename
        extension: File extension (without the dot)
        data_dir: Directory to store the file
        
    Returns:
        Path to the file
    """
    # Make sure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create filename
    filename = f"{prefix}_{timestamp}.{extension}"
    
    # Return full path
    return os.path.join(data_dir, filename)