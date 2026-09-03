"""2D Combo Selector package for 2D chromatography combination analysis."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("2dcomboselector")
except PackageNotFoundError:  # Source checkout before installation.
    __version__ = "1.0.0"

__all__ = ["__version__"]
