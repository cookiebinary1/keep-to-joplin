# Plan to Programming

This document outlines the development phases, technical decisions, and future roadmap for the `keep_to_joplin.py` converter.

## Phase 1: Core Functionality (Completed)

The initial version of the script focuses on the essential requirement: converting text and checklist notes to Markdown.

-   **Language**: Python 3 (Standard Library only).
-   **Input**: Google Takeout JSON export (directory scan).
-   **Output**: Joplin-compatible Markdown files.
-   **Key Features**:
    -   [x] Recursive directory scanning.
    -   [x] JSON parsing with error resilience.
    -   [x] Text note conversion (HTML stripping).
    -   [x] Checklist conversion (Markdown `- [ ]` syntax).
    -   [x] Metadata preservation (Created/Updated dates, Tags/Labels).
    -   [x] Status handling (Trashed, Pinned, Archived).
    -   [x] Safe filename generation (Slugify + collision handling).

## Phase 2: Enhancements (Roadmap)

These features are planned for future iterations to improve the fidelity of the import.

### 1. Attachment Support
Currently, attachments are listed in the YAML frontmatter but not copied.
-   **Goal**: Copy images/audio files to a `resources` subdirectory.
-   **Implementation**:
    -   Parse `attachments` list in JSON.
    -   Copy file from `Takeout/Keep/<filename>` to `output/resources/<filename>`.
    -   Update Markdown to include `![image](resources/filename)` links.

### 2. Rich Text Formatting
Currently, HTML is stripped to plain text.
-   **Goal**: Preserve bold, italic, and links.
-   **Implementation**:
    -   Replace `MLStripper` with a more sophisticated parser (e.g., extending `HTMLParser` to convert `<b>` to `**`, `<a>` to `[]()`, etc.).
    -   *Constraint*: Must remain within Python Standard Library (avoiding `BeautifulSoup` or `pandoc`).

### 3. Advanced Error Handling
-   **Goal**: Better reporting for malformed files.
-   **Implementation**:
    -   Generate a `report.log` file with details of skipped or failed notes.

## Phase 3: Integration

### 1. Direct Joplin API Import
-   **Goal**: Import directly into Joplin via its Data API instead of generating files.
-   **Implementation**:
    -   Use `urllib.request` to POST notes to Joplin's local web server (usually `http://localhost:41184`).
    -   Requires Joplin to be running and Web Clipper service enabled.

## Technical Debt / Refactoring

-   **Unit Tests**: Add a `tests/` directory with sample JSONs and expected Markdown outputs.
-   **Type Hinting**: Ensure full coverage of type hints for better developer experience.
