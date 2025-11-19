#!/bin/bash
# Helper script for code signing and notarizing the macOS executable
# Requires: Apple Developer account and Xcode Command Line Tools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

EXECUTABLE="dist/keep_to_joplin"

if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: Executable not found at $EXECUTABLE"
    echo "Please run ./build_macos.sh first"
    exit 1
fi

echo "Code Signing and Notarization Helper"
echo "====================================="
echo ""

# Check for codesign
if ! command -v codesign &> /dev/null; then
    echo "Error: codesign not found. Please install Xcode Command Line Tools:"
    echo "  xcode-select --install"
    exit 1
fi

# List available signing identities
echo "Available code signing identities:"
echo "-----------------------------------"
security find-identity -v -p codesigning | grep "Developer ID" || {
    echo "No Developer ID found. You need a Developer ID Application certificate."
    echo "Get one from: https://developer.apple.com/account/resources/certificates/list"
    exit 1
}
echo ""

# Prompt for identity
read -p "Enter the full name of your Developer ID (or press Enter to skip signing): " SIGNING_IDENTITY

if [ -z "$SIGNING_IDENTITY" ]; then
    echo "Skipping code signing."
    exit 0
fi

# Sign the executable
echo ""
echo "Signing executable..."
codesign --force --deep --sign "$SIGNING_IDENTITY" "$EXECUTABLE"

# Verify signature
echo ""
echo "Verifying signature..."
codesign --verify --verbose "$EXECUTABLE" || {
    echo "Error: Signature verification failed"
    exit 1
}

echo "Signature verified successfully!"
echo ""

# Check if notarytool is available
if ! command -v xcrun notarytool &> /dev/null; then
    echo "Note: xcrun notarytool not found. Skipping notarization."
    echo "Notarization requires Xcode 13+ and an Apple Developer account."
    exit 0
fi

# Ask about notarization
read -p "Do you want to notarize the executable? (y/N): " NOTARIZE

if [ "$NOTARIZE" != "y" ] && [ "$NOTARIZE" != "Y" ]; then
    echo "Skipping notarization."
    exit 0
fi

echo ""
echo "Notarization requires:"
echo "  1. Apple ID email"
echo "  2. Team ID (found in Apple Developer account)"
echo "  3. App-specific password (create at appleid.apple.com)"
echo ""

read -p "Apple ID email: " APPLE_ID
read -p "Team ID: " TEAM_ID
read -sp "App-specific password: " APP_PASSWORD
echo ""

echo ""
echo "Submitting for notarization (this may take a few minutes)..."
xcrun notarytool submit "$EXECUTABLE" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID" \
    --password "$APP_PASSWORD" \
    --wait

if [ $? -eq 0 ]; then
    echo ""
    echo "Notarization successful! Stapling ticket..."
    xcrun stapler staple "$EXECUTABLE"
    echo ""
    echo "Done! The executable is now signed and notarized."
    echo "Users can run it without Gatekeeper warnings."
else
    echo ""
    echo "Notarization failed. Check the error messages above."
    exit 1
fi

