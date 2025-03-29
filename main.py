"""
py24so - Python wrapper for 24SevenOffice API

This script provides information about the py24so package and how to use it.
For actual usage, you should import the package in your code.
"""

import sys
from py24so import __version__


def main():
    """Display information about the package."""
    print(f"py24so v{__version__} - Python wrapper for 24SevenOffice API")
    print("\nThis is a library package and is not meant to be run directly.")
    print("For usage examples, see the examples directory.")
    
    print("\nBasic usage:")
    print("  from py24so import Client24SO")
    print("  client = Client24SO(client_id, client_secret, organization_id)")
    print("  customers = client.customers.list()")
    
    print("\nInstallation options:")
    print("  Using pip:")
    print("    pip install py24so")
    print("    pip install py24so[http2]  # With HTTP/2 support")
    
    print("  Using UV (faster):")
    print("    uv pip install py24so")
    print("    uv pip install py24so[http2]  # With HTTP/2 support")
    
    print("\nDevelopment setup:")
    print("  Using the Makefile (recommended):")
    print("    make venv        # Create virtual environment")
    print("    make install-dev # Install development dependencies")
    print("    make test        # Run tests")
    print("    make format      # Format code")
    print("    make lint        # Run linters")
    
    print("  Manually with UV:")
    print("    uv venv")
    print("    uv pip install -e \".[dev,docs]\"")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
