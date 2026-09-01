## Final Orthogonality Assessment

Defines how the final orthogonality result is calculated.

**Default** applies the recommended consensus approach. Each orthogonality metric first ranks the tested combinations. Metrics showing similar ranking behavior are grouped to limit redundancy, the ranks are averaged within each group, and the resulting group ranks are aggregated using a **Borda-based procedure**. This produces a consensus ranking that combines complementary aspects of orthogonality without allowing a large group of correlated metrics to dominate the result.

**Custom** allows the user to select one or more orthogonality metrics. When several metrics are selected, their normalized results are aggregated using either the **mean** or the **median**. The median is less sensitive to an individual metric giving an unusually high or low result, whereas the mean gives equal influence to all selected metrics.


