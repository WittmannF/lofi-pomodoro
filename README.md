# lofi-pomodoro

A simple, relaxing CLI Pomodoro timer that plays lo-fi beats during work sessions to help you stay focused and calm.

## Features

* **CLI Progress Bar**: Live countdown and progress bar using [Rich](https://github.com/Textualize/rich).
* **Lo-fi Audio Playback**: Randomly plays tracks from your specified folder using [pygame](https://www.pygame.org/).
* **Default Playlist**: If no `--music-folder` is provided, a built-in playlist of open-license lo-fi tracks will be used from the repository.
* **Configurable Durations**: Customize work, short break, and long break lengths.
* **Cycle Support**: Set the number of work/break cycles before a long break.
* **Simple Alerts**: Terminal beep and messages when switching phases.
* **Break Sounds**: Different ambient sounds during work and break periods.
* **Session Resume**: Resume a session from where you left off using the `--resume` option.
* **Audio Control**: Adjust volume and toggle work music/break sounds independently.
* **Music Controls**: Press 's' to skip, 'p' to pause/unpause, or 'i' to ignore a song during work sessions.

## Example of CLI
```bash
source .venv/bin/activate && pomodoro
pygame 2.6.1 (SDL 2.28.4, Python 3.12.2)
Hello from the pygame community. https://www.pygame.org/contribute.html
[+] Found 254 tracks in: /Users/wittmann/repos/pomodoro/pomodoro/default-playlist (12 ignored)
🎹  Press 's' to skip, 'p' to pause/unpause timer & music, 'i' to ignore song


🔄  Cycle 1 of 4

🎵  Now playing: Ghostrifter-Official-Back-Home(chosic.com).mp3

🎵  Now playing: Balloon(chosic.com).mp3

🎵  Now playing: roa-music-walk-around-lofi-version(chosic.com).mp3

🎵  Now playing: journey-end(chosic.com).mp3

🎵  Now playing: Daydreams-chosic.com_.mp3

🎵  Now playing: And-So-It-Begins-Inspired-By-Crush-Sometimes(chosic.com).mp3

🎵  Now playing: breathe-chill-lofi-beats-362644.mp3

🎵  Now playing: Wondering(chosic.com).mp3

🎵  Now playing: Ghostrifter-Official-Simplicit-Nights(chosic.com).mp3

🎵  Now playing: Little-Wishes-chosic.com_.mp3

🛀  Time for a break!

Break ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:01

✅  Break over — back to work!


🔄  Cycle 2 of 4

🎵  Now playing: Wonderment(chosic.com).mp3

🎵  Now playing: ambient-lofi-lofi-music-344112.mp3

🎵  Now playing: purrple-cat-dreams-come-true(chosic.com).mp3

Work ━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:17:22
```

## Installation

Clone the repository and install locally:

```bash
git clone https://github.com/WittmannF/lofi-pomodoro.git
cd lofi-pomodoro
uv venv .venv && source .venv/bin/activate
uv pip install -e .
```

## Getting Started

### Optional script dependencies

The helper scripts each have their own dependencies beyond the core timer. Install only what you need:

| Script | Purpose | Install |
|--------|---------|---------|
| `scripts/scrape_songs.py` | Download lo-fi tracks from Chosic | `uv pip install -e ".[scrape]"` |
| `scripts/scrape_fma.py` | Download tracks from Free Music Archive | `uv pip install -e ".[scrape]"` |
| `scripts/download_youtube.py` | Download audio from YouTube | `uv pip install -e ".[youtube]"` + `brew install ffmpeg` |
| `scripts/fix_id3_tags.py` | Strip empty ID3 frames to silence pygame warnings | `uv pip install -e ".[id3]"` |

To install all optional dependencies at once:

```bash
uv pip install -e ".[scripts]"
```

See [docs/scripts.md](docs/scripts.md) for the full CLI reference for each script.

### Downloading Free Music

The project includes scripts to build your playlist from free sources.

**From Chosic** (lo-fi, no login required):

```bash
python scripts/scrape_songs.py
```

**From Free Music Archive** (35 000+ lo-fi tracks, no login required):

```bash
python scripts/scrape_fma.py
```

**From YouTube** (add URLs to `youtube_links.txt` first):

```bash
python scripts/download_youtube.py
```

All scripts save tracks directly to `pomodoro/default-playlist/` and remember what was already downloaded so re-runs are safe.

**Note:** You can also use any folder containing `.mp3`, `.wav`, or `.ogg` files as your music source. Simply point the timer to your folder using the `--music-folder` option.

### Fixing ID3 Tag Warnings

Some MP3 files (especially AI-generated or auto-tagged tracks) contain empty ID3 comment/lyric frames that cause pygame to print a harmless but noisy warning:

```
[src/libmpg123/id3.c:process_comment():584] error: No comment text / valid description?
```

To silence this, remove the empty frames with the included script (non-empty comments and lyrics are preserved):

```bash
# Install eyeD3 (one-time)
pip install eyed3

# Fix all tracks in the default playlist
python scripts/fix_id3_tags.py

# Preview what would change without modifying files
python scripts/fix_id3_tags.py --dry-run

# Fix a custom folder
python scripts/fix_id3_tags.py -d /path/to/music
```

## Usage

### Basic Usage

Run the timer with your music folder:

```bash
pomodoro --music-folder /path/to/your/music
```

Or use the default playlist (if available in `pomodoro/default-playlist/`):

```bash
pomodoro
```

Example with custom settings:

```bash
pomodoro \
  --music-folder ./music \
  --work 50 \
  --short 10 \
  --long 20 \
  --cycles 3 \
  --volume 0.7
```

Resume a session with remaining time:

```bash
pomodoro --resume 15  # Resume with 15 minutes remaining in first work cycle
```

Run without music or break sounds:

```bash
pomodoro --no-work-music --no-break-sound  # Run silently
```

### Music Controls

During work sessions, you can control the music playback:
- Press `s` to skip to the next track
- Press `p` to pause/unpause the timer and music
- Press `i` to ignore the current song (adds it to `.ignored_songs` file)
- The current track name is displayed when it starts playing
- Tracks won't repeat until all tracks have been played

### Command-Line Arguments

| Argument           | Description                                                                                                     | Default    |
| ------------------ | --------------------------------------------------------------------------------------------------------------- | ---------- |
| `--music-folder`   | Path to folder containing `.mp3`, `.wav`, or `.ogg` files. If omitted, a default playlist is used (if available). | (optional) |
| `--work`           | Work duration in minutes                                                                                        | `25`       |
| `--short`          | Short break duration in minutes                                                                                 | `5`        |
| `--long`           | Long break duration in minutes                                                                                  | `15`       |
| `--cycles`         | Number of work/break cycles before a long break                                                                 | `4`        |
| `--resume`         | Resume with X minutes remaining in the first work cycle                                                         | (optional) |
| `--no-work-music`  | Disable the work music                                                                                          | `false`    |
| `--no-break-sound` | Disable the break sound effect                                                                                  | `false`    |
| `--break-sound`    | Break sound to use: `rain`, `fireplace`, `wind`, `soft-wind`, `random`, or path to custom sound file          | `random`   |
| `--volume`         | Set the volume (0.0 to 1.0)                                                                                     | `1.0`      |
| `--reset-ignored`  | Reset the list of ignored songs                                                                                 | (optional) |
| `--spotify`        | Use Spotify for work music (requires Premium)                                                                   | `false`    |
| `--spotify-playlist` | Playlist preset name (`lofi`, `deep-focus`, `chill`, `jazz`) or full Spotify URI                               | (optional) |
| `--spotify-device` | Target Spotify device name                                                                                      | (active)   |

### Spotify Mode

Control your Spotify playback directly during work sessions instead of playing local files. Break sounds (rain, fireplace, etc.) still play locally.

**Requirements:** Spotify Premium + Spotify app open on any device.

**Setup (one-time):**

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app
2. Set the Redirect URI to `http://127.0.0.1:8888/callback`
3. Check "Web API" and save
4. Install the spotify extra:

```bash
uv pip install -e ".[spotify]"
```

5. Run with `--spotify` — on first run it will ask for your Client ID and open the browser for authorization:

```bash
pomodoro --spotify
```

The Client ID is saved to `~/.config/pomodoro/spotify.json` and the auth token is cached, so subsequent runs are instant.

**With a preset playlist:**

```bash
pomodoro --spotify --spotify-playlist lofi
pomodoro --spotify --spotify-playlist deep-focus
pomodoro --spotify --spotify-playlist chill
```

Built-in presets: `lofi`, `lofi-beats`, `jazz`, `deep-focus`, `chill`.

**With a custom Spotify URI:**

```bash
pomodoro --spotify --spotify-playlist spotify:playlist:37i9dQZF1DX0SM0LYsmbMT
```

**Adding your own presets** — edit `~/.config/pomodoro/spotify.json`:

```json
{
  "client_id": "...",
  "playlists": {
    "metal": "spotify:playlist:your-uri-here",
    "ambient": "spotify:playlist:another-uri"
  }
}
```

Then use them by name: `pomodoro --spotify --spotify-playlist metal`

**Targeting a specific device:**

```bash
pomodoro --spotify --spotify-device "MacBook Pro"
```

## Development

1. Clone the repo:

   ```bash
   git clone https://github.com/WittmannF/lofi-pomodoro.git
   cd lofi-pomodoro
   ```

2. Create a virtual environment and install:

   ```bash
   uv venv .venv && source .venv/bin/activate
   uv pip install -e .
   ```

3. Try it out:

   ```bash
   # Download some music first
   python scripts/scrape_songs.py

   # Run the timer
   pomodoro
   ```

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open a pull request or submit an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
