"""Download the project's default playlist into a per-user cache."""

from __future__ import annotations

import json
import os
import ssl
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from platformdirs import user_cache_path
import truststore

REPOSITORY = "WittmannF/lofi-pomodoro"
PLAYLIST_PATH = "pomodoro/default-playlist"
PLAYLIST_REF = "main"
USER_AGENT = "lofi-pomodoro"
TLS_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def default_playlist_dir() -> Path:
    """Return the stable, per-user location for downloaded tracks."""
    return Path(user_cache_path("lofi-pomodoro")) / "default-playlist"


def _get_playlist_files() -> list[dict[str, str]]:
    url = (
        f"https://api.github.com/repos/{REPOSITORY}/contents/"
        f"{PLAYLIST_PATH}?ref={PLAYLIST_REF}"
    )
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30, context=TLS_CONTEXT) as response:
        content = json.load(response)
    return [
        item
        for item in content
        if item.get("type") == "file"
        and item.get("name", "").lower().endswith((".mp3", ".wav", ".ogg"))
        and item.get("download_url")
    ]


def _download_track(item: dict[str, str], destination: Path) -> None:
    request = urllib.request.Request(
        item["download_url"], headers={"User-Agent": USER_AGENT}
    )
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".part", dir=destination.parent
    )
    try:
        with os.fdopen(file_descriptor, "wb") as output:
            with urllib.request.urlopen(
                request, timeout=120, context=TLS_CONTEXT
            ) as response:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def ensure_default_playlist() -> Path:
    """Return the cached playlist, fetching missing files from the public repo."""
    directory = default_playlist_dir()
    directory.mkdir(parents=True, exist_ok=True)

    marker = directory / ".complete"
    if marker.exists():
        return directory

    print("[+] Downloading the default playlist (this may take a few minutes)...")
    try:
        files = _get_playlist_files()
        if not files:
            raise RuntimeError("the repository has no downloadable playlist files")

        missing = [
            item
            for item in files
            if not (directory / item["name"]).is_file()
            or (directory / item["name"]).stat().st_size == 0
        ]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(_download_track, item, directory / item["name"]): item
                for item in missing
            }
            failures: list[str] = []
            for index, future in enumerate(as_completed(futures), start=1):
                item = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    failures.append(f"{item['name']}: {exc}")
                print(f"[+] Playlist download: {index}/{len(missing)} tracks")

        tracks = (
            list(directory.glob("*.mp3"))
            + list(directory.glob("*.wav"))
            + list(directory.glob("*.ogg"))
        )
        if not tracks:
            raise RuntimeError("no tracks could be downloaded: " + "; ".join(failures))
        if failures:
            print(f"[!] {len(failures)} tracks failed to download; using the rest.")
        else:
            marker.write_text(PLAYLIST_REF, encoding="utf-8")
    except (OSError, urllib.error.URLError, json.JSONDecodeError, RuntimeError) as exc:
        tracks = (
            list(directory.glob("*.mp3"))
            + list(directory.glob("*.wav"))
            + list(directory.glob("*.ogg"))
        )
        if not tracks:
            raise RuntimeError(
                f"could not download the default playlist ({exc}). "
                "Check your internet connection or pass --music-folder."
            ) from exc
        print(f"[!] Playlist download was incomplete ({exc}); using cached tracks.")

    return directory
