#!/usr/bin/env python3
"""
lofi-pomodoro.py
----------------
CLI Pomodoro timer that plays lo-fi tracks, lets you press **s** to skip
to the next song, and beeps between phases.

Dependencies:
  pip install rich pygame
"""

import argparse
import os
import queue
import random
import sys
import threading
import time

from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
import pygame

# Global variables
SUPPORTED_AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")

# Break sound options mapping
BREAK_SOUND_OPTIONS = {
    "rain": "rain.mp3",
    "fireplace": "fireplace.mp3",
    "wind": "wind.mp3",
    "soft-wind": "soft-wind.mp3",
    # "random": None,  # Placeholder for random sound
}


# --------------------------------------------------------------------------- #
#                               FILE HELPERS                                  #
# --------------------------------------------------------------------------- #
def get_break_sound(break_sound_option: str | None = None) -> str | None:
    """
    Return path to the break sound based on the option or custom path.

    Args:
        break_sound_option: Either a predefined option name, a custom path, or None for default

    Returns:
        Path to the break sound file or None if not found
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    break_sounds_dir = os.path.join(project_root, "break-sounds")

    # If no option provided, use default (rain)
    if break_sound_option is None:
        break_sound_option = "rain"

    # Check if the option is a custom path (has audio extension)
    if any(
        break_sound_option.lower().endswith(ext) for ext in SUPPORTED_AUDIO_EXTENSIONS
    ):
        # If it's an absolute path, use it directly
        if os.path.isabs(break_sound_option):
            return break_sound_option if os.path.exists(break_sound_option) else None
        # Otherwise, look in the break-sounds directory
        sound_path = os.path.join(break_sounds_dir, break_sound_option)
        return sound_path if os.path.exists(sound_path) else None

    # Handle predefined options
    if break_sound_option in BREAK_SOUND_OPTIONS:
        sound_path = os.path.join(
            break_sounds_dir, BREAK_SOUND_OPTIONS[break_sound_option]
        )
        return sound_path if os.path.exists(sound_path) else None

    return None


def load_music_files(folder: str) -> list[str]:
    """Return a list of audio files in *folder* (mp3/wav/ogg)."""
    if not os.path.isdir(folder):
        print(f"[!] Music folder not found: {folder}")
        return []

    files = [
        f for f in os.listdir(folder) if f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)
    ]
    if not files:
        print(f"[!] No audio files in: {folder}")
        return []

    print(f"[+] Found {len(files)} tracks in: {folder}")
    return [os.path.join(folder, f) for f in files]


def get_default_playlist() -> list[str]:
    """Tracks shipped in ./default-playlist/ (optional)."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    return load_music_files(os.path.join(project_root, "default-playlist"))


# --------------------------------------------------------------------------- #
#                              AUDIO THREAD                                   #
# --------------------------------------------------------------------------- #
def music_player_loop(
    playlist: list[str],
    skip_queue: queue.Queue,
    loop_forever: bool = False,
):
    """
    Continuously play random tracks.  When *skip_queue* gets a signal,
    stops the current track and moves to the next.
    """
    if not playlist:
        return

    pygame.mixer.init()
    played: set[str] = set()

    while True:
        # Reset list if all songs played and we want endless music
        if not playlist:
            break
        if len(played) == len(playlist):
            if loop_forever:
                played.clear()
                print("\n🔄  Playlist finished, starting over …")
            else:
                break

        track = random.choice([t for t in playlist if t not in played])
        played.add(track)

        print(f"\n🎵  Now playing: {os.path.basename(track)}")
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
        except Exception as exc:  # noqa: BLE001
            print(f"[!] Couldn't play {track}: {exc}")
            time.sleep(1)
            continue

        # Wait until song ends or skip key pressed
        while pygame.mixer.music.get_busy():
            try:
                skip_queue.get_nowait()
                pygame.mixer.music.stop()
            except queue.Empty:
                pass
            time.sleep(0.2)


# --------------------------------------------------------------------------- #
#                           CROSS-PLATFORM KEY LISTENER                       #
# --------------------------------------------------------------------------- #
def start_skip_listener(skip_queue: queue.Queue, stop_event: threading.Event) -> None:
    """
    Background thread reading a single keystroke.

    Press lowercase or uppercase **S** in the *same* terminal to enqueue a skip.
    Uses only std-lib (termios/tty on POSIX or msvcrt on Windows).
    """

    def _stdin_worker_posix() -> None:  # Unix, macOS, Linux
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        tty.setcbreak(fd)  # raw mode – no Enter needed
        try:
            while not stop_event.is_set():
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r:
                    ch = sys.stdin.read(1)
                    if ch.lower() == "s":
                        skip_queue.put(True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)

    def _stdin_worker_windows() -> None:  # Windows
        import msvcrt

        while not stop_event.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch.lower() == "s":
                    skip_queue.put(True)
            time.sleep(0.1)

    worker = _stdin_worker_windows if os.name == "nt" else _stdin_worker_posix
    threading.Thread(target=worker, daemon=True).start()


# --------------------------------------------------------------------------- #
#                            TIMER / STATE MACHINE                            #
# --------------------------------------------------------------------------- #
def beep() -> None:
    """Terminal bell – simple and portable."""
    print("\a", end="", flush=True)


def run_phase(label: str, seconds: int) -> None:
    """Render a progress bar for *seconds*."""
    with Progress(
        TextColumn(f"[bold]{label}"),
        BarColumn(),
        TimeRemainingColumn(),
    ) as prog:
        task = prog.add_task("", total=seconds)
        while not prog.finished:
            time.sleep(1)
            prog.update(task, advance=1)


def run_cycle(
    work_sec: int,
    break_sec: int,
    playlist: list[str],
    break_sound: str | None,
    skip_queue: queue.Queue,
    remaining_work_sec: int | None = None,
) -> None:
    """Single work → break cycle."""
    # ---- Work Phase ----
    music_thread = threading.Thread(
        target=music_player_loop,
        args=(playlist, skip_queue, True),
        daemon=True,
    )
    music_thread.start()

    # Use remaining time if provided, otherwise use full work time
    total_work = remaining_work_sec if remaining_work_sec is not None else work_sec
    run_phase("Work", total_work)

    pygame.mixer.music.stop()
    beep()
    print("\n🛀  Time for a break!\n")

    # ---- Break Phase ----
    if break_sound:
        try:
            pygame.mixer.music.load(break_sound)
            pygame.mixer.music.play(-1)
        except Exception as exc:  # noqa: BLE001
            print(f"[!] Couldn't play break sound: {exc}")

    run_phase("Break", break_sec)

    pygame.mixer.music.stop()
    beep()
    print("\n✅  Break over — back to work!\n")


# --------------------------------------------------------------------------- #
#                                   MAIN                                      #
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="CLI Lo-fi Pomodoro Timer")

    parser.add_argument("--work", type=int, default=25, help="work minutes (25)")
    parser.add_argument("--short", type=int, default=5, help="short break minutes (5)")
    parser.add_argument("--long", type=int, default=15, help="long break minutes (15)")
    parser.add_argument("--cycles", type=int, default=4, help="work/break cycles (4)")
    parser.add_argument("--music-folder", type=str, help="folder with tracks")
    parser.add_argument(
        "--no-work-music", action="store_true", help="disable music during work"
    )
    parser.add_argument(
        "--no-break-sound", action="store_true", help="disable sound in breaks"
    )
    parser.add_argument(
        "--break-sound",
        type=str,
        default="rain",
        help="break sound to use (default: rain). Can be one of: "
        + ", ".join(BREAK_SOUND_OPTIONS.keys())
        + ", or a path to a custom sound file",
    )
    parser.add_argument(
        "--volume", type=float, default=1.0, help="volume 0.0–1.0 (1.0)"
    )
    parser.add_argument(
        "--resume",
        type=int,
        help="resume with X minutes remaining in the first work cycle",
    )
    args = parser.parse_args()

    if not 0.0 <= args.volume <= 1.0:
        parser.error("Volume must be between 0.0 and 1.0")

    # Convert resume time to seconds if provided
    remaining_work_sec = args.resume * 60 if args.resume is not None else None
    if remaining_work_sec is not None:
        print(f"\n⏱️  Resuming with {args.resume} minutes remaining in first work cycle")

    # ---------- Load audio ----------
    playlist: list[str] = []
    if not args.no_work_music:
        if args.music_folder:
            playlist = load_music_files(args.music_folder)
        else:
            playlist = get_default_playlist()

        if not playlist:
            print("[!] No tracks found – running without work music.")

    break_sound = None if args.no_break_sound else get_break_sound(args.break_sound)
    if not break_sound and not args.no_break_sound:
        print(f"[!] Break sound '{args.break_sound}' not found – muted breaks.")

    pygame.mixer.init()
    pygame.mixer.music.set_volume(args.volume)

    # ---------- Key listener ----------
    skip_queue: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    start_skip_listener(skip_queue, stop_event)
    print("🎹  Press 's' to skip to the next track\n")

    # ---------- Cycles ----------
    for cycle in range(1, args.cycles + 1):
        print(f"\n🔄  Cycle {cycle} of {args.cycles}")
        # Only use remaining time for the first cycle
        remaining = remaining_work_sec if cycle == 1 else None
        run_cycle(
            args.work * 60,
            args.short * 60,
            playlist,
            break_sound,
            skip_queue,
            remaining,
        )

    # ---------- Long break ----------
    print(f"\n🎉  {args.cycles} cycles done — enjoy a longer break!")
    run_phase("Long Break", args.long * 60)
    beep()
    print("\n🏁  All done! Great job.")

    stop_event.set()  # stop the key listener


if __name__ == "__main__":
    main()
