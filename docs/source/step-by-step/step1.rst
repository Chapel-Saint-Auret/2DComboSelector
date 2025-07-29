Step 1: Data Preparation
========================

This section explains how to prepare your data for **2DComboSelector**.

Before using the tool, it is essential to carefully design your experiments to ensure the data you load will enable a reliable assessment of orthogonality and peak capacity across 1D-LC conditions.

Start by selecting a representative set of compounds relevant to your target application. In the study behind this tool, a mix of over 300 environmentally significant organic micropollutants (OMPs) was used, but a smaller or more targeted set can be chosen depending on your analytical goals.

Perform preliminary **scouting runs** under a wide range of chromatographic conditions in one-dimensional liquid chromatography (1D-LC), varying column chemistries, mobile phases, and pH. The goal of these scouting runs is to screen as many plausible 1D conditions as possible. From these runs, identify well-separated peaks for your representative compounds under each tested condition.

For each 1D-LC condition, you must extract two key pieces of information from your chromatograms:

- **Retention Times**: record the retention time for each representative compound, ideally confirmed through mass spectrometry or UV detection, for every 1D condition tested. This data will be used by the tool to create normalized retention time tables and visualize potential 2D combinations.
- **Experimental Peak Capacity**: calculate the experimental peak capacity for each 1D-LC condition using peak widths of representative peaks. Peak capacity provides a measure of separation performance in a single dimension, and is critical for predicting the potential 2D peak capacity.


Retention Time Table
--------------------

The retention time table should include raw retention times (in minutes or seconds) of each peak under every 1D-LC condition. Each column typically represents a different 1D condition, and each row corresponds to a specific compound or peak.

+-------------------+-------------------+-------------------+-------------------+
| 1D LC Condition 1 | 1D LC Condition 2 | 1D LC Condition 3 | 1D LC Condition 4 |
+===================+===================+===================+===================+
| 1.15              | 0.98              | 1.33              | 1.05              |
+-------------------+-------------------+-------------------+-------------------+
| 2.87              | 3.22              | 2.45              | 3.05              |
+-------------------+-------------------+-------------------+-------------------+
| 4.56              | 5.12              | 4.77              | 5.45              |
+-------------------+-------------------+-------------------+-------------------+
| 6.34              | 7.25              | 6.88              | 7.12              |
+-------------------+-------------------+-------------------+-------------------+
| 8.02              | 9.11              | 8.35              | 9.27              |
+-------------------+-------------------+-------------------+-------------------+

Example of 4 1D-LC conditions with retention times of given compounds

Experimental Peak Capacity Table
--------------------------------

The experimental 1D peak capacity table should contain the calculated peak capacity value for each 1D-LC condition. This value reflects the resolving power of the condition and will be used by the tool to estimate the predicted and practical 2D peak capacities.

+-------------------+-------------------+-------------------+-------------------+
| 1D LC Condition 1 | 1D LC Condition 2 | 1D LC Condition 3 | 1D LC Condition 4 |
+===================+===================+===================+===================+
| 115.6             | 48.1              | 111.8             | 92.1              |
+-------------------+-------------------+-------------------+-------------------+

Example of 4 1D-LC conditions with their experimental 1D peak capacity

Load Data
---------

- Load retention time by clicking on the **Import** button and selecting the Excel spreadsheet where the retention time data are located.

.. figure:: /_static/images/step-by-step/step1/import_rt.gif
   :width: 50%
   :align: center
   :alt: GitHub template for the tutorial

   Retention time data


- Load experimental 1D peak capacity by clicking on the **Import** button and selecting the Excel spreadsheet where the experimental peak capacity data are located.

.. figure:: /_static/images/step-by-step/step1/import_th_peak.gif
   :width: 50%
   :align: center
   :alt: GitHub template for the tutorial

   experimental 1D peak capacity data
.. note::

   The tables can start anywhere in the spreadsheet, as long as they respect the format shown in the sections above. The titles for the 1D LC conditions must be exactly the same in both the retention time and peak capacity tables — any difference, including extra spaces or mismatched characters, will cause the combination table building to fail.


Accepted Table Formats
----------------------

Both the retention time and experimental peak capacity tables must be organized in a structured spreadsheet format (Excel .xlsx or .xls files).


