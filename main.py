#!/usr/bin/env python3
"""
Obsidian Task Management - Command line interface.
"""

import argparse
import sys
from pathlib import Path
import os

# Import core functions
try:
    from obsidian_tasks import refresh_tasks_cache
except ImportError:
    print("Error: Could not import obsidian_tasks module.")
    sys.exit(1)


def clean_tasks(vault_path: Path, dry_run: bool = False):
    """Delete completed tasks from markdown files."""
    # TODO: Implement
    print(f"Cleaning completed tasks in {vault_path} (dry_run={dry_run})")
    print("Not implemented yet.")


def main():
    parser = argparse.ArgumentParser(
        description="Manage tasks in an Obsidian vault.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --vault ~/obsidian-vault --clean --dry-run
  %(prog)s --vault ~/obsidian-vault --clean
  %(prog)s --refresh-cache
  %(prog)s --vault ~/obsidian-vault --cache-file ~/tasks.json

Environment variables:
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
    if args.clean and args.refresh_cache:
        parser.error("--clean and --refresh-cache are mutually exclusive")

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
        clean_tasks(Path(vault_path).expanduser().resolve(), dry_run=args.dry_run)
    elif args.refresh_cache:
        refresh_tasks_cache(vault_path, cache_file_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()