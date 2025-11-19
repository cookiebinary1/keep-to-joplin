#!/bin/bash
# Script to create GitHub release archives for multiple platforms
# Usage: ./create_release.sh <version> [release_notes] [--auto]
#
# Options:
#   --auto    Automatically create GitHub release using gh CLI

set -e

VERSION="$1"
RELEASE_NOTES="$2"
AUTO_RELEASE=false

# Check for --auto flag
if [[ "$2" == "--auto" ]] || [[ "$3" == "--auto" ]]; then
    AUTO_RELEASE=true
    if [[ "$2" == "--auto" ]]; then
        RELEASE_NOTES=""
    fi
fi

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [release_notes] [--auto]"
    echo "Example: $0 v1.0.0 'Initial release'"
    echo "Example: $0 v1.0.0 'Initial release' --auto  # Auto-create GitHub release"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "Error: dist/ directory not found"
    echo "Run the appropriate build script first:"
    echo "  - macOS: ./build.sh"
    echo "  - Linux: ./build-linux.sh"
    echo "  - Windows: build-windows.bat"
    exit 1
fi

ARCHIVES=()

# macOS - check for .app bundle
if [ -d "dist/keep_to_joplin.app" ]; then
    ZIP_NAME="keep-to-joplin-${VERSION}-macos.zip"
    echo "Creating macOS archive..."
    cd dist
    zip -r "../${ZIP_NAME}" keep_to_joplin.app > /dev/null 2>&1
    cd ..
    if [ -f "${ZIP_NAME}" ]; then
        ARCHIVES+=("${ZIP_NAME}")
        echo "✓ Created: ${ZIP_NAME}"
    else
        echo "✗ Failed to create ${ZIP_NAME}"
    fi
fi

# Linux - check for executable (but not if macOS app or Windows exe exists)
if [ -f "dist/keep_to_joplin" ] && [ ! -d "dist/keep_to_joplin.app" ] && [ ! -f "dist/keep_to_joplin.exe" ]; then
    # Verify it's actually a Linux executable (if file command is available)
    IS_LINUX=true
    if command -v file &> /dev/null; then
        if ! file "dist/keep_to_joplin" | grep -qE "(ELF|executable|Linux)"; then
            IS_LINUX=false
        fi
    fi
    
    if [ "$IS_LINUX" = true ]; then
        ZIP_NAME="keep-to-joplin-${VERSION}-linux.zip"
        echo "Creating Linux archive..."
        cd dist
        zip "../${ZIP_NAME}" keep_to_joplin > /dev/null 2>&1
        cd ..
        if [ -f "${ZIP_NAME}" ]; then
            ARCHIVES+=("${ZIP_NAME}")
            echo "✓ Created: ${ZIP_NAME}"
        else
            echo "✗ Failed to create ${ZIP_NAME}"
        fi
    fi
fi

# Windows - check for .exe
if [ -f "dist/keep_to_joplin.exe" ]; then
    ZIP_NAME="keep-to-joplin-${VERSION}-windows.zip"
    echo "Creating Windows archive..."
    cd dist
    zip "../${ZIP_NAME}" keep_to_joplin.exe > /dev/null 2>&1
    cd ..
    if [ -f "${ZIP_NAME}" ]; then
        ARCHIVES+=("${ZIP_NAME}")
        echo "✓ Created: ${ZIP_NAME}"
    else
        echo "✗ Failed to create ${ZIP_NAME}"
    fi
fi

if [ ${#ARCHIVES[@]} -eq 0 ]; then
    echo ""
    echo "Error: No built executables found in dist/"
    echo ""
    echo "Found in dist/:"
    ls -la dist/ 2>/dev/null || echo "  (empty or does not exist)"
    echo ""
    echo "Run the appropriate build script first:"
    echo "  - macOS: ./build.sh"
    echo "  - Linux: ./build-linux.sh"
    echo "  - Windows: build-windows.bat"
    exit 1
fi

echo ""
echo "Release archives created:"
for archive in "${ARCHIVES[@]}"; do
    SIZE=$(ls -lh "${archive}" | awk '{print $5}')
    echo "  - ${archive} (${SIZE})"
done
echo ""

# Create GitHub release command or auto-create
ARCHIVE_ARGS=$(IFS=' '; echo "${ARCHIVES[*]}")

if [ "$AUTO_RELEASE" = true ]; then
    if ! command -v gh &> /dev/null; then
        echo "Error: GitHub CLI (gh) not found. Install it or use manual release."
        echo ""
        echo "Manual release command:"
        echo "  gh release create ${VERSION} ${ARCHIVE_ARGS} --title 'Release ${VERSION}' --notes '${RELEASE_NOTES:-Release ${VERSION}}'"
        exit 1
    fi
    
    echo "Creating GitHub release..."
    NOTES="${RELEASE_NOTES:-Release ${VERSION}}"
    if gh release create "${VERSION}" ${ARCHIVE_ARGS} --title "Release ${VERSION}" --notes "${NOTES}"; then
        echo ""
        echo "✓ GitHub release created successfully!"
        echo "  https://github.com/cookiebinary1/keep-to-joplin/releases/tag/${VERSION}"
    else
        echo ""
        echo "✗ Failed to create GitHub release"
        echo "You can try manually:"
        echo "  gh release create ${VERSION} ${ARCHIVE_ARGS} --title 'Release ${VERSION}' --notes '${NOTES}'"
        exit 1
    fi
else
    echo "To create a GitHub release:"
    echo "  gh release create ${VERSION} ${ARCHIVE_ARGS} --title 'Release ${VERSION}' --notes '${RELEASE_NOTES:-Release ${VERSION}}'"
    echo ""
    echo "Or use --auto flag to automatically create the release:"
    echo "  $0 ${VERSION} '${RELEASE_NOTES:-Release notes}' --auto"
    echo ""
fi

