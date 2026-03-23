#!/usr/bin/env python3
"""
Obsidian Task Management - Command line interface.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import os

# Import core functions
try:
    from . import refresh_tasks_cache, delete_completed_tasks, load_env
except ImportError:
    print("Error: Could not import obsidian_tasks module.")
    sys.exit(1)


def clean_tasks(
    vault_path: Path,
    cache_file_path: Optional[Path],
    dry_run: bool = False,
    refresh_cache: bool = False,
) -> None:
    """
    Delete completed tasks from markdown files.
    """
    try:
        stats = delete_completed_tasks(
            vault_path=str(vault_path),
            cache_file_path=str(cache_file_path) if cache_file_path else None,
            refresh_cache=refresh_cache,
            dry_run=dry_run,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("\n=== Deletion Statistics ===")
    print(f"Tasks deleted: {stats['tasks_deleted']}")
    print(f"Files modified: {stats['files_modified']}")
    print(f"Skipped notes: {stats['skipped_notes']}")
    if stats.get('dry_run'):
        print("(Dry run – no changes were written)")
    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for err in stats['errors']:
            print(f"  - {err}")


def main():
    # Load environment variables from .env file if available
    load_env()
    
    parser = argparse.ArgumentParser(
        description="Manage tasks in an Obsidian vault.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --vault ~/obsidian-vault --clean --dry-run
  %(prog)s --vault ~/obsidian-vault --clean
  %(prog)s --vault ~/obsidian-vault --clean --refresh-cache
  %(prog)s --refresh-cache
  %(prog)s --vault ~/obsidian-vault --cache-file ~/tasks.json

Environment variables (can be set in .env file):
  OVTM_VAULT_PATH          default vault path
  OVTM_TASK_CACHE_FILEPATH default cache file path
""",
    )

    # Vault path (optional, uses env var)
    parser.add_argument(
        "--vault",
        dest="vault_path",
        help="Path to Obsidian vault root (overrides OVTM_VAULT_PATH)",
    )

    # Actions
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete completed tasks ([x]) from markdown files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files (requires --clean)",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Scan vault for active tasks and write JSON cache",
    )
    parser.add_argument(
        "--cache-file",
        dest="cache_file_path",
        help="Path to write tasks cache (overrides OVTM_TASK_CACHE_FILEPATH)",
    )
    

    args = parser.parse_args()

    # Validate arguments
    # (--clean and --refresh‑cache can be combined; refresh‑cache will run before deletion)

    if args.dry_run and not args.clean:
        parser.error("--dry-run requires --clean")

    # Determine vault path
    vault_path = args.vault_path or os.environ.get("OVTM_VAULT_PATH")
    if (args.clean or args.refresh_cache) and vault_path is None:
        parser.error(
            "Vault path must be provided via --vault or OVTM_VAULT_PATH environment variable"
        )

    # Determine cache file path
    cache_file_path = args.cache_file_path or os.environ.get(
        "OVTM_TASK_CACHE_FILEPATH"
    )
    if args.refresh_cache and cache_file_path is None:
        parser.error(
            "Cache file path must be provided via --cache-file or OVTM_TASK_CACHE_FILEPATH environment variable"
        )

    # Execute actions
    if args.clean:
        cache_path = Path(cache_file_path).expanduser().resolve() if cache_file_path else None
        clean_tasks(
            vault_path=Path(vault_path).expanduser().resolve(),
            cache_file_path=cache_path,
            dry_run=args.dry_run,
            refresh_cache=args.refresh_cache,
        )
    elif args.refresh_cache:
        refresh_tasks_cache(vault_path, cache_file_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()