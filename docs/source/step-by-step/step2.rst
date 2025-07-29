Step 2: Retention Time Normalization
====================================

Purpose
-------

Ensuring fair comparison across 1D conditions by bringing retention times to a common scale.

Normalization Methods
---------------------

Three normalization methods are available:

.. figure:: /_static/images/step-by-step/step2/normalization.png
   :width: 50%
   :align: center
   :alt:

   Separation space scaling technique

- **Min-Max Normalization**:
  Retention times are scaled between the first and last eluting compound in each dimension. This preserves the relative spread of peaks across the full gradient.

- **Void-Max Normalization**:
  Retention times are scaled between the system void time (Rt₀) and the last eluting compound. This method accounts for system dead volume and is useful when early peaks near Rt₀ carry significant information.

.. figure:: /_static/images/step-by-step/step2/void_max.png
   :width: 65%
   :align: center
   :alt:



- **Wosel Normalization**:
  A custom normalization approach developed for cases where early eluting peaks must be either emphasized or down-weighted. Wosel normalization adjusts the scaling non-linearly to better capture details in early elution regions.

.. figure:: /_static/images/step-by-step/step2/wosel.png
   :width: 65%
   :align: center
   :alt:


Here is how the normalization parameters should be formatted in an Excel spreadsheet according to the chosen normalization technique:

+-------------------+-------------------+-------------------+-------------------+
| Rt₀ Condition 1   | Rt₀ Condition 2   | Rt₀ Condition 3   | Rt₀ Condition 4   |
+===================+===================+===================+===================+
| 0.6               | 0.1               | 0.8               | 1.1               |
+-------------------+-------------------+-------------------+-------------------+

Example of void times (Rt₀) for four 1D-LC conditions. The same format applies for Rt\ :sub:end values (representing each condition’s gradient end time).


Choosing the Appropriate Normalization
--------------------------------------

Selecting the right normalization depends on your dataset and analysis goals:

- Use **Min-Max** when you want uniform scaling across the chromatogram.
- Choose **Void-Max** if you need to account for void time and baseline shifts.
- Apply **Wosel** if early-eluting peaks are critical or need specialized treatment.

Once the parameter for the selected normalization technique is loaded click on the :guilabel:`Normalize data`.
button to proceed


Normalized Retention Time Outputs
---------------------------------

After normalization, retention times are stored in the output table with normalized values in the range defined by the selected method. These normalized retention times ensure fair and meaningful comparison across 1D separations with different time scales.

.. figure:: /_static/images/step-by-step/step2/normalization_table.png
   :width: 100%
   :align: center
   :alt:

   Normalized retention time table


.. note::

   If your retention times are already normalized, you do not need to select any scaling method. The data can simply be loaded using the same procedure as for unnormalized retention times.


