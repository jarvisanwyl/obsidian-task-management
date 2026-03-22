# Obsidian Task Management - Specification

## Purpose
This Python script manages tasks within an Obsidian vault. It provides two main functions:
1. Delete all completed tasks (marked with `[x]`) from markdown files in the vault
2. Export all active tasks to a JSON file for external processing

## Problem Statement
Obsidian vaults often contain many task lists in markdown files. Completed tasks (`[x]`) accumulate over time and clutter notes. Additionally, there's no easy way to get an overview of all active tasks across the entire vault with their metadata (due dates, priorities, etc.).

## Inputs
- Path to Obsidian vault root directory
- (Optional) Output directory for JSON export
- (Optional) Configuration for task patterns and filtering

## Outputs
1. **Clean vault**: Markdown files with completed tasks removed
2. **JSON export**: File containing all active tasks with structured data:
   - Task name/description
   - Due date (ISO format YYYY-MM-DD) if present
   - Priority indicator if present
   - Path to note (relative to vault root)
   - Note name (filename)

## Requirements

### Function 1: Delete Completed Tasks
- Find all markdown files (`.md`) in the vault
- Identify completed tasks: lines containing `[x]` between square brackets (e.g., `- [x] Task description`)
- Remove these lines from the files
- Preserve file structure and other content
- Handle edge cases: tasks with nested checkboxes, tasks with additional metadata

### Function 2: Export Active Tasks to JSON
- Find all markdown files in the vault
- Identify active tasks: lines containing `[ ]` (empty checkbox) between square brackets
- Parse each task for:
  - Task description (text after checkbox)
  - Due date: pattern like `📅 YYYY-MM-DD` or similar date format
  - Priority: indicators like `⏫` (high), `🔺` (medium), `🔽` (low) or similar
  - Note metadata: file path and name
- Output JSON structure:
  ```json
  [
    {
      "task": "Task description",
      "due_date": "2026-03-25",  // optional, null if not present
      "priority": "high",         // optional, null if not present
      "note_path": "folder/note.md",
      "note_name": "note.md"
    }
  ]
  ```

## Implementation Notes
- Use regex patterns to identify tasks and extract metadata
- Process files efficiently (consider large vaults with thousands of files)
- Create backup of files before deletion (or implement dry-run mode)
- Command-line interface with options for each function
- Logging for operations performed

## Usage Examples
```bash
# Delete completed tasks (dry run first)
python obsidian_tasks.py --vault ~/obsidian-vault --clean --dry-run

# Delete completed tasks (actual)
python obsidian_tasks.py --vault ~/obsidian-vault --clean

# Export active tasks to JSON
python obsidian_tasks.py --vault ~/obsidian-vault --export --output tasks.json
```

## Dependencies
- Python 3.12+
- Standard library only (no external packages initially):
  - `re` for regex patterns
  - `json` for JSON output
  - `pathlib` for file operations
  - `argparse` for CLI

## Future Enhancements
- Support for different task formats (dataview, tasks plugin)
- Filtering by tags, folders, or date ranges
- Integration with Obsidian's internal task management
- Scheduled runs via cron