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
import shutil
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Callable, List, Optional, Set, Tuple

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
    annotations: List[dict] = field(default_factory=list)


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

AttachmentRef = Tuple[str, str, str]

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
    Normalizes string for attachments: lowercase, removes unsafe characters,
    and converts spaces/hyphens to single hyphen.
    """
    value = str(value)
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value


def sanitize_note_filename(value: str) -> str:
    """Keep spaces and case, but drop path separators and illegal characters."""
    value = str(value).strip()
    if not value:
        return ""
    cleaned = re.sub(r'[\\/:*"<>|]+', "", value)
    cleaned = cleaned.rstrip(". ")
    return cleaned


def get_safe_filename(title: str, output_dir: str, created_usec: int) -> str:
    """
    Generates a unique filename for the note, preserving case/spaces.
    """
    base_name = sanitize_note_filename(title)
    if not base_name:
        base_name = f"note-{created_usec}"

    filename = f"{base_name}.md"
    counter = 1
    while os.path.exists(os.path.join(output_dir, filename)):
        counter += 1
        filename = f"{base_name} ({counter}).md"
    return filename


def get_unique_attachment_name(
    original: str, target_dir: str, used_names: Set[str]
) -> str:
    """Generate a filename for attachments that avoids collisions."""
    base, ext = os.path.splitext(original)
    base = slugify(base) or "attachment"
    filename = f"{base}{ext}"
    counter = 1
    while filename in used_names or os.path.exists(os.path.join(target_dir, filename)):
        counter += 1
        filename = f"{base}-{counter}{ext}"
    used_names.add(filename)
    return filename


def get_unique_attachment_name(
    original: str, target_dir: str, used_names: Set[str]
) -> str:
    """Generate a filesystem-safe filename for attachments without collisions."""
    base, ext = os.path.splitext(original)
    base = slugify(base) or "attachment"
    filename = f"{base}{ext}"
    counter = 1
    while filename in used_names or os.path.exists(os.path.join(target_dir, filename)):
        counter += 1
        filename = f"{base}-{counter}{ext}"
    used_names.add(filename)
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

    annotations = data.get("annotations", [])

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
        annotations=annotations,
    )


def note_to_markdown(
    note: Note, attachment_refs: Optional[List[AttachmentRef]] = None
) -> str:
    """Render a note as Markdown with optional HTML wrappers."""
    lines: List[str] = []

    body_lines: List[str] = []

    attachment_refs = attachment_refs or []

    if note.content:
        body_lines.append(note.content.rstrip())
        body_lines.append("")

    color_label = (note.color or "DEFAULT").upper()
    has_colored_background = color_label != "DEFAULT" and color_label in COLOR_MAP

    if note.items:
        for text, checked in note.items:
            mark = "x" if checked else " "
            if has_colored_background:
                # Use HTML with black color for checkboxes when background is colored
                checkbox_html = f'- [{mark}] {text}'
                body_lines.append(checkbox_html)
            else:
                body_lines.append(f"- [{mark}] {text}")
        body_lines.append("")

    if body_lines and body_lines[-1] == "":
        body_lines.pop()

    if note.labels:
        if body_lines:
            body_lines.append("")
        body_lines.append("Labels: " + ", ".join(note.labels))

    if attachment_refs:
        if body_lines:
            body_lines.append("")
        body_lines.append("Attachments:")
        for original_name, rel_path, mimetype in attachment_refs:
            if mimetype.startswith("image/"):
                body_lines.append(f"![{original_name}]({rel_path})")
            else:
                body_lines.append(f"[{original_name}]({rel_path})")

    if note.annotations:
        link_lines = []
        for ann in note.annotations:
            url = ann.get("url")
            if not url:
                continue
            link_text = ann.get("title") or ann.get("description") or url
            description = ann.get("description")
            formatted = f"- [{link_text}]({url})"
            if description and description != link_text:
                formatted += f" — {description}"
            link_lines.append(formatted)
        if link_lines:
            if body_lines:
                body_lines.append("")
            body_lines.append("Links:")
            body_lines.extend(link_lines)

    timestamp_source = note.updated_usec or note.created_usec
    timestamp_label = "Updated" if note.updated_usec else "Created"
    timestamp_text = parse_timestamp(timestamp_source)
    footer = (
        '<small style="color: #555;">'
        f"{timestamp_label}: {timestamp_text}"
        "</small>"
    )

    # Remove trailing blank line if present
    while body_lines and body_lines[-1] == "":
        body_lines.pop()

    if has_colored_background:
        color_hex = COLOR_MAP[color_label]
        lines.append(
            '<div class="keep-note" style="background-color: '
            f"{color_hex}; color: black; padding: 16px; border-radius: 8px; "
            'margin-bottom: 16px;">'
        )
        lines.append("")
        if body_lines:
            lines.extend(body_lines)
        lines.append(footer)
        lines.append("</div>")
    else:
        if body_lines:
            lines.extend(body_lines)
        lines.append(footer)

    return "\n".join(lines).strip() + "\n"


def convert_keep_notes(
    input_dir: str,
    output_dir: str,
    *,
    dry_run: bool = False,
    verbose: bool = False,
    include_trashed: bool = False,
    include_archived: bool = False,
    log_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Convert Google Keep JSON notes from input_dir into Markdown files under output_dir.
    """

    def log(message: str) -> None:
        if log_callback:
            log_callback(message)
        elif verbose:
            print(message)

    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")

    if not dry_run:
        os.makedirs(output_dir, exist_ok=True)

    stats = {
        "processed": 0,
        "exported": 0,
        "skipped_trashed": 0,
        "skipped_archived": 0,
        "skipped_invalid": 0,
        "errors": 0,
    }

    log(f"Scanning '{input_dir}'...")

    notes_to_export: List[Tuple[Note, str]] = []

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            stats["processed"] += 1
            filepath = os.path.join(root, file)
            log(f"Processing: {file}")

            note = parse_note_json(filepath)
            if not note:
                stats["skipped_invalid"] += 1
                log("  -> Invalid or empty JSON")
                continue

            if note.is_trashed and not include_trashed:
                stats["skipped_trashed"] += 1
                log("  -> Skipped (Trashed)")
                continue

            if note.is_archived and not include_archived:
                stats["skipped_archived"] += 1
                log("  -> Skipped (Archived)")
                continue

            notes_to_export.append((note, filepath))

    notes_to_export.sort(
        key=lambda pair: (
            1 if pair[0].is_pinned else 0,
            int(pair[0].updated_usec or 0),
        )
    )

    resources_dir = os.path.join(output_dir, "resources")
    resources_ready = False
    used_attachment_names: Set[str] = set()

    for note, filepath in notes_to_export:
        attachment_refs: List[AttachmentRef] = []

        if note.attachments:
            for att in note.attachments:
                file_rel = att.get("filePath")
                if not file_rel:
                    continue
                source_file = os.path.join(os.path.dirname(filepath), file_rel)
                if not os.path.isfile(source_file):
                    log(f"  -> Attachment missing: {file_rel}")
                    continue

                dest_name = get_unique_attachment_name(
                    file_rel, resources_dir, used_attachment_names
                )
                rel_path = os.path.join("resources", dest_name)

                if dry_run:
                    log(
                        f"  -> [Dry Run] Would copy attachment {file_rel} -> {rel_path}"
                    )
                else:
                    if not resources_ready:
                        os.makedirs(resources_dir, exist_ok=True)
                        resources_ready = True
                    dest_path = os.path.join(resources_dir, dest_name)
                    try:
                        shutil.copy2(source_file, dest_path)
                        log(f"  -> Copied attachment {file_rel} -> {rel_path}")
                    except OSError as e:
                        log(f"  -> Attachment copy failed: {e}")
                        stats["errors"] += 1
                        continue

                attachment_refs.append(
                    (os.path.basename(file_rel), rel_path, att.get("mimetype", ""))
                )

        md_content = note_to_markdown(note, attachment_refs)

        safe_filename = get_safe_filename(note.title, output_dir, note.created_usec)
        output_path = os.path.join(output_dir, safe_filename)

        if dry_run:
            log(
                f"[Dry Run] Would write: {output_path} (from {os.path.basename(filepath)})"
            )
        else:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                log(f"  -> Wrote: {safe_filename}")
            except OSError as e:
                log(f"Error writing {output_path}: {e}")
                stats["errors"] += 1
                continue

        stats["exported"] += 1

    return stats


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

    print(f"Scanning '{args.input}'...")

    log_callback = print if args.dry_run or args.verbose else None

    try:
        stats = convert_keep_notes(
            args.input,
            args.output,
            dry_run=args.dry_run,
            verbose=args.verbose,
            log_callback=log_callback,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\nSummary")
    print("=======")
    print(f"Processed: {stats['processed']} JSON files")
    print(f"Exported notes: {stats['exported']}")
    print(f"Skipped trashed: {stats['skipped_trashed']}")
    print(f"Skipped archived: {stats['skipped_archived']}")
    print(f"Skipped invalid: {stats['skipped_invalid']}")
    if stats["errors"] > 0:
        print(f"Write errors: {stats['errors']}")
    print(f"Output directory: {args.output}")


if __name__ == "__main__":
    main()
