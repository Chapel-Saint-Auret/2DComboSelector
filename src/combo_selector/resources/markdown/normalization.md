## Data Normalization

Normalization transforms retention times into comparable normalized coordinates before plotting and orthogonality evaluation.

This step reduces the effect of differences in retention scale between conditions and allows 

all combinations to be compared within a common separation space.

The selected normalization is applied independently to each tested condition and only affects 

the processed data used for visualization and metric calculation, not the original imported values.

Three normalization methods are available:

	- **Min-max**
	
	- **WOSEL**
	
	- **Void-Max**

Min-max normalization is recommended as the default option. For WOSEL and Void-Max normalization, additional input parameters are required. 

These fields appear in the settings panel on the left when the corresponding method is selected.
