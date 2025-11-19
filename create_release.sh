#!/bin/bash
# Script to create GitHub release archives for multiple platforms
# Usage: ./create_release.sh <version> [release_notes]

set -e

VERSION="$1"
RELEASE_NOTES="$2"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [release_notes]"
    echo "Example: $0 v1.0.0 'Initial release'"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCHIVES=()

# macOS
if [ -d "dist/keep_to_joplin.app" ]; then
    ZIP_NAME="keep-to-joplin-${VERSION}-macos.zip"
    echo "Creating macOS archive..."
    cd dist
    zip -r "../${ZIP_NAME}" keep_to_joplin.app > /dev/null
    cd ..
    ARCHIVES+=("${ZIP_NAME}")
    echo "✓ Created: ${ZIP_NAME}"
fi

# Linux
if [ -f "dist/keep_to_joplin" ] && [ ! -d "dist/keep_to_joplin.app" ]; then
    ZIP_NAME="keep-to-joplin-${VERSION}-linux.zip"
    echo "Creating Linux archive..."
    cd dist
    zip "../${ZIP_NAME}" keep_to_joplin > /dev/null
    cd ..
    ARCHIVES+=("${ZIP_NAME}")
    echo "✓ Created: ${ZIP_NAME}"
fi

# Windows
if [ -f "dist/keep_to_joplin.exe" ]; then
    ZIP_NAME="keep-to-joplin-${VERSION}-windows.zip"
    echo "Creating Windows archive..."
    cd dist
    zip "../${ZIP_NAME}" keep_to_joplin.exe > /dev/null
    cd ..
    ARCHIVES+=("${ZIP_NAME}")
    echo "✓ Created: ${ZIP_NAME}"
fi

if [ ${#ARCHIVES[@]} -eq 0 ]; then
    echo "Error: No built executables found in dist/"
    echo "Run the appropriate build script first:"
    echo "  - macOS: ./build.sh"
    echo "  - Linux: ./build-linux.sh"
    echo "  - Windows: build-windows.bat"
    exit 1
fi

echo ""
echo "Release archives created:"
for archive in "${ARCHIVES[@]}"; do
    echo "  - ${archive}"
done
echo ""

# Create GitHub release command
ARCHIVE_ARGS=$(IFS=' '; echo "${ARCHIVES[*]}")
echo "To create a GitHub release:"
echo "  gh release create ${VERSION} ${ARCHIVE_ARGS} --title 'Release ${VERSION}' --notes '${RELEASE_NOTES:-Release ${VERSION}}'"
echo ""

