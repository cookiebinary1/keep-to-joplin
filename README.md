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

The project includes a build script that creates a standalone macOS executable:

```bash
./build.sh
```

This will:
- Create a `.venv` virtual environment (if needed)
- Install PyInstaller and PyQt6
- Build a standalone executable at `dist/keep_to_joplin`

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

To create a GitHub release with the built executable:

1. Build the executable:
   ```bash
   ./build.sh
   ```

2. Create a release archive:
   ```bash
   ./create_release.sh v1.0.0 "Release notes here"
   ```

3. Create a GitHub release:
   - Go to [GitHub Releases](https://github.com/cookiebinary1/keep-to-joplin/releases/new)
   - Or use GitHub CLI: `gh release create v1.0.0 keep-to-joplin-v1.0.0-macos.zip --title "Release v1.0.0" --notes "Release notes"`

The release archive will be created in the project root directory.

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

