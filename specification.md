# Obsidian Task Management - Specification

## Purpose
This Python script manages tasks within an Obsidian vault. It provides two main functions:
1. Delete all completed tasks (marked with `[x]`) from markdown files in the vault
2. Export all active tasks to a JSON file for external processing

## Problem Statement
Obsidian vaults often contain many task lists in markdown files. Completed tasks (`[x]`) accumulate over time and clutter notes. Additionally, there's no easy way to get an overview of all active tasks across the entire vault with their metadata (due dates, priorities, etc.).

## Inputs
- **Vault path**: Path to Obsidian vault root directory. Default from environment variable `OVTM_VAULT_PATH`, overridden by command‑line argument.
- **Cache file path**: Where to write the tasks JSON cache. Default from environment variable `OVTM_TASK_CACHE_FILEPATH`, overridden by command‑line argument.
- (Optional) Configuration for task patterns and filtering (future)

## Outputs
1. **Clean vault**: Markdown files with completed tasks removed
2. **Tasks cache JSON**: File containing all active tasks from notes with `status: active`, structured as:
   - `task`: Description text
   - `due_date`: ISO date (`YYYY‑MM‑DD`) if present, else `null`
   - `priority`: `"high"`, `"medium"`, `"low"` (mapped from icons), else `null`
   - `note_path`: Relative path from vault root
   - `note_tags`: List of tags from note frontmatter
   - `task_tags`: List of tags attached to the specific task

## Requirements

### Function 1: Delete Completed Tasks
- Find all markdown files (`.md`) in the vault
- Identify completed tasks: lines containing `[x]` between square brackets (e.g., `- [x] Task description`)
- Remove these lines from the files
- Preserve file structure and other content
- Handle edge cases: tasks with nested checkboxes, tasks with additional metadata

### Function 2: Refresh Tasks Cache
- **Parameters**: `vault_path` (str), `task_cache_file_path` (str)
- **Defaults**: Environment variables `OVTM_VAULT_PATH` and `OVTM_TASK_CACHE_FILEPATH` provide defaults; arguments override them.
- **File filtering**:
  1. Scan all `.md` files in the vault (recursively)
  2. Skip files that do not contain an opening square bracket `[` (quick filter)
  3. For remaining files, read frontmatter (YAML between `---` delimiters)
  4. Keep only files whose frontmatter includes `status: active`
- **Task extraction**: For each kept file, locate all task lines:
  - Active tasks: lines containing `[ ]` (empty checkbox)
  - Optionally also capture completed tasks `[x]` for reporting (but not for cache)
- **Task parsing**: For each task line extract:
  - `task`: The description text after the checkbox (trimmed)
  - `due_date`: If a date in ISO format `YYYY‑MM‑DD` appears (e.g., `📅 2026‑03‑25`), capture it; otherwise `null`
  - `priority`: If a priority icon (`⏫`, `🔺`, `🔽` or similar) appears, map to `"high"`, `"medium"`, `"low"`; otherwise `null`
  - `note_path`: Path relative to vault root (e.g., `"folder/note.md"`)
  - `note_tags`: List of tags from the note's frontmatter (field `tags`, usually a YAML list)
  - `task_tags`: List of tags attached to this specific task (tags that appear inline, e.g., `#tag`)
- **Output JSON**:
  ```json
  [
    {
      "task": "Task description",
      "due_date": "2026‑03‑25",   // optional, null if not present
      "priority": "high",          // optional, null if not present
      "note_path": "folder/note.md",
      "note_tags": ["project", "meeting"],
      "task_tags": ["urgent", "review"]
    }
  ]
  ```
- **Performance**: Use efficient scanning; avoid reading entire vault into memory.

## Implementation Notes
- Use regex patterns to identify tasks and extract metadata
- Process files efficiently (consider large vaults with thousands of files)
  - First filter: skip `.md` files that don't contain an opening square bracket `[`
  - Second filter: read frontmatter (YAML between `---`) and keep only notes with `status: active`
- Frontmatter parsing: implement a simple YAML subset parser for `status` and `tags` fields (no external dependency). If more complex frontmatter is needed later, consider adding `pyyaml` dependency.
- Create backup of files before deletion (or implement dry-run mode)
- Command-line interface with options for each function
- Logging for operations performed
- Environment variables `OVTM_VAULT_PATH` and `OVTM_TASK_CACHE_FILEPATH` provide defaults; can be set in `.env` file (python‑dotenv optional dependency)

## Usage Examples
```bash
# Delete completed tasks (dry run first)
python obsidian_tasks.py --vault ~/obsidian-vault --clean --dry-run

# Delete completed tasks (actual)
python obsidian_tasks.py --vault ~/obsidian-vault --clean

# Refresh tasks cache (using environment variables for paths)
python obsidian_tasks.py --refresh-cache

# Refresh tasks cache with explicit paths
python obsidian_tasks.py --vault ~/obsidian-vault --cache-file ~/tasks.json
```

## Dependencies
- Python 3.12+
- Standard library plus optional python‑dotenv for .env loading:
  - `re` for regex patterns
  - `json` for JSON output
  - `pathlib` for file operations
  - `argparse` for CLI
  - `yaml` (simple custom parser) for frontmatter parsing (subset of YAML for `status` and `tags` fields only)
  - `python‑dotenv` (optional) for loading environment variables from `.env` files

## Future Enhancements
- Support for different task formats (dataview, tasks plugin)
- Filtering by tags, folders, or date ranges
- Integration with Obsidian's internal task management
- Scheduled runs via cron