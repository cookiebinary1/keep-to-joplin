# Building the Standalone Executable

This document describes how to build a standalone GUI executable for macOS that doesn't require Python to be installed.

## Prerequisites

- macOS with Python 3.8+ installed
- Virtual environment support (venv module)

## Build Process

### Automated Build

Use the provided build script:

```bash
./build_macos.sh
```

This script will:
1. Create a `.venv` virtual environment (if it doesn't exist)
2. Install PyInstaller in the virtual environment
3. Build the standalone executable using PyInstaller
4. Output the executable to `dist/keep_to_joplin`

### Manual Build

If you prefer to build manually:

```bash
# Create virtual environment (if needed)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build the executable
./.venv/bin/python -m PyInstaller --onefile --name keep_to_joplin keep_to_joplin_gui.py
```

## Testing

### Quick Test

Run the test script to verify the build:

```bash
./test_gui.sh
```

### Manual Testing

1. **CLI Test (dry-run)**:
   ```bash
   ./dist/keep_to_joplin --dry-run --input Takeout/Keep --output /tmp/joplin_out
   ```

2. **GUI Test**:
   ```bash
   ./dist/keep_to_joplin
   ```
   
   Or double-click `dist/keep_to_joplin` in Finder.

## Code Signing and Notarization (macOS Distribution)

If you plan to distribute the executable to other macOS users, you should sign and notarize it to avoid Gatekeeper warnings.

### Requirements

- Apple Developer account (free or paid)
- Xcode Command Line Tools installed
- Valid code signing certificate

### Signing the Executable

1. **Get your Developer ID**:
   ```bash
   security find-identity -v -p codesigning
   ```

2. **Sign the executable**:
   ```bash
   codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" dist/keep_to_joplin
   ```

3. **Verify the signature**:
   ```bash
   codesign --verify --verbose dist/keep_to_joplin
   spctl --assess --verbose dist/keep_to_joplin
   ```

### Notarization (for distribution outside App Store)

1. **Create an app-specific password** in your Apple ID account settings

2. **Notarize the executable**:
   ```bash
   xcrun notarytool submit dist/keep_to_joplin \
     --apple-id your@email.com \
     --team-id YOUR_TEAM_ID \
     --password "app-specific-password" \
     --wait
   ```

3. **Staple the notarization ticket**:
   ```bash
   xcrun stapler staple dist/keep_to_joplin
   ```

### Alternative: Create a .dmg for Distribution

For better user experience, package the executable in a .dmg:

```bash
# Create a temporary directory
mkdir -p dist_package

# Copy the executable
cp dist/keep_to_joplin dist_package/

# Create DMG
hdiutil create -volname "Keep to Joplin" -srcfolder dist_package -ov -format UDZO dist/keep_to_joplin.dmg

# Sign the DMG
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" dist/keep_to_joplin.dmg

# Cleanup
rm -rf dist_package
```

## Troubleshooting

### "Executable not found" error

Make sure the build completed successfully and check that `dist/keep_to_joplin` exists.

### Gatekeeper warnings

If users see "unidentified developer" warnings:
- Sign the executable (see above)
- For personal use, users can right-click and select "Open" to bypass Gatekeeper once

### PyInstaller warnings

Some warnings during build are normal. Check `build/keep_to_joplin/warn-keep_to_joplin.txt` for details. Common warnings about missing modules can usually be ignored if the executable works.

### GUI doesn't start

1. Check that PyQt6 is properly bundled (should be automatic)
2. Try running from terminal to see error messages:
   ```bash
   ./dist/keep_to_joplin 2>&1 | tee gui_errors.log
   ```

## File Structure

After building:

```
.
├── .venv/              # Virtual environment (not included in distribution)
├── build/              # Build artifacts (can be deleted)
├── dist/
│   └── keep_to_joplin  # The standalone executable (distribute this)
├── keep_to_joplin.py   # CLI source
├── keep_to_joplin_gui.py  # GUI source
└── *.spec              # PyInstaller spec files (can be deleted)
```

## Notes

- The executable is ~7MB and includes Python, PyQt6, and all dependencies
- The build uses `--onefile` which creates a single executable (slower startup, but simpler distribution)
- For faster startup, consider using `--onedir` instead, but you'll need to distribute the entire directory

