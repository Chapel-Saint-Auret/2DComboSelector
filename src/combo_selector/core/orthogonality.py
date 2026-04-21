"""Core orthogonality analysis model for 2D chromatography combination selection.

This module provides :class:`Orthogonality`, a thin facade that composes five
focused mixin classes into a single object that can be passed to any UI page.

All constants and helpers used across the sub-modules live in
:mod:`combo_selector.core.orthogonality_utils` and are re-exported here so
that existing imports (e.g. ``from combo_selector.core.orthogonality import
METRIC_MAPPING``) continue to work without modification.
"""

from PySide6.QtCore import QObject, Signal

from combo_selector.core.orthogonality_utils import *  # noqa: F401,F403 – re-export for callers
from combo_selector.core.data_manager import DataManager
from combo_selector.core.metric_engine import MetricEngine
from combo_selector.core.redundancy import Redundancy
from combo_selector.core.results_builder import ResultsBuilder
from combo_selector.core.scoring import Scoring
from combo_selector.ui.widgets.nan_policy_widget import NanPolicyDialog


class Orthogonality(DataManager, MetricEngine, Redundancy, Scoring, ResultsBuilder, QObject):
    """Facade that unifies data management, metric computation, redundancy analysis,
    scoring, and results building into a single model object.

    All public methods are inherited from the mixin classes:

    * :class:`~combo_selector.core.data_manager.DataManager` – data loading and
      normalisation.
    * :class:`~combo_selector.core.metric_engine.MetricEngine` – orthogonality
      metric computation (pure Python, no Qt).
    * :class:`~combo_selector.core.redundancy.Redundancy` – correlation group
      analysis.
    * :class:`~combo_selector.core.scoring.Scoring` – consensus/coverage/
      distribution scoring.
    * :class:`~combo_selector.core.results_builder.ResultsBuilder` – results
      table construction and final recommendations.

    The facade itself only owns the Qt ``Signal``, the ``__init__`` method,
    and the ``NanPolicyDialog`` instance that requires a live Qt application.
    """

    progressChanged = Signal(int)

    def __init__(self):
        """Initialize the Orthogonality object with default values and data structures."""
        QObject.__init__(self)
        self.nan_policy_dialog = NanPolicyDialog(model=self)
        self.removed_condition_list = []
        self.removed_compound_list = []
        self.column_names = []
        self.compound_name_list = []
        self.metric_rho_coverage = None
        self.group_rho_coverage = None
        self.group_rho_distribution = None
        self.metric_rho_distribution = None
        self.norm_ret_time_table = None
        self.orthogonality_corr_mat = None
        self.orthogonality_score = None
        self.orthogonality_dict = None
        self.has_nan_value = False
        self.nan_policy_option1_threshold = 50
        self.nan_policy_option2_threshold = 50
        self.table_data = None
        self.om_function_map = None
        self.nb_peaks = None
        self.bin_number = 14
        self.nb_condition = 0
        self.nb_combination = 0
        self.retention_time_df = None
        self.retention_time_df_2d_peaks = None
        self.use_suggested_score = True
        self.status = "no_data"
        self.peak_capacity_status = "no_data"
        self.init_data()
        self.reset_om_status_computation_state()
