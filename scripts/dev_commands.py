#!/usr/bin/env python
"""
Development commands for the py24so package.

This script provides a list of common commands for development.
"""

import sys
from pathlib import Path


def main():
    """Display available development commands."""
    commands = [
        ("Install development dependencies (pip)", "pip install -e '.[dev,docs]'"),
        ("Install development dependencies (uv)", "uv pip install -e '.[dev,docs]'"),
        ("Run tests", "pytest"),
        ("Run tests with coverage", "pytest --cov=py24so"),
        ("Run linting", "ruff check py24so tests examples"),
        ("Run type checking", "mypy py24so tests examples"),
        ("Format code", "black py24so tests examples && isort py24so tests examples"),
        ("Build package (pip)", "python -m build"),
        ("Build package (uv)", "uv pip build"),
        ("Generate docs", "mkdocs build"),
        ("Serve docs locally", "mkdocs serve"),
    ]
    
    print("py24so Development Commands\n")
    print("Available commands:")
    
    for i, (description, command) in enumerate(commands, 1):
        print(f"{i}. {description}")
        print(f"   $ {command}")
        print()
    
    print("Development setup with pip:")
    print("1. Create a virtual environment: python -m venv .venv")
    print("2. Activate the virtual environment:")
    print("   - Windows: .venv\\Scripts\\activate")
    print("   - Unix/MacOS: source .venv/bin/activate")
    print("3. Install dev dependencies: pip install -e '.[dev,docs]'")
    
    print("\nDevelopment setup with UV:")
    print("1. Create a virtual environment: uv venv")
    print("2. Activate the virtual environment:")
    print("   - Windows: .venv\\Scripts\\activate")
    print("   - Unix/MacOS: source .venv/bin/activate")
    print("3. Install dev dependencies: uv pip install -e '.[dev,docs]'")
    
    return 0


if __name__ == "__main__":
    # Make sure the scripts directory is created
    scripts_dir = Path(__file__).parent
    scripts_dir.mkdir(exist_ok=True)
    
    sys.exit(main()) 