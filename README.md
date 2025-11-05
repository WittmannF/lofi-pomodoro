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
pip install -e .
```

## Getting Started

### Downloading Free Music

The project includes a script to download free lo-fi music from [Chosic](https://www.chosic.com). You can use it to build your own playlist.

**Note:** The scrape script requires additional dependencies. Install them with:

```bash
pip install requests beautifulsoup4
```

Then you can use the script:

```bash
# Download lo-fi tracks (default style)
python scripts/scrape_songs.py
```

The script will:
- Download MP3 files from Chosic's free music library
- Save them to `chosic/{style}/` by default (e.g., `chosic/lofi/`)
- Remember what it has already downloaded (so you can re-run it safely)
- Use respectful crawling with delays between requests

**Note:** You can also use any folder containing `.mp3`, `.wav`, or `.ogg` files as your music source. Simply point the timer to your folder using the `--music-folder` option.

## Usage

### Basic Usage

Run the timer with your music folder:

```bash
lofi-pomodoro --music-folder /path/to/your/music
```

Or use the default playlist (if available in `pomodoro/default-playlist/`):

```bash
lofi-pomodoro
```

Example with custom settings:

```bash
lofi-pomodoro \
  --music-folder ./music \
  --work 50 \
  --short 10 \
  --long 20 \
  --cycles 3 \
  --volume 0.7
```

Resume a session with remaining time:

```bash
lofi-pomodoro --resume 15  # Resume with 15 minutes remaining in first work cycle
```

Run without music or break sounds:

```bash
lofi-pomodoro --no-work-music --no-break-sound  # Run silently
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

## Development

1. Clone the repo:

   ```bash
   git clone https://github.com/WittmannF/lofi-pomodoro.git
   cd lofi-pomodoro
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install the package in editable mode:

   ```bash
   pip install -e .
   ```

4. Try it out:

   ```bash
   # Download some music first
   python scripts/scrape_songs.py

   # Run the timer
   python -m pomodoro --music-folder chosic/lofi
   ```

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open a pull request or submit an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
