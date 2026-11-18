import unittest
from soundcloud_studio.core.soundcloud import SoundCloudService

class SoundCloudValidationTests(unittest.TestCase):
    def test_accepts_public_soundcloud_url(self):
        self.assertEqual(
            SoundCloudService.validate_url("https://soundcloud.com/example"),
            "https://soundcloud.com/example"
        )

    def test_rejects_non_soundcloud_url(self):
        with self.assertRaises(ValueError):
            SoundCloudService.validate_url("https://example.com/user")

if __name__ == "__main__":
    unittest.main()
