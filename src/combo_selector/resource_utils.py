"""Lightweight resource-path resolution shared by startup and UI modules."""

import os
import sys


def resource_path(relative_path: str) -> str:
    """Return a resource path for source, installed, and PyInstaller builds."""
    if getattr(sys, "frozen", False):
        base = os.path.join(os.path.dirname(sys.executable), "_internal", "resources")
        absolute_path = os.path.join(base, relative_path)
        if os.path.exists(absolute_path):
            return absolute_path
        raise FileNotFoundError(
            f"Resource not found: {relative_path} (expected at {absolute_path})"
        )

    try:
        from importlib.resources import files

        resource_file = files("combo_selector.resources") / relative_path
        if resource_file.is_file():
            return str(resource_file)
    except Exception:
        pass

    development_path = os.path.join(
        os.path.dirname(__file__), "resources", relative_path
    )
    if os.path.exists(development_path):
        return development_path
    raise FileNotFoundError(
        f"Resource not found: {relative_path} (checked {development_path})"
    )
