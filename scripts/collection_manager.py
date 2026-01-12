#!/usr/bin/env python3
"""
Collection (folder) management for Zotero library.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from zotero_client import get_client
from config import EXPORTS_DIR


class CollectionManager:
    def __init__(self):
        self.client = get_client()
        self._collections_cache: Dict[str, Dict] = {}
    
    def get_collection_tree(self) -> List[Dict[str, Any]]:
        """Get hierarchical collection tree."""
        collections = self.client.get_all_collections()
        
        # Build lookup dict
        lookup = {}
        for coll in collections:
            key = coll["key"]
            lookup[key] = {
                "key": key,
                "name": coll["data"]["name"],
                "parent": coll["data"].get("parentCollection"),
                "children": [],
                "item_count": coll["meta"].get("numItems", 0),
            }
        
        # Build tree
        roots = []
        for key, node in lookup.items():
            parent_key = node["parent"]
            if parent_key and parent_key in lookup:
                lookup[parent_key]["children"].append(node)
            else:
                roots.append(node)
        
        return roots
    
    def print_tree(self, nodes: List[Dict] = None, indent: int = 0):
        """Print collection tree to console."""
        if nodes is None:
            nodes = self.get_collection_tree()
        
        for node in sorted(nodes, key=lambda x: x["name"]):
            prefix = "  " * indent + ("├── " if indent > 0 else "")
            print(f"{prefix}{node['name']} ({node['item_count']} items) [{node['key']}]")
            if node["children"]:
                self.print_tree(node["children"], indent + 1)
    
    def export_tree_markdown(self, output_path: Optional[Path] = None) -> str:
        """Export collection tree as Markdown."""
        def _to_md(nodes: List[Dict], level: int = 0) -> List[str]:
            lines = []
            for node in sorted(nodes, key=lambda x: x["name"]):
                indent = "  " * level
                lines.append(f"{indent}- **{node['name']}** ({node['item_count']} items)")
                if node["children"]:
                    lines.extend(_to_md(node["children"], level + 1))
            return lines
        
        tree = self.get_collection_tree()
        content = "# Zotero Collections\n\n" + "\n".join(_to_md(tree))
        
        if output_path:
            output_path.write_text(content, encoding="utf-8")
            print(f"Exported to: {output_path}")
        
        return content
    
    def export_tree_json(self, output_path: Optional[Path] = None) -> Dict:
        """Export collection tree as JSON."""
        tree = self.get_collection_tree()
        
        if output_path:
            output_path.write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Exported to: {output_path}")
        
        return tree
    
    def list_collection_items(self, collection_key: str) -> List[Dict]:
        """List all items in a collection."""
        items = self.client.get_collection_items(collection_key)
        return [
            {
                "key": item["key"],
                "title": item["data"].get("title", ""),
                "creators": item["data"].get("creators", []),
                "year": item["data"].get("date", "")[:4] if item["data"].get("date") else "",
                "type": item["data"].get("itemType", ""),
            }
            for item in items
            if item["data"].get("itemType") != "attachment"
        ]
    
    def find_collection_by_name(self, name: str) -> Optional[Dict]:
        """Find a collection by name (case-insensitive)."""
        collections = self.client.get_all_collections()
        name_lower = name.lower()
        for coll in collections:
            if coll["data"]["name"].lower() == name_lower:
                return coll
        return None
    
    def create_collection(self, name: str, parent_name: Optional[str] = None) -> bool:
        """Create a new collection, optionally under a parent."""
        parent_key = None
        if parent_name:
            parent = self.find_collection_by_name(parent_name)
            if not parent:
                print(f"Parent collection '{parent_name}' not found")
                return False
            parent_key = parent["key"]
        
        result = self.client.create_collection(name, parent_key)
        if result and "successful" in result:
            print(f"Created collection: {name}")
            return True
        print(f"Failed to create collection: {name}")
        return False
    
    def organize_by_year(self, source_collection: str) -> Dict[str, int]:
        """Organize items in a collection by year into sub-collections."""
        source = self.find_collection_by_name(source_collection)
        if not source:
            print(f"Collection '{source_collection}' not found")
            return {}
        
        items = self.client.get_collection_items(source["key"])
        year_counts = {}
        
        for item in items:
            if item["data"].get("itemType") == "attachment":
                continue
            
            date = item["data"].get("date", "")
            year = date[:4] if date and date[:4].isdigit() else "Unknown"
            
            # Create year sub-collection if needed
            year_coll_name = f"{source_collection}-{year}"
            year_coll = self.find_collection_by_name(year_coll_name)
            if not year_coll:
                self.client.create_collection(year_coll_name, source["key"])
                year_coll = self.find_collection_by_name(year_coll_name)
            
            if year_coll:
                self.client.add_item_to_collection(item["key"], year_coll["key"])
                year_counts[year] = year_counts.get(year, 0) + 1
        
        print(f"Organized {sum(year_counts.values())} items by year:")
        for year, count in sorted(year_counts.items()):
            print(f"  {year}: {count} items")
        
        return year_counts


def main():
    parser = argparse.ArgumentParser(description="Zotero Collection Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # tree command
    tree_parser = subparsers.add_parser("tree", help="Show collection tree")
    tree_parser.add_argument("--json", action="store_true", help="Output as JSON")
    tree_parser.add_argument("--markdown", action="store_true", help="Output as Markdown")
    tree_parser.add_argument("-o", "--output", help="Output file path")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List items in a collection")
    list_parser.add_argument("collection", help="Collection name or key")
    
    # create command
    create_parser = subparsers.add_parser("create", help="Create a new collection")
    create_parser.add_argument("name", help="Collection name")
    create_parser.add_argument("--parent", help="Parent collection name")
    
    # organize command
    org_parser = subparsers.add_parser("organize", help="Organize collection by year")
    org_parser.add_argument("collection", help="Collection name")
    
    # test command
    subparsers.add_parser("test", help="Test Zotero connection")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = CollectionManager()
    
    if args.command == "test":
        if manager.client.test_connection():
            print("Connection successful!")
        else:
            print("Connection failed!")
    
    elif args.command == "tree":
        if args.json:
            output = Path(args.output) if args.output else EXPORTS_DIR / "collections.json"
            manager.export_tree_json(output)
        elif args.markdown:
            output = Path(args.output) if args.output else EXPORTS_DIR / "collections.md"
            manager.export_tree_markdown(output)
        else:
            manager.print_tree()
    
    elif args.command == "list":
        coll = manager.find_collection_by_name(args.collection)
        if not coll:
            print(f"Collection '{args.collection}' not found")
            return
        items = manager.list_collection_items(coll["key"])
        for item in items:
            authors = ", ".join(
                c.get("lastName", c.get("name", "")) 
                for c in item["creators"][:2]
            )
            if len(item["creators"]) > 2:
                authors += " et al."
            print(f"[{item['year']}] {item['title'][:60]}... - {authors}")
    
    elif args.command == "create":
        manager.create_collection(args.name, args.parent)
    
    elif args.command == "organize":
        manager.organize_by_year(args.collection)


if __name__ == "__main__":
    main()
