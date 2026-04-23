#!/usr/bin/env python3
"""
Download free lo-fi MP3s from Free Music Archive (freemusicarchive.org).

Scrapes genre pages, extracts track metadata from data-track-info JSON,
and streams each track via the /stream/ endpoint (no login required).

Usage
-----
$ python scrape_fma.py                        # default: Lo-fi genre
$ python scrape_fma.py -g Lo-fi-Instrumental  # different genre
$ python scrape_fma.py -o data                # custom output folder
$ python scrape_fma.py --dry-run              # list only, no downloads
$ python scrape_fma.py --max-pages 10         # limit pages crawled
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Generator, List, Set

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://freemusicarchive.org"
GENRE_URL = BASE_URL + "/genre/{genre}/"
PER_PAGE = 20
CRAWL_DELAY = 2  # seconds between requests
STATE_FILE = ".fma_downloaded_ids.txt"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Safari/605.1.15"
)

SAFE_CHARS = re.compile(r'[^\w\-. ]+')


def build_session() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    sess.mount("https://", HTTPAdapter(max_retries=retry))
    return sess


def safe_filename(artist: str, title: str) -> str:
    artist = SAFE_CHARS.sub('_', artist).strip('_')
    title = SAFE_CHARS.sub('_', title).strip('_')
    # Strip any .mp3 suffix that FMA sometimes embeds in the title field
    title = re.sub(r'\.mp3$', '', title, flags=re.IGNORECASE)
    return f"{artist}_-_{title}_fma.mp3"


def genre_pages(genre: str, sess: requests.Session, max_pages: int | None) -> Generator[List[dict], None, None]:
    """Yield lists of track-info dicts, one list per page."""
    page = 1
    while True:
        if max_pages and page > max_pages:
            break
        url = GENRE_URL.format(genre=genre)
        params = {"page": page, "per_page": PER_PAGE}
        resp = sess.get(url, params=params, timeout=20)
        if resp.status_code == 404:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("div.play-item[data-track-info]")
        if not items:
            break

        tracks = []
        for item in items:
            try:
                info = json.loads(item["data-track-info"])
                tracks.append(info)
            except (KeyError, json.JSONDecodeError):
                continue

        if not tracks:
            break

        print(f"[+] Page {page}: {len(tracks)} tracks", flush=True)
        yield tracks
        page += 1
        time.sleep(CRAWL_DELAY)


def stream_url_to_mp3_url(stream_url: str, sess: requests.Session) -> str | None:
    """Follow the /stream/ redirect to get the direct CDN MP3 URL."""
    resp = sess.get(stream_url, allow_redirects=False, timeout=20)
    location = resp.headers.get("location", "")
    if location.endswith(".mp3"):
        return location
    return None


def download_mp3(mp3_url: str, dest: str, sess: requests.Session) -> None:
    with sess.get(mp3_url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)


def crawl(genre: str, out_dir: str, dry_run: bool, max_pages: int | None) -> None:
    os.makedirs(out_dir, exist_ok=True)
    state_path = os.path.join(out_dir, STATE_FILE)

    done: Set[str] = set()
    if os.path.exists(state_path):
        with open(state_path) as fh:
            done.update(line.strip() for line in fh if line.strip())

    sess = build_session()

    for tracks in genre_pages(genre, sess, max_pages):
        for info in tracks:
            track_id = str(info.get("id", ""))
            if not track_id or track_id in done:
                continue

            artist = info.get("artistName", "Unknown")
            title = info.get("title", "Unknown")
            stream_url = info.get("playbackUrl", "")

            if not stream_url:
                print(f"    • {track_id}  [{artist} - {title}]  → no stream URL", flush=True)
                continue

            fname = safe_filename(artist, title)
            print(f"    • {track_id}  [{artist} - {title}]  → {fname}", flush=True)

            if dry_run:
                continue

            mp3_url = stream_url_to_mp3_url(stream_url, sess)
            if not mp3_url:
                print(f"      ! could not resolve MP3 URL", file=sys.stderr)
                continue

            dest = os.path.join(out_dir, fname)
            try:
                download_mp3(mp3_url, dest, sess)
            except Exception as exc:
                print(f"      ! download failed: {exc}", file=sys.stderr)
                continue

            done.add(track_id)
            with open(state_path, "a") as fh:
                fh.write(track_id + "\n")

            time.sleep(CRAWL_DELAY)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download free lo-fi MP3s from freemusicarchive.org"
    )
    parser.add_argument(
        "-g", "--genre",
        default="Lo-fi",
        help="FMA genre slug to scrape (default: Lo-fi). "
             "Other options: Lo-fi-Instrumental, Ambient, Chillwave",
    )
    parser.add_argument(
        "-o", "--out",
        default="pomodoro/default-playlist",
        help="Output directory (default: pomodoro/default-playlist)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List tracks without downloading",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to crawl (default: all)",
    )
    args = parser.parse_args()
    crawl(args.genre, args.out, args.dry_run, args.max_pages)


if __name__ == "__main__":
    main()
