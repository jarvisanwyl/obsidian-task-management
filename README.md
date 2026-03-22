# Obsidian Task Management

A Python utility for managing tasks in Obsidian vaults.

## Overview
This tool helps maintain task lists in Obsidian markdown files by:
- Removing completed tasks (`[x]`) to reduce clutter
- Exporting active tasks to JSON for overview and external processing

## Quick Start
1. Ensure you have Python 3.12+ and UV installed
2. Clone this repository
3. Run with:
   ```bash
   uv run python src/main.py --help
   ```

## Features
- **Clean completed tasks**: Automatically remove checked-off tasks from markdown files
- **Export active tasks**: Generate JSON overview of all pending tasks with metadata
- **Safe operations**: Dry-run mode available before making changes
- **Flexible configuration**: Customize task patterns and output formats

## Project Structure
```
obsidian-task-management/
├── src/                    # Source code
├── tests/                  # Test files
├── pyproject.toml         # Project dependencies
├── README.md              # This file
└── specification.md       # Detailed specification
```

## Development
See `specification.md` for detailed requirements and implementation notes.