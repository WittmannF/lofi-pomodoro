import io
import unittest
from contextlib import redirect_stdout

from pomodoro.spotify_player import SpotifyPlayer, is_transient_spotify_error


class FakeSpotifyClient:
    def __init__(self, playback_responses=None):
        self.playback_responses = list(playback_responses or [])
        self.pause_calls = 0
        self.resume_calls = 0
        self.skip_calls = 0

    def current_playback(self):
        response = self.playback_responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def pause_playback(self, device_id=None):
        self.pause_calls += 1
        raise TimeoutError("read timed out")

    def start_playback(self, device_id=None, **kwargs):
        self.resume_calls += 1
        raise TimeoutError("read timed out")

    def next_track(self, device_id=None):
        self.skip_calls += 1
        raise TimeoutError("read timed out")


class SpotifyPlayerTransientErrorTest(unittest.TestCase):
    def make_player(self, fake_spotify):
        player = SpotifyPlayer()
        player.sp = fake_spotify
        player._device_id = "device-1"
        return player

    def test_timeout_is_transient_spotify_error(self):
        self.assertTrue(is_transient_spotify_error(TimeoutError("read timed out")))

    def test_now_playing_recovers_after_transient_timeout(self):
        fake_spotify = FakeSpotifyClient(
            [
                TimeoutError("read timed out"),
                {
                    "item": {
                        "name": "Blue Skies",
                        "artists": [{"name": "Jost Esser"}, {"name": "Banks"}],
                    }
                },
            ]
        )
        player = self.make_player(fake_spotify)

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertIsNone(player.now_playing())
            self.assertEqual(player.now_playing(), "Jost Esser, Banks \u2013 Blue Skies")

        self.assertIn("[Spotify] Could not poll Spotify playback", output.getvalue())

    def test_is_playing_returns_false_after_transient_timeout(self):
        fake_spotify = FakeSpotifyClient([TimeoutError("read timed out")])
        player = self.make_player(fake_spotify)

        with redirect_stdout(io.StringIO()):
            self.assertFalse(player.is_playing())

    def test_control_methods_do_not_raise_on_transient_timeout(self):
        fake_spotify = FakeSpotifyClient()
        player = self.make_player(fake_spotify)

        with redirect_stdout(io.StringIO()):
            player.pause()
            player.resume()
            player.skip()

        self.assertEqual(fake_spotify.pause_calls, 1)
        self.assertEqual(fake_spotify.resume_calls, 1)
        self.assertEqual(fake_spotify.skip_calls, 1)


if __name__ == "__main__":
    unittest.main()
