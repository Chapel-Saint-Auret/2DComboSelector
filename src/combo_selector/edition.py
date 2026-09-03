"""Application edition selection.

The edition controls presentation-only differences between the public and
internal builds. Scientific calculations must not depend on this setting.
"""

from enum import Enum
from typing import Union


class Edition(str, Enum):
    """Supported application editions."""

    PUBLIC = "public"
    INTERNAL = "internal"


EDITION = Edition.PUBLIC


def set_edition(edition: Union[Edition, str]) -> None:
    """Select the application edition.

    Args:
        edition: An :class:`Edition` value or its string representation.

    Raises:
        ValueError: If *edition* is not a supported edition.
    """
    global EDITION
    EDITION = Edition(edition)


def is_public_edition() -> bool:
    """Return whether the public presentation is selected."""
    return EDITION is Edition.PUBLIC


def is_internal_edition() -> bool:
    """Return whether the internal presentation is selected."""
    return EDITION is Edition.INTERNAL


__all__ = [
    "EDITION",
    "Edition",
    "is_internal_edition",
    "is_public_edition",
    "set_edition",
]
