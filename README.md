# Zotero Library

Personal Zotero library management repository with API integration.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API credentials:
```bash
cp .env.example .env
# Edit .env with your Zotero API key and library ID
# Get from: https://www.zotero.org/settings/keys
```

3. Test connection:
```bash
cd scripts && python collection_manager.py test
```

## Usage

### Collection Management

```bash
cd scripts

# Show collection tree
python collection_manager.py tree

# Export tree as Markdown
python collection_manager.py tree --markdown

# Export tree as JSON
python collection_manager.py tree --json

# List items in a collection
python collection_manager.py list "Collection Name"

# Create new collection
python collection_manager.py create "New Collection"
python collection_manager.py create "Sub Collection" --parent "Parent Collection"

# Organize collection by year
python collection_manager.py organize "Collection Name"
```

### Export Library

```bash
cd scripts

# Export all items as BibTeX
python export_library.py bibtex

# Export specific collection as JSON
python export_library.py json -c "Collection Name"

# Export as Markdown reading list
python export_library.py markdown
```

## Directory Structure

```
.
├── scripts/      # Management scripts
├── exports/      # Exported bibliography files (BibTeX, JSON, Markdown)
├── notes/        # Reading notes and annotations
├── styles/       # Custom CSL citation styles
└── attachments/  # Important attachment backups
```
