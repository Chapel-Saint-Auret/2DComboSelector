"""Application profile definitions for advanced and user-facing launches."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppProfile:
    """Describe which parts of the UI are exposed for a launch profile."""

    key: str
    display_name: str
    show_pairwise_page: bool
    show_redundancy_page: bool
    show_export_page: bool
    allow_custom_results_settings: bool


APP_PROFILES = {
    "advanced": AppProfile(
        key="advanced",
        display_name="Advanced",
        show_pairwise_page=True,
        show_redundancy_page=True,
        show_export_page=True,
        allow_custom_results_settings=True,
    ),
    "user": AppProfile(
        key="user",
        display_name="User",
        show_pairwise_page=False,
        show_redundancy_page=False,
        show_export_page=True,
        allow_custom_results_settings=False,
    ),
}


def resolve_app_profile(profile_name: str | None) -> AppProfile:
    """Return a known application profile, defaulting to the advanced one."""

    if not profile_name:
        return APP_PROFILES["advanced"]
    return APP_PROFILES.get(profile_name.lower(), APP_PROFILES["advanced"])
