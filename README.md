# Obsidian Task Management

[![Public Repository](https://img.shields.io/badge/Repository-Public-brightgreen)](https://github.com/jarvisanwyl/obsidian-task-management)

A Python utility for managing tasks in Obsidian vaults.

## Overview
This tool helps maintain task lists in Obsidian markdown files by:
- Removing completed tasks (`[x]`) to reduce clutter
- Exporting active tasks to JSON for overview and external processing

## Installation

### From GitHub (remote)
The easiest way to install the latest version directly from the public repository:

```bash
pipx install git+https://github.com/jarvisanwyl/obsidian-task-management.git
```

Or with pip (global or virtual environment):

```bash
pip install git+https://github.com/jarvisanwyl/obsidian-task-management.git
```

### From local source
If you have cloned the repository locally:

```bash
pipx install .
```

```bash
pip install .
```

After installation, the command `obsidian-task-management` is available globally. You can also run the module directly with `python -m obsidian_tasks`.

## Quick Start

### Option 1: Install from GitHub
```bash
pipx install git+https://github.com/jarvisanwyl/obsidian-task-management.git
obsidian-task-management --help
```

### Option 2: Clone and install locally
```bash
git clone https://github.com/jarvisanwyl/obsidian-task-management.git
cd obsidian-task-management
pipx install .  # or pip install .
obsidian-task-management --help
```

### Option 3: Run without installing
```bash
git clone https://github.com/jarvisanwyl/obsidian-task-management.git
cd obsidian-task-management
python -m obsidian_tasks --help
```

### Configuration
Set environment variables `OVTM_VAULT_PATH` and `OVTM_TASK_CACHE_FILEPATH` or pass them via command line.

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