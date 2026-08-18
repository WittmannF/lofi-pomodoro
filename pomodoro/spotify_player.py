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

try:
    from requests.exceptions import RequestException
except ImportError:
    RequestException = None

try:
    from urllib3.exceptions import HTTPError as Urllib3HTTPError
except ImportError:
    Urllib3HTTPError = None


SCOPES = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
CACHE_PATH = os.path.join(os.path.expanduser("~"), ".cache", "pomodoro-spotify")
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "pomodoro")
CONFIG_FILE = os.path.join(CONFIG_DIR, "spotify.json")
TRANSIENT_SPOTIFY_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}
API_WARNING_COOLDOWN_SEC = 30


NETWORK_EXCEPTIONS = tuple(
    exc
    for exc in (RequestException, Urllib3HTTPError, TimeoutError)
    if exc is not None
)


def is_transient_spotify_error(error: Exception) -> bool:
    if is_spotify_api_exception(error):
        return getattr(error, "http_status", None) in TRANSIENT_SPOTIFY_HTTP_STATUSES
    return isinstance(error, NETWORK_EXCEPTIONS)


def is_spotify_api_exception(error: Exception) -> bool:
    return SpotifyException is not Exception and isinstance(error, SpotifyException)


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def print_auth_error_help(error: Exception) -> None:
    print(f"[Spotify] Authentication failed: {error}")

    error_text = str(error).lower()
    if "invalid_grant" in error_text or "refresh token revoked" in error_text:
        print("[Spotify] Your saved Spotify login token is no longer valid.")
        print("[Spotify] Remove the cached token and run pomodoro again to log in:")
        print(f"  rm {CACHE_PATH}")


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


DEFAULT_PLAYLISTS = {
    "lofi": "spotify:playlist:37i9dQZF1DX0SM0LYsmbMT",
    "lofi-beats": "spotify:playlist:37i9dQZF1DX0SM0LYsmbMT",
    "jazz": "spotify:playlist:37i9dQZF1DX0SM0LYsmbMT",
    "deep-focus": "spotify:playlist:37i9dQZF1DWZeKCadgRdKQ",
    "chill": "spotify:playlist:37i9dQZF1DX4WYpdgoIcn6",
}


def resolve_playlist(name_or_uri: str | None) -> str | None:
    if name_or_uri is None:
        return None
    if name_or_uri.startswith("spotify:"):
        return name_or_uri
    config = load_config()
    user_playlists = config.get("playlists", {})
    if name_or_uri in user_playlists:
        return user_playlists[name_or_uri]
    if name_or_uri in DEFAULT_PLAYLISTS:
        return DEFAULT_PLAYLISTS[name_or_uri]
    print(f"[Spotify] Unknown playlist preset '{name_or_uri}'. Available:")
    all_presets = {**DEFAULT_PLAYLISTS, **user_playlists}
    for k in sorted(all_presets):
        print(f"  - {k}")
    print(f"  (or pass a full URI like spotify:playlist:...)")
    return None


def setup_config() -> str | None:
    print("[Spotify] First-time setup.")
    print("[Spotify] You need a Client ID from https://developer.spotify.com/dashboard")
    print(f"[Spotify] Create an app, set redirect URI to: {DEFAULT_REDIRECT_URI}")
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


def list_devices() -> None:
    client_id = get_client_id()
    if not client_id:
        client_id = setup_config()
        if not client_id:
            return

    redirect_uri = get_redirect_uri()
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

    auth_manager = SpotifyPKCE(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        cache_path=CACHE_PATH,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    try:
        devices = sp.devices()
    except Exception as e:
        print(f"[Spotify] Error fetching devices: {e}")
        return

    if not devices or not devices.get("devices"):
        print("[Spotify] No devices found. Open Spotify on any device first.")
        return

    print("[Spotify] Available devices:")
    for i, d in enumerate(devices["devices"], 1):
        status = "active" if d["is_active"] else "inactive"
        print(f"  {i}. {d['name']} ({d['type']}) [{status}]")
        print(f"     ID: {d['id']}")


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
        self._api_warning_times: dict[str, float] = {}

    def _warn_api_error(self, action: str, error: Exception) -> None:
        now = time.monotonic()
        last_warning = self._api_warning_times.get(action, 0)
        if now - last_warning < API_WARNING_COOLDOWN_SEC:
            return

        self._api_warning_times[action] = now
        print(f"[Spotify] Could not {action}: {error}")

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
            print_auth_error_help(e)
            return False

        self._device_id = self._resolve_device()
        if self._device_id is None:
            return False

        return True

    def _resolve_device(self) -> str | None:
        try:
            devices = self.sp.devices()
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("fetch Spotify devices", e)
                return None
            if is_spotify_api_exception(e):
                print(f"[Spotify] Error fetching devices: {e}")
                return None
            raise

        if not devices or not devices.get("devices"):
            print("[Spotify] No active devices found. Open Spotify on any device first.")
            return None

        device_list = devices["devices"]

        if self.device_name:
            # By number
            if self.device_name.isdigit():
                idx = int(self.device_name) - 1
                if 0 <= idx < len(device_list):
                    chosen = device_list[idx]
                    print(f"[Spotify] Using device: {chosen['name']}")
                    return chosen["id"]
                print(f"[Spotify] Device #{self.device_name} out of range. Available:")
                for i, d in enumerate(device_list, 1):
                    print(f"  {i}. {d['name']} ({d['type']})")
                return None
            # By ID
            for d in device_list:
                if d["id"] == self.device_name:
                    print(f"[Spotify] Using device: {d['name']}")
                    return d["id"]
            # By name (case-insensitive)
            for d in device_list:
                if d["name"].lower() == self.device_name.lower():
                    print(f"[Spotify] Using device: {d['name']}")
                    return d["id"]
            print(f"[Spotify] Device '{self.device_name}' not found. Available:")
            for i, d in enumerate(device_list, 1):
                print(f"  {i}. {d['name']} ({d['type']})")
            return None

        active = next((d for d in device_list if d["is_active"]), None)
        if active:
            print(f"[Spotify] Active device: {active['name']}")
            return active["id"]

        print("[Spotify] No active device found. Open Spotify on your computer or phone and play any track for a second, then try again.")
        print("[Spotify] Available devices (inactive):")
        for d in device_list:
            print(f"  - {d['name']} ({d['type']})")
        return None

    def play(self) -> None:
        try:
            kwargs = {"device_id": self._device_id}
            if self.playlist_uri:
                kwargs["context_uri"] = self.playlist_uri
            self.sp.shuffle(True, device_id=self._device_id)
            self.sp.start_playback(**kwargs)
            self._paused = False
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("start Spotify playback", e)
                return
            if not is_spotify_api_exception(e):
                raise
            if e.http_status == 403:
                print("[Spotify] Error: Spotify Premium is required for playback control.")
                raise
            if e.http_status == 404:
                print("[Spotify] Error: Device not reachable. Open Spotify and play a track for a second, then retry.")
                raise
            print(f"[Spotify] Playback error: {e}")

    def pause(self) -> None:
        try:
            self.sp.pause_playback(device_id=self._device_id)
            self._paused = True
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("pause Spotify playback", e)
                return
            if (
                is_spotify_api_exception(e)
                and "Player command failed: Restriction violated" in str(e)
            ):
                return
            if not is_spotify_api_exception(e):
                raise
            print(f"[Spotify] Pause error: {e}")

    def resume(self) -> None:
        try:
            self.sp.start_playback(device_id=self._device_id)
            self._paused = False
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("resume Spotify playback", e)
                return
            if not is_spotify_api_exception(e):
                raise
            print(f"[Spotify] Resume error: {e}")

    def skip(self) -> None:
        try:
            self.sp.next_track(device_id=self._device_id)
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("skip Spotify track", e)
                return
            if not is_spotify_api_exception(e):
                raise
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
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("poll Spotify playback", e)
                return None
            if is_spotify_api_exception(e):
                return None
            raise

    def is_playing(self) -> bool:
        try:
            current = self.sp.current_playback()
            return bool(current and current.get("is_playing"))
        except Exception as e:
            if is_transient_spotify_error(e):
                self._warn_api_error("poll Spotify playback", e)
                return False
            if is_spotify_api_exception(e):
                return False
            raise


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
