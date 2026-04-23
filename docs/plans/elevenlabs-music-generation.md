# ElevenLabs Music Generation Support Plan

## Goal

Add optional ElevenLabs music generation support to the CLI Pomodoro app so users can generate focus-friendly music tracks from prompts and play them during work sessions alongside the existing bundled or folder-based playlist behavior.

The first implementation should be conservative: generate audio files into a local cache/output folder, then feed those files into the existing `pygame` playlist flow. This keeps live timer playback reliable and avoids coupling the Pomodoro loop directly to network latency or API failures.

## Current Project Context

- The app is currently implemented in `pomodoro/__main__.py`.
- Music playback is local-file based through `pygame.mixer.music`.
- Work music is loaded by `load_music_files()` from either `--music-folder` or the bundled default playlist.
- The music player runs in a daemon thread via `music_player_loop()` and accepts skip, pause, and ignore commands through queues.
- Ignored songs are stored as local paths in `.ignored_songs`.
- There are no automated tests or linting configs today; `CLAUDE.md` recommends manual validation with short timers such as `pomodoro --work 1 --short 1`.

## External API Notes

Relevant ElevenLabs docs checked while preparing this plan:

- Compose music endpoint: https://elevenlabs.io/docs/api-reference/music/compose
- Stream music endpoint: https://elevenlabs.io/docs/api-reference/music/stream
- Python SDK repository: https://github.com/elevenlabs/elevenlabs-python
- Eleven Music help article: https://help.elevenlabs.io/hc/en-us/articles/37780368848785-What-is-Eleven-Music

Important constraints to account for:

- The SDK package is `elevenlabs`.
- The generated music model is currently `music_v1`.
- Prompt-based generation accepts `prompt`, `music_length_ms`, `model_id`, and `force_instrumental`.
- `music_length_ms` must be between 10,000 and 300,000 milliseconds.
- The default generated output format is MP3 at `mp3_44100_128`.
- API access requires an ElevenLabs API key, expected as `ELEVENLABS_API_KEY`.
- Music API access may require a paid ElevenLabs plan.

## Proposed UX

Add CLI options that are explicit and opt-in:

| Option | Purpose |
| --- | --- |
| `--elevenlabs-generate` | Enable ElevenLabs generation before the Pomodoro session starts. |
| `--elevenlabs-prompt TEXT` | Prompt used for generation. Default can be a focus-oriented lo-fi prompt. |
| `--elevenlabs-track-count N` | Number of tracks to generate before starting. Default: `1`. |
| `--elevenlabs-length SEC` | Track duration in seconds. Clamp or validate to 10-300. Default: `300` or work duration capped to 300. |
| `--elevenlabs-output-dir PATH` | Where generated tracks are saved. Default: `playlists/elevenlabs` or `.pomodoro/elevenlabs`. |
| `--elevenlabs-force-instrumental` | Pass `force_instrumental=True`; default should be true for focus use. |
| `--elevenlabs-use-cache` | Reuse existing generated tracks for the same prompt/settings before generating new ones. Default: true. |

The first version should avoid streaming playback. Generation should happen before the timer starts, with clear terminal progress and errors. If generation fails, the app should fall back to the default playlist or `--music-folder` unless the user requested ElevenLabs-only behavior in a later option.

Example target usage:

```bash
ELEVENLABS_API_KEY=... pomodoro \
  --elevenlabs-generate \
  --elevenlabs-prompt "Generate a calm instrumental lofi song for studying and concentration" \
  --elevenlabs-track-count 2 \
  --elevenlabs-length 180
```

## Implementation Strategy

### 1. Add dependency

Add `elevenlabs` to project dependencies in `pyproject.toml` and `requirements.txt`.

Keep import failures user-friendly:

- Do not import the SDK at module import time if ElevenLabs generation is disabled.
- Import it inside the generation function.
- If the dependency is missing, print an actionable message and continue with local music fallback.

### 2. Add generation helpers

Create helper functions in `pomodoro/__main__.py` first, since the app is currently single-file:

- `validate_elevenlabs_length(seconds: int) -> int`
- `get_elevenlabs_output_dir(path: str | None) -> str`
- `build_elevenlabs_filename(prompt, length, model, index) -> str`
- `generate_elevenlabs_tracks(...) -> list[str]`

The generation helper should:

1. Read `ELEVENLABS_API_KEY` from the environment.
2. Validate that the key exists before attempting generation.
3. Create the output directory if needed.
4. Call:

   ```python
   from elevenlabs.client import ElevenLabs

   client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
   audio = client.music.compose(
       prompt=prompt,
       music_length_ms=length_seconds * 1000,
       model_id="music_v1",
       force_instrumental=force_instrumental,
   )
   ```

5. Write the returned audio bytes or byte iterator to an `.mp3` file.
6. Return generated file paths that can be appended to the existing playlist.

The exact write logic needs to handle SDK return type defensively:

- If the response is `bytes`, write it directly.
- If it is an iterable of `bytes`, stream chunks into the file.
- If the SDK exposes a response object with `.data`, write `.data`.

### 3. Cache generated tracks

Avoid accidental repeated paid generations:

- Derive a stable hash from prompt, length, model, instrumental flag, and output format.
- Store files as:

  ```text
  playlists/elevenlabs/<hash>-001.mp3
  playlists/elevenlabs/<hash>-002.mp3
  ```

- When `--elevenlabs-use-cache` is enabled, reuse matching files before generating more.
- Print whether a track is reused or newly generated.

This should be the default because generation has credit cost and network latency.

### 4. Wire generated tracks into playback

Recommended first behavior:

- Load existing playlist exactly as today.
- If `--elevenlabs-generate` is set, generate or reuse tracks.
- Prepend generated tracks to the playlist so users hear generated music first.
- If no local tracks exist but generated tracks exist, run solely on generated tracks.
- If generation fails and local tracks exist, continue with local tracks.
- If both generation and local loading fail, keep the current "running without work music" behavior.

This limits changes to the current playback thread and keeps skip/pause/ignore working because generated tracks are normal local files.

### 5. Handle ignore behavior

Generated files should work with the existing ignore system because `.ignored_songs` stores file paths.

Decision to make during implementation:

- Keep ignored generated files on disk, just filtered out by `.ignored_songs`.
- Do not delete them automatically, because a generated file may cost credits and the user may want it later.

### 6. Error handling

Expected failures:

- Missing `ELEVENLABS_API_KEY`.
- Missing `elevenlabs` dependency.
- Invalid generation length.
- API authentication or plan error.
- API validation error for prompt or duration.
- Network failure.
- File write failure.

Behavior:

- Print concise warnings.
- Never crash a Pomodoro session if fallback local music is available.
- Use `parser.error(...)` only for invalid CLI input such as out-of-range length.
- Do not print API keys or full sensitive headers.

### 7. Documentation updates

Update `README.md` after implementation with:

- Setup instructions for `ELEVENLABS_API_KEY`.
- Install note for the `elevenlabs` dependency.
- CLI examples.
- A clear note that API generation can consume ElevenLabs credits and may require a paid plan.
- A recommendation to use instrumental prompts for focus sessions.

Update `CLAUDE.md` with new CLI flags and manual testing commands.

### 8. Manual validation

Because the repo has no automated tests today, validate manually:

```bash
pomodoro --work 1 --short 1 --cycles 1 --no-work-music
pomodoro --work 1 --short 1 --cycles 1 --music-folder playlists/elevenlabs
ELEVENLABS_API_KEY=... pomodoro --elevenlabs-generate --elevenlabs-length 10 --work 1 --short 1 --cycles 1
```

Also validate failure modes:

```bash
unset ELEVENLABS_API_KEY
pomodoro --elevenlabs-generate --elevenlabs-length 10 --work 1 --short 1 --cycles 1
pomodoro --elevenlabs-generate --elevenlabs-length 9
pomodoro --elevenlabs-generate --elevenlabs-length 301
```

## Open Questions

- Should generated tracks be prepended to the existing playlist, replace it, or be selected by a separate `--music-source elevenlabs` option?
- Should the default output directory be committed-friendly `playlists/elevenlabs` or user-local `.pomodoro/elevenlabs`?
- Should generation happen synchronously before the session starts, or should a later version generate the next track in the background while the current track plays?
- Should we expose ElevenLabs `output_format` immediately, or keep the first version MP3-only to match `pygame` and simplify validation?
- Should prompts be saved in a small metadata JSON next to each generated track for traceability?

## Recommended First Cut

Implement the file-cache approach with synchronous pre-session generation, generated tracks prepended to the playlist, MP3-only output, `force_instrumental=True` by default, and local fallback on API failure. This gives users the feature with minimal disruption to the existing timer and playback code.
