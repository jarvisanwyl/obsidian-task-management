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
                "completed": task_data["completed"],
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
    Find all task lines (with checkbox) in markdown content.
    Returns list of lines that match task pattern, both active [ ] and completed [x]/[X].
    """
    # Pattern: dash, space, bracket, space or x/X, bracket, space, rest of line
    task_pattern = r"^[ \t]*[-*+][ \t]+\[[ xX]\][ \t]+.*$"
    lines = []
    for line in content.splitlines():
        if re.match(task_pattern, line):
            lines.append(line)
    return lines


def parse_task_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single task line into structured data.
    Returns dict with keys: description, due_date, priority, tags, completed.
    """
    # Remove leading whitespace and bullet
    line = line.strip()
    # Remove bullet: could be -, *, +
    if line.startswith("- ") or line.startswith("* ") or line.startswith("+ "):
        line = line[2:].strip()
    # Expect [ ], [x], or [X] at start now
    if not (line.startswith("[ ] ") or line[:4].lower() == "[x] "):
        return None
    # Determine completion status
    completed = line[:4].lower() == "[x] "
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
        "completed": completed,
    }


def delete_completed_tasks_per_cache(
    vault_path: str,
    cache_file_path: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Delete completed tasks listed in a JSON cache.

    Parameters
    ----------
    vault_path : str
        Path to Obsidian vault root.
    cache_file_path : str
        Path to JSON cache file (must exist).
    dry_run : bool, default False
        If True, only simulate deletion and report what would be deleted.

    Returns
    -------
    Dict[str, Any]
        Statistics:
        - "tasks_deleted": number of tasks removed (or would be removed)
        - "files_modified": number of note files changed (or would be changed)
        - "errors": list of error messages (empty if none)
        - "skipped_notes": number of notes skipped (not found or no matches)
        - "dry_run": True if dry_run was requested
    """
    # Load cache
    cache_path = Path(cache_file_path).expanduser().resolve()
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_path}")

    with open(cache_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # Filter completed tasks
    completed_tasks = [t for t in tasks if t.get("completed") is True]
    if not completed_tasks:
        return {
            "tasks_deleted": 0,
            "files_modified": 0,
            "errors": [],
            "skipped_notes": 0,
            "dry_run": dry_run,
        }

    # Group by note_path
    notes_dict = {}
    for task in completed_tasks:
        note_path = task.get("note_path")
        if note_path is None:
            continue
        notes_dict.setdefault(note_path, []).append(task)

    vault_root = Path(vault_path).expanduser().resolve()
    stats = {
        "tasks_deleted": 0,
        "files_modified": 0,
        "errors": [],
        "skipped_notes": 0,
        "dry_run": dry_run,
    }

    # Helper to clean a task description (remove tags, date markers, priority icons)
    def clean_description(text: str) -> str:
        """Remove tags (#tag), date markers (📅 YYYY-MM-DD), priority icons."""
        # Remove tags
        words = text.split()
        words = [w for w in words if not w.startswith("#")]
        text = " ".join(words)
        # Remove date marker 📅 YYYY-MM-DD
        text = re.sub(r"📅\s*\d{4}-\d{2}-\d{2}", "", text)
        # Remove priority icons
        for icon in ("⏫", "🔺", "🔽"):
            text = text.replace(icon, "")
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # Process each note
    for note_rel, note_tasks in notes_dict.items():
        note_abs = vault_root / note_rel
        if not note_abs.exists():
            stats["skipped_notes"] += 1
            stats["errors"].append(f"Note not found: {note_rel}")
            continue

        try:
            with open(note_abs, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            stats["skipped_notes"] += 1
            stats["errors"].append(f"Could not read {note_rel}: {e}")
            continue

        # Determine which lines to delete
        lines_to_delete = set()
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            # Check if this line is a completed task ([x] or [X])
            if not re.match(r"^[ \t]*[-*+][ \t]+\[[xX]\]", line_stripped):
                continue
            # Remove bullet and checkbox
            desc_start = line_stripped.find("]") + 1
            raw_desc = line_stripped[desc_start:].strip()
            cleaned_desc = clean_description(raw_desc)
            for task in note_tasks:
                cached_desc = task.get("task", "")
                if cached_desc and cached_desc == cleaned_desc:
                    # Exact match
                    lines_to_delete.add(i)
                    # If dry run, print the line that would be deleted
                    if dry_run:
                        print(f"DRY RUN: Would delete line {i+1} in {note_rel}: {line_stripped}")
                    break

        if not lines_to_delete:
            stats["skipped_notes"] += 1
            continue

        if not dry_run:
            # Write back the file with those lines removed
            new_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
            try:
                with open(note_abs, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception as e:
                stats["errors"].append(f"Could not write {note_rel}: {e}")
                continue

        stats["tasks_deleted"] += len(lines_to_delete)
        if not dry_run:
            stats["files_modified"] += 1

    return stats


def delete_completed_tasks(
    vault_path: Optional[str] = None,
    cache_file_path: Optional[str] = None,
    refresh_cache: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    High‑level function to delete completed tasks from an Obsidian vault.

    Parameters
    ----------
    vault_path : str, optional
        Path to Obsidian vault root. Defaults from OVTM_VAULT_PATH environment variable.
    cache_file_path : str, optional
        Path to JSON cache file. Defaults from OVTM_TASK_CACHE_FILEPATH.
    refresh_cache : bool, default False
        If True, refresh the cache before deletion.
    dry_run : bool, default False
        If True, only simulate deletion and report what would be deleted.

    Returns
    -------
    Dict[str, Any]
        Statistics from delete_completed_tasks_per_cache.
    """
    # Load environment variables from .env file if available
    load_env()
    if vault_path is not None:
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
    if cache_file_path is None:
        cache_file_path = os.environ.get("OVTM_TASK_CACHE_FILEPATH")
        if cache_file_path is None:
            raise ValueError(
                "cache_file_path must be provided or OVTM_TASK_CACHE_FILEPATH must be set"
            )

    vault_path = Path(vault_path).expanduser().resolve()
    cache_file_path = Path(cache_file_path).expanduser().resolve()

    if refresh_cache:
        refresh_tasks_cache(str(vault_path), str(cache_file_path))

    return delete_completed_tasks_per_cache(
        str(vault_path), str(cache_file_path), dry_run
    )


