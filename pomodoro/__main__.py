#!/usr/bin/env python3
import os
import time
import random
import threading
import argparse

from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
import pygame


def get_default_playlist():
    """Return paths to default lo-fi tracks included in the package."""
    try:
        # Get the project root directory (2 levels up from __main__.py)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_music_dir = os.path.join(project_root, "default-playlist")

        if os.path.exists(default_music_dir):
            return load_music_files(default_music_dir)

        print(f"[!] Default playlist directory not found at: {default_music_dir}")
        return []
    except Exception as e:
        print(f"[!] Error loading default playlist: {e}")
        return []


def load_music_files(folder):
    """Return list of full paths to audio files in `folder`."""
    if not os.path.exists(folder):
        print(f"[!] Music folder not found: {folder}")
        return []
    exts = (".mp3", ".wav", ".ogg")
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    if not files:
        print(f"[!] No audio files found in: {folder}")
        return []
    print(f"[+] Found {len(files)} audio files in: {folder}")
    return [os.path.join(folder, f) for f in files]


def music_player_loop(playlist):
    """Continuously play random tracks from playlist."""
    if not playlist:
        return

    pygame.mixer.init()
    while True:
        track = random.choice(playlist)
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(1)
        except Exception as e:
            print(f"[!] Couldn't play {track}: {e}")
            time.sleep(1)


def beep():
    """Fallback beep if you want a simple alert."""
    print("\a", end="", flush=True)


def run_cycle(work_sec, break_sec, playlist):
    """Run a single work→break cycle."""
    # Start music thread if we have a playlist
    music_thread = None
    if playlist:
        music_thread = threading.Thread(
            target=music_player_loop, args=(playlist,), daemon=True
        )
        music_thread.start()

    # WORK PHASE
    with Progress(
        TextColumn("[bold green]Work"),
        BarColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("", total=work_sec)
        while not progress.finished:
            time.sleep(1)
            progress.update(task, advance=1)

    # switch to break: stop music, beep
    if playlist:
        pygame.mixer.music.stop()
    beep()
    print("\n🛀  Time for a break!\n")

    # BREAK PHASE
    with Progress(
        TextColumn("[bold cyan]Break"),
        BarColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("", total=break_sec)
        while not progress.finished:
            time.sleep(1)
            progress.update(task, advance=1)

    beep()
    print("\n✅  Break over — back to work!\n")


def main():
    p = argparse.ArgumentParser(description="CLI Lofi Pomodoro Timer")
    p.add_argument("--work", type=int, default=25, help="work minutes (default: 25)")
    p.add_argument(
        "--short", type=int, default=5, help="short break minutes (default: 5)"
    )
    p.add_argument(
        "--long", type=int, default=15, help="long break minutes (default: 15)"
    )
    p.add_argument(
        "--cycles",
        type=int,
        default=4,
        help="number of work/break cycles before long break",
    )
    p.add_argument(
        "--music-folder",
        type=str,
        help="path to folder with your lofi tracks (optional)",
    )
    args = p.parse_args()

    # Get playlist from user folder or default
    playlist = []
    if args.music_folder:
        playlist = load_music_files(args.music_folder)
        if not playlist:
            print(f"No audio files found in {args.music_folder}")
    else:
        playlist = get_default_playlist()
        if not playlist:
            print("No default playlist found. Running without music.")

    for i in range(1, args.cycles + 1):
        print(f"\n🔄  Cycle {i} of {args.cycles}")
        run_cycle(args.work * 60, args.short * 60, playlist)

    # final long break
    print(f"\n🎉  {args.cycles} cycles done—enjoy a longer break!")
    with Progress(
        TextColumn("[bold magenta]Long Break"),
        BarColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("", total=args.long * 60)
        while not progress.finished:
            time.sleep(1)
            progress.update(task, advance=1)
    beep()
    print("\n🏁  All done! Great job.")


if __name__ == "__main__":
    main()
