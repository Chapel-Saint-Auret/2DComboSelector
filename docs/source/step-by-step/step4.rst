Step 4 – Orthogonality Metric (OM) Calculation
==============================================

Purpose
-------

The **Orthogonality Metric Calculation** page enables systematic, quantitative evaluation of the separation space coverage of each predicted 2D-LC condition. This step is essential for assessing how effectively peaks are spread across the 2D space, which directly impacts the resolving power and the practical value of a selected combination.

- The goal is to provide a reliable, unbiased assessment of **orthogonality**, avoiding the limitations of single-metric approaches by allowing users to calculate and compare multiple metrics.

Selecting and Computing Metrics
-------------------------------

- Use the **OM calculation** panel on the left side of the page to select the orthogonality metrics you wish to compute. You can either select individual metrics or use the “Select all” option for a comprehensive evaluation.

.. figure:: /_static/images/step-by-step/step4/om_list.png
   :width: 35%
   :align: center
   :alt:

   OM list

- Once your metrics are chosen, click the :guilabel:`Compute metrics` button to calculate the orthogonality scores for each predicted 2D combination generated in previous steps.


- The tool supports the following **metrics**, covering different aspects of separation orthogonality:

  - **Convex hull relative area**
  - **Bin box counting**
  - **Gilar-Watson method**
  - **Modeling approach**
  - **Conditional entropy**
  - **Pearson correlation**
  - **Spearman correlation**
  - **Kendall correlation**
  - **Asterisk equations**
  - **Nearest neighbor distances** (**arithmetic**, **geometric**, **harmonic** means)
  - **%FIT**
  - **%BIN**

  The reference papers and detailed equations for each metric will be provided in the **Theory** section of the documentation.

Number of Bin Boxes Parameter
-----------------------------

The **Number of bin boxes** parameter is used as an input when computing the **Bin box counting**, **Gilar-Watson method**, and **Modeling approach** metrics. It defines how finely the 2D separation space is divided when calculating peak occupancy and distribution. A higher number of bins increases resolution but may reduce robustness for small datasets, while a lower number of bins may oversimplify complex separations. For detailed explanation of this parameter, refer to the Theory section.

.. figure:: /_static/images/step-by-step/step4/nb_bin_box.png
   :align: center
   :alt:

   OM list


Visualizing and Comparing Metrics
---------------------------------

.. figure:: /_static/images/step-by-step/step4/om_visualization.png
   :align: center
   :alt:

   Example of OM visualization plot

- The **OM visualization** area shows plots of the computed orthogonality metrics for each selected set.
- You can display up to **four plots simultaneously**, allowing side-by-side comparisons of different sets or metrics.
- Comparing metrics visually helps you identify sets that maximize separation space coverage and peak dispersion, which is critical for selecting optimal 2D-LC conditions.

OM Result Table
---------------

.. figure:: /_static/images/step-by-step/step4/om_results_table.png
   :align: center
   :alt:

   OM result table

- The **OM result table** summarizes all computed orthogonality metrics for each 2D combination.
- The table provides a quick overview, listing each set with its calculated values for all selected metrics.
- **Interpreting the scores**: orthogonality values range from 0 (no orthogonality: peaks overlap) to 1 (complete orthogonality: ideal dispersion). These scores allow straightforward comparison of potential 2D-LC combinations.
- Sets with higher orthogonality values are generally preferable, as they indicate better distribution of peaks across the 2D separation space.

This page equips you with powerful, automated tools to evaluate and compare multiple orthogonality metrics systematically, enabling more informed decisions when selecting 2D-LC conditions with high resolving power.
