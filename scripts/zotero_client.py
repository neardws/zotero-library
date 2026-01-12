"""
Zotero API client wrapper.
"""
import logging
from typing import Optional, Dict, Any, List

try:
    from pyzotero import zotero
    PYZOTERO_AVAILABLE = True
except ImportError:
    PYZOTERO_AVAILABLE = False

from config import ZOTERO_CONFIG

logger = logging.getLogger(__name__)


class ZoteroClient:
    def __init__(self, config: Dict[str, Any] = None):
        if not PYZOTERO_AVAILABLE:
            raise ImportError("pyzotero not available. Install with: pip install pyzotero")
        
        config = config or ZOTERO_CONFIG
        
        if not config.get("api_key") or not config.get("library_id"):
            raise ValueError(
                "Zotero API key and library ID required. "
                "Set ZOTERO_API_KEY and ZOTERO_LIBRARY_ID in .env file"
            )
        
        self.zot = zotero.Zotero(
            config["library_id"],
            config["library_type"],
            config["api_key"]
        )
        logger.info("Zotero client initialized")
    
    def test_connection(self) -> bool:
        """Test the Zotero API connection."""
        try:
            self.zot.key_info()
            logger.info("Zotero connection successful")
            return True
        except Exception as e:
            logger.error(f"Zotero connection failed: {e}")
            return False
    
    def get_all_collections(self) -> List[Dict[str, Any]]:
        """Get all collections (folders) in the library."""
        return self.zot.collections()
    
    def get_collection(self, collection_key: str) -> Dict[str, Any]:
        """Get a specific collection by key."""
        return self.zot.collection(collection_key)
    
    def get_collection_items(self, collection_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all items in a collection."""
        return self.zot.collection_items(collection_key, limit=limit)
    
    def get_all_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all items in the library."""
        return self.zot.items(limit=limit)
    
    def get_top_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top-level items (no parent)."""
        return self.zot.top(limit=limit)
    
    def create_collection(self, name: str, parent_key: Optional[str] = None) -> Dict[str, Any]:
        """Create a new collection."""
        payload = [{"name": name}]
        if parent_key:
            payload[0]["parentCollection"] = parent_key
        return self.zot.create_collections(payload)
    
    def delete_collection(self, collection_key: str) -> bool:
        """Delete a collection."""
        try:
            self.zot.delete_collection(collection_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def update_collection(self, collection_key: str, name: str) -> bool:
        """Rename a collection."""
        try:
            coll = self.zot.collection(collection_key)
            coll["data"]["name"] = name
            self.zot.update_collection(coll)
            return True
        except Exception as e:
            logger.error(f"Failed to update collection: {e}")
            return False
    
    def add_item_to_collection(self, item_key: str, collection_key: str) -> bool:
        """Add an item to a collection."""
        try:
            item = self.zot.item(item_key)
            collections = item["data"].get("collections", [])
            if collection_key not in collections:
                collections.append(collection_key)
                item["data"]["collections"] = collections
                self.zot.update_item(item)
            return True
        except Exception as e:
            logger.error(f"Failed to add item to collection: {e}")
            return False
    
    def remove_item_from_collection(self, item_key: str, collection_key: str) -> bool:
        """Remove an item from a collection."""
        try:
            item = self.zot.item(item_key)
            collections = item["data"].get("collections", [])
            if collection_key in collections:
                collections.remove(collection_key)
                item["data"]["collections"] = collections
                self.zot.update_item(item)
            return True
        except Exception as e:
            logger.error(f"Failed to remove item from collection: {e}")
            return False
    
    def search_items(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search items by query."""
        return self.zot.items(q=query, limit=limit)


_client: Optional[ZoteroClient] = None

def get_client() -> ZoteroClient:
    """Get or create the Zotero client singleton."""
    global _client
    if _client is None:
        _client = ZoteroClient()
    return _client
