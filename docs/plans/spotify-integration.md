# Spotify Integration Plan

## Goal

Add an optional `--spotify` mode that replaces the local `pygame`-based music player with direct Spotify playback control during work phases, while keeping all existing behavior (break sounds, key shortcuts, timer logic, ignore list) intact.

The integration must be **opt-in and additive**: users without Spotify or without Premium should experience zero regressions. Local playlist mode remains the default.

---

## Current Project Context

- Single-file app: `pomodoro/__main__.py`.
- Music playback is local-file based via `pygame.mixer.music`, shuffled in `music_player_loop()`.
- `run_cycle()` spawns a daemon `music_thread` for the work phase, stops it on break.
- Key listener writes `"skip"`, `"toggle_pause"`, `"ignore"` to `control_queue`, and `"toggle_pause"` to `timer_queue`.
- Break sounds play locally via pygame regardless of music source — this does **not** change.
- No automated tests; manual validation with `--work 1 --short 1`.

---

## External API Notes

Relevant Spotipy docs checked while preparing this plan:

- Spotipy docs: https://spotipy.readthedocs.io/en/2.26.0/
- Spotify Web API reference: https://developer.spotify.com/documentation/web-api

Important constraints:

- **Spotify Premium is required** for playback control endpoints (`start_playback`, `pause_playback`, `next_track`). The free tier will get 403 errors — must be caught and communicated clearly.
- Spotipy controls the **Spotify app** on a device; it does not stream audio itself. The Spotify client (desktop, mobile, or web player) must be open and active.
- Authorization uses **`SpotifyPKCE`** (Authorization Code Flow with PKCE extension). This is the recommended flow for desktop/CLI apps — **no client secret required**, only a client ID. On first run, a browser window opens for the user to grant permission; a temporary local HTTP server catches the callback. The token is cached locally at `~/.cache/pomodoro-spotify` and refreshed automatically on subsequent runs.
- Required OAuth scopes for this feature: `user-modify-playback-state`, `user-read-playback-state`, `user-read-currently-playing`.
- The user must create an app at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), set the redirect URI to `http://localhost:8888/callback`, and export `SPOTIPY_CLIENT_ID`.

---

## New CLI Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--spotify` | false | Enable Spotify mode (replaces local music player) |
| `--spotify-playlist` | user's active playback | Spotify playlist/album URI (e.g. `spotify:playlist:37i9dQZF1DX0SM0LYsmbMT`) |
| `--spotify-device` | active device | Target device name (e.g. `"MacBook Pro"`) |

Credentials come from environment variables only — no CLI flags for secrets:
- `SPOTIPY_CLIENT_ID` (required)
- `SPOTIPY_REDIRECT_URI` (optional, default `http://localhost:8888/callback`)

---

## Architecture

### New module: `pomodoro/spotify_player.py`

To keep `__main__.py` clean, Spotify logic lives in a separate module. This avoids importing `spotipy` at the top level — it's only imported if `--spotify` is passed, so users without the package installed are unaffected.

```
pomodoro/
  __main__.py          ← adds --spotify flags, instantiates SpotifyPlayer
  spotify_player.py    ← new: SpotifyPlayer class + spotify_player_loop()
```

### `SpotifyPlayer` class

```python
class SpotifyPlayer:
    def __init__(self, playlist_uri=None, device_name=None)
    def authenticate(self) -> bool          # opens browser on first run, caches token
    def get_device_id(self) -> str | None   # resolves device by name or picks active
    def play(self)                          # start_playback with shuffle on target device
    def pause(self)                         # pause_playback
    def resume(self)                        # start_playback (no context_uri = resume)
    def skip(self)                          # next_track
    def now_playing(self) -> str | None     # returns "Artist – Track" string
    def is_playing(self) -> bool            # check if playback is active
```

### `spotify_player_loop(player, control_queue)`

A drop-in replacement for `music_player_loop()` that:

1. Calls `player.play()` at start.
2. Polls `control_queue` every 200 ms (same as local loop).
3. Reacts to `"skip"` → `player.skip()`, `"toggle_pause"` → `player.pause()`/`player.resume()`.
4. Polls `player.now_playing()` every ~5 s and prints track name when it changes.
5. `"ignore"` command: **not applicable** in Spotify mode — print a notice instead of crashing.
6. On any `spotipy.SpotifyException`: log the error and continue (don't crash the timer).

The loop runs as a daemon thread, exactly like the existing music thread, so `run_cycle()` needs no structural changes.

### Changes to `run_cycle()`

```python
def run_cycle(..., spotify_player=None):
    if spotify_player:
        music_thread = threading.Thread(
            target=spotify_player_loop,
            args=(spotify_player, control_queue),
            daemon=True,
        )
    else:
        music_thread = threading.Thread(
            target=music_player_loop,
            args=(playlist, control_queue, True),
            daemon=True,
        )
    music_thread.start()
    run_phase(...)
    # on break: stop local pygame OR pause Spotify
    if spotify_player:
        spotify_player.pause()
    else:
        pygame.mixer.music.stop()
```

### Changes to `main()`

1. Parse new flags.
2. If `--spotify`: import `spotify_player` module (inside `if` block — lazy import so missing `spotipy` only errors when actually used), instantiate `SpotifyPlayer`, call `authenticate()`.
3. If auth fails or device not found: print clear error and exit (don't silently fall back — the user explicitly asked for Spotify mode).
4. Pass `spotify_player` down to `run_cycle()`.
5. When `--spotify` is active, skip all `pygame.mixer` initialization and local playlist loading.

---

## Auth Setup Flow (First Run)

```
$ pomodoro --spotify
[Spotify] Opening browser for authorization…
[Spotify] Authenticated as Fernando Wittmann
[Spotify] Active device: MacBook Pro
🎹  Press 's' to skip, 'p' to pause/unpause, 'i' to ignore song (local only)
```

On subsequent runs the cached token is used silently.

---

## Error Handling Matrix

| Situation | Behavior |
|-----------|----------|
| `spotipy` not installed | Clear error: "Install with: uv pip install spotipy" |
| Credentials missing | Clear error listing which env vars are missing |
| No active Spotify device | Error: "Open Spotify on any device first" |
| Free tier (403 on playback) | Error: "Spotify Premium required for playback control" |
| Network blip mid-session | Log warning, continue timer — music may pause |
| `SpotifyException` on skip/pause | Log warning, do not crash |

---

## Dependencies

Add to `pyproject.toml` as an optional extra (alongside existing extras):

```toml
[project.optional-dependencies]
spotify = ["spotipy>=2.24.0"]
```

Install with:

```bash
uv pip install -e ".[spotify]"
```

This keeps `spotipy` out of the base install and doesn't break existing users. The `scripts` meta-extra should NOT include spotify — it's a runtime feature, not a script dependency.

---

## `.gitignore` additions

```
.cache          # Spotipy token cache (already may be listed)
.cache-*        # Spotipy alternate cache filenames
```

---

## Implementation Steps

1. **Add `spotipy` optional dep** to `pyproject.toml`.
2. **Update `.gitignore`** to exclude `.cache` / `.cache-*`.
3. **Create `pomodoro/spotify_player.py`** with `SpotifyPlayer` class and `spotify_player_loop()`.
4. **Update `__main__.py`**: add CLI flags, conditional import, instantiation, pass `spotify_player` to `run_cycle()`.
5. **Update `run_cycle()`**: accept optional `spotify_player`, branch music thread and break logic.
6. **Update README**: Spotify setup section (create app, set env vars, install extra, run).
7. **Manual test**:
   - `pomodoro --work 1 --short 1` — local mode unchanged.
   - `pomodoro --work 1 --short 1 --spotify` — Spotify plays during work, pauses on break.
   - Kill network mid-session — timer keeps running.
   - Press `s`, `p` — skip and pause work correctly.

---

## What Does NOT Change

- Local playlist mode (default behavior).
- Break sound playback (always local via pygame).
- Timer logic, `run_phase()`, key listener, pause tracking.
- `--ignore` / ignored songs file (local-only feature; Spotify mode prints a notice).
- All existing CLI flags.
