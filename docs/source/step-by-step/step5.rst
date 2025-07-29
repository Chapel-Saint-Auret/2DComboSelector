.. _step5-orthogonality-score:

Step 5 – Redundancy Check
=========================

Purpose
-------

The **Redundancy Check** page helps identify which orthogonality metrics convey unique information and which are redundant. After computing orthogonality metrics on the previous **OM Calculation** page, the tool builds a **correlation matrix** of the selected metrics to analyze how they relate to each other. This visualization allows you to streamline metric selection for further analysis, avoiding unnecessary complexity by focusing on metrics that provide complementary insights.

Correlation Matrix Visualization
--------------------------------

.. figure:: /_static/images/step-by-step/step5/corr_mat_visualization.png
   :width: 100%
   :align: center
   :alt:

- The **Correlation matrix visualization** panel displays pairwise correlation coefficients among all computed orthogonality metrics. This matrix, generated from the metric results, shows how metrics relate numerically, using a customizable color scale to highlight positive or negative correlations.

- Metrics with a correlation coefficient **equal to or above the selected threshold** indicate redundancy, as they behave similarly across datasets and provide overlapping information.

Correlation Parameters
----------------------

.. figure:: /_static/images/step-by-step/step5/corr_parameters.png
   :width: 35%
   :align: center
   :alt:

- **Correlation threshold**: Defines the minimum correlation value (absolute) above which metrics are considered redundant. The default threshold is **0.85**, but you can adjust it to be more or less strict.

- **Threshold tolerance**: Allows fine-tuning of redundancy detection. If a metric's correlation coefficient differs from the threshold by less than or equal to the tolerance, it is included in the same group.

- **Matrix display options**:

  - **Show correlated metrics**
    Highlights metrics grouped according to your threshold.

  - **Show hierarchical clustering**
    Reorders the rows and columns of the matrix using hierarchical clustering algorithms, grouping similar metrics together visually. This helps quickly identify clusters of metrics with similar behavior and better understand metric relationships.

  - **Show lower triangle matrix**
    Hides the upper triangle of the symmetric matrix to simplify visualization.

  - **Show upper triangle matrix**
    Hides the lower triangle of the symmetric matrix for a clearer view of the upper part of the correlation matrix.


- **Color scale**: Lets you adjust the matrix’s color gradient to improve contrast or adapt it for presentations.

Groups Table
------------
.. figure:: /_static/images/step-by-step/step5/correlation_table.png
   :width: 100%
   :align: center
   :alt:

Once the **correlation threshold** and **tolerance** are set, the tool automatically forms **groups of correlated metrics**. Metrics within the same group have correlation coefficients **equal to or above the defined threshold**, meaning they behave similarly across analyzed datasets. The **Orthogonality result correlation table** summarizes these groups below the matrix:

- **Group**: Lists the group identifier (e.g., A, B, C...).
- **Correlated OM**: Displays metrics included in each group based on the correlation threshold.

.. important::
   Groups are only formed after metrics are computed on the **OM Calculation** page. If you adjust the correlation threshold or tolerance, **the groups and matrix update immediately**, helping you iteratively refine your redundancy analysis.



Orthogonality Score
-------------------

The orthogonality suggested score is calculated by grouping the orthogonality metrics obtained during redundancy analysis. Metrics within each group are averaged, and then these group means are combined into a single overall score. This approach avoids biases associated with relying on a single metric, as detailed in the reference study (Chapel et al., 2025), and ensures a comprehensive assessment of separation quality.

**Calculation**
For each group of correlated metrics, the average orthogonality value is computed. The final orthogonality score, :math:`O_{\text{score}}`, is then the mean of these group averages. A generic formula can be expressed as:

.. math::

   O_{\text{suggested score}} = \frac{1}{N} \sum_{i=1}^{N} \overline{O_{i}}

Where:
- :math:`N` is the number of groups formed based on the correlation matrix of metrics.
- :math:`\overline{O_{i}}` is the average orthogonality value within group *i*.

For example, with six groups, the formula would expand to:

.. math::

   O_{\text{suggested score}} = \frac{\overline{O_A} + \overline{O_B} + \overline{O_C} + \overline{O_D} + \overline{O_E} + \overline{O_F}}{6}


By integrating multiple metrics into a single score, the tool supports robust decision-making in method development and ensures reliable, reproducible evaluations of 2D-LC systems.

**Reference**
The principles, metric definitions, and calculation details for the orthogonality score can be found in the study by Chapel et al. (2025), *Journal of Chromatography A*, DOI: `10.1016/j.chroma.2025.465861 <https://doi.org/10.1016/j.chroma.2025.465861>`_.
