"""Tests for the Python executor tool."""
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.tools.python_executor import execute_python_code
from adk_agents.tools.result_cache import cache_query_result


class TestPythonExecutor(unittest.TestCase):
    """Test the Python executor functionality."""
    
    def test_basic_execution(self):
        """Test basic Python code execution."""
        code = "result = {'test': 'success', 'value': 42}"
        result = execute_python_code(code)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['result']['test'], 'success')
        self.assertEqual(result['result']['value'], 42)
    
    def test_print_capture(self):
        """Test that print statements are captured."""
        code = """
print("Hello from Python!")
result = {'printed': True}
"""
        result = execute_python_code(code)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn("Hello from Python!", result['output'])
        self.assertEqual(result['result']['printed'], True)
    
    def test_pandas_numpy_available(self):
        """Test that pandas and numpy are available."""
        code = """
import pandas as pd
import numpy as np

df = pd.DataFrame({'a': [1, 2, 3]})
mean_value = np.mean(df['a'])

result = {
    'pandas_version': pd.__version__,
    'numpy_version': np.__version__,
    'mean': float(mean_value)
}
"""
        result = execute_python_code(code)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('pandas_version', result['result'])
        self.assertIn('numpy_version', result['result'])
        self.assertEqual(result['result']['mean'], 2.0)
    
    def test_error_handling(self):
        """Test error handling and recovery."""
        code = "undefined_variable"
        result = execute_python_code(code)
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error_type'], 'NameError')
        self.assertIn("undefined_variable", result['error'])
    
    def test_no_result_variable(self):
        """Test execution without defining result variable."""
        code = "x = 42"
        result = execute_python_code(code)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['result'], {})
    
    @patch('adk_agents.tools.result_cache.get_cached_result')
    def test_with_cached_data(self, mock_get_cached):
        """Test execution with cached data."""
        # Mock cached data
        mock_get_cached.return_value = {
            "data": {
                "results": [
                    {"equipment": "LINE1", "oee": 75},
                    {"equipment": "LINE2", "oee": 82},
                    {"equipment": "LINE3", "oee": 90}
                ]
            }
        }
        
        code = """
df = pd.DataFrame(data)
result = {
    'row_count': len(df),
    'average_oee': df['oee'].mean(),
    'below_benchmark': (df['oee'] < 85).sum()
}
"""
        result = execute_python_code(code, cache_id="test_cache_123")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['result']['row_count'], 3)
        self.assertEqual(result['result']['average_oee'], 82.33333333333333)
        self.assertEqual(result['result']['below_benchmark'], 2)
    
    def test_complex_analysis(self):
        """Test more complex analysis patterns."""
        code = """
# Create sample data
data = [
    {'timestamp': '2024-01-01 10:00', 'value': 100},
    {'timestamp': '2024-01-01 11:00', 'value': 120},
    {'timestamp': '2024-01-01 12:00', 'value': 80},
]

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour

# Analysis
hourly_avg = df.groupby('hour')['value'].mean()
max_hour = hourly_avg.idxmax()

result = {
    'hourly_averages': hourly_avg.to_dict(),
    'peak_hour': int(max_hour),
    'peak_value': float(hourly_avg[max_hour])
}
"""
        result = execute_python_code(code)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['result']['peak_hour'], 11)
        self.assertEqual(result['result']['peak_value'], 120.0)
    
    def test_state_tracking(self):
        """Test state tracking with ToolContext."""
        # Create a simple mock for ToolContext with state
        class MockContext:
            def __init__(self):
                self.state = {}
        
        mock_context = MockContext()
        
        code = "result = {'test': 'success'}"
        result = execute_python_code(code, tool_context=mock_context)
        
        self.assertEqual(result['status'], 'success')
        # Check that state was updated
        self.assertIn('python_analyses', mock_context.state)
        self.assertEqual(len(mock_context.state['python_analyses']), 1)
        self.assertTrue(mock_context.state['python_analyses'][0]['success'])


if __name__ == '__main__':
    unittest.main()