# Keep to Joplin Converter

A tool to convert Google Keep notes (exported via Google Takeout) into Markdown files suitable for importing into Joplin.

## Quick Start

### Using the Standalone GUI (macOS)

1. Build the executable:
   ```bash
   ./build.sh
   ```

2. Run the GUI:
   ```bash
   ./dist/keep_to_joplin
   ```

### Using the Command-Line Tool

```bash
python3 keep_to_joplin.py --input Takeout/Keep --output /path/to/output
```

## Documentation

- **[DESCRIPTION.md](DESCRIPTION.md)** - Full feature description and usage
- **[BUILD.md](BUILD.md)** - Detailed build instructions and code signing guide

## Building the Standalone Executable

The project includes platform-specific build scripts:

### macOS
```bash
./build.sh
```

### Linux
```bash
./build-linux.sh
```

### Windows
```cmd
build-windows.bat
```

Each build script will:
- Create a `.venv` virtual environment (if needed)
- Install PyInstaller and PyQt6
- Build a standalone executable in `dist/`
  - macOS: `dist/keep_to_joplin.app`
  - Linux: `dist/keep_to_joplin`
  - Windows: `dist/keep_to_joplin.exe`

## Testing

Test the built executable:

```bash
./test_gui.sh
```

## Code Signing (Optional)

If you plan to distribute the executable, you can sign and notarize it:

```bash
./sign_and_notarize.sh
```

See [BUILD.md](BUILD.md) for detailed instructions.

## Creating Releases

To create a GitHub release with built executables for multiple platforms:

1. Build executables for each platform:
   ```bash
   # On macOS
   ./build.sh
   
   # On Linux
   ./build-linux.sh
   
   # On Windows
   build-windows.bat
   ```

2. Create release archives (run on each platform, or copy dist/ from each):
   ```bash
   ./create_release.sh v1.0.0 "Release notes here"
   ```

3. Create a GitHub release:
   ```bash
   gh release create v1.0.0 \
     keep-to-joplin-v1.0.0-macos.zip \
     keep-to-joplin-v1.0.0-linux.zip \
     keep-to-joplin-v1.0.0-windows.zip \
     --title "Release v1.0.0" \
     --notes "Release notes"
   ```

The `create_release.sh` script automatically detects which platform executables are available and creates archives for them.

### Automated Builds (GitHub Actions)

The project includes a GitHub Actions workflow that automatically builds executables for all platforms when you push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This will automatically:
- Build executables for macOS, Linux, and Windows
- Create release archives
- Create a GitHub release with all platform builds

## Project Structure

```
.
├── keep_to_joplin.py      # CLI version
├── keep_to_joplin_gui.py  # GUI version
├── build.sh               # Build script
├── test_gui.sh            # Test script
├── sign_and_notarize.sh   # Code signing helper
├── .venv/                 # Virtual environment (created by build.sh)
├── dist/                   # Built executables
└── build/                  # Build artifacts
```

