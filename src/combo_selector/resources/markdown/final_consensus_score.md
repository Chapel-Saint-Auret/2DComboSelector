## Final Consensus Score

Combined score calculated from the normalized utilities of the main ranking criteria before final reranking.

It reflects the overall multi-criteria performance of each combination based on **Orthogonality Utility**, **Elution Domain Utility**, and **Peak Capacity Utility** (when available).

When the penalty option is enabled, the score is adjusted to prevent combinations with critically low **Orthogonality Utility** or **Elution Domain Utility** from being highly ranked solely because of strong performance on the other criteria.

The initial score is calculated as:

	- S_raw = (U_O + U_P + U_D )/ 3 
	
or, when peak capacity is unavailable:

	- S_raw =(U_O + U_D )/ 2
	
The penalty factors are:

    - P_O = min(1,UO /0.3) 
	
	- P_D = min(1,UD/0.25) 
	
and the final score is:
  
	- S_final = S_raw * P_O * P_D 
	
Therefore, no penalty is applied when **UO ≥ 0.30** and **UD ≥ 0.25**. Below these thresholds, the score is progressively reduced according to the corresponding utility value.

Higher values indicate better overall multi-criteria performance. The resulting scores are then reranked to obtain the final consensus rank.