## Orthogonality Utility

In default mode, an Orthogonality Rank is obtained for each combination using a Borda-based consensus, in which the ranks assigned by the different orthogonality metric groups are aggregated. This approach combines complementary interpretations of orthogonality while limiting the influence of redundant metrics.

In custom mode, the Orthogonality Rank is obtained from the user-selected metric or metrics. When several metrics are selected, their normalized results are combined using the chosen aggregation method, either the mean or the median, and the combinations are then ranked according to the resulting aggregated value. 

Because the resulting consensus is rank-based, it does not provide an absolute measure of orthogonality. It is therefore converted into a normalized utility for use in the final multi-criteria score:

	- Uₒ = 1 − (Rₒ − 1) / (N − 1)
where **Rₒ** is the Orthogonality Rank and **N** is the total number of tested combinations.

Values range from **0** to **1**, with higher values corresponding to better relative rankings. This utility expresses the position of a combination within the tested dataset, so it should not be interpreted as an absolute orthogonality score or directly compared across different datasets in the default mode. 

<body>
    <p>Here is an inline equation: \( E = mc^2 \)</p>
    <p>And here is a block equation:</p>
    $$ \int_{a}^{b} f(x) \,dx = F(b) - F(a) $$
</body>