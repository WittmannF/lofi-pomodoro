#!/usr/bin/env python3
"""
generate_music.py — Generate focus music tracks using the ElevenLabs Music API.

Reads prompts from a YAML file, generates MP3s into an output directory,
and caches results by content hash to avoid redundant API calls.

Usage:
    python scripts/generate_music.py
    python scripts/generate_music.py --prompts custom_prompts.yaml
    python scripts/generate_music.py --no-cache
    python scripts/generate_music.py --dry-run
"""

import argparse
import hashlib
import os
import sys
import time


def _load_dotenv() -> None:
    """Load missing env vars from .env in the project root."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, ".env")
    if not os.path.exists(env_file):
        return
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()

try:
    import yaml
except ImportError:
    print("[!] Missing dependency: uv pip install -e \".[elevenlabs]\"")
    sys.exit(1)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROMPTS_FILE = os.path.join(_PROJECT_ROOT, "elevenlabs_prompts.yaml")


def _cache_key(prompt: str, music_length_ms: int, model_id: str) -> str:
    content = f"{prompt}|{music_length_ms}|{model_id}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def _output_path(output_dir: str, name: str, key: str) -> str:
    return os.path.join(output_dir, f"{name}_{key}.mp3")


def _generate(client, prompt: str, length_ms: int, model_id: str, dest: str) -> bool:
    try:
        result = client.music.compose(
            prompt=prompt,
            music_length_ms=length_ms,
            model_id=model_id,
        )
        audio_data = result if isinstance(result, bytes) else b"".join(result)
        with open(dest, "wb") as f:
            f.write(audio_data)
        return True
    except Exception as exc:
        print(f"\n    [!] Generation failed: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate lo-fi focus tracks with ElevenLabs Music API"
    )
    parser.add_argument(
        "--prompts",
        default=DEFAULT_PROMPTS_FILE,
        metavar="FILE",
        help="YAML prompts file (default: elevenlabs_prompts.yaml)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Regenerate even if a cached file already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without making API calls",
    )
    args = parser.parse_args()

    if not os.path.exists(args.prompts):
        print(f"[!] Prompts file not found: {args.prompts}")
        sys.exit(1)

    with open(args.prompts) as f:
        config = yaml.safe_load(f)

    prompts = config.get("prompts", [])
    if not prompts:
        print("[!] No prompts found in YAML file")
        sys.exit(1)

    default_length_ms = config.get("music_length_ms", 180_000)
    default_model = config.get("model_id", "music_v1")

    raw_output_dir = config.get("output_dir", "playlists/elevenlabs")
    output_dir = (
        raw_output_dir
        if os.path.isabs(raw_output_dir)
        else os.path.join(_PROJECT_ROOT, raw_output_dir)
    )

    print(f"[+] {len(prompts)} prompts loaded from: {args.prompts}")
    print(f"[+] Output: {output_dir}")
    print()

    if args.dry_run:
        print("DRY RUN — no API calls will be made\n")
        for p in prompts:
            name = p.get("name", "unnamed")
            length_ms = max(10_000, min(300_000, p.get("music_length_ms", default_length_ms)))
            model = p.get("model_id", default_model)
            key = _cache_key(p["prompt"], length_ms, model)
            path = _output_path(output_dir, name, key)
            cached = os.path.exists(path) and not args.no_cache
            status = "CACHED  " if cached else "GENERATE"
            snippet = p["prompt"][:80] + ("…" if len(p["prompt"]) > 80 else "")
            print(f"  [{status}] {name} ({length_ms // 1000}s) — {snippet}")
        return

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("[!] ELEVENLABS_API_KEY is not set. Add it to .env or export it.")
        sys.exit(1)

    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        print('[!] Missing dependency: uv pip install -e ".[elevenlabs]"')
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)
    os.makedirs(output_dir, exist_ok=True)

    generated = cached_count = failed = 0

    for i, p in enumerate(prompts, 1):
        name = p.get("name", f"track_{i:02d}")
        prompt_text = p["prompt"]
        length_ms = max(10_000, min(300_000, p.get("music_length_ms", default_length_ms)))
        model = p.get("model_id", default_model)

        key = _cache_key(prompt_text, length_ms, model)
        dest = _output_path(output_dir, name, key)

        print(f"[{i}/{len(prompts)}] {name}")
        print(f"    prompt : {prompt_text[:90]}{'…' if len(prompt_text) > 90 else ''}")
        print(f"    length : {length_ms // 1000}s  |  model: {model}")

        if os.path.exists(dest) and not args.no_cache:
            print(f"    ✓ cached  → {os.path.basename(dest)}\n")
            cached_count += 1
            continue

        print("    ⏳ generating…", end="", flush=True)
        t0 = time.monotonic()
        ok = _generate(client, prompt_text, length_ms, model, dest)
        elapsed = time.monotonic() - t0

        if ok:
            size_kb = os.path.getsize(dest) // 1024
            print(f"\r    ✓ saved    → {os.path.basename(dest)} ({size_kb} KB, {elapsed:.1f}s)\n")
            generated += 1
        else:
            failed += 1
            print()

    print("=" * 52)
    print(f"Generated: {generated}  |  Cached: {cached_count}  |  Failed: {failed}")
    if generated + cached_count > 0:
        print(f"\nPlay with pomodoro:")
        print(f"  pomodoro --music-folder {raw_output_dir}")


if __name__ == "__main__":
    main()
