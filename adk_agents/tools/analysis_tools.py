"""
Data Analysis Tools for Google ADK - pattern detection and financial modeling.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from ..config.settings import DEFAULT_OEE_BENCHMARK, DEFAULT_ANALYSIS_WINDOW_DAYS


class TemporalAnalysisParams(BaseModel):
    """Parameters for temporal pattern analysis."""
    data: List[Dict] = Field(..., description="Time series data to analyze")
    time_column: str = Field("timestamp", description="Name of timestamp column")
    value_columns: List[str] = Field(..., description="Columns to analyze")
    group_by: Optional[List[str]] = Field(None, description="Columns to group by")
    aggregation: str = Field("mean", description="Aggregation method: mean, sum, count")


class FinancialImpactParams(BaseModel):
    """Parameters for financial impact calculation."""
    metric_data: List[Dict] = Field(..., description="Performance metric data")
    benchmark: float = Field(DEFAULT_OEE_BENCHMARK, description="Performance benchmark")
    volume_column: str = Field("units_produced", description="Production volume column")
    margin_column: str = Field("unit_margin", description="Profit margin column")
    time_period_days: int = Field(365, description="Time period for annualization")


class AnomalyDetectionParams(BaseModel):
    """Parameters for anomaly detection."""
    data: List[Dict] = Field(..., description="Data to analyze for anomalies")
    method: str = Field("statistical", description="Detection method: statistical, clustering")
    sensitivity: float = Field(2.0, description="Sensitivity threshold (std deviations)")


async def analyze_temporal_patterns(
    params: TemporalAnalysisParams
) -> Dict[str, Any]:
    """
    Analyze temporal patterns in time series data.
    
    Identifies:
    - Hourly/daily/weekly patterns
    - Peak periods
    - Trend analysis
    - Clustering of events
    """
    # Extract parameters from Pydantic model
    data = params.data
    time_column = params.time_column
    value_columns = params.value_columns
    group_by = params.group_by
    aggregation = params.aggregation
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            return {
                'success': False,
                'error': 'No data provided'
            }
        
        # Convert timestamp column
        if time_column in df.columns:
            df[time_column] = pd.to_datetime(df[time_column])
        else:
            return {
                'success': False,
                'error': f'Time column {time_column} not found'
            }
        
        # Extract time components
        df['hour'] = df[time_column].dt.hour
        df['day_of_week'] = df[time_column].dt.dayofweek
        df['day_name'] = df[time_column].dt.day_name()
        df['date'] = df[time_column].dt.date
        
        results = {
            'success': True,
            'patterns': {},
            'insights': []
        }
        
        # Analyze each value column
        if not value_columns:
            value_columns = [col for col in df.columns 
                           if col not in [time_column, 'hour', 'day_of_week', 'day_name', 'date']]
        
        for col in value_columns:
            if col not in df.columns:
                continue
            
            # Hourly patterns
            hourly = df.groupby('hour')[col].agg(aggregation).round(2)
            peak_hour = hourly.idxmax()
            low_hour = hourly.idxmin()
            
            # Daily patterns
            daily = df.groupby('day_name')[col].agg(aggregation).round(2)
            
            # Trend over time
            daily_trend = df.groupby('date')[col].agg(aggregation)
            
            results['patterns'][col] = {
                'hourly': {
                    'values': hourly.to_dict(),
                    'peak_hour': int(peak_hour),
                    'low_hour': int(low_hour),
                    'peak_value': float(hourly[peak_hour]),
                    'low_value': float(hourly[low_hour])
                },
                'daily': daily.to_dict(),
                'trend_direction': 'increasing' if daily_trend.iloc[-1] > daily_trend.iloc[0] else 'decreasing'
            }
            
            # Generate insights
            if hourly[peak_hour] > hourly.mean() * 1.5:
                results['insights'].append(
                    f"{col} shows significant peak at hour {peak_hour} "
                    f"({hourly[peak_hour]:.1f} vs avg {hourly.mean():.1f})"
                )
        
        # Event clustering analysis
        if 'event' in [col.lower() for col in df.columns]:
            results['clustering'] = _analyze_event_clustering(df, time_column)
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Temporal analysis failed: {str(e)}'
        }


async def calculate_financial_impact(
    params: FinancialImpactParams
) -> Dict[str, Any]:
    """
    Calculate financial impact of performance gaps.
    
    Returns:
    - Current performance value
    - Improvement opportunity
    - Annual financial impact
    - ROI scenarios
    """
    # Extract parameters from Pydantic model
    metric_data = params.metric_data
    benchmark = params.benchmark
    volume_column = params.volume_column
    margin_column = params.margin_column
    time_period_days = params.time_period_days
    
    try:
        df = pd.DataFrame(metric_data)
        
        if df.empty:
            return {
                'success': False,
                'error': 'No data provided'
            }
        
        results = {
            'success': True,
            'current_performance': {},
            'improvement_opportunity': {},
            'financial_impact': {},
            'roi_scenarios': []
        }
        
        # Calculate current performance
        if 'oee_score' in df.columns:
            current_oee = df['oee_score'].mean()
            oee_gap = benchmark - current_oee
            
            results['current_performance']['oee'] = round(current_oee, 1)
            results['current_performance']['benchmark'] = benchmark
            results['current_performance']['gap'] = round(oee_gap, 1)
            
            # Calculate volume impact
            if volume_column in df.columns and margin_column in df.columns:
                current_volume = df[volume_column].sum()
                avg_margin = df[margin_column].mean()
                
                # Calculate potential volume increase
                potential_increase_pct = oee_gap / 100  # OEE gap as percentage
                volume_opportunity = current_volume * potential_increase_pct
                
                # Annualize based on data period
                data_days = (df['timestamp'].max() - df['timestamp'].min()).days if 'timestamp' in df.columns else 1
                annualization_factor = time_period_days / max(data_days, 1)
                
                annual_volume_opportunity = volume_opportunity * annualization_factor
                annual_financial_impact = annual_volume_opportunity * avg_margin
                
                results['improvement_opportunity'] = {
                    'volume_increase': round(annual_volume_opportunity, 0),
                    'percentage_increase': round(potential_increase_pct * 100, 1)
                }
                
                results['financial_impact'] = {
                    'annual_value': round(annual_financial_impact, 0),
                    'monthly_value': round(annual_financial_impact / 12, 0),
                    'daily_value': round(annual_financial_impact / 365, 0)
                }
                
                # ROI scenarios
                for improvement_pct in [0.1, 0.25, 0.5, 0.75, 1.0]:
                    scenario_impact = annual_financial_impact * improvement_pct
                    results['roi_scenarios'].append({
                        'improvement_achieved': f"{int(improvement_pct * 100)}%",
                        'oee_improvement': round(oee_gap * improvement_pct, 1),
                        'annual_value': round(scenario_impact, 0),
                        'investment_payback_months': _estimate_payback_months(scenario_impact)
                    })
        
        # Quality impact analysis
        if 'scrap_units' in df.columns and 'good_units' in df.columns:
            total_scrap = df['scrap_units'].sum()
            total_good = df['good_units'].sum()
            scrap_rate = total_scrap / (total_scrap + total_good)
            
            if margin_column in df.columns:
                scrap_cost = total_scrap * df[margin_column].mean() * annualization_factor
                results['financial_impact']['quality_loss'] = round(scrap_cost, 0)
                results['current_performance']['scrap_rate'] = round(scrap_rate * 100, 2)
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Financial calculation failed: {str(e)}'
        }


async def detect_anomalies(
    params: AnomalyDetectionParams
) -> Dict[str, Any]:
    """
    Detect anomalies in operational data.
    
    Methods:
    - Statistical: Based on standard deviation
    - Clustering: Based on density
    """
    # Extract parameters from Pydantic model
    data = params.data
    method = params.method
    sensitivity = params.sensitivity
    
    try:
        df = pd.DataFrame(data)
        
        if df.empty:
            return {
                'success': False,
                'error': 'No data provided'
            }
        
        results = {
            'success': True,
            'anomalies': [],
            'summary': {}
        }
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if method == "statistical":
            for col in numeric_cols:
                if col in df.columns:
                    mean = df[col].mean()
                    std = df[col].std()
                    
                    # Find anomalies
                    lower_bound = mean - (sensitivity * std)
                    upper_bound = mean + (sensitivity * std)
                    
                    anomalies = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                    
                    if not anomalies.empty:
                        results['anomalies'].extend([
                            {
                                'column': col,
                                'index': idx,
                                'value': row[col],
                                'deviation': abs(row[col] - mean) / std,
                                'type': 'high' if row[col] > upper_bound else 'low',
                                'details': row.to_dict()
                            }
                            for idx, row in anomalies.iterrows()
                        ])
            
            results['summary'] = {
                'total_anomalies': len(results['anomalies']),
                'method': method,
                'sensitivity': sensitivity,
                'columns_analyzed': numeric_cols
            }
        
        # Sort anomalies by deviation
        results['anomalies'] = sorted(
            results['anomalies'], 
            key=lambda x: x['deviation'], 
            reverse=True
        )[:20]  # Top 20 anomalies
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Anomaly detection failed: {str(e)}'
        }


def _analyze_event_clustering(df: pd.DataFrame, time_column: str) -> Dict[str, Any]:
    """Analyze clustering of events in time."""
    df_sorted = df.sort_values(time_column)
    
    # Calculate time differences
    df_sorted['time_diff'] = df_sorted[time_column].diff()
    
    # Find clusters (events within 15 minutes)
    cluster_threshold = pd.Timedelta(minutes=15)
    df_sorted['cluster_id'] = (df_sorted['time_diff'] > cluster_threshold).cumsum()
    
    # Analyze clusters
    cluster_sizes = df_sorted.groupby('cluster_id').size()
    
    return {
        'total_clusters': len(cluster_sizes),
        'avg_cluster_size': round(cluster_sizes.mean(), 1),
        'max_cluster_size': int(cluster_sizes.max()),
        'events_in_clusters': int(cluster_sizes[cluster_sizes > 1].sum()),
        'clustering_rate': round(cluster_sizes[cluster_sizes > 1].sum() / len(df) * 100, 1)
    }


def _estimate_payback_months(annual_value: float) -> int:
    """Estimate investment payback period based on value."""
    # Rough estimates based on typical improvement costs
    if annual_value < 50000:
        return 3  # Small improvements
    elif annual_value < 200000:
        return 6  # Medium improvements
    else:
        return 12  # Major improvements


# Create ADK tools
# FunctionTool automatically extracts metadata from the function's docstring
temporal_analysis_tool = FunctionTool(analyze_temporal_patterns)

financial_modeling_tool = FunctionTool(calculate_financial_impact)

anomaly_detection_tool = FunctionTool(detect_anomalies)