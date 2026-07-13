## Final Consensus Score

Combined score calculated from the normalized utilities of the main ranking criteria before final reranking.

It reflects the overall multi-criteria performance of each combination based on **Orthogonality Utility**, **Elution Domain Utility**, and **Peak Capacity Utility** (when available).

It is calculated as:

	- **S_final = (U_O + U_P + U_D) / 3**

or, when peak capacity is unavailable:
	
	- **S_final = (U_O + U_D) / 2**
	
Higher values indicate better overall performance.
