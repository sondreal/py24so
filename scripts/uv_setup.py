#!/usr/bin/env python
"""
UV setup helper script for the py24so package.

This script helps with common UV-related development tasks.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and handle errors."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=capture_output)
    return result


def create_venv(args):
    """Create a virtual environment using UV."""
    venv_path = Path(args.path) if args.path else Path(".venv")
    
    cmd = ["uv", "venv", "--python", args.python]
    if venv_path.name != ".venv":
        cmd.extend(["--name", str(venv_path)])
    
    run_command(cmd)
    
    print(f"\nVirtual environment created at: {venv_path}")
    print("\nTo activate the virtual environment:")
    if os.name == "nt":  # Windows
        print(f"{venv_path}\\Scripts\\activate")
    else:  # Unix/macOS
        print(f"source {venv_path}/bin/activate")


def install_deps(args):
    """Install dependencies using UV."""
    cmd = ["uv", "pip", "install"]
    
    if args.editable:
        cmd.append("-e")
        
    if args.dev:
        cmd.append(".[dev,docs]")
    elif args.http2:
        cmd.append(".[http2]")
    else:
        cmd.append(".")
        
    if args.upgrade:
        cmd.append("--upgrade")
        
    run_command(cmd)


def sync_deps(args):
    """Sync dependencies from pyproject.toml using UV."""
    cmd = ["uv", "pip", "sync"]
    
    if args.prod_only:
        cmd.append("--only-prod")
        
    if args.dev:
        cmd.append("--dev")
        
    run_command(cmd)
    

def build_package(args):
    """Build package using UV."""
    cmd = ["uv", "pip", "build"]
    
    if args.wheel:
        cmd.append("--wheel")
    elif args.sdist:
        cmd.append("--sdist")
    else:
        cmd.extend(["--wheel", "--sdist"])  # Default behavior
        
    run_command(cmd)


def publish_package(args):
    """Publish package to PyPI using UV."""
    cmd = ["uv", "pip", "publish"]
    
    if args.test:
        cmd.append("--repository=testpypi")
        
    run_command(cmd)


def main():
    """Parse arguments and execute the requested command."""
    parser = argparse.ArgumentParser(description="UV helper script for py24so")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # venv command
    venv_parser = subparsers.add_parser("venv", help="Create a virtual environment")
    venv_parser.add_argument("--path", help="Path to create the virtual environment")
    venv_parser.add_argument("--python", default="python3", 
                            help="Python interpreter to use (default: python3)")
    
    # install command
    install_parser = subparsers.add_parser("install", help="Install dependencies")
    install_parser.add_argument("--editable", "-e", action="store_true", 
                               help="Install in editable mode")
    install_parser.add_argument("--dev", action="store_true", 
                               help="Install development dependencies")
    install_parser.add_argument("--http2", action="store_true", 
                               help="Install with HTTP/2 support")
    install_parser.add_argument("--upgrade", "-U", action="store_true", 
                               help="Upgrade dependencies")
    
    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync dependencies")
    sync_parser.add_argument("--prod-only", action="store_true", 
                            help="Only sync production dependencies")
    sync_parser.add_argument("--dev", action="store_true", 
                            help="Sync development dependencies")
    
    # build command
    build_parser = subparsers.add_parser("build", help="Build package")
    build_parser.add_argument("--wheel", action="store_true", 
                             help="Build wheel only")
    build_parser.add_argument("--sdist", action="store_true", 
                             help="Build source distribution only")
    
    # publish command
    publish_parser = subparsers.add_parser("publish", help="Publish package to PyPI")
    publish_parser.add_argument("--test", action="store_true", 
                               help="Publish to TestPyPI")
    
    args = parser.parse_args()
    
    # Execute the requested command
    if args.command == "venv":
        create_venv(args)
    elif args.command == "install":
        install_deps(args)
    elif args.command == "sync":
        sync_deps(args)
    elif args.command == "build":
        build_package(args)
    elif args.command == "publish":
        publish_package(args)
    else:
        parser.print_help()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main()) 