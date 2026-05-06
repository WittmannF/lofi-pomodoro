# Scripts Reference

Helper scripts for downloading and maintaining your music playlist.
All scripts save to `pomodoro/default-playlist/` by default and track
what's already been downloaded so re-runs are safe.

---

## scrape_songs.py

Downloads free lo-fi MP3s from [Chosic](https://www.chosic.com).

**Requires:** `uv pip install -e ".[scrape]"`

```
usage: scrape_songs.py [-h] [-s STYLE] [-o OUT] [--dry-run]

options:
  -s, --style STYLE   Music style/tag to scrape (default: lofi)
  -o, --out OUT       Root output directory (default: ./chosic)
  --dry-run           List tracks without downloading
```

**Examples:**

```bash
# Download lo-fi tracks into the default playlist
python scripts/scrape_songs.py -o pomodoro/default-playlist

# Preview what would be downloaded
python scripts/scrape_songs.py --dry-run

# Download a different style
python scripts/scrape_songs.py -s ambient -o pomodoro/default-playlist
```

**Notes:**
- State file: `.downloaded_ids.txt` inside the output folder
- Crawls all pages until none remain; uses a 2-second delay between requests

---

## scrape_fma.py

Downloads free lo-fi MP3s from [Free Music Archive](https://freemusicarchive.org) (35 000+ tracks, no login required).

**Requires:** `uv pip install -e ".[scrape]"`

```
usage: scrape_fma.py [-h] [-g GENRE] [-o OUT] [--dry-run] [--max-pages N]

options:
  -g, --genre GENRE     FMA genre slug to scrape (default: Lo-fi)
  -o, --out OUT         Output directory (default: pomodoro/default-playlist)
  --dry-run             List tracks without downloading
  --max-pages N         Maximum number of pages to crawl (default: all)
```

**Examples:**

```bash
# Download Lo-fi genre
python scripts/scrape_fma.py

# Download a different genre
python scripts/scrape_fma.py -g Lo-fi-Instrumental
python scripts/scrape_fma.py -g Ambient
python scripts/scrape_fma.py -g Chillwave

# Limit to the first 10 pages (≈200 tracks)
python scripts/scrape_fma.py --max-pages 10

# Preview without downloading
python scripts/scrape_fma.py --dry-run --max-pages 5
```

**Notes:**
- State file: `.fma_downloaded_ids.txt` inside the output folder
- Uses the `/stream/` endpoint — no login required
- 2-second delay between requests

---

## download_youtube.py

Downloads audio from YouTube as 192 kbps MP3s using [yt-dlp](https://github.com/yt-dlp/yt-dlp).
Supports individual videos, playlists, and channels.

**Requires:** `uv pip install -e ".[youtube]"` and `brew install ffmpeg`

```
usage: download_youtube.py [-h] [-f FILE] [-o OUT] [--dry-run]
                           [--max-size MB] [--timeout SECONDS]

options:
  -f, --file FILE       Text file with YouTube URLs, one per line
                        (default: youtube_links.txt)
  -o, --out OUT         Output directory (default: pomodoro/default-playlist)
  --dry-run             Resolve and list tracks without downloading
  --max-size MB         Skip videos whose estimated size exceeds this value
                        in MB (default: 100). Useful to avoid live streams.
  --timeout SECONDS     Per-download socket timeout in seconds (default: 120)
```

**Link file format (`youtube_links.txt`):**

```
# Lines starting with '#' are ignored, as are blank lines.
# Supports individual videos, playlists (?list=...), and channels.

https://www.youtube.com/watch?v=5qap5aO4i9A
https://www.youtube.com/playlist?list=PLofht4PTcKYnaH8w5olJCI-wUTuSO3ZAL
```

**Examples:**

```bash
# Download everything in youtube_links.txt
python scripts/download_youtube.py

# Use a different links file
python scripts/download_youtube.py -f my_playlist.txt

# Preview what would be downloaded
python scripts/download_youtube.py --dry-run

# Download to a custom folder
python scripts/download_youtube.py -o /path/to/music
```

**Notes:**
- State file: `.yt_downloaded_ids.txt` inside the output folder
- Filenames follow the pattern `Artist - Title [videoID].mp3`
- Live streams are detected and skipped automatically
- Use `--max-size` to guard against unexpectedly large files (live radio, mixes)

---

## generate_music.py

Generates lo-fi focus music tracks using the [ElevenLabs Music API](https://elevenlabs.io/docs/api-reference/music/compose)
and saves them as MP3s in `playlists/elevenlabs/`. Prompts are read from a YAML
file and results are cached by content hash to avoid redundant (paid) API calls.

Prompts are grounded in the cognitive science literature — all tracks are
instrumental, target 70–90 BPM for alpha-wave focus, use predictable structure to
minimise cognitive load, and incorporate nature textures where relevant.
See `docs/music-science-studying.md` for the research behind the prompt design.

**Requires:** `uv pip install -e ".[elevenlabs]"` and `ELEVENLABS_API_KEY` in `.env`
or exported in the shell.

```
usage: generate_music.py [-h] [--prompts FILE] [--no-cache] [--dry-run]

options:
  --prompts FILE   YAML prompts file (default: elevenlabs_prompts.yaml)
  --no-cache       Regenerate even if a cached file already exists
  --dry-run        Show what would be generated without making API calls
```

**Examples:**

```bash
# Generate all tracks defined in elevenlabs_prompts.yaml
python scripts/generate_music.py

# Preview what would be generated (no API calls)
python scripts/generate_music.py --dry-run

# Use a custom prompts file
python scripts/generate_music.py --prompts my_prompts.yaml

# Force regeneration even if cache exists
python scripts/generate_music.py --no-cache

# Then play the generated tracks with the Pomodoro timer
pomodoro --music-folder playlists/elevenlabs
```

**YAML prompt file format** (`elevenlabs_prompts.yaml`):

```yaml
output_dir: playlists/elevenlabs   # relative to project root
music_length_ms: 180000            # default length (10000–300000 ms)
model_id: music_v1                 # ElevenLabs model

prompts:
  - name: lofi-deep-focus          # used in the output filename
    prompt: "Calm lo-fi hip hop instrumental at 75 BPM…"
    music_length_ms: 120000        # optional per-track override
```

**Notes:**
- Output filenames: `{name}_{hash}.mp3` — re-running with the same prompt reuses
  the existing file unless `--no-cache` is passed
- Generation may consume ElevenLabs credits and may require a paid plan
- The `nature-restoration` prompt (no music, only nature sounds) is designed for
  break time; pipe it with `--break-sound` or play it manually during pauses

---

## fix_id3_tags.py

Strips empty COMM/USLT ID3 frames from MP3 files to silence the pygame/libmpg123 warning:
`[src/libmpg123/id3.c:process_comment():584] error: No comment text / valid description?`

Only empty frames are removed; real lyrics and meaningful comments are preserved.

**Requires:** `uv pip install -e ".[id3]"`

```
usage: fix_id3_tags.py [-h] [-d DIR] [--dry-run]

options:
  -d, --dir DIR   Directory to scan (default: pomodoro/default-playlist)
  --dry-run       Report files that need fixing without modifying them
```

**Examples:**

```bash
# Fix all tracks in the default playlist
python scripts/fix_id3_tags.py

# Preview which files would be changed
python scripts/fix_id3_tags.py --dry-run

# Fix a custom folder
python scripts/fix_id3_tags.py -d /path/to/music
```

**Notes:**
- Scans subdirectories recursively
- Only removes frames where both `text` and `description` are empty
