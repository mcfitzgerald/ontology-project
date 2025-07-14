"""
Analysis patterns extracted from the $2.5M opportunity discoveries.
"""

CAPACITY_OPTIMIZATION_PATTERN = """
Pattern: Hidden Capacity Analysis
1. Identify equipment with performance below benchmark (85% OEE)
2. Calculate current vs potential production volume
3. Determine downstream impact on connected equipment
4. Apply unit margins to volume gaps
5. Annualize the opportunity value
6. Recommend specific improvements with ROI timelines

Example: LINE2-PCK at 63% OEE = 11.8% capacity gain = $341K-$700K/year
"""

TEMPORAL_PATTERN_RECOGNITION = """
Pattern: Time-Based Problem Clustering
1. Extract event timestamps and group by time dimensions
2. Identify clustering within 15-minute windows
3. Analyze shift-based variations (day vs night)
4. Calculate frequency and duration of issues
5. Quantify production loss during problem periods
6. Build predictive maintenance triggers

Example: 60% of jams occur within 10 min of previous = $250K-$350K opportunity
"""

QUALITY_COST_TRADEOFF = """
Pattern: Quality Improvement ROI
1. Segment scrap rates by product and margin levels
2. Focus on high-margin products first
3. Model scrap reduction scenarios (10%, 25%, 50%)
4. Calculate material savings and increased good output
5. Estimate investment requirements
6. Prioritize by payback period

Example: 1% quality gain on Energy Drinks = $144K/year, 3-4 month payback
"""

ROOT_CAUSE_CASCADE = """
Pattern: Upstream-Downstream Impact Analysis
1. Trace equipment relationships (isUpstreamOf)
2. Identify bottleneck equipment constraining flow
3. Calculate cascade effects on downstream equipment
4. Quantify idle time and lost production
5. Model system-wide improvement impact

Example: Filler bottleneck ’ Packer/Palletizer underutilization
"""

MICRO_STOP_AGGREGATION = """
Pattern: Small Problems, Big Impact
1. Identify stops under 5 minutes (often ignored)
2. Calculate frequency across shifts/days
3. Aggregate total time loss
4. Apply production rate to get volume loss
5. Highlight that many small stops = major issue

Example: LINE2-PCK 25% micro-stops = 2 hours/day loss = $341K/year
"""