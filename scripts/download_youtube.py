#!/usr/bin/env python3
"""
Download audio from YouTube links as MP3s using yt-dlp.

Reads a plain-text file with one YouTube URL per line (videos, playlists,
or channels). Lines starting with '#' and blank lines are ignored.
Already-downloaded IDs are tracked in a state file so re-runs are safe.
Live streams and videos exceeding the size limit are skipped automatically.

Usage
-----
$ python scripts/download_youtube.py                        # uses youtube_links.txt
$ python scripts/download_youtube.py -f my_links.txt        # custom links file
$ python scripts/download_youtube.py -o /path/to/music      # custom output folder
$ python scripts/download_youtube.py --dry-run              # list without downloading
$ python scripts/download_youtube.py --max-size 50          # skip files over 50 MB
$ python scripts/download_youtube.py --timeout 300          # per-download timeout (s)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import List, Optional, Set

_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})")

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
DEFAULT_MAX_SIZE_MB = 100   # skip anything larger (live streams are typically huge)
DEFAULT_TIMEOUT_S = 120     # per-download socket timeout in seconds


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


def _video_id_from_url(url: str) -> Optional[str]:
    """Extract the 11-char video ID from a plain video URL without a network call."""
    m = _VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def resolve_ids(url: str, done: Set[str]) -> List[dict]:
    """Return list of {id, title, url, is_live, filesize_mb} for all videos reachable from url.

    For plain video URLs whose ID is already in *done*, skip the network call entirely.
    """
    # Fast path: single video URL that was already downloaded
    vid_id = _video_id_from_url(url)
    if vid_id and vid_id in done:
        return [{"id": vid_id, "title": vid_id, "url": url, "is_live": False, "filesize_mb": 0, "_already_done": True}]

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,  # full info needed to detect live streams and size
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info is None:
        return []

    def _entry(e: dict) -> dict:
        filesize = e.get("filesize") or e.get("filesize_approx") or 0
        return {
            "id": e["id"],
            "title": e.get("title", e["id"]),
            "url": e.get("webpage_url") or e.get("url") or url,
            "is_live": bool(e.get("is_live") or e.get("was_live")),
            "filesize_mb": filesize / (1024 * 1024),
        }

    if info.get("_type") == "playlist":
        return [_entry(e) for e in (info.get("entries") or []) if e and e.get("id")]
    return [_entry(info)]


def download_audio(url: str, out_dir: str, timeout_s: int) -> None:
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
        "socket_timeout": timeout_s,
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
    parser.add_argument(
        "--max-size",
        type=float,
        default=DEFAULT_MAX_SIZE_MB,
        metavar="MB",
        help=f"Skip videos whose estimated size exceeds this value in MB (default: {DEFAULT_MAX_SIZE_MB})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        metavar="SECONDS",
        help=f"Per-download socket timeout in seconds (default: {DEFAULT_TIMEOUT_S})",
    )
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    state_path = os.path.join(args.out, STATE_FILE)
    done = load_done(state_path)
    links = load_links(args.file)

    print(f"[+] Loaded {len(links)} URL(s) from {args.file}")

    total_queued = total_skipped = total_ok = total_fail = total_ignored = 0

    for url in links:
        print(f"\n[>] {url}", flush=True)
        try:
            entries = resolve_ids(url, done)
        except Exception as exc:
            print(f"  [!] Could not resolve: {exc}", file=sys.stderr)
            continue

        for entry in entries:
            vid_id = entry["id"]
            title = entry["title"]
            total_queued += 1

            if vid_id in done or entry.get("_already_done"):
                total_skipped += 1
                print(f"  ~ skip (already downloaded): {title}")
                continue

            if entry["is_live"]:
                total_ignored += 1
                print(f"  ~ skip (live stream): {title}")
                continue

            size_mb = entry["filesize_mb"]
            if size_mb > args.max_size:
                total_ignored += 1
                print(f"  ~ skip (too large: {size_mb:.0f} MB > {args.max_size:.0f} MB): {title}")
                continue

            size_hint = f" (~{size_mb:.0f} MB)" if size_mb > 0 else ""
            print(f"  • {title}{size_hint}", flush=True)

            if args.dry_run:
                continue

            try:
                download_audio(entry["url"], args.out, args.timeout)
                mark_done(state_path, vid_id)
                total_ok += 1
            except Exception as exc:
                print(f"    [!] Failed: {exc}", file=sys.stderr)
                total_fail += 1

    if args.dry_run:
        print(f"\n[+] {total_queued} track(s) found ({total_skipped} already downloaded, {total_ignored} would be skipped)")
    else:
        print(f"\n[+] {total_ok} downloaded, {total_skipped} skipped, {total_ignored} ignored, {total_fail} failed")


if __name__ == "__main__":
    main()
