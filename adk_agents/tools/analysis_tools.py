"""Analysis tools for pattern detection and ROI calculation."""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..config.settings import OEE_BENCHMARK, ANALYSIS_WINDOW_DAYS

logger = logging.getLogger(__name__)

def analyze_patterns(data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """Perform pattern analysis on query results.
    
    Args:
        data: Query results from SPARQL
        analysis_type: Type of analysis to perform
    
    Returns:
        Analysis results with insights
    """
    if "error" in data:
        return {"error": "Cannot analyze failed query results"}
    
    # Check for data in various formats
    has_data = False
    if "results" in data and data["results"].get("bindings"):
        has_data = True
    elif "data" in data and "results" in data["data"]:
        has_data = True
    
    if not has_data:
        return {"error": "No data to analyze"}
    
    # Convert to DataFrame for easier analysis
    # Handle both formats: direct results or nested in data
    if "results" in data and "bindings" in data["results"]:
        bindings = data["results"]["bindings"]
    elif "data" in data and "results" in data["data"]:
        # Handle the wrapped format from execute_sparql
        bindings = data["data"]["results"]
    else:
        bindings = []
    
    df_data = []
    
    # Handle different result formats
    if isinstance(bindings, list) and bindings and isinstance(bindings[0], dict):
        # Standard SPARQL bindings format
        for binding in bindings:
            row = {}
            for var, value in binding.items():
                if isinstance(value, dict) and "value" in value:
                    row[var] = value.get("value", "")
                else:
                    row[var] = value
            df_data.append(row)
    elif isinstance(bindings, list) and bindings:
        # Simple list format (from our API)
        # Assume columns are provided
        if "columns" in data.get("data", data):
            columns = data.get("data", data)["columns"]
            for result_row in bindings:
                row = dict(zip(columns, result_row))
                df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Perform analysis based on type
    if analysis_type == "temporal":
        return analyze_temporal_patterns(df)
    elif analysis_type == "capacity":
        return analyze_capacity_patterns(df)
    elif analysis_type == "quality":
        return analyze_quality_patterns(df)
    elif analysis_type == "aggregation":
        return analyze_aggregation_patterns(df)
    else:
        return analyze_general_patterns(df)

def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze temporal patterns in data."""
    insights = []
    
    # Look for date/time columns
    date_columns = [col for col in df.columns if any(term in col.lower() for term in ["date", "time", "timestamp"])]
    
    if date_columns:
        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col])
                
                # Calculate time range
                time_range = df[col].max() - df[col].min()
                insights.append(f"Data spans {time_range.days} days")
                
                # Check for gaps
                df_sorted = df.sort_values(col)
                time_diffs = df_sorted[col].diff()
                avg_gap = time_diffs.mean()
                max_gap = time_diffs.max()
                
                if max_gap > avg_gap * 3:
                    insights.append(f"Significant data gap detected: {max_gap}")
                
            except Exception as e:
                logger.warning(f"Failed to parse date column {col}: {e}")
    
    # Look for numeric trends
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        if len(df) > 10:  # Need enough data for trend
            values = df[col].dropna()
            if len(values) > 0:
                # Simple linear trend
                x = np.arange(len(values))
                slope, _ = np.polyfit(x, values, 1)
                
                if abs(slope) > 0.01 * values.mean():
                    direction = "increasing" if slope > 0 else "decreasing"
                    insights.append(f"{col} shows {direction} trend")
    
    return {
        "pattern_type": "temporal",
        "insights": insights,
        "data_points": len(df),
        "columns_analyzed": list(df.columns)
    }

def analyze_capacity_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze capacity-related patterns (OEE, performance, etc.)."""
    insights = []
    metrics = {}
    
    # Look for OEE-related columns
    oee_columns = [col for col in df.columns if any(term in col.lower() for term in ["oee", "availability", "performance", "quality"])]
    
    for col in oee_columns:
        try:
            values = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(values) > 0:
                metrics[col] = {
                    "mean": float(values.mean()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "std": float(values.std())
                }
                
                # Compare to benchmark
                if "oee" in col.lower():
                    below_benchmark = (values < OEE_BENCHMARK).sum()
                    pct_below = (below_benchmark / len(values)) * 100
                    
                    if pct_below > 20:
                        insights.append(f"{pct_below:.1f}% of OEE values below {OEE_BENCHMARK}% benchmark")
                    
                    # Find worst performers
                    if "line" in df.columns or "equipment" in df.columns:
                        group_col = "line" if "line" in df.columns else "equipment"
                        worst = df.groupby(group_col)[col].mean().sort_values().head(3)
                        
                        for equip, value in worst.items():
                            insights.append(f"{equip} has low average {col}: {value:.1f}%")
                
        except Exception as e:
            logger.warning(f"Failed to analyze column {col}: {e}")
    
    return {
        "pattern_type": "capacity",
        "insights": insights,
        "metrics": metrics,
        "benchmark_used": OEE_BENCHMARK
    }

def analyze_quality_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze quality-related patterns."""
    insights = []
    metrics = {}
    
    # Look for quality-related columns
    quality_columns = [col for col in df.columns if any(term in col.lower() for term in ["quality", "defect", "reject", "scrap"])]
    
    for col in quality_columns:
        try:
            values = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(values) > 0:
                metrics[col] = {
                    "total": float(values.sum()),
                    "mean": float(values.mean()),
                    "max": float(values.max())
                }
                
                # Check for high defect rates
                if "rate" in col.lower() or "percent" in col.lower():
                    high_defect = (values > 5).sum()  # 5% threshold
                    if high_defect > 0:
                        insights.append(f"{high_defect} instances of high {col} (>5%)")
                
        except Exception as e:
            logger.warning(f"Failed to analyze column {col}: {e}")
    
    # Look for patterns by product/line
    if "product" in df.columns:
        for col in quality_columns:
            try:
                product_quality = df.groupby("product")[col].mean().sort_values(ascending=False).head(3)
                for product, value in product_quality.items():
                    insights.append(f"{product} has high {col}: {value:.2f}")
            except:
                pass
    
    return {
        "pattern_type": "quality",
        "insights": insights,
        "metrics": metrics
    }

def analyze_aggregation_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform aggregation analysis (COUNT, GROUP BY) using pandas.
    
    This is used as a fallback when SPARQL COUNT/GROUP BY returns IRIs instead of numbers.
    """
    insights = []
    results = {}
    
    # Detect grouping columns (columns with repeated values)
    grouping_candidates = []
    for col in df.columns:
        # A column is a grouping candidate if it has fewer unique values than total rows
        # and has at least some repeated values
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio < 0.9:  # Column has repeated values (at least 10% repetition)
            grouping_candidates.append(col)
    
    if not grouping_candidates:
        # No obvious grouping columns, just count total rows
        results["total_count"] = len(df)
        insights.append(f"Total records: {len(df)}")
    else:
        # Perform GROUP BY counting on the most likely grouping column
        # (the one with the fewest unique values)
        primary_group = min(grouping_candidates, key=lambda x: df[x].nunique())
        
        # Count by primary grouping column
        grouped_counts = df.groupby(primary_group).size().to_dict()
        results["counts_by_" + primary_group] = grouped_counts
        
        # Sort by count descending
        sorted_counts = sorted(grouped_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Add insights
        insights.append(f"Grouped by {primary_group}: {len(grouped_counts)} unique values")
        insights.append(f"Top 3 {primary_group} by count:")
        for value, count in sorted_counts[:3]:
            insights.append(f"  - {value}: {count} records")
        
        # If there are multiple grouping candidates, do multi-level grouping
        if len(grouping_candidates) > 1:
            secondary_group = [g for g in grouping_candidates if g != primary_group][0]
            multi_grouped = df.groupby([primary_group, secondary_group]).size()
            
            # Find interesting patterns
            max_combo = multi_grouped.idxmax()
            max_count = multi_grouped.max()
            insights.append(f"Most common combination: {primary_group}={max_combo[0]}, {secondary_group}={max_combo[1]} ({max_count} records)")
    
    # Calculate percentages
    total = len(df)
    if grouping_candidates and "counts_by_" + primary_group in results:
        percentages = {}
        for key, count in results["counts_by_" + primary_group].items():
            percentages[key] = round((count / total) * 100, 2)
        results["percentages_by_" + primary_group] = percentages
    
    return {
        "pattern_type": "aggregation",
        "insights": insights,
        "results": results,
        "total_records": len(df),
        "grouping_columns": grouping_candidates
    }

def analyze_general_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """General pattern analysis for unclassified data."""
    insights = []
    
    # Basic statistics
    insights.append(f"Dataset contains {len(df)} records with {len(df.columns)} columns")
    
    # Check for missing data
    missing = df.isnull().sum()
    high_missing = missing[missing > len(df) * 0.1]
    if len(high_missing) > 0:
        for col, count in high_missing.items():
            pct = (count / len(df)) * 100
            insights.append(f"{col} has {pct:.1f}% missing values")
    
    # Find categorical patterns
    for col in df.columns:
        if df[col].dtype == 'object':
            unique_count = df[col].nunique()
            if unique_count < 20:  # Likely categorical
                value_counts = df[col].value_counts().head(3)
                for value, count in value_counts.items():
                    pct = (count / len(df)) * 100
                    if pct > 20:
                        insights.append(f"{col}='{value}' appears in {pct:.1f}% of records")
    
    return {
        "pattern_type": "general",
        "insights": insights,
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": list(df.columns)
    }

def calculate_roi(
    current_performance: float,
    target_performance: float,
    annual_volume: float,
    unit_value: float
) -> Dict[str, Any]:
    """Calculate financial impact and ROI.
    
    Args:
        current_performance: Current performance percentage
        target_performance: Target performance percentage
        annual_volume: Annual production volume
        unit_value: Value per unit produced
    
    Returns:
        ROI calculation results
    """
    # Calculate improvement
    improvement = target_performance - current_performance
    
    if improvement <= 0:
        return {
            "error": "Target performance must be higher than current performance",
            "current": current_performance,
            "target": target_performance
        }
    
    # Calculate additional output
    current_output = annual_volume * (current_performance / 100)
    target_output = annual_volume * (target_performance / 100)
    additional_output = target_output - current_output
    
    # Calculate financial impact
    annual_benefit = additional_output * unit_value
    
    # Estimate implementation cost (rough estimate - 10% of annual benefit)
    estimated_cost = annual_benefit * 0.1
    
    # Calculate ROI
    roi_percent = ((annual_benefit - estimated_cost) / estimated_cost) * 100
    payback_months = (estimated_cost / annual_benefit) * 12
    
    # 5-year projection
    five_year_benefit = annual_benefit * 5
    five_year_roi = ((five_year_benefit - estimated_cost) / estimated_cost) * 100
    
    return {
        "current_performance": current_performance,
        "target_performance": target_performance,
        "improvement_percentage": improvement,
        "current_annual_output": int(current_output),
        "target_annual_output": int(target_output),
        "additional_annual_output": int(additional_output),
        "unit_value": unit_value,
        "annual_benefit": round(annual_benefit, 2),
        "estimated_implementation_cost": round(estimated_cost, 2),
        "roi_percentage": round(roi_percent, 1),
        "payback_months": round(payback_months, 1),
        "five_year_benefit": round(five_year_benefit, 2),
        "five_year_roi": round(five_year_roi, 1),
        "assumptions": [
            "Implementation cost estimated at 10% of annual benefit",
            "Benefits assumed constant over 5 years",
            "No inflation or discounting applied"
        ]
    }

def find_optimization_opportunities(df: pd.DataFrame, metric_column: str, threshold: float) -> List[Dict[str, Any]]:
    """Find specific optimization opportunities in the data."""
    opportunities = []
    
    try:
        # Convert metric to numeric
        df[metric_column] = pd.to_numeric(df[metric_column], errors='coerce')
        
        # Find underperformers
        below_threshold = df[df[metric_column] < threshold]
        
        # Group by equipment/line if available
        group_columns = [col for col in df.columns if col.lower() in ["line", "equipment", "machine", "station"]]
        
        if group_columns and len(below_threshold) > 0:
            group_col = group_columns[0]
            
            for equipment in below_threshold[group_col].unique():
                equip_data = below_threshold[below_threshold[group_col] == equipment]
                
                opportunity = {
                    "equipment": equipment,
                    "current_performance": float(equip_data[metric_column].mean()),
                    "gap_to_threshold": float(threshold - equip_data[metric_column].mean()),
                    "frequency": len(equip_data),
                    "potential_improvement": f"{threshold - equip_data[metric_column].mean():.1f}%"
                }
                
                # Add time context if available
                date_columns = [col for col in df.columns if "date" in col.lower() or "time" in col.lower()]
                if date_columns:
                    try:
                        dates = pd.to_datetime(equip_data[date_columns[0]])
                        opportunity["last_occurrence"] = dates.max().strftime("%Y-%m-%d")
                        opportunity["first_occurrence"] = dates.min().strftime("%Y-%m-%d")
                    except:
                        pass
                
                opportunities.append(opportunity)
        
        # Sort by potential impact
        opportunities.sort(key=lambda x: x["gap_to_threshold"], reverse=True)
        
    except Exception as e:
        logger.error(f"Failed to find opportunities: {e}")
    
    return opportunities[:10]  # Return top 10 opportunities