# Advanced Analysis with Python

When SPARQL queries return large datasets (indicated by cache_id), use execute_python_code for sophisticated analysis.

## IMPORTANT: DataFrame Pre-Loading
When you provide a cache_id, the DataFrame 'df' is automatically pre-loaded with proper column names.
You do NOT need to call any API functions - just use 'df' directly.

## Example Usage:
```python
# DataFrame 'df' is already loaded when cache_id is provided
print(f"Analyzing {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")

# Direct column access - columns are named without the '?' prefix
avg_oee = df['oee'].mean()  # NOT df['?oee']
top_equipment = df.groupby('equipment')['oee'].mean().sort_values(ascending=False)

# Must define 'result' dict with findings
result = {
    "average_oee": avg_oee,
    "top_performer": top_equipment.index[0],
    "bottom_performer": top_equipment.index[-1]
}
```

## Analysis Workflow:
1. **Explore Structure**: Check df.shape, df.columns, df.head()
2. **Understand Data**: Use df.describe(), check for nulls
3. **Find Patterns**: Group by dimensions, calculate statistics
4. **Return Results**: Always define 'result' dict

## Common Analysis Patterns:

### Time Series Analysis
```python
# Convert timestamp column to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Group by hour/day/week
df['hour'] = df['timestamp'].dt.hour
hourly_patterns = df.groupby('hour')['oee'].mean()

result = {
    "peak_hour": hourly_patterns.idxmax(),
    "lowest_hour": hourly_patterns.idxmin()
}
```

### Aggregation Fallback (when SPARQL COUNT fails)
```python
# Count by group when SPARQL aggregation returns IRIs
reason_counts = df['reason'].value_counts()

result = {
    "top_reason": reason_counts.index[0],
    "reason_distribution": reason_counts.to_dict()
}
```

### Statistical Analysis
```python
# Calculate percentiles, correlations, etc.
oee_percentiles = df['oee'].quantile([0.25, 0.5, 0.75])
correlation = df[['oee', 'quality', 'performance']].corr()

result = {
    "oee_quartiles": oee_percentiles.to_dict(),
    "performance_quality_correlation": correlation.loc['performance', 'quality']
}
```

## Error Recovery:
- If you get NameError about 'df': Check that cache_id was provided
- If you get KeyError on columns: Use df.columns.tolist() to see exact names
- Build incrementally - test simple operations before complex analysis

## Available Libraries:
- pandas (as pd)
- numpy (as np)
- datetime
- collections
- itertools
- statistics

## Best Practices:
1. Always check data structure first
2. Handle missing values appropriately
3. Use vectorized operations for performance
4. Return clear, actionable insights in the result dict
5. Include both summary statistics and specific examples