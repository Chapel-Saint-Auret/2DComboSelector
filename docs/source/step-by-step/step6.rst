Step 6 – Results & Final Selection
==================================

Purpose
-------
The **Results** page is the final step of the tool, where users identify the optimal 2D-LC condition among all pairwise combinations tested.
It ranks all combinations using a newly introduced criterion: the **hypothetical 2D peak capacity**. This value is derived using the orthogonality score and indicates how effectively a combination might perform.

.. figure:: /_static/images/step-by-step/step6/use_score.png
   :width: 30%
   :align: center
   :alt:

- The **suggested score** corresponds to the orthogonality score previously introduced in :ref:`step5-orthogonality-score`.
- The **computed score** offers flexibility by allowing users to manually select which orthogonality metrics to include. The score is computed as the average of the selected OM values for each 2D combination:


- To calculate a computed score:

  1. Select the metrics from the **Computed OM list**.
  2. Click the **Compute score** button.

.. figure:: /_static/images/step-by-step/step6/compute_score.png
   :width: 35%
   :align: center
   :alt:

Hypothetical 2D Peak Capacity
-----------------------------
The hypothetical 2D peak capacity is computed from the orthogonality score using the formula described in the paper:

.. math::
   n_{2D,pred} = O_{\text{score}} \times n_{2D,pred}

.. math::
   n_{2D,pred} = n_{exp,1} \times n_{exp,2}

Where:
- :math:`O_{\text{score}}` is either the suggested or computed orthogonality score.
- :math:`n_{exp,1}` and :math:`n_{exp,2}` are the experimental peak capacities in the first and second dimensions.

The **ranking** of combinations is then based on their hypothetical 2D peak capacity. A higher value indicates a more promising separation.

Result Visualization
--------------------
- This section plots the **orthogonality score** against the **hypothetical 2D peak capacity**.
- Each **point** on the plot corresponds to a unique 2D combination.

.. figure:: /_static/images/step-by-step/step6/result_plot.png
   :width: 60%
   :align: center
   :alt:

- Users can generate up to **four plots simultaneously** to compare different scoring approaches:
- Compare **Suggested vs Computed** scores
- Compare **Oscore vs Hypothetical 2D peak capacity**
- Compare **OM vs OM**

.. figure:: /_static/images/step-by-step/step6/score_comparison.png
   :width: 35%
   :align: center
   :alt:

This enables fast visual screening of conditions that are both orthogonal and capable of delivering high separation performance.

Final Result Table
------------------
- Displays:
  - The 2D combination name
  - Suggested score
  - Computed score (if selected)
  - Hypothetical 2D peak capacity
  - Final ranking

- The table updates automatically based on the selected :math:`O_{\text{score}}` (suggested or computed), allowing users to compare the impact of different metric selections on final ranking.

.. figure:: /_static/images/step-by-step/step6/result_table.png
   :width: 100%
   :align: center
   :alt:
