"""Integration test for discovery flow with Python analysis."""
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.tools.sparql_tool import execute_sparql
from adk_agents.tools.python_executor import execute_python_code
from adk_agents.tools.result_cache import cache_query_result


class TestDiscoveryFlowWithPython(unittest.TestCase):
    """Test the full discovery flow with Python analysis."""
    
    def test_large_dataset_python_analysis(self):
        """Test the flow: SPARQL query → Large result → Cache → Python analysis."""
        
        # Step 1: Mock a large SPARQL result in list format (as it comes from our API)
        large_result = {
            "status": "success",
            "data": {
                "columns": ["equipment", "timestamp", "oee", "performance", "quality"],
                "results": [
                    [
                        f"LINE{i%3+1}",
                        f"2024-01-{i%30+1:02d} {i%24:02d}:00:00",
                        70 + (i % 20),
                        75 + (i % 15),
                        95 + (i % 5)
                    ]
                    for i in range(1000)  # 1000 rows of data
                ]
            }
        }
        
        # Step 2: Cache the result
        cache_id, summary = cache_query_result("SELECT * FROM large_dataset", large_result)
        self.assertIsNotNone(cache_id)
        self.assertIn("row_count", summary)
        self.assertEqual(summary["row_count"], 1000)
        
        # Step 3: Use Python to analyze the cached data
        # Note: When data comes from cache in list format, we need to convert to dict format
        analysis_code = """
# Convert list format to dict format for easier analysis
if data and isinstance(data[0], list):
    # Data is in list format, need to create dicts
    columns = ['equipment', 'timestamp', 'oee', 'performance', 'quality']
    data_dicts = [dict(zip(columns, row)) for row in data]
    df = pd.DataFrame(data_dicts)
else:
    # Data is already in dict format
    df = pd.DataFrame(data)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['day'] = df['timestamp'].dt.day

# Analysis 1: Equipment performance
equipment_stats = df.groupby('equipment')['oee'].agg(['mean', 'min', 'max', 'count'])

# Analysis 2: Hourly patterns
hourly_avg = df.groupby('hour')['oee'].mean()
peak_hours = hourly_avg.nlargest(3)

# Analysis 3: Below benchmark count
below_benchmark = df[df['oee'] < 85].groupby('equipment').size()

# Analysis 4: Financial impact
units_per_hour = 150
unit_value = 25
hours_below_benchmark = len(df[df['oee'] < 85])
lost_capacity_percent = (85 - df[df['oee'] < 85]['oee'].mean()) / 100
annual_impact = hours_below_benchmark * units_per_hour * unit_value * lost_capacity_percent * 365 / 1000  # Scale for test data

result = {
    'equipment_performance': equipment_stats.to_dict('index'),
    'peak_hours': peak_hours.to_dict(),
    'below_benchmark_counts': below_benchmark.to_dict(),
    'financial_impact': {
        'hours_below_benchmark': hours_below_benchmark,
        'average_gap_to_benchmark': float(85 - df[df['oee'] < 85]['oee'].mean()),
        'estimated_annual_loss': float(annual_impact)
    }
}
"""
        
        result = execute_python_code(analysis_code, cache_id=cache_id)
        
        # Step 4: Verify the analysis results
        self.assertEqual(result['status'], 'success')
        self.assertIn('equipment_performance', result['result'])
        self.assertIn('peak_hours', result['result'])
        self.assertIn('financial_impact', result['result'])
        
        # Check that we found equipment performance stats
        equip_perf = result['result']['equipment_performance']
        self.assertIn('LINE1', equip_perf)
        self.assertIn('mean', equip_perf['LINE1'])
        
        # Check financial impact was calculated
        financial = result['result']['financial_impact']
        self.assertGreater(financial['hours_below_benchmark'], 0)
        self.assertGreater(financial['estimated_annual_loss'], 0)
    
    def test_iterative_python_discovery(self):
        """Test iterative discovery pattern with Python."""
        
        # Mock simple cached data
        with patch('adk_agents.tools.result_cache.get_cached_result') as mock_get:
            mock_get.return_value = {
                "data": {
                    "results": [
                        {"equipment": "LINE1", "downtime_reason": "JAM", "duration": 15},
                        {"equipment": "LINE1", "downtime_reason": "JAM", "duration": 20},
                        {"equipment": "LINE2", "downtime_reason": "MAINT", "duration": 120},
                        {"equipment": "LINE1", "downtime_reason": "JAM", "duration": 10},
                        {"equipment": "LINE3", "downtime_reason": "SETUP", "duration": 45},
                    ]
                }
            }
            
            # Iteration 1: Explore the data
            code_v1 = """
df = pd.DataFrame(data)
print(f"Data shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Unique equipment: {df['equipment'].unique()}")

result = {
    'row_count': len(df),
    'equipment_list': list(df['equipment'].unique()),
    'downtime_reasons': list(df['downtime_reason'].unique())
}
"""
            result1 = execute_python_code(code_v1, cache_id="test_cache")
            self.assertEqual(result1['status'], 'success')
            self.assertIn("Data shape:", result1['output'])
            
            # Iteration 2: Dig deeper based on discovery
            code_v2 = """
df = pd.DataFrame(data)

# Focus on the frequent JAM issues
jam_data = df[df['downtime_reason'] == 'JAM']
jam_by_equipment = jam_data.groupby('equipment').agg({
    'duration': ['count', 'sum', 'mean']
})

# Calculate impact
total_jam_time = jam_data['duration'].sum()
jam_equipment = jam_data['equipment'].value_counts().index[0]

result = {
    'total_jam_events': len(jam_data),
    'total_jam_duration': int(total_jam_time),
    'most_affected_equipment': jam_equipment,
    'jam_frequency': jam_data.groupby('equipment').size().to_dict()
}
"""
            result2 = execute_python_code(code_v2, cache_id="test_cache")
            self.assertEqual(result2['status'], 'success')
            self.assertEqual(result2['result']['total_jam_events'], 3)
            self.assertEqual(result2['result']['most_affected_equipment'], 'LINE1')
    
    def test_error_recovery_pattern(self):
        """Test that errors guide the next iteration."""
        
        # Mock some data first
        with patch('adk_agents.tools.result_cache.get_cached_result') as mock_get:
            mock_get.return_value = {
                "data": {
                    "results": [
                        {"equipment": "LINE1", "value": 100},
                        {"equipment": "LINE2", "value": 200}
                    ]
                }
            }
            
            # First attempt with error
            code_with_error = """
df = pd.DataFrame(data)
# Try to access non-existent column
avg_value = df['nonexistent_column'].mean()
result = {'avg': avg_value}
"""
            
            result = execute_python_code(code_with_error, cache_id="test_cache")
            self.assertEqual(result['status'], 'error')
            self.assertIn('nonexistent_column', result['error'])
            self.assertEqual(result['error_type'], 'KeyError')
        
        # Second attempt, learning from error
        code_fixed = """
# First check what columns exist
result = {'status': 'need_data_structure'}
"""
        
        result2 = execute_python_code(code_fixed)
        self.assertEqual(result2['status'], 'success')
        self.assertEqual(result2['result']['status'], 'need_data_structure')


if __name__ == '__main__':
    unittest.main()