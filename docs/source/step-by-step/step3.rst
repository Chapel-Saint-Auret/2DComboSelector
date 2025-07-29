Step 3 – Pairwise Combination & Plotting
========================================

Purpose
-------

The **Data Plotting Pairwise** page provides an interactive interface to explore predicted 2D separations formed by pairwise combinations of your 1D-LC conditions.

- The tool automatically identifies all unique pairwise combinations of sets from your retention time table, representing potential 2D-LC separations. These unique pairs are summarized in the :ref:`2D combination table <combination-table>` at the bottom of the page.
- Each combination corresponds to a predicted 2D separation where retention times from two different 1D-LC conditions are plotted against each other.

Plotting combinations
---------------------

.. figure:: /_static/images/step-by-step/step3/dataset_visualization.png
   :align: center
   :alt:

   Dataset visualization

- You can select specific sets in the **Dataset selection** panel on the left side of the page. Choose up to **four sets simultaneously** to display side-by-side plots for quick and direct comparison.
- Comparing multiple sets visually helps identify combinations with the most evenly distributed peaks, which indicates higher orthogonality—a key factor in selecting effective 2D-LC conditions.
- Each plot dynamically updates based on your selections, allowing fast screening of which pairwise combinations offer complementary separations.

Info & Table
------------

- Displays the number of sets and the total number of unique 2D combinations detected.
- Provides a quick overview so you can immediately verify that your data have been loaded correctly and combinations generated as expected.


.. _combination-table:

.. figure:: /_static/images/step-by-step/step3/2d_combination_table.png
   :align: center
   :alt:

   2D Combination table

This page gives users an at-a-glance understanding of how their 1D-LC conditions interact in potential 2D pairings and supports informed decisions on which sets to prioritize for orthogonality evaluation.
