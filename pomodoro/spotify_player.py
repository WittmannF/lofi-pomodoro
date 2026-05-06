"""
Spotify playback controller for pomodoro.

Uses Spotipy with PKCE auth flow (no client secret needed).
Requires Spotify Premium for playback control.
"""

import json
import os
import queue
import time

try:
    import spotipy
    from spotipy.oauth2 import SpotifyPKCE
    from spotipy.exceptions import SpotifyException
except ImportError:
    spotipy = None
    SpotifyPKCE = None
    SpotifyException = Exception


SCOPES = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
CACHE_PATH = os.path.join(os.path.expanduser("~"), ".cache", "pomodoro-spotify")
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pomodoro")
CONFIG_FILE = os.path.join(CONFIG_DIR, "spotify.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_client_id() -> str | None:
    env_val = os.environ.get("SPOTIPY_CLIENT_ID")
    if env_val:
        return env_val
    config = load_config()
    return config.get("client_id")


def get_redirect_uri() -> str:
    env_val = os.environ.get("SPOTIPY_REDIRECT_URI")
    if env_val:
        return env_val
    config = load_config()
    return config.get("redirect_uri", DEFAULT_REDIRECT_URI)


def setup_config() -> str | None:
    print("[Spotify] First-time setup.")
    print("[Spotify] You need a Client ID from https://developer.spotify.com/dashboard")
    print("[Spotify] Create an app, set redirect URI to: https://localhost:8888/callback")
    print()
    client_id = input("[Spotify] Paste your Client ID: ").strip()
    if not client_id:
        print("[Spotify] No Client ID provided.")
        return None

    config = load_config()
    config["client_id"] = client_id
    config["redirect_uri"] = DEFAULT_REDIRECT_URI
    save_config(config)
    print(f"[Spotify] Saved to {CONFIG_FILE}")
    return client_id


class SpotifyPlayer:
    def __init__(self, playlist_uri=None, device_name=None):
        if spotipy is None:
            raise RuntimeError(
                "spotipy is not installed. Install with: uv pip install -e \".[spotify]\""
            )
        self.playlist_uri = playlist_uri
        self.device_name = device_name
        self.sp = None
        self._device_id = None
        self._paused = False
        self._last_track = None

    def authenticate(self) -> bool:
        client_id = get_client_id()
        if not client_id:
            client_id = setup_config()
            if not client_id:
                return False

        redirect_uri = get_redirect_uri()

        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

        auth_manager = SpotifyPKCE(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=SCOPES,
            cache_path=CACHE_PATH,
        )

        try:
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            user = self.sp.current_user()
            print(f"[Spotify] Authenticated as {user['display_name']}")
        except Exception as e:
            print(f"[Spotify] Authentication failed: {e}")
            return False

        self._device_id = self._resolve_device()
        if self._device_id is None:
            return False

        return True

    def _resolve_device(self) -> str | None:
        try:
            devices = self.sp.devices()
        except SpotifyException as e:
            print(f"[Spotify] Error fetching devices: {e}")
            return None

        if not devices or not devices.get("devices"):
            print("[Spotify] No active devices found. Open Spotify on any device first.")
            return None

        device_list = devices["devices"]

        if self.device_name:
            for d in device_list:
                if d["name"].lower() == self.device_name.lower():
                    print(f"[Spotify] Using device: {d['name']}")
                    return d["id"]
            print(f"[Spotify] Device '{self.device_name}' not found. Available:")
            for d in device_list:
                print(f"  - {d['name']} ({d['type']})")
            return None

        active = next((d for d in device_list if d["is_active"]), None)
        if active:
            print(f"[Spotify] Active device: {active['name']}")
            return active["id"]

        fallback = device_list[0]
        print(f"[Spotify] No active device, using: {fallback['name']}")
        return fallback["id"]

    def play(self) -> None:
        try:
            kwargs = {"device_id": self._device_id}
            if self.playlist_uri:
                kwargs["context_uri"] = self.playlist_uri
            self.sp.shuffle(True, device_id=self._device_id)
            self.sp.start_playback(**kwargs)
            self._paused = False
        except SpotifyException as e:
            if e.http_status == 403:
                print("[Spotify] Error: Spotify Premium is required for playback control.")
                raise
            print(f"[Spotify] Playback error: {e}")

    def pause(self) -> None:
        try:
            self.sp.pause_playback(device_id=self._device_id)
            self._paused = True
        except SpotifyException as e:
            if "Player command failed: Restriction violated" in str(e):
                return
            print(f"[Spotify] Pause error: {e}")

    def resume(self) -> None:
        try:
            self.sp.start_playback(device_id=self._device_id)
            self._paused = False
        except SpotifyException as e:
            print(f"[Spotify] Resume error: {e}")

    def skip(self) -> None:
        try:
            self.sp.next_track(device_id=self._device_id)
        except SpotifyException as e:
            print(f"[Spotify] Skip error: {e}")

    def now_playing(self) -> str | None:
        try:
            current = self.sp.current_playback()
            if not current or not current.get("item"):
                return None
            item = current["item"]
            artists = ", ".join(a["name"] for a in item.get("artists", []))
            track = item.get("name", "Unknown")
            return f"{artists} – {track}" if artists else track
        except SpotifyException:
            return None

    def is_playing(self) -> bool:
        try:
            current = self.sp.current_playback()
            return bool(current and current.get("is_playing"))
        except SpotifyException:
            return False


def spotify_player_loop(
    player: SpotifyPlayer, control_queue: queue.Queue, stop_event: "threading.Event"
) -> None:
    """
    Drop-in replacement for music_player_loop that controls Spotify.
    Runs as a daemon thread. Exits when stop_event is set.
    """
    import threading

    try:
        player.play()
    except Exception:
        return

    time.sleep(1)
    last_track_display = player.now_playing()
    if last_track_display:
        print(f"\n🎵  Now playing: {last_track_display}")
    last_check = time.monotonic()

    while not stop_event.is_set():
        try:
            cmd = control_queue.get(timeout=0.2)
            if cmd is True or cmd == "skip":
                player.skip()
                last_track_display = None
                time.sleep(0.5)
            elif cmd == "toggle_pause":
                if player._paused:
                    player.resume()
                else:
                    player.pause()
            elif cmd == "ignore":
                print("  (ignore not available in Spotify mode)")
        except queue.Empty:
            pass

        now = time.monotonic()
        if now - last_check > 5:
            last_check = now
            track = player.now_playing()
            if track and track != last_track_display:
                last_track_display = track
                print(f"\n🎵  Now playing: {track}")
