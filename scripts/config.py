"""
Configuration for Zotero library management.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Paths
EXPORTS_DIR = BASE_DIR / "exports"
NOTES_DIR = BASE_DIR / "notes"
STYLES_DIR = BASE_DIR / "styles"

# Zotero API configuration
ZOTERO_CONFIG = {
    "library_id": os.environ.get("ZOTERO_LIBRARY_ID", ""),
    "library_type": "user",  # or "group"
    "api_key": os.environ.get("ZOTERO_API_KEY", ""),
}

# Export settings
EXPORT_SETTINGS = {
    "bibtex_format": "bibtex",  # or "biblatex"
    "include_attachments": False,
    "include_notes": True,
}
