"""Tests for handler utilities and message processing."""
import unittest
from src.constants.commands import find_command_key
from src.constants.messages import get_greeting_response, get_activity_level
from src.utils.text_utils import (
    reverse_text, contains_link, contains_hashtag,
    is_arabic_only, is_english_only, extract_command_arg,
)


class TestCommandRouting(unittest.TestCase):
    def test_start_command(self):
        self.assertEqual(find_command_key("/start"), "start")

    def test_arabic_ban(self):
        self.assertEqual(find_command_key("حظر"), "ban")
        self.assertEqual(find_command_key("حظر 12345"), "ban")

    def test_arabic_mute(self):
        self.assertEqual(find_command_key("كتم"), "mute")

    def test_unknown_command(self):
        self.assertIsNone(find_command_key("random text"))

    def test_games(self):
        self.assertEqual(find_command_key("الالعاب"), "games_menu")
        self.assertEqual(find_command_key("السمايلات"), "emoji_game")


class TestTextUtils(unittest.TestCase):
    def test_reverse_text(self):
        self.assertEqual(reverse_text("hello"), "olleh")
        self.assertEqual(reverse_text("مرحبا"), "ابحرم")

    def test_contains_link(self):
        self.assertTrue(contains_link("visit https://example.com"))
        self.assertTrue(contains_link("join t.me/channel"))
        self.assertFalse(contains_link("just text"))

    def test_contains_hashtag(self):
        self.assertTrue(contains_hashtag("#hello world"))
        self.assertFalse(contains_hashtag("no hashtag"))

    def test_arabic_only(self):
        self.assertTrue(is_arabic_only("مرحبا"))
        self.assertFalse(is_arabic_only("hello"))
        self.assertTrue(is_arabic_only("مرحبا 123"))  # numbers allowed

    def test_english_only(self):
        self.assertTrue(is_english_only("hello"))
        self.assertFalse(is_english_only("مرحبا"))

    def test_extract_command_arg(self):
        self.assertEqual(extract_command_arg("حظر 12345"), "12345")
        self.assertEqual(extract_command_arg("حظر"), "")


class TestMessages(unittest.TestCase):
    def test_greeting_response(self):
        response = get_greeting_response("السلام عليكم")
        self.assertIsNotNone(response)

    def test_no_greeting(self):
        self.assertIsNone(get_greeting_response("random"))

    def test_activity_level(self):
        self.assertEqual(get_activity_level(0), "غير نشط 😶")
        self.assertIn("🔥", get_activity_level(1500))


if __name__ == "__main__":
    unittest.main()
