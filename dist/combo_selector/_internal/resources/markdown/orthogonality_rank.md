## Orthogonality Rank

Consensus rank calculated from the selected orthogonality metrics. First, each metric is used to rank the tested combinations. 

When metric values are equal or near-equal according to a predefined tolerance rule, the corresponding combinations are assigned a midrank. 

The resulting metric-specific ranks are then compared using a Kendall rank-correlation matrix to identify metrics that behave similarly across the tested combinations. 

Metrics showing similar ranking patterns are grouped, and the ranks within each group are aggregated using the mean, 

so that each group contributes a single rank value for each combination. 

Finally, these group-specific rank values are combined using a Borda-type rank aggregation to obtain a single consensus orthogonality rank.

This approach reduces the influence of redundant metrics and provides a more robust consensus ranking, 

while limiting the impact of value-driven effects that could artificially pull a score up or down in a value-based aggregation

Lower ranks indicate better overall orthogonality.

