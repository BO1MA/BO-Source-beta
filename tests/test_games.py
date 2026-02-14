"""Tests for game logic."""
import unittest
from src.handlers.games import EMOJI_POOL, ARABIC_LETTERS


class TestGameData(unittest.TestCase):
    def test_emoji_pool_not_empty(self):
        self.assertGreater(len(EMOJI_POOL), 0)

    def test_arabic_letters_count(self):
        self.assertEqual(len(ARABIC_LETTERS), 28)

    def test_all_emojis_are_strings(self):
        for emoji in EMOJI_POOL:
            self.assertIsInstance(emoji, str)

    def test_arabic_letters_unique(self):
        self.assertEqual(len(ARABIC_LETTERS), len(set(ARABIC_LETTERS)))


if __name__ == "__main__":
    unittest.main()
