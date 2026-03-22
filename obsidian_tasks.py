#!/usr/bin/env python3
"""
Obsidian Task Management - Core functionality.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_env(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from .env file if dotenv is available.
    
    If dotenv is not installed, this function does nothing.
    If env_path is not provided, looks for .env in current directory and parent directories.
    """
    if load_dotenv is None:
        return
    if env_path is None:
        load_dotenv(override=True)
    else:
        load_dotenv(dotenv_path=env_path, override=True)


def refresh_tasks_cache(
    vault_path: Optional[str] = None,
    task_cache_file_path: Optional[str] = None,
) -> None:
    """
    Scan an Obsidian vault for active tasks and write them to a JSON cache.

    Parameters
    ----------
    vault_path : str, optional
        Path to the Obsidian vault root.
        Defaults to environment variable OVTM_VAULT_PATH.
    task_cache_file_path : str, optional
        Path where the JSON cache file should be written.
        Defaults to environment variable OVTM_TASK_CACHE_FILEPATH.

    Raises
    ------
    ValueError
        If vault_path is not provided and OVTM_VAULT_PATH is not set.
    """
    # Load environment variables from .env file if available
    load_env()
    if vault_path is not None:
        # Also try to load .env from the vault directory
        vault_env_path = Path(vault_path) / ".env"
        if vault_env_path.exists():
            load_env(vault_env_path)
    
    # Resolve paths from environment variables if not provided
    if vault_path is None:
        vault_path = os.environ.get("OVTM_VAULT_PATH")
        if vault_path is None:
            raise ValueError(
                "vault_path must be provided or OVTM_VAULT_PATH must be set"
            )
    if task_cache_file_path is None:
        task_cache_file_path = os.environ.get("OVTM_TASK_CACHE_FILEPATH")
        if task_cache_file_path is None:
            raise ValueError(
                "task_cache_file_path must be provided or OVTM_TASK_CACHE_FILEPATH must be set"
            )

    vault_root = Path(vault_path).expanduser().resolve()
    cache_path = Path(task_cache_file_path).expanduser().resolve()

    print(f"Scanning vault: {vault_root}")
    print(f"Writing cache: {cache_path}")

    tasks = []
    md_files = list(vault_root.rglob("*.md"))

    print(f"Found {len(md_files)} markdown files.")

    # First pass: filter files that contain an opening square bracket
    files_with_brackets = []
    for md_file in md_files:
        try:
            # Quick check: read first few KB for '['
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read(8192)
                if "[" in content:
                    files_with_brackets.append(md_file)
        except Exception as e:
            print(f"Warning: could not read {md_file}: {e}")

    print(f"{len(files_with_brackets)} files contain '['.")

    # Second pass: parse frontmatter and keep only status: active
    active_files = []
    for md_file in files_with_brackets:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: could not read {md_file}: {e}")
            continue

        frontmatter = parse_frontmatter(content)
        status = frontmatter.get("status")
        if status == "active":
            active_files.append((md_file, frontmatter))

    print(f"{len(active_files)} files have status: active.")

    # Third pass: extract tasks from active files
    for md_file, frontmatter in active_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: could not read {md_file}: {e}")
            continue

        note_tags = frontmatter.get("tags", [])
        if isinstance(note_tags, str):
            note_tags = [note_tags]

        note_path = md_file.relative_to(vault_root).as_posix()

        for task_line in find_task_lines(content):
            task_data = parse_task_line(task_line)
            if task_data is None:
                continue

            task_obj = {
                "task": task_data["description"],
                "due_date": task_data["due_date"],
                "priority": task_data["priority"],
                "note_path": note_path,
                "note_tags": note_tags,
                "task_tags": task_data["tags"],
            }
            tasks.append(task_obj)

    print(f"Extracted {len(tasks)} tasks.")

    # Write JSON cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    print(f"Cache written to {cache_path}")


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    Parse YAML frontmatter from markdown content.
    Expects frontmatter between `---` delimiters at the start of the file.

    Returns an empty dict if no frontmatter is found.
    Supports simple key‑value pairs and list values (single‑line or multi‑line).
    """
    frontmatter = {}
    # Match frontmatter block: ---\n...\n---
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    if not match:
        return frontmatter

    yaml_lines = match.group(1).splitlines()
    i = 0
    while i < len(yaml_lines):
        line = yaml_lines[i].rstrip()
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            i += 1
            continue
        # Key‑value pair
        if ":" in line:
            key, rest = line.split(":", 1)
            key = key.strip()
            value = rest.strip()
            # Check if value is a start of a multi‑line list
            if value == "":
                # List might follow on next lines with indentation
                items = []
                j = i + 1
                while j < len(yaml_lines) and yaml_lines[j].startswith("  "):
                    item_line = yaml_lines[j].strip()
                    if item_line.startswith("- "):
                        items.append(item_line[2:].strip().strip('"\''))
                    j += 1
                if items:
                    frontmatter[key] = items
                    i = j
                    continue
                else:
                    # Empty value → treat as empty string
                    frontmatter[key] = ""
                    i += 1
                    continue
            # Single‑line list syntax [item1, item2]
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                if inner:
                    items = [item.strip().strip('"\'') for item in inner.split(",")]
                else:
                    items = []
                frontmatter[key] = items
            # Single‑line dash‑list (rare)
            elif value.startswith("- "):
                # Assume single‑line dash list like "- item1, - item2" (non‑standard)
                parts = [p.strip() for p in value.split("-") if p.strip()]
                items = [p.strip('"\'') for p in parts]
                frontmatter[key] = items
            else:
                # Simple scalar
                frontmatter[key] = value.strip('"\'')
            i += 1
        else:
            # Line without colon → ignore (could be part of a multi‑line string, not needed)
            i += 1
    return frontmatter


def find_task_lines(content: str) -> List[str]:
    """
    Find all active task lines (with empty checkbox) in markdown content.
    Returns list of lines that match task pattern.
    """
    # Pattern: dash, space, bracket, space, bracket, space, rest of line
    task_pattern = r"^[ \t]*[-*+][ \t]+\[ \][ \t]+.*$"
    lines = []
    for line in content.splitlines():
        if re.match(task_pattern, line):
            lines.append(line)
    return lines


def parse_task_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single task line into structured data.
    Returns dict with keys: description, due_date, priority, tags.
    """
    # Remove leading whitespace and bullet
    line = line.strip()
    # Remove bullet: could be -, *, +
    if line.startswith("- ") or line.startswith("* ") or line.startswith("+ "):
        line = line[2:].strip()
    # Expect [ ] or [x] at start now
    if not (line.startswith("[ ] ") or line.startswith("[x] ")):
        return None
    # Remove checkbox
    line = line[4:].strip()

    # Extract inline tags (#tag)
    tags = []
    words = line.split()
    for word in words:
        if word.startswith("#") and len(word) > 1:
            tags.append(word[1:])  # Remove '#'
    # Remove tags from description
    desc_words = [w for w in words if not w.startswith("#")]
    description = " ".join(desc_words)

    # Extract due date (📅 YYYY-MM-DD)
    due_date = None
    date_pattern = r"📅\s*(\d{4}-\d{2}-\d{2})"
    match = re.search(date_pattern, description)
    if match:
        due_date = match.group(1)
        # Remove the date marker from description
        description = re.sub(date_pattern, "", description).strip()

    # Extract priority icons
    priority = None
    priority_map = {
        "⏫": "high",
        "🔺": "medium",
        "🔽": "low",
    }
    for icon, level in priority_map.items():
        if icon in description:
            priority = level
            # Remove icon from description
            description = description.replace(icon, "").strip()
            break

    # Clean up extra spaces
    description = re.sub(r"\s+", " ", description).strip()

    return {
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "tags": tags,
    }


if __name__ == "__main__":
    # For quick testing
    import sys
    if len(sys.argv) > 1:
        vault = sys.argv[1]
        cache = sys.argv[2] if len(sys.argv) > 2 else "tasks.json"
        refresh_tasks_cache(vault, cache)
    else:
        print("Usage: python obsidian_tasks.py <vault_path> [cache_file]")
        sys.exit(1)