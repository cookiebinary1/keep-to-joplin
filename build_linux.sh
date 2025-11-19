#!/bin/bash
# Build script for keep_to_joplin GUI executable for Linux using PyInstaller
# This script uses the private .venv to avoid breaking system Python

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing/upgrading dependencies..."
pip install --upgrade pyinstaller PyQt6 > /dev/null 2>&1

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Build the executable
echo "Building standalone executable for Linux..."
python -m PyInstaller \
    --onefile \
    --name keep_to_joplin \
    --windowed \
    keep_to_joplin_gui.py

echo ""
echo "Build complete! Executable is at: dist/keep_to_joplin"
echo "Size: $(ls -lh dist/keep_to_joplin | awk '{print $5}')"
echo ""
echo "To test the GUI, run: ./dist/keep_to_joplin"

