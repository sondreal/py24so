#!/usr/bin/env python3
"""
Format all Python code in the repository with Black and isort.

Usage:
    python scripts/format_code.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, **kwargs):
    """Run a command and print its output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        # Use UTF-8 encoding explicitly to handle special characters on Windows
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding="utf-8",  # Explicitly set encoding
            errors="replace",  # Replace invalid characters
            **kwargs
        )
        print(result.stdout)
        return result.returncode
    except UnicodeDecodeError:
        # Fallback for encoding errors
        print("Warning: Encountered encoding issues. Running command without capturing output...")
        result = subprocess.run(cmd)
        return result.returncode


def main():
    """Main function."""
    # Get the repository root directory
    repo_root = Path(__file__).parent.parent.absolute()
    
    # Change to the repository root
    os.chdir(repo_root)
    
    # Directories to format
    dirs = ["py24so", "tests"]
    
    # Format with Black
    black_result = run_command(["black"] + dirs)
    
    # Sort imports with isort
    isort_result = run_command(["isort"] + dirs)
    
    # Return error code if any command failed
    return max(black_result, isort_result)


if __name__ == "__main__":
    sys.exit(main()) 