# lofi-pomodoro

A CLI Pomodoro timer that plays music during work sessions — use the bundled lo-fi playlist or control your Spotify directly from the terminal.

## Features

* **CLI Progress Bar**: Live countdown and progress bar using [Rich](https://github.com/Textualize/rich).
* **Spotify Mode**: Control your Spotify playback during work sessions (requires Premium).
* **Lo-fi Audio Playback**: Bundled playlist of 250+ open-license lo-fi tracks via pygame.
* **Break Sounds**: Ambient sounds (rain, fireplace, wind) play automatically during breaks.
* **Configurable Durations**: Customize work, short break, and long break lengths.
* **Cycle Support**: Set the number of work/break cycles before a long break.
* **Session Resume**: Resume a session from where you left off using `--resume`.
* **Music Controls**: Press `s` to skip, `p` to pause/unpause, `i` to ignore, `q` to quit.

---

## Quick Start

**Local mode** (bundled playlist, no setup needed):

```bash
git clone https://github.com/WittmannF/lofi-pomodoro.git
cd lofi-pomodoro
uv venv .venv && source .venv/bin/activate
uv pip install -e .
pomodoro
```

**Spotify mode** (controls your Spotify app):

```bash
uv pip install -e ".[spotify]"
pomodoro --spotify --spotify-playlist lofi
```

On first run it will ask for your Spotify Client ID and open the browser for authorization. After that it's instant.

---

## Usage

### Basic

```bash
pomodoro                                        # bundled lo-fi playlist
pomodoro --music-folder ~/my-music              # custom folder
pomodoro --work 50 --short 10 --long 30         # custom durations
pomodoro --resume 15                            # resume with 15 min left
pomodoro --no-work-music --no-break-sound       # silent mode
```

### Spotify Mode

Control your Spotify playback during work sessions. Break sounds (rain, fireplace, etc.) still play locally.

**Requirements:** Spotify Premium + Spotify app open on any device.

**One-time setup:**

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app
2. Set the Redirect URI to `http://127.0.0.1:8888/callback`
3. Check "Web API" and save
4. Install the Spotify extra: `uv pip install -e ".[spotify]"`

**Run:**

```bash
pomodoro --spotify                                                        # resumes whatever is playing
pomodoro --spotify --spotify-playlist lofi                                # built-in preset
pomodoro --spotify --spotify-playlist spotify:playlist:37i9dQZF1DX0SM0LYsmbMT  # custom URI
```

Built-in playlist presets: `lofi`, `lofi-beats`, `jazz`, `deep-focus`, `chill`.

**Adding your own presets** — edit `~/.config/pomodoro/spotify.json`:

```json
{
  "client_id": "...",
  "playlists": {
    "metal": "spotify:playlist:your-uri-here"
  }
}
```

**List and select devices:**

```bash
pomodoro --spotify-devices                      # list available devices
pomodoro --spotify --spotify-device 1           # select by number
pomodoro --spotify --spotify-device "MacBook Pro"  # select by name
```

### Music Controls

During work sessions:

| Key | Action |
|-----|--------|
| `s` | Skip to next track |
| `p` | Pause/unpause timer and music |
| `i` | Ignore current song (local mode only) |
| `q` | Quit session cleanly |

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--work` | Work duration in minutes | `25` |
| `--short` | Short break duration in minutes | `5` |
| `--long` | Long break duration in minutes | `15` |
| `--cycles` | Cycles before a long break | `4` |
| `--resume` | Resume with X minutes left in first cycle | — |
| `--music-folder` | Custom music folder | bundled playlist |
| `--no-work-music` | Disable work music | `false` |
| `--no-break-sound` | Disable break sounds | `false` |
| `--break-sound` | Break sound: `rain`, `fireplace`, `wind`, `soft-wind`, `random`, or path | `random` |
| `--volume` | Volume 0.0–1.0 | `1.0` |
| `--reset-ignored` | Clear the ignored songs list | — |
| `--spotify` | Enable Spotify mode (requires Premium) | `false` |
| `--spotify-playlist` | Preset name or full Spotify URI | active playback |
| `--spotify-device` | Device name, number, or ID | active device |
| `--spotify-devices` | List available Spotify devices and exit | — |

---

## Music Sources

The bundled playlist has 250+ tracks. You can expand it with the included scripts:

| Script | Source | Install |
|--------|--------|---------|
| `scripts/scrape_songs.py` | Chosic (lo-fi, no login) | `uv pip install -e ".[scrape]"` |
| `scripts/scrape_fma.py` | Free Music Archive (35k+ tracks) | `uv pip install -e ".[scrape]"` |
| `scripts/download_youtube.py` | YouTube (add URLs to `youtube_links.txt`) | `uv pip install -e ".[youtube]"` + `brew install ffmpeg` |

All scripts save to `pomodoro/default-playlist/` and skip already-downloaded tracks.

See [docs/scripts.md](docs/scripts.md) for the full CLI reference.

---

## Development

```bash
git clone https://github.com/WittmannF/lofi-pomodoro.git
cd lofi-pomodoro
uv venv .venv && source .venv/bin/activate
uv pip install -e .
pomodoro --work 1 --short 1   # quick test cycle
```

### Fixing ID3 Tag Warnings

Some MP3 files contain empty ID3 frames that cause pygame to print a harmless warning. To silence them:

```bash
uv pip install -e ".[id3]"
python scripts/fix_id3_tags.py           # fix all tracks
python scripts/fix_id3_tags.py --dry-run # preview changes
python scripts/fix_id3_tags.py -d /path  # fix custom folder
```

---

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open a pull request or submit an issue on GitHub.

## License

MIT — see [LICENSE](LICENSE).
