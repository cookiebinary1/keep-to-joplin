#!/usr/bin/env python3
"""
Google Keep to Joplin Converter
===============================

This script converts Google Keep notes exported via Google Takeout (JSON format)
into Markdown files suitable for importing into Joplin.

Usage:
    python3 keep_to_joplin.py --input <path_to_keep_json_dir> --output <path_to_output_dir>

Example:
    python3 keep_to_joplin.py --input Takeout/Keep --output JoplinImport

Features:
- Converts text notes and checklists.
- Preserves creation and modification timestamps.
- Preserves labels/tags.
- Handles archived/pinned/trashed status via frontmatter.
- Generates unique filenames based on note titles.
"""

import argparse
import datetime
import json
import os
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import List, Optional, Tuple

# --- HTML Stripper ---


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return "".join(self.text)


def strip_tags(html_content: str) -> str:
    """Strips HTML tags from a string using HTMLParser."""
    if not html_content:
        return ""
    s = MLStripper()
    s.feed(html_content)
    return s.get_data()


# --- Data Structures ---


@dataclass
class Note:
    title: str
    content: str = ""
    items: List[Tuple[str, bool]] = field(
        default_factory=list
    )  # List of (text, is_checked)
    created_usec: int = 0
    updated_usec: int = 0
    is_trashed: bool = False
    is_pinned: bool = False
    is_archived: bool = False
    labels: List[str] = field(default_factory=list)
    color: str = "DEFAULT"
    attachments: List[dict] = field(default_factory=list)


# Mapping of Google Keep color labels to hex values for inline styling.
COLOR_MAP = {
    "DEFAULT": "#ffffff",
    "RED": "#ff6d3f",
    "ORANGE": "#ff9b00",
    "YELLOW": "#ffda00",
    "GREEN": "#95d641",
    "TEAL": "#1ce8b5",
    "BLUE": "#3fc3ff",
    "GRAY": "#b8c4c9",
    "CERULEAN": "#82b1ff",
    "PURPLE": "#b388ff",
    "PINK": "#f8bbd0",
    "BROWN": "#d7ccc8",
}

# --- Core Logic ---


def parse_timestamp(usec: int) -> str:
    """Converts microsecond timestamp to ISO 8601 UTC string."""
    try:
        # Google Keep timestamps are in microseconds
        dt = datetime.datetime.fromtimestamp(usec / 1_000_000, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(value: str) -> str:
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = str(value)
    # Replace unsafe characters with nothing or space
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    # Replace spaces with hyphens
    value = re.sub(r"[-\s]+", "-", value)
    return value


def get_safe_filename(title: str, output_dir: str, created_usec: int) -> str:
    """
    Generates a unique filename for the note.
    """
    base_name = slugify(title)
    if not base_name:
        base_name = f"note-{created_usec}"

    filename = f"{base_name}.md"
    counter = 1

    while os.path.exists(os.path.join(output_dir, filename)):
        counter += 1
        filename = f"{base_name}-{counter}.md"

    return filename


def parse_note_json(filepath: str) -> Optional[Note]:
    """
    Parses a single Google Keep JSON file into a Note object.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return None

    # Basic validation - check if it looks like a Keep note
    if not isinstance(data, dict):
        return None

    title = data.get("title", "")

    # Timestamps
    created_usec = int(data.get("createdTimestampUsec", 0) or 0)
    updated_usec = int(data.get("userEditedTimestampUsec", 0) or 0)

    # Flags
    is_trashed = data.get("isTrashed", False)
    is_pinned = data.get("isPinned", False)
    is_archived = data.get("isArchived", False)
    color = data.get("color", "DEFAULT")

    # Labels
    labels = []
    if "labels" in data and isinstance(data["labels"], list):
        for label_obj in data["labels"]:
            if "name" in label_obj:
                labels.append(label_obj["name"])

    # Content
    content = ""
    items = []

    # Handle text content
    if "textContent" in data:
        content = data["textContent"]
    else:
        html_value = data.get("textContentHtml") or data.get("textHtml")
        if html_value:
            content = strip_tags(html_value)

    # Handle list content (checklists)
    if "listContent" in data and isinstance(data["listContent"], list):
        for item in data["listContent"]:
            text = item.get("text", "")
            if not text and "textHtml" in item:
                text = strip_tags(item["textHtml"])

            is_checked = item.get("isChecked", False)
            items.append((text, is_checked))

    # Attachments (metadata only)
    attachments = data.get("attachments", [])

    return Note(
        title=title,
        content=content,
        items=items,
        created_usec=created_usec,
        updated_usec=updated_usec,
        is_trashed=is_trashed,
        is_pinned=is_pinned,
        is_archived=is_archived,
        labels=labels,
        color=color,
        attachments=attachments,
    )


def note_to_markdown(note: Note) -> str:
    """
    Converts a Note object to a Markdown string with YAML frontmatter.
    """
    # Frontmatter
    lines = ["---"]
    lines.append(f"created: {parse_timestamp(note.created_usec)}")
    lines.append(f"updated: {parse_timestamp(note.updated_usec)}")
    lines.append(f"pinned: {str(note.is_pinned).lower()}")
    lines.append(f"archived: {str(note.is_archived).lower()}")
    lines.append(f"trashed: {str(note.is_trashed).lower()}")
    lines.append(f"color: {note.color}")

    if note.labels:
        lines.append("labels:")
        for label in note.labels:
            lines.append(f"  - {label}")

    if note.attachments:
        lines.append("attachments:")
        for att in note.attachments:
            # Just listing attachment info, not linking files as we don't copy them
            filename = att.get("filePath", "unknown")
            mimetype = att.get("mimetype", "unknown")
            lines.append(f"  - {filename} ({mimetype})")

    lines.append("---\n")

    title_header = note.title if note.title else "Untitled Note"
    lines.append(f"# {title_header}\n")

    body_lines: List[str] = []

    if note.content:
        body_lines.append(note.content.rstrip())
        body_lines.append("")

    if note.items:
        for text, checked in note.items:
            mark = "x" if checked else " "
            body_lines.append(f"- [{mark}] {text}")
        body_lines.append("")

    # Remove trailing blank line if present
    while body_lines and body_lines[-1] == "":
        body_lines.pop()

    if body_lines:
        color_label = (note.color or "DEFAULT").upper()
        if color_label != "DEFAULT" and color_label in COLOR_MAP:
            color_hex = COLOR_MAP[color_label]
            lines.append(
                '<div class="keep-note" style="background-color: '
                f"{color_hex}; color: black; padding: 16px; border-radius: 8px; "
                'margin-bottom: 16px;">'
            )
            lines.extend(body_lines)
            lines.append("</div>")
        else:
            lines.extend(body_lines)

    return "\n".join(lines).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Convert Google Keep JSON exports to Joplin Markdown."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to directory containing Google Keep JSON files",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to output directory for Markdown files",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not write files, only print actions"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print verbose output"
    )

    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(
                f"Error: Could not create output directory '{output_dir}': {e}",
                file=sys.stderr,
            )
            sys.exit(1)

    stats = {
        "processed": 0,
        "exported": 0,
        "skipped_trashed": 0,
        "skipped_archived": 0,
        "skipped_invalid": 0,
        "errors": 0,
    }

    print(f"Scanning '{input_dir}'...")

    notes_to_export: List[Tuple[Note, str]] = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            stats["processed"] += 1
            filepath = os.path.join(root, file)

            if args.verbose:
                print(f"Processing: {file}")

            note = parse_note_json(filepath)

            if not note:
                stats["skipped_invalid"] += 1
                if args.verbose:
                    print(f"  -> Invalid or empty JSON")
                continue
            if note.is_trashed:
                stats["skipped_trashed"] += 1
                if args.verbose:
                    print(f"  -> Skipped (Trashed)")
                continue
            if note.is_archived:
                stats["skipped_archived"] += 1
                if args.verbose:
                    print(f"  -> Skipped (Archived)")
                continue

            notes_to_export.append((note, filepath))

    notes_to_export.sort(
        key=lambda pair: (
            0 if pair[0].is_pinned else 1,
            -int(pair[0].updated_usec or 0),
        )
    )

    for note, filepath in notes_to_export:
        # Generate Markdown
        md_content = note_to_markdown(note)

        # Determine filename
        safe_filename = get_safe_filename(note.title, output_dir, note.created_usec)
        output_path = os.path.join(output_dir, safe_filename)

        if args.dry_run:
            print(
                f"[Dry Run] Would write: {output_path} (from {os.path.basename(filepath)})"
            )
        else:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                if args.verbose:
                    print(f"  -> Wrote: {safe_filename}")
            except IOError as e:
                print(f"Error writing {output_path}: {e}", file=sys.stderr)
                stats["errors"] += 1
                continue

        stats["exported"] += 1

    print("\nSummary")
    print("=======")
    print(f"Processed: {stats['processed']} JSON files")
    print(f"Exported notes: {stats['exported']}")
    print(f"Skipped trashed: {stats['skipped_trashed']}")
    print(f"Skipped archived: {stats['skipped_archived']}")
    print(f"Skipped invalid: {stats['skipped_invalid']}")
    if stats["errors"] > 0:
        print(f"Write errors: {stats['errors']}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
