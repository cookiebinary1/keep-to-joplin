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
    echo "  - macOS: ./build_macos.sh"
    echo "  - Linux: ./build_linux.sh"
    echo "  - Windows: build_windows.bat"
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

# Linux - check for executable and verify it's actually a Linux binary
if [ -f "dist/keep_to_joplin" ]; then
    # Verify it's actually a Linux executable (not macOS or Windows)
    IS_LINUX=false
    
    # Check if it's NOT a macOS app bundle (we already checked for .app separately)
    # Check if it's NOT a Windows exe (we already checked for .exe separately)
    # So if we have keep_to_joplin file, it should be Linux (or macOS binary, but we check with file command)
    
    if command -v file &> /dev/null; then
        FILE_TYPE=$(file "dist/keep_to_joplin" 2>/dev/null)
        # Check if it's an ELF binary (Linux) or contains "Linux" or "executable" but not "Mach-O" (macOS)
        if echo "$FILE_TYPE" | grep -qE "(ELF|Linux|executable)" && ! echo "$FILE_TYPE" | grep -qE "(Mach-O|macOS|Apple)"; then
            IS_LINUX=true
        fi
    else
        # If file command is not available, assume it's Linux if it's not .app or .exe
        # This is a fallback - ideally file command should be available
        IS_LINUX=true
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
    echo "  - macOS: ./build_macos.sh"
    echo "  - Linux: ./build_linux.sh"
    echo "  - Windows: build_windows.bat"
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
    
    # Check if release already exists
    if gh release view "${VERSION}" &>/dev/null; then
        echo "Warning: Release ${VERSION} already exists!"
        echo ""
        echo "Options:"
        echo "  1. Upload new files to existing release (recommended)"
        echo "  2. Delete existing release and create new one"
        echo "  3. Use a different version tag"
        echo ""
        echo "Uploading files to existing release..."
        NOTES="${RELEASE_NOTES:-Release ${VERSION}}"
        
        # Upload files to existing release
        UPLOAD_SUCCESS=true
        for archive in "${ARCHIVES[@]}"; do
            if ! gh release upload "${VERSION}" "${archive}" --clobber; then
                UPLOAD_SUCCESS=false
                echo "✗ Failed to upload ${archive}"
            else
                echo "✓ Uploaded ${archive}"
            fi
        done
        
        if [ "$UPLOAD_SUCCESS" = true ]; then
            echo ""
            echo "✓ Files uploaded to existing release successfully!"
            echo "  https://github.com/cookiebinary1/keep-to-joplin/releases/tag/${VERSION}"
            echo ""
            echo "Note: To update release notes, use:"
            echo "  gh release edit ${VERSION} --notes '${NOTES}'"
        else
            echo ""
            echo "✗ Some files failed to upload"
            echo ""
            echo "To manually upload files:"
            for archive in "${ARCHIVES[@]}"; do
                echo "  gh release upload ${VERSION} ${archive} --clobber"
            done
            exit 1
        fi
    else
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
    fi
else
    echo "To create a GitHub release:"
    echo "  gh release create ${VERSION} ${ARCHIVE_ARGS} --title 'Release ${VERSION}' --notes '${RELEASE_NOTES:-Release ${VERSION}}'"
    echo ""
    echo "Or use --auto flag to automatically create the release:"
    echo "  $0 ${VERSION} '${RELEASE_NOTES:-Release notes}' --auto"
    echo ""
fi

