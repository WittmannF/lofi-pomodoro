import unittest

from pomodoro.__main__ import build_parser


class SpotifyCliArgumentsTest(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_spotify_without_playlist_uses_current_playback(self):
        args = self.parser.parse_args(["--spotify"])

        self.assertEqual(args.spotify, "")
        self.assertIsNone(args.spotify_playlist)

    def test_spotify_accepts_preset_after_flag(self):
        args = self.parser.parse_args(["--spotify", "lofi"])

        self.assertEqual(args.spotify, "lofi")

    def test_spotify_accepts_uri_after_flag(self):
        uri = "spotify:playlist:37i9dQZF1DX0SM0LYsmbMT"
        args = self.parser.parse_args(["--spotify", uri])

        self.assertEqual(args.spotify, uri)

    def test_spotify_flag_still_works_before_other_options(self):
        args = self.parser.parse_args(
            ["--spotify", "--spotify-device", "MacBook Pro"]
        )

        self.assertEqual(args.spotify, "")
        self.assertEqual(args.spotify_device, "MacBook Pro")

    def test_legacy_spotify_playlist_flag_remains_available(self):
        args = self.parser.parse_args(
            ["--spotify", "--spotify-playlist", "deep-focus"]
        )

        self.assertEqual(args.spotify, "")
        self.assertEqual(args.spotify_playlist, "deep-focus")


if __name__ == "__main__":
    unittest.main()
