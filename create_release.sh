#!/bin/bash
# Script to create a GitHub release with the built executable
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

# Check if dist/keep_to_joplin.app exists
if [ ! -d "dist/keep_to_joplin.app" ]; then
    echo "Error: dist/keep_to_joplin.app not found. Run ./build.sh first."
    exit 1
fi

# Create a zip file for distribution
ZIP_NAME="keep-to-joplin-${VERSION}-macos.zip"
echo "Creating zip archive..."
cd dist
zip -r "../${ZIP_NAME}" keep_to_joplin.app > /dev/null
cd ..

echo ""
echo "Release archive created: ${ZIP_NAME}"
echo ""
echo "To create a GitHub release:"
echo "1. Go to: https://github.com/cookiebinary1/keep-to-joplin/releases/new"
echo "2. Tag: ${VERSION}"
echo "3. Title: Release ${VERSION}"
echo "4. Description: ${RELEASE_NOTES:-Release ${VERSION}}"
echo "5. Upload: ${ZIP_NAME}"
echo ""
echo "Or use GitHub CLI (if installed):"
echo "  gh release create ${VERSION} ${ZIP_NAME} --title 'Release ${VERSION}' --notes '${RELEASE_NOTES:-Release ${VERSION}}'"
echo ""

