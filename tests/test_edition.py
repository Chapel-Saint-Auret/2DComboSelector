"""Tests for application edition selection."""

import unittest

from combo_selector import edition


class EditionTests(unittest.TestCase):
    def tearDown(self) -> None:
        edition.set_edition(edition.Edition.PUBLIC)

    def test_public_edition_is_the_safe_default(self) -> None:
        self.assertIs(edition.EDITION, edition.Edition.PUBLIC)
        self.assertTrue(edition.is_public_edition())
        self.assertFalse(edition.is_internal_edition())

    def test_internal_edition_can_be_selected(self) -> None:
        edition.set_edition("internal")

        self.assertIs(edition.EDITION, edition.Edition.INTERNAL)
        self.assertTrue(edition.is_internal_edition())
        self.assertFalse(edition.is_public_edition())

    def test_unknown_edition_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            edition.set_edition("unknown")

        self.assertIs(edition.EDITION, edition.Edition.PUBLIC)


if __name__ == "__main__":
    unittest.main()
