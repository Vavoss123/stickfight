import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from updater import parse_version, is_newer


class Versions(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("0.10.0"), (0, 10, 0))
        self.assertEqual(parse_version("v2.0.0-beta"), (2, 0, 0))

    def test_newer(self):
        self.assertTrue(is_newer("v0.2.0", "0.1.0"))
        self.assertTrue(is_newer("v0.10.0", "0.9.0"))
        self.assertTrue(is_newer("v1.0", "0.9.9"))
        self.assertFalse(is_newer("v0.1.0", "0.1.0"))
        self.assertFalse(is_newer("v0.1.0", "0.2.0"))


if __name__ == "__main__":
    unittest.main()
