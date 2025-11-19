#!/bin/bash
# Test script to verify the GUI executable works

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

EXECUTABLE="dist/keep_to_joplin"

if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: Executable not found at $EXECUTABLE"
    echo "Please run ./build_macos.sh first"
    exit 1
fi

echo "Testing GUI executable..."
echo "Executable: $EXECUTABLE"
echo "Size: $(ls -lh "$EXECUTABLE" | awk '{print $5}')"
echo "Type: $(file "$EXECUTABLE")"
echo ""

# Check if executable is actually executable
if [ ! -x "$EXECUTABLE" ]; then
    echo "Warning: File is not executable, fixing permissions..."
    chmod +x "$EXECUTABLE"
fi

# Test CLI version first (dry-run)
echo "Testing CLI functionality (dry-run)..."
if [ -d "Takeout/Keep" ]; then
    "$EXECUTABLE" --dry-run --input Takeout/Keep --output /tmp/joplin_test_out 2>&1 | head -20
    echo ""
    echo "CLI test completed. Check output above for any errors."
else
    echo "Warning: Takeout/Keep directory not found, skipping CLI test"
fi

echo ""
echo "To test the GUI interactively, run:"
echo "  ./dist/keep_to_joplin"
echo ""
echo "Or double-click the executable in Finder."

