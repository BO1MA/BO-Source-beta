"""Tests for the role and permission system."""
import unittest
from src.constants.roles import (
    ROLE_MAIN_DEVELOPER, ROLE_ADMIN, ROLE_MEMBER, ROLE_CREATOR,
    get_role_name, is_higher_role, get_role_level_by_name,
)


class TestRoles(unittest.TestCase):
    def test_role_hierarchy(self):
        self.assertTrue(is_higher_role(ROLE_MAIN_DEVELOPER, ROLE_ADMIN))
        self.assertTrue(is_higher_role(ROLE_ADMIN, ROLE_MEMBER))
        self.assertFalse(is_higher_role(ROLE_MEMBER, ROLE_ADMIN))

    def test_same_role_not_higher(self):
        self.assertFalse(is_higher_role(ROLE_ADMIN, ROLE_ADMIN))

    def test_role_name_arabic(self):
        self.assertEqual(get_role_name(ROLE_MAIN_DEVELOPER), "المطور الاساسي")
        self.assertEqual(get_role_name(ROLE_ADMIN), "الادمن")

    def test_role_name_english(self):
        self.assertEqual(get_role_name(ROLE_MAIN_DEVELOPER, "en"), "Main Developer")

    def test_unknown_role(self):
        self.assertEqual(get_role_name(999), "عضو")

    def test_role_by_name(self):
        self.assertEqual(get_role_level_by_name("الادمن"), ROLE_ADMIN)
        self.assertEqual(get_role_level_by_name("المنشئ"), ROLE_CREATOR)
        self.assertEqual(get_role_level_by_name("unknown"), ROLE_MEMBER)


if __name__ == "__main__":
    unittest.main()
