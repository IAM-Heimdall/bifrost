# app/utils/docs.py
import markdown
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Base directory for documentation files
DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"

def render_markdown_file(filename: str) -> Optional[str]:
    """
    Read and render a markdown file to HTML.
    
    Args:
        filename: The markdown file name (e.g., 'api-reference.md')
        
    Returns:
        Rendered HTML string or None if file not found
    """
    try:
        file_path = DOCS_DIR / filename
        
        if not file_path.exists():
            logger.warning(f"Documentation file not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix image URLs for whitepaper
        content = _fix_image_urls(content, filename)
        
        # Configure markdown with useful extensions
        md = markdown.Markdown(extensions=[
            'codehilite',      # Syntax highlighting
            'fenced_code',     # ```code``` blocks
            'tables',          # Table support
            'toc',             # Table of contents
            'nl2br',           # Convert newlines to <br>
            'attr_list'        # Allow attributes on elements
        ], extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False,  # Use CSS classes instead
                'noclasses': True
            },
            'toc': {
                'permalink': False,  # Disable permalink symbols
                'anchorlink': True
            }
        })
        
        html_content = md.convert(content)
        
        # Post-process HTML for consistency
        html_content = _post_process_html(html_content, filename)
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error rendering markdown file {filename}: {e}")
        return None

def render_markdown_with_metadata(filename: str) -> Dict[str, Any]:
    """
    Read and render a markdown file to HTML with metadata extraction.
    
    Args:
        filename: The markdown file name (e.g., 'api-reference.md')
        
    Returns:
        Dictionary with 'content', 'toc', and 'meta' keys
    """
    try:
        file_path = DOCS_DIR / filename
        
        if not file_path.exists():
            logger.warning(f"Documentation file not found: {file_path}")
            return {"content": None, "toc": "", "meta": {}}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix image URLs
        content = _fix_image_urls(content, filename)
        
        # Configure markdown with metadata and TOC extensions
        md = markdown.Markdown(extensions=[
            'meta',            # YAML metadata support
            'codehilite',      # Syntax highlighting
            'fenced_code',     # ```code``` blocks
            'tables',          # Table support
            'toc',             # Table of contents
            'nl2br',           # Convert newlines to <br>
            'attr_list'        # Allow attributes on elements
        ], extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': False,
                'noclasses': True
            },
            'toc': {
                'permalink': False,  # Disable permalink symbols
                'anchorlink': True
            }
        })
        
        html_content = md.convert(content)
        
        # Post-process HTML for consistency
        html_content = _post_process_html(html_content, filename)
        
        return {
            "content": html_content,
            "toc": md.toc if hasattr(md, 'toc') else "",
            "meta": md.Meta if hasattr(md, 'Meta') else {}
        }
        
    except Exception as e:
        logger.error(f"Error rendering markdown file {filename}: {e}")
        return {"content": None, "toc": "", "meta": {}}

def _fix_image_urls(content: str, filename: str) -> str:
    """Fix image URLs to work with Flask static files."""
    if filename == 'whitepaper.md':
        # Fix the sequence diagram URL
        content = content.replace(
            '{{ site.baseurl}}/app/static/assets/sequence-diagram.png',
            '/static/assets/sequence-diagram.png'
        )
        # Also handle any other potential Flask template syntax
        content = re.sub(
            r'\{\{\s*site\.baseurl\s*\}\}',
            '',
            content
        )
    return content

def _post_process_html(html_content: str, filename: str) -> str:
    """Post-process HTML for better styling and consistency."""
    
    # Ensure all code blocks have consistent classes
    html_content = re.sub(
        r'<pre><code class="language-(\w+)"',
        r'<pre class="docs-code-block"><code class="language-\1"',
        html_content
    )
    
    # Add classes to regular code blocks without language
    html_content = re.sub(
        r'<pre><code>',
        r'<pre class="docs-code-block"><code>',
        html_content
    )
    
    # Ensure tables have proper classes
    html_content = re.sub(
        r'<table>',
        r'<table class="docs-table">',
        html_content
    )
    
    # Add responsive image classes
    html_content = re.sub(
        r'<img([^>]*)>',
        r'<img\1 class="docs-image">',
        html_content
    )
    
    # Fix any remaining template syntax in links
    html_content = re.sub(
        r'href="[^"]*\{\{[^}]*\}\}[^"]*"',
        'href="#"',
        html_content
    )
    
    return html_content

def get_available_docs() -> list:
    """Get list of available documentation files."""
    try:
        if not DOCS_DIR.exists():
            logger.info(f"Creating docs directory: {DOCS_DIR}")
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
            return []
        
        markdown_files = [f.name for f in DOCS_DIR.glob("*.md")]
        logger.debug(f"Found {len(markdown_files)} markdown files: {markdown_files}")
        return markdown_files
    except Exception as e:
        logger.error(f"Error listing docs: {e}")
        return []

def ensure_docs_directory():
    """Ensure the docs directory exists."""
    try:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Docs directory ensured at: {DOCS_DIR}")
    except Exception as e:
        logger.error(f"Error creating docs directory: {e}")

def get_doc_info(filename: str) -> Dict[str, Any]:
    """
    Get information about a documentation file without rendering it.
    
    Args:
        filename: The markdown file name
        
    Returns:
        Dictionary with file info
    """
    try:
        file_path = DOCS_DIR / filename
        
        if not file_path.exists():
            return {"exists": False, "size": 0, "modified": None}
        
        stat = file_path.stat()
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "path": str(file_path)
        }
    except Exception as e:
        logger.error(f"Error getting doc info for {filename}: {e}")
        return {"exists": False, "size": 0, "modified": None}