"""
Utility functions used across the backend.
"""
import os
import re
import uuid
import platform
import subprocess
from pathlib import Path


def generate_id() -> str:
    """Generate a short unique ID."""
    return str(uuid.uuid4())[:8]


def slugify_name(name: str) -> str:
    """Create a filesystem-safe slug from a name."""
    s = name.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s)
    return s.strip('-') or 'untitled'


def open_folder(path: Path):
    """Open a folder in the OS file explorer."""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:  # Linux
        subprocess.Popen(["xdg-open", path])


def truncate_text(text: str, length: int = 100) -> str:
    """Truncate text to a maximum length."""
    if len(text) <= length:
        return text
    return text[:length] + "..."
