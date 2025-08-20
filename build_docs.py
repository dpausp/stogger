#!/usr/bin/env python3
"""
Build script for nicestlog documentation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        subprocess.run(
            cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True
        )
        print(f"✅ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {cmd}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main build function."""
    print("🚀 Building nicestlog documentation...")

    # Change to docs directory
    docs_dir = Path(__file__).parent / "docs"
    if not docs_dir.exists():
        print("❌ docs/ directory not found!")
        return 1

    os.chdir(docs_dir)

    # Clean previous build
    build_dir = docs_dir / "_build"
    if build_dir.exists():
        print("🧹 Cleaning previous build...")
        shutil.rmtree(build_dir)

    # Install dependencies (if using pip)
    print("📦 Installing documentation dependencies...")
    if not run_command("python -m pip install -r requirements.txt"):
        print("⚠️  Could not install via pip, trying with uv...")
        if not run_command("uv pip install -r requirements.txt"):
            print("❌ Failed to install dependencies!")
            return 1

    # Build HTML documentation
    print("📚 Building HTML documentation...")
    if not run_command("python -m sphinx -b html . _build/html"):
        print("❌ Failed to build documentation!")
        return 1

    # Success!
    html_path = build_dir / "html" / "index.html"
    print("✨ Documentation built successfully!")
    print(f"📖 Open: {html_path.absolute()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
