"""Tests for application edition selection."""

# Test inventory:
# - Verify that PUBLIC is the safe default and exposes only approved plots.
# - Verify that INTERNAL exposes the complete plot catalogue.
# - Verify that an unknown edition is rejected without changing the default.

import unittest

from combo_selector import edition
from combo_selector.plot_types import ALL_PLOT_TYPES, PUBLIC_PLOT_TYPES, get_plot_types


class EditionTests(unittest.TestCase):
    """Verify feature visibility for every supported application edition."""

    def tearDown(self) -> None:
        """Restore the public edition so tests remain independent."""
        # Prevent an internal-edition test from affecting the next test instance.
        edition.set_edition(edition.Edition.PUBLIC)

    def test_public_edition_is_the_safe_default(self) -> None:
        """The default build must expose exactly the five approved public plots."""
        # Arrange the exact user-facing plot catalogue approved for PUBLIC builds.
        expected_public_plots = [
            "Multi-Criteria Space",
            "Metric Removal Impact On Orthogonality Rank",
            "Chromatographic Mode Performance",
            "Recommendation Distribution",
            "Feasibility Profile",
        ]

        # Assert the default flag, helper predicates, and resulting plot list.
        self.assertIs(edition.EDITION, edition.Edition.PUBLIC)
        self.assertTrue(edition.is_public_edition())
        self.assertFalse(edition.is_internal_edition())
        self.assertListEqual(PUBLIC_PLOT_TYPES, expected_public_plots)
        self.assertListEqual(get_plot_types(), expected_public_plots)

    def test_internal_edition_can_be_selected(self) -> None:
        """Selecting the internal edition must expose every available plot."""
        # Act by selecting INTERNAL through the same string input used by builds.
        edition.set_edition("internal")

        # Assert that the edition flag and complete catalogue change together.
        self.assertIs(edition.EDITION, edition.Edition.INTERNAL)
        self.assertTrue(edition.is_internal_edition())
        self.assertFalse(edition.is_public_edition())
        self.assertListEqual(get_plot_types(), ALL_PLOT_TYPES)

    def test_unknown_edition_is_rejected(self) -> None:
        """An unsupported edition name must fail without changing the default."""
        # Act and assert that unsupported configuration cannot be applied.
        with self.assertRaises(ValueError):
            edition.set_edition("unknown")

        # Assert that rejection leaves the safe PUBLIC default unchanged.
        self.assertIs(edition.EDITION, edition.Edition.PUBLIC)


if __name__ == "__main__":
    unittest.main()
