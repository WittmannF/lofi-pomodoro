# Post — Reddit r/Python

**Subreddit:** r/Python  
**Tipo:** Text post com link para GitHub  
**Tom:** técnico, direto, sem hype

---

## Título (opções)

**Opção A (foco na stack):**
> I built a terminal Pomodoro timer with a built-in lo-fi player using pygame and Rich

**Opção B (foco na experiência):**
> Show r/Python: pomodoro CLI — 250 bundled lo-fi tracks, keyboard controls, no browser needed

**Opção C (foco no diferencial):**
> My Pomodoro timer plays lo-fi music in the terminal and skips tracks with 's' — built with pygame + threading

---

## Corpo do post

```
Hey r/Python,

I built a CLI Pomodoro timer that also plays lo-fi music directly in the terminal.
No Electron, no browser tab, no Spotify — just `pip install pomodoro-lofi` and go.

**What it does:**
- 25/5/15 min Pomodoro cycles with a Rich progress bar
- 250+ bundled lo-fi tracks (works completely offline)
- Keyboard controls during the session: `s` skip, `p` pause, `i` ignore (never play again)
- Custom music folder support (`--music-folder /path`)
- Break sounds (rain, fireplace, wind) that play during short breaks
- Optional ElevenLabs integration to generate AI music before your session

**Stack:**
- `pygame` for audio playback
- `rich` for the terminal UI
- `threading` + `queue` for the music player daemon and key listener
- Single-file architecture (`pomodoro/__main__.py`)

**Install:**
pip install pomodoro-lofi

**Run:**
pomodoro                          # default 25/5/15
pomodoro --work 1 --short 1       # short cycles for testing
pomodoro --music-folder ~/music   # custom folder

GitHub: [link]

Would love feedback on the threading model — the music player and key listener run
as daemon threads communicating via queues. Worked well in practice but curious if
others have done this differently.
```

---

## Comentário de follow-up (postar como primeiro comentário)

```
For those curious about the implementation:

The app runs as a state machine on the main thread. Two daemon threads handle music
and keyboard input, communicating via two separate queues:

- control_queue: key listener → music player (skip/pause/ignore)
- timer_queue: key listener → main thread (pause/unpause the countdown)

The key listener uses select/termios/tty on POSIX and msvcrt on Windows for
non-blocking reads. Works without pressing Enter.

Happy to answer architecture questions.
```
