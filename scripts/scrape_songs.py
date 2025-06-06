#!/usr/bin/env python3
"""
Download free-music MP3s from Chosic.

Features
--------
• Crawls every result page of a given style/tag (default: "lofi")
• Extracts unique track-IDs from the list pages
• Visits each /download-audio/<id>/ page, grabs the MP3 link, downloads it
• Remembers what it already fetched across runs
    └── .downloaded_ids.txt (one ID per line, written after a successful save)
• Respectful crawling: 2-second delay + retry/back-off on transient errors

Usage
-----
$ python scrape_songs.py                       # default style 'lofi'
$ python scrape_songs.py -s ambient            # different tag
$ python scrape_songs.py -s lofi -o data       # custom output folder
$ python scrape_songs.py --dry-run             # list only, no downloads
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
from typing import Generator, Iterable, List, Set, Tuple

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------------------------------------------------------------#
#  Configuration constants
# -----------------------------------------------------------------------------#
BASE_URL = "https://www.chosic.com"
LIST_URL = BASE_URL + "/free-music/{style}/"
PAGE_URL = BASE_URL + "/free-music/{style}/page/{page}/"

DL_REGEX = re.compile(r"/download-audio/(\d+)/")
MP3_REGEX = re.compile(r"https://www\.chosic\.com/wp-content/uploads/[^\"']+\.mp3")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Safari/605.1.15"
)
STATE_FILE = ".downloaded_ids.txt"
CRAWL_DELAY = 2  # seconds


# -----------------------------------------------------------------------------#
#  Helpers
# -----------------------------------------------------------------------------#
def build_session() -> requests.Session:
    """Return a requests.Session with retry/back-off and custom UA."""
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


def paginated_list_urls(
    style: str, sess: requests.Session
) -> Generator[str, None, None]:
    """
    Yield every result-page URL (page/1, page/2, …) until we hit 404
    or a page that contains no tracks.
    """
    page = 1
    while True:
        url = (
            LIST_URL.format(style=style)
            if page == 1
            else PAGE_URL.format(style=style, page=page)
        )
        resp = sess.get(url, timeout=20)
        if resp.status_code == 404:
            break

        # Stop if the page no longer has any /download-audio/ links
        if not DL_REGEX.search(resp.text):
            break

        yield url
        page += 1
        time.sleep(CRAWL_DELAY)  # polite


def extract_track_ids(html_text: str) -> List[Tuple[str, str]]:
    """
    Return **unique** (id, full_download_page_url) tuples found in the markup.
    """
    seen: Set[str] = set()
    results: List[Tuple[str, str]] = []

    for m in DL_REGEX.finditer(html_text):
        tid = m.group(1)
        if tid not in seen:
            seen.add(tid)
            results.append((tid, f"{BASE_URL}/download-audio/{tid}/"))
    return results


def mp3_link_from_track_page(track_url: str, sess: requests.Session) -> str | None:
    """
    Fetch a /download-audio/<id>/ page and return the first .mp3 link, or None.
    """
    resp = sess.get(track_url, timeout=20)
    match = MP3_REGEX.search(resp.text)
    return html.unescape(match.group(0)) if match else None


def save_mp3(url: str, dest_path: str, sess: requests.Session) -> None:
    """Stream-download the MP3 to *dest_path*."""
    with sess.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)


# -----------------------------------------------------------------------------#
#  Main crawler
# -----------------------------------------------------------------------------#
def crawl(style: str, out_dir: str, dry_run: bool = False) -> None:
    """
    The core crawling routine.
    *out_dir* will look like  chosic/<style>/[…].mp3
    """
    os.makedirs(out_dir, exist_ok=True)
    state_path = os.path.join(out_dir, STATE_FILE)

    # ------------------------------------------------------------------#
    #  Load already-downloaded IDs from state file
    # ------------------------------------------------------------------#
    done: Set[str] = set()
    if os.path.exists(state_path):
        with open(state_path) as fh:
            done.update(line.strip() for line in fh if line.strip())

    sess = build_session()

    # ------------------------------------------------------------------#
    #  Walk through paginated list pages
    # ------------------------------------------------------------------#
    for page_url in paginated_list_urls(style, sess):
        print(f"[+] Page {page_url}", flush=True)
        page_html = sess.get(page_url, timeout=20).text

        for track_id, track_page in extract_track_ids(page_html):
            # Skip duplicates (already downloaded or already processed in this batch)
            if track_id in done:
                continue

            # ------------------------------------------------------------------#
            #  Visit the track page to fetch the MP3 link
            # ------------------------------------------------------------------#
            mp3_url = mp3_link_from_track_page(track_page, sess)
            if not mp3_url:
                print(f"    • {track_id}  →  [no mp3 found]", flush=True)
                continue

            fname = os.path.basename(mp3_url)
            print(f"    • {track_id}  →  {fname}", flush=True)

            if dry_run:
                continue

            # ------------------------------------------------------------------#
            #  Download & save
            # ------------------------------------------------------------------#
            dest = os.path.join(out_dir, fname)
            try:
                save_mp3(mp3_url, dest, sess)
            except Exception as exc:  # noqa: BLE001
                print(f"      ! download failed: {exc}", file=sys.stderr)
                continue  # don't mark as done
            else:
                # Mark as downloaded immediately (append to file)
                done.add(track_id)
                with open(state_path, "a") as fh:
                    fh.write(track_id + "\n")

            time.sleep(CRAWL_DELAY)  # throttle single-host downloads


# -----------------------------------------------------------------------------#
#  CLI entry point
# -----------------------------------------------------------------------------#
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download free-music MP3s from https://www.chosic.com"
    )
    parser.add_argument(
        "-s",
        "--style",
        default="lofi",
        help="Music style / tag to scrape (default: lofi)",
    )
    parser.add_argument(
        "-o",
        "--out",
        default="chosic",
        help="Root output directory (default: ./chosic)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't download files, just list what would be fetched",
    )
    args = parser.parse_args()

    # Each style gets its own sub-folder and state file
    crawl(args.style, os.path.join(args.out, args.style), args.dry_run)


if __name__ == "__main__":
    main()
