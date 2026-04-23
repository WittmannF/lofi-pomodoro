#!/usr/bin/env python3
"""
Strip empty COMM/USLT ID3 frames from MP3 files to silence the pygame/libmpg123
warning: "No comment text / valid description?"

Only frames with empty text and empty description are removed; frames with real
content (e.g. actual lyrics or meaningful comments) are left intact.

Usage
-----
$ python scripts/fix_id3_tags.py                          # fix default playlist
$ python scripts/fix_id3_tags.py -d /path/to/music        # custom folder
$ python scripts/fix_id3_tags.py --dry-run                # show what would change
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    import eyed3
    from eyed3.utils import log as eyed3_log
    import logging
    eyed3_log.setLevel(logging.ERROR)  # suppress eyed3's own chatter
except ImportError:
    print(
        "eyed3 not installed. Run `pip install eyed3` (or `uv pip install eyed3`).",
        file=sys.stderr,
    )
    sys.exit(1)


def _is_empty_frame(frame) -> bool:
    text = getattr(frame, "text", None) or ""
    desc = getattr(frame, "description", None) or ""
    return not text.strip() and not desc.strip()


def fix_file(path: str, dry_run: bool) -> bool:
    """Return True if the file had empty frames that were (or would be) removed."""
    af = eyed3.load(path)
    if af is None or af.tag is None:
        return False

    tag = af.tag
    changed = False

    empty_comments = [f for f in tag.comments if _is_empty_frame(f)]
    if empty_comments:
        changed = True
        if not dry_run:
            for frame in empty_comments:
                tag.comments.remove(frame.description.encode(), frame.lang)

    empty_lyrics = [f for f in tag.lyrics if _is_empty_frame(f)]
    if empty_lyrics:
        changed = True
        if not dry_run:
            for frame in empty_lyrics:
                tag.lyrics.remove(frame.description.encode(), frame.lang)

    if changed and not dry_run:
        try:
            tag.save()
        except Exception as exc:
            print(f"  [!] Could not save {os.path.basename(path)}: {exc}", file=sys.stderr)
            return False

    return changed


def main() -> None:
    default_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "pomodoro", "default-playlist",
    )
    parser = argparse.ArgumentParser(
        description="Remove empty COMM/USLT ID3 frames from MP3s to silence libmpg123 warnings"
    )
    parser.add_argument("-d", "--dir", default=default_dir,
                        help=f"Directory to scan (default: {default_dir})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report files that need fixing without changing them")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"[!] Directory not found: {args.dir}", file=sys.stderr)
        sys.exit(1)

    total = fixed = 0
    for root, _, files in os.walk(args.dir):
        for fname in files:
            if not fname.lower().endswith(".mp3"):
                continue
            path = os.path.join(root, fname)
            total += 1
            changed = fix_file(path, args.dry_run)
            if changed:
                fixed += 1
                verb = "would fix" if args.dry_run else "fixed"
                print(f"  {verb}: {fname}")

    action = "need fixing" if args.dry_run else "fixed"
    print(f"\n[+] Scanned {total} files — {fixed} {action}")


if __name__ == "__main__":
    main()
