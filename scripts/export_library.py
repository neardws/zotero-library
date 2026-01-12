#!/usr/bin/env python3
"""
Export Zotero library data to various formats.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from zotero_client import get_client
from config import EXPORTS_DIR


class LibraryExporter:
    def __init__(self):
        self.client = get_client()
    
    def export_bibtex(self, collection_key: Optional[str] = None, output_path: Optional[Path] = None) -> str:
        """Export items as BibTeX format."""
        if collection_key:
            items = self.client.get_collection_items(collection_key, limit=500)
        else:
            items = self.client.get_top_items(limit=500)
        
        bibtex_entries = []
        for item in items:
            data = item["data"]
            item_type = data.get("itemType", "")
            
            if item_type in ["attachment", "note"]:
                continue
            
            entry = self._item_to_bibtex(data)
            if entry:
                bibtex_entries.append(entry)
        
        content = "\n\n".join(bibtex_entries)
        
        if output_path:
            output_path.write_text(content, encoding="utf-8")
            print(f"Exported {len(bibtex_entries)} items to: {output_path}")
        
        return content
    
    def _item_to_bibtex(self, data: Dict[str, Any]) -> str:
        """Convert a Zotero item to BibTeX entry."""
        item_type = data.get("itemType", "")
        
        # Map Zotero types to BibTeX types
        type_map = {
            "journalArticle": "article",
            "conferencePaper": "inproceedings",
            "book": "book",
            "bookSection": "incollection",
            "thesis": "phdthesis",
            "report": "techreport",
            "webpage": "misc",
        }
        bib_type = type_map.get(item_type, "misc")
        
        # Generate citation key
        creators = data.get("creators", [])
        first_author = ""
        if creators:
            first_author = creators[0].get("lastName", creators[0].get("name", "unknown"))
        year = data.get("date", "")[:4] if data.get("date") else "nodate"
        title_word = data.get("title", "").split()[0] if data.get("title") else "notitle"
        cite_key = f"{first_author.lower()}{year}{title_word.lower()}"
        cite_key = "".join(c for c in cite_key if c.isalnum())
        
        # Build entry
        fields = []
        
        # Authors
        if creators:
            authors = " and ".join(
                f"{c.get('lastName', '')}, {c.get('firstName', '')}" 
                if c.get("lastName") else c.get("name", "")
                for c in creators if c.get("creatorType") == "author"
            )
            if authors:
                fields.append(f"  author = {{{authors}}}")
        
        # Title
        if data.get("title"):
            fields.append(f"  title = {{{data['title']}}}")
        
        # Year
        if year and year != "nodate":
            fields.append(f"  year = {{{year}}}")
        
        # Journal/Conference
        if item_type == "journalArticle" and data.get("publicationTitle"):
            fields.append(f"  journal = {{{data['publicationTitle']}}}")
        elif item_type == "conferencePaper" and data.get("conferenceName"):
            fields.append(f"  booktitle = {{{data['conferenceName']}}}")
        
        # DOI
        if data.get("DOI"):
            fields.append(f"  doi = {{{data['DOI']}}}")
        
        # URL
        if data.get("url"):
            fields.append(f"  url = {{{data['url']}}}")
        
        # Volume, Issue, Pages
        if data.get("volume"):
            fields.append(f"  volume = {{{data['volume']}}}")
        if data.get("issue"):
            fields.append(f"  number = {{{data['issue']}}}")
        if data.get("pages"):
            fields.append(f"  pages = {{{data['pages']}}}")
        
        if not fields:
            return ""
        
        return f"@{bib_type}{{{cite_key},\n" + ",\n".join(fields) + "\n}"
    
    def export_json(self, collection_key: Optional[str] = None, output_path: Optional[Path] = None) -> List[Dict]:
        """Export items as JSON."""
        if collection_key:
            items = self.client.get_collection_items(collection_key, limit=500)
        else:
            items = self.client.get_top_items(limit=500)
        
        export_data = []
        for item in items:
            data = item["data"]
            if data.get("itemType") in ["attachment", "note"]:
                continue
            
            export_data.append({
                "key": item["key"],
                "type": data.get("itemType"),
                "title": data.get("title"),
                "creators": data.get("creators", []),
                "date": data.get("date"),
                "DOI": data.get("DOI"),
                "url": data.get("url"),
                "abstract": data.get("abstractNote"),
                "tags": [t["tag"] for t in data.get("tags", [])],
                "collections": data.get("collections", []),
            })
        
        if output_path:
            output_path.write_text(
                json.dumps(export_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"Exported {len(export_data)} items to: {output_path}")
        
        return export_data
    
    def export_markdown_list(self, collection_key: Optional[str] = None, output_path: Optional[Path] = None) -> str:
        """Export items as Markdown reading list."""
        if collection_key:
            items = self.client.get_collection_items(collection_key, limit=500)
        else:
            items = self.client.get_top_items(limit=500)
        
        lines = [f"# Zotero Library Export\n", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
        
        # Group by year
        by_year: Dict[str, List] = {}
        for item in items:
            data = item["data"]
            if data.get("itemType") in ["attachment", "note"]:
                continue
            
            year = data.get("date", "")[:4] if data.get("date") else "Unknown"
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(data)
        
        for year in sorted(by_year.keys(), reverse=True):
            lines.append(f"\n## {year}\n")
            for data in by_year[year]:
                creators = data.get("creators", [])
                authors = ", ".join(
                    c.get("lastName", c.get("name", ""))
                    for c in creators[:3]
                )
                if len(creators) > 3:
                    authors += " et al."
                
                title = data.get("title", "Untitled")
                doi = data.get("DOI", "")
                
                if doi:
                    lines.append(f"- **{title}** - {authors} [DOI](https://doi.org/{doi})")
                else:
                    lines.append(f"- **{title}** - {authors}")
        
        content = "\n".join(lines)
        
        if output_path:
            output_path.write_text(content, encoding="utf-8")
            print(f"Exported {sum(len(v) for v in by_year.values())} items to: {output_path}")
        
        return content


def main():
    parser = argparse.ArgumentParser(description="Zotero Library Exporter")
    parser.add_argument("format", choices=["bibtex", "json", "markdown"], help="Export format")
    parser.add_argument("-c", "--collection", help="Collection name (exports all if not specified)")
    parser.add_argument("-o", "--output", help="Output file path")
    
    args = parser.parse_args()
    
    exporter = LibraryExporter()
    
    # Find collection key if specified
    collection_key = None
    if args.collection:
        from collection_manager import CollectionManager
        manager = CollectionManager()
        coll = manager.find_collection_by_name(args.collection)
        if coll:
            collection_key = coll["key"]
        else:
            print(f"Collection '{args.collection}' not found")
            return
    
    # Determine output path
    timestamp = datetime.now().strftime("%Y%m%d")
    suffix = f"-{args.collection}" if args.collection else ""
    
    if args.format == "bibtex":
        output = Path(args.output) if args.output else EXPORTS_DIR / f"library{suffix}-{timestamp}.bib"
        exporter.export_bibtex(collection_key, output)
    
    elif args.format == "json":
        output = Path(args.output) if args.output else EXPORTS_DIR / f"library{suffix}-{timestamp}.json"
        exporter.export_json(collection_key, output)
    
    elif args.format == "markdown":
        output = Path(args.output) if args.output else EXPORTS_DIR / f"library{suffix}-{timestamp}.md"
        exporter.export_markdown_list(collection_key, output)


if __name__ == "__main__":
    main()
