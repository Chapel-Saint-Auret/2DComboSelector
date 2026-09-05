"""Tests for application edition selection."""

import unittest

from combo_selector import edition
from combo_selector.plot_types import ALL_PLOT_TYPES, PUBLIC_PLOT_TYPES, get_plot_types


class EditionTests(unittest.TestCase):
    def tearDown(self) -> None:
        """Restore the public edition so tests remain independent."""
        edition.set_edition(edition.Edition.PUBLIC)

    def test_public_edition_is_the_safe_default(self) -> None:
        """The default build must expose exactly the five approved public plots."""
        expected_public_plots = [
            "Multi-Criteria Space",
            "Metric Removal Impact On Orthogonality Rank",
            "Chromatographic Mode Performance",
            "Recommendation Distribution",
            "Feasibility Profile",
        ]

        self.assertIs(edition.EDITION, edition.Edition.PUBLIC)
        self.assertTrue(edition.is_public_edition())
        self.assertFalse(edition.is_internal_edition())
        self.assertListEqual(PUBLIC_PLOT_TYPES, expected_public_plots)
        self.assertListEqual(get_plot_types(), expected_public_plots)

    def test_internal_edition_can_be_selected(self) -> None:
        """Selecting the internal edition must expose every available plot."""
        edition.set_edition("internal")

        self.assertIs(edition.EDITION, edition.Edition.INTERNAL)
        self.assertTrue(edition.is_internal_edition())
        self.assertFalse(edition.is_public_edition())
        self.assertListEqual(get_plot_types(), ALL_PLOT_TYPES)

    def test_unknown_edition_is_rejected(self) -> None:
        """An unsupported edition name must fail without changing the default."""
        with self.assertRaises(ValueError):
            edition.set_edition("unknown")

        self.assertIs(edition.EDITION, edition.Edition.PUBLIC)


if __name__ == "__main__":
    unittest.main()
