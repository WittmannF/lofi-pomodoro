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

## Installation

Clone the repository and install locally:

```bash
git clone https://github.com/WittmannF/lofi-pomodoro.git
cd lofi-pomodoro
pip install -e .
```

## Usage

Run the timer with your music folder:

```bash
lofi-pomodoro --music-folder /path/to/your/music
```

Or use the default playlist:

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

### Command-Line Arguments

| Argument           | Description                                                                                                     | Default    |
| ------------------ | --------------------------------------------------------------------------------------------------------------- | ---------- |
| `--music-folder`   | Path to folder containing `.mp3`, `.wav`, or `.ogg` files. If omitted, a default open-license playlist is used. | (optional) |
| `--work`           | Work duration in minutes                                                                                        | `25`       |
| `--short`          | Short break duration in minutes                                                                                 | `5`        |
| `--long`           | Long break duration in minutes                                                                                  | `15`       |
| `--cycles`         | Number of work/break cycles before a long break                                                                 | `4`        |
| `--resume`         | Resume with X minutes remaining in the first work cycle                                                         | (optional) |
| `--no-work-music`  | Disable the work music                                                                                          | `false`    |
| `--no-break-sound` | Disable the break sound effect                                                                                  | `false`    |
| `--volume`         | Set the volume (0.0 to 1.0)                                                                                     | `1.0`      |

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
3. Run tests (if available) or try it out:

   ```bash
   python pomodoro.py --music-folder ./music
   ```

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open a pull request or submit an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
