from time import sleep, time
from typing import Dict, Tuple, List
import unittest


TIMEOUT_SEC = 1.0


class NoAvailableColors(Exception):
    pass


# this palette is developed based on seaborn's 'color_palette()'' function
_palette = [
    (0.9, 0.0, 0.04),
    (0.54, 0.16, 0.8),
    (1.0, 0.48, 0.0),
    (0.94, 0.29, 0.75),
    (0.1, 0.78, 0.21),
]


class ColorAssigner:
    def __init__(self, palette: List[Tuple[float, float, float]]):
        self._palette = palette
        # stores compound to color assignment (compound -> color)
        self._compound_to_color = {}
        # tracks when each compound was last used (compound -> time_last_used)
        self._compound_last_used = {}
        # tracks color availability (color -> available)
        self._color_avaliable = {color: True for color in _palette}

    def color_for_compound(self, compound: str) -> Tuple[float, float, float]:
        """
        Returns a color to display the given 'compound' in an image. Will always return the same value for a
        compound. When a compound is seen the first time, the next available color form a pre-defined pallet
        is assigned.
        Each individual assignment is deleted after it was not used for TIMEOUT_SEC
        
        Raises:
            NoAvailableColors: If all palette colors are already assigned.
        """
        current_time = time()
        compound_to_color_assignment = self.get_compound_to_color_assignments()
        if compound in compound_to_color_assignment:
            self._compound_last_used[compound] = current_time
            return compound_to_color_assignment[compound]
        else:
            try:
                color_index = list(self._color_avaliable.values()).index(True)
                color = _palette[color_index]
                self._color_avaliable[color] = False
                self._compound_last_used[compound] = current_time
                self._compound_to_color[compound] = color
                return color
            except ValueError:
                raise NoAvailableColors("All pallete colors are currently assigned")

    def get_compound_to_color_assignments(self) -> Dict:
        """
        Returns a dict containing all known compound -> color assignments. May be used to render a legend.
        Example return value: {"Aceton" : (0.9, 0.0, 0.04), "Benzol" : (0.54, 0.16, 0.8)}
        """
        current_time = time()
        expired_compound_assignemnt = []
        for compound, last_used in self._compound_last_used.items():
            if current_time - last_used > TIMEOUT_SEC:
                color = self._compound_to_color[compound]
                self._color_avaliable[color] = True
                expired_compound_assignemnt.append(compound)

        for compound in expired_compound_assignemnt:
            del self._compound_last_used[compound]
            del self._compound_to_color[compound]
        return self._compound_to_color


class TestColorForCompound(unittest.TestCase):
    def setUp(self):
        self.color_assigner = ColorAssigner(_palette)

    def test_color_assignment(self):
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))
        self.assertEqual(self.color_assigner.color_for_compound("Benzol"), (0.54, 0.16, 0.8))
        self.assertEqual(self.color_assigner.color_for_compound("Aceton"), (1.0, 0.48, 0.0))

    def test_returns_same_color_for_same_compound(self):
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))

    def test_assignment_does_not_expire_when_used_before_timeout(self):
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))
        sleep(0.7)
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))

    def test_assigns_avialabe_color_after_expiration(self):
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))
        self.assertEqual(self.color_assigner.color_for_compound("Benzol"), (0.54, 0.16, 0.8))
        sleep(1)
        self.assertEqual(self.color_assigner.color_for_compound("Aceton"), (0.9, 0.0, 0.04))

    def test_no_avaiable_colors_for_new_compound(self):
        with self.assertRaises(NoAvailableColors) as cm:
            self.color_assigner.color_for_compound("Ammoniak")
            self.color_assigner.color_for_compound("Benzol")
            self.color_assigner.color_for_compound("Aceton")
            self.color_assigner.color_for_compound("Kohlenmonoxid")
            self.color_assigner.color_for_compound("Chloroform")
            self.color_assigner.color_for_compound("Methanol")
            self.assertEqual("All pallete colors are currently assigned", cm.exception)

    def test_color_assignment_complete_flow(self):
        self.assertEqual(self.color_assigner.color_for_compound("Ammoniak"), (0.9, 0.0, 0.04))
        self.assertEqual(self.color_assigner.color_for_compound("Benzol"), (0.54, 0.16, 0.8))
        self.assertEqual(self.color_assigner.color_for_compound("Aceton"), (1.0, 0.48, 0.0))
        sleep(0.7)
        self.assertEqual(self.color_assigner.color_for_compound("Benzol"), (0.54, 0.16, 0.8))
        sleep(0.7)
        self.assertEqual(self.color_assigner.color_for_compound("Benzol"), (0.54, 0.16, 0.8))
        self.assertEqual(self.color_assigner.color_for_compound("Aceton"), (0.9, 0.0, 0.04))
