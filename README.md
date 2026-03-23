# Obsidian Task Management

A Python utility for managing tasks in Obsidian vaults.

## Overview
This tool helps maintain task lists in Obsidian markdown files by:
- Removing completed tasks (`[x]`) to reduce clutter
- Exporting active tasks to JSON for overview and external processing

## Installation

### Via pipx (recommended)
```bash
pipx install .
```

### Via pip (global or virtual environment)
```bash
pip install .
```

After installation, the command `obsidian-task-management` is available globally. You can also run the module directly with `python -m obsidian_tasks`.

## Quick Start
1. Clone this repository
2. Install (see above) or run directly:
   ```bash
   python -m obsidian_tasks --help
   ```
3. Configure environment variables `OVTM_VAULT_PATH` and `OVTM_TASK_CACHE_FILEPATH` or pass them via command line.

## Features
- **Clean completed tasks**: Automatically remove checked-off tasks from markdown files
- **Export active tasks**: Generate JSON overview of all pending tasks with metadata
- **Safe operations**: Dry-run mode available before making changes
- **Flexible configuration**: Customize task patterns and output formats

## Project Structure
```
obsidian-task-management/
├── src/
│   └── obsidian_tasks/    # Package source (__init__.py, cli.py, __main__.py)
├── tests/                  # Test files
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # This file
└── specification.md       # Detailed specification
```

## Development
See `specification.md` for detailed requirements and implementation notes.