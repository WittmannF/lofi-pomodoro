#!/usr/bin/env python3
"""
Download audio from YouTube links as MP3s using yt-dlp.

Reads a plain-text file with one YouTube URL per line (videos, playlists,
or channels). Lines starting with '#' and blank lines are ignored.
Already-downloaded IDs are tracked in a state file so re-runs are safe.

Usage
-----
$ python scripts/download_youtube.py                        # uses youtube_links.txt
$ python scripts/download_youtube.py -f my_links.txt        # custom links file
$ python scripts/download_youtube.py -o /path/to/music      # custom output folder
$ python scripts/download_youtube.py --dry-run              # list without downloading
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Set

try:
    import yt_dlp
except ImportError:
    print(
        "yt-dlp not installed. Run `pip install yt-dlp` (or `uv pip install yt-dlp`).",
        file=sys.stderr,
    )
    sys.exit(1)

STATE_FILE = ".yt_downloaded_ids.txt"
DEFAULT_LINKS_FILE = "youtube_links.txt"


def load_links(path: str) -> List[str]:
    if not os.path.exists(path):
        print(f"[!] Links file not found: {path}", file=sys.stderr)
        sys.exit(1)
    links = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                links.append(line)
    return links


def load_done(state_path: str) -> Set[str]:
    if not os.path.exists(state_path):
        return set()
    with open(state_path, encoding="utf-8") as fh:
        return {line.strip() for line in fh if line.strip()}


def mark_done(state_path: str, video_id: str) -> None:
    with open(state_path, "a", encoding="utf-8") as fh:
        fh.write(video_id + "\n")


def resolve_ids(url: str) -> List[dict]:
    """Return list of {id, title, url} for all videos reachable from url."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # don't download, just enumerate
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info is None:
        return []
    if info.get("_type") == "playlist":
        return [
            {"id": e["id"], "title": e.get("title", e["id"]), "url": e["url"]}
            for e in (info.get("entries") or [])
            if e and e.get("id")
        ]
    return [{"id": info["id"], "title": info.get("title", info["id"]), "url": url}]


def download_audio(url: str, out_dir: str) -> None:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(uploader)s - %(title)s [%(id)s].%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(repo_root, "pomodoro", "default-playlist")

    parser = argparse.ArgumentParser(
        description="Download YouTube audio as MP3s into the pomodoro playlist"
    )
    parser.add_argument(
        "-f", "--file",
        default=DEFAULT_LINKS_FILE,
        help=f"Text file with YouTube URLs, one per line (default: {DEFAULT_LINKS_FILE})",
    )
    parser.add_argument(
        "-o", "--out",
        default=default_out,
        help=f"Output directory (default: {default_out})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve and list tracks without downloading",
    )
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    state_path = os.path.join(args.out, STATE_FILE)
    done = load_done(state_path)
    links = load_links(args.file)

    print(f"[+] Loaded {len(links)} URL(s) from {args.file}")

    total_queued = total_skipped = total_ok = total_fail = 0

    for url in links:
        print(f"\n[>] {url}", flush=True)
        try:
            entries = resolve_ids(url)
        except Exception as exc:
            print(f"  [!] Could not resolve: {exc}", file=sys.stderr)
            continue

        for entry in entries:
            vid_id = entry["id"]
            title = entry["title"]
            total_queued += 1

            if vid_id in done:
                total_skipped += 1
                print(f"  ~ skip (already downloaded): {title}")
                continue

            print(f"  • {title}", flush=True)

            if args.dry_run:
                continue

            try:
                download_audio(entry["url"], args.out)
                mark_done(state_path, vid_id)
                total_ok += 1
            except Exception as exc:
                print(f"    [!] Failed: {exc}", file=sys.stderr)
                total_fail += 1

    if args.dry_run:
        print(f"\n[+] {total_queued} track(s) found ({total_skipped} already downloaded)")
    else:
        print(f"\n[+] {total_ok} downloaded, {total_skipped} skipped, {total_fail} failed")


if __name__ == "__main__":
    main()
