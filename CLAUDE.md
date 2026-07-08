# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup & Running

Install in editable mode (use `uv` per global preferences):

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

Optional extras:

```bash
uv pip install -e ".[spotify]"   # Spotify playback control (requires Premium)
uv pip install -e ".[youtube]"   # yt-dlp for download_youtube.py (also needs ffmpeg)
uv pip install -e ".[scrape]"    # requests + bs4 for FMA/Chosic scrapers
uv pip install -e ".[id3]"       # eyed3 for fix_id3_tags.py
```

Run the timer:

```bash
pomodoro                          # default 25/5/15 min with bundled playlist
pomodoro --work 1 --short 1       # short cycles for manual testing
pomodoro --music-folder /path/to/music --volume 0.7
pomodoro --resume 15              # resume with 15 min left in first work cycle
```

There are no automated tests or linting configs. Manual test with short cycles (`--work 1 --short 1`).

## Architecture

Everything lives in a single file: `pomodoro/__main__.py`. The application runs as a state machine across multiple threads:

- **Main thread** — parses args, drives the cycle loop (`main()` → `run_cycle()` → `run_phase()`)
- **Music player thread** (daemon) — `music_player_loop()`: shuffles tracks from the playlist, responds to `control_queue` commands (`"skip"`, `"toggle_pause"`, `"ignore"`)
- **Key listener thread** (daemon) — `start_key_listener()`: non-blocking keyboard reads, writes `"skip"/"toggle_pause"/"ignore"` to `control_queue` and `"pause"/"unpause"` to `timer_queue`. POSIX uses `select`/`termios`/`tty`; Windows uses `msvcrt`.

**Inter-thread communication:**

| Queue | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `control_queue` | key listener | music player | skip / pause / ignore track |
| `timer_queue` | key listener | `run_phase()` | pause/unpause the countdown |

**Key functions:**

- `run_phase(label, duration, ...)` — renders the Rich progress bar, tracks paused time accurately so pauses don't distort the countdown
- `run_cycle(work, short/long break, ...)` — one full work→break cycle; spawns/joins the music thread
- `beep()` — generates an 800 Hz sine wave via pygame (terminal bell fallback)
- `get_break_sound()` — resolves break sound by name (`rain`, `fireplace`, `wind`, `soft-wind`, `random`) or custom path; sounds are bundled in `pomodoro/break-sounds/`
- `load_music_files()` / `load_ignored_songs()` / `add_to_ignored_songs()` — manage the playlist and the `.ignored_songs` persistence file

Default playlist (250+ lo-fi tracks) ships inside the package at `pomodoro/default-playlist/`. The scraper for downloading additional free tracks is in `scripts/scrape_songs.py`.

## CLI Arguments

| Flag | Default | Purpose |
|------|---------|---------|
| `--work` | 25 | Work duration (min) |
| `--short` | 5 | Short break (min) |
| `--long` | 15 | Long break (min) |
| `--cycles` | 4 | Cycles before long break |
| `--music-folder` | bundled | Custom music folder |
| `--no-work-music` | false | Disable work music |
| `--no-break-sound` | false | Disable break sounds |
| `--break-sound` | random | rain/fireplace/wind/soft-wind/random/path |
| `--volume` | 1.0 | 0.0–1.0 |
| `--resume` | — | Minutes remaining in first work cycle |
| `--reset-ignored` | false | Clear `.ignored_songs` |
| `--snooze` | 10 | Snooze duration in minutes at end of work phase (0 to disable) |

Keyboard shortcuts during a session: `s` skip song / snooze (at end-of-work prompt), `p` pause/unpause, `i` ignore song, `q` quit.

## Spotify Mode

`pomodoro/spotify_player.py` contains a separate module that provides a drop-in replacement for the local music thread. It uses Spotipy with PKCE auth (no client secret); credentials are stored at `~/.config/pomodoro/spotify.json`.

```bash
pomodoro --spotify                                  # prompts for Client ID on first run
pomodoro --spotify --spotify-playlist deep-focus    # preset: lofi / deep-focus / chill
pomodoro --spotify --spotify-playlist "spotify:playlist:..."
pomodoro --spotify-devices                          # list available devices and exit
pomodoro --spotify --spotify-device "MacBook Pro"   # target a specific device
```

`spotify_player_loop()` in that module mirrors the same `control_queue` interface as `music_player_loop()`, so `run_cycle()` branches on `spotify_player` being set without changing the core flow.

## Scripts

Utility scripts in `scripts/` (not part of the installed package):

| Script | Extra | Purpose |
|--------|-------|---------|
| `scrape_songs.py` | `scrape` | Download free lo-fi tracks from Chosic |
| `scrape_fma.py` | `scrape` | Download tracks from Free Music Archive |
| `download_youtube.py` | `youtube` | Download audio from YouTube into the playlist |
| `fix_id3_tags.py` | `id3` | Clean/normalize ID3 tags on downloaded MP3s |
| `generate_music.py` | `elevenlabs` | Generate music via ElevenLabs API |
