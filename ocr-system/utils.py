# utils.py
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def generate_id(content: str) -> str:
    """Generate a unique ID from content"""
    return hashlib.md5(content.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_bytes(size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def safe_json_loads(data: str) -> Dict:
    """Safely load JSON data"""
    try:
        return json.loads(data)
    except:
        return {}

def safe_json_dumps(data: Any) -> str:
    """Safely dump JSON data"""
    try:
        return json.dumps(data, default=str)
    except:
        return str(data)

def get_file_info(file_path: str) -> Dict:
    """Get file information"""
    import os
    from pathlib import Path

    path = Path(file_path)
    return {
        'filename': path.name,
        'extension': path.suffix.lower(),
        'size': path.stat().st_size if path.exists() else 0,
        'created_at': datetime.fromtimestamp(path.stat().st_ctime) if path.exists() else None,
        'modified_at': datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None,
    }
