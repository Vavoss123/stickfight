import unittest

from engine.fighter import Profile
from engine.looks import HAIRS, default_look, look_of


class Looks(unittest.TestCase):
    def test_same_name_same_look(self):
        self.assertEqual(default_look("Dan Reyes"), default_look("Dan Reyes"))

    def test_saved_look_wins_and_survives_a_save(self):
        p = Profile(name="Sam Okoro", look={"hair": "afro", "beard": True, "skin": 3})
        back = Profile.from_dict(p.to_dict())
        look = look_of(back)
        self.assertEqual((look["hair"], look["beard"], look["skin"]), ("afro", True, 3))

    def test_bad_values_are_fixed(self):
        look = look_of(Profile(name="X", look={"hair": "wig", "skin": 99, "nonsense": 1}))
        self.assertIn(look["hair"], HAIRS)
        self.assertNotIn("nonsense", look)

    def test_old_saves_without_a_look_load(self):
        d = Profile(name="Old").to_dict()
        del d["look"]
        self.assertEqual(Profile.from_dict(d).look, {})


if __name__ == "__main__":
    unittest.main()
