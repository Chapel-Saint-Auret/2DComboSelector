# Re-export colour configs from the central constants module so that existing
# imports (``from combo_selector.ui.config.table_color_config import ...``)
# continue to work without modification.
from combo_selector.constants import (  # noqa: F401
    COLOR_CONFIG_TABLE_FEASIBILITY,
    COLOR_CONFIG_TABLE_RECOMMENDATION,
    COLOR_CONFIG_FINAL_EVALUATION,
)
