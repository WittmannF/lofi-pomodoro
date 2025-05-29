#!/usr/bin/env python3
import os
import time
import random
import threading
import argparse

from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
import pygame


def get_break_sound():
    """Get the path to the break sound file."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sound_path = os.path.join(project_root, "break-sounds", "crickets.mp3")

    if os.path.exists(sound_path):
        return sound_path
    print(f"[!] Break sound not found at: {sound_path}")
    return None


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


def music_player_loop(playlist, is_break=False, break_sound=None):
    """Continuously play random tracks from playlist or break sound."""
    if not playlist and not is_break:
        return

    pygame.mixer.init()
    played_tracks = set()  # Keep track of played tracks in current session

    while True:
        try:
            if is_break and break_sound:
                pygame.mixer.music.load(break_sound)
                pygame.mixer.music.play(-1)  # Loop the break sound
                while pygame.mixer.music.get_busy():
                    time.sleep(1)
            else:
                # If all tracks have been played, reset the played tracks
                if len(played_tracks) == len(playlist):
                    played_tracks.clear()
                    print("\n🔄  Playlist completed, starting over...")

                # Get a track that hasn't been played yet
                available_tracks = [t for t in playlist if t not in played_tracks]
                track = random.choice(available_tracks)
                played_tracks.add(track)

                pygame.mixer.music.load(track)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(1)
        except Exception as e:
            print(f"[!] Couldn't play sound: {e}")
            time.sleep(1)


def beep():
    """Fallback beep if you want a simple alert."""
    print("\a", end="", flush=True)


def run_cycle(work_sec, break_sec, playlist, break_sound, remaining_work_sec=None):
    """Run a single work→break cycle."""
    # Start music thread if we have a playlist
    music_thread = None
    if playlist or break_sound:
        music_thread = threading.Thread(
            target=music_player_loop, args=(playlist, False, break_sound), daemon=True
        )
        music_thread.start()

    # WORK PHASE
    with Progress(
        TextColumn("[bold green]Work"),
        BarColumn(),
        TimeRemainingColumn(),
    ) as progress:
        # Use remaining time if provided, otherwise use full work time
        total_work = remaining_work_sec if remaining_work_sec is not None else work_sec
        task = progress.add_task("", total=total_work)
        while not progress.finished:
            time.sleep(1)
            progress.update(task, advance=1)

    # switch to break: stop music, beep
    if playlist or break_sound:
        pygame.mixer.music.stop()
        # Start break sound
        if break_sound:
            music_thread = threading.Thread(
                target=music_player_loop,
                args=(playlist, True, break_sound),
                daemon=True,
            )
            music_thread.start()
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

    # Stop break sound
    if break_sound:
        pygame.mixer.music.stop()
    beep()
    print("\n✅  Break over — back to work!\n")


def main():
    p = argparse.ArgumentParser(description="CLI Lofi Pomodoro Timer")
    p.add_argument(
        "--work", type=int, default=25, help="work duration in minutes (default: 25)"
    )
    p.add_argument(
        "--short",
        type=int,
        default=5,
        help="short break duration in minutes (default: 5)",
    )
    p.add_argument(
        "--long",
        type=int,
        default=15,
        help="long break duration in minutes (default: 15)",
    )
    p.add_argument(
        "--cycles",
        type=int,
        default=4,
        help="number of work/break cycles before a long break (default: 4)",
    )
    p.add_argument(
        "--music-folder",
        type=str,
        help="path to folder with your lofi tracks (optional)",
    )
    p.add_argument(
        "--resume",
        type=int,
        help="resume with X minutes remaining in the first work cycle",
    )
    p.add_argument(
        "--no-break-sound",
        action="store_true",
        help="disable the break sound effect",
    )
    p.add_argument(
        "--no-work-music",
        action="store_true",
        help="disable the work music",
    )
    p.add_argument(
        "--volume",
        type=float,
        default=1.0,
        help="set the volume (0.0 to 1.0, default: 1.0)",
    )
    args = p.parse_args()

    # Validate volume
    if not 0.0 <= args.volume <= 1.0:
        print("[!] Volume must be between 0.0 and 1.0")
        return

    # Get playlist from user folder or default
    playlist = []
    if not args.no_work_music:
        if args.music_folder:
            playlist = load_music_files(args.music_folder)
            if not playlist:
                print(f"No audio files found in {args.music_folder}")
        else:
            playlist = get_default_playlist()
            if not playlist:
                print("No default playlist found. Running without music.")

    # Get break sound
    break_sound = None if args.no_break_sound else get_break_sound()
    if not break_sound and not args.no_break_sound:
        print("Running without break sound effect.")

    # Convert resume time to seconds if provided
    remaining_work_sec = args.resume * 60 if args.resume is not None else None
    if remaining_work_sec is not None:
        print(f"\n⏱️  Resuming with {args.resume} minutes remaining in first work cycle")

    # Initialize pygame mixer with volume
    pygame.mixer.init()
    pygame.mixer.music.set_volume(args.volume)

    for i in range(1, args.cycles + 1):
        print(f"\n🔄  Cycle {i} of {args.cycles}")
        # Only use remaining time for the first cycle
        remaining = remaining_work_sec if i == 1 else None
        run_cycle(args.work * 60, args.short * 60, playlist, break_sound, remaining)

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
