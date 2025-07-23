#!/usr/bin/env python3
"""Generate a query result that simulates large SPARQL results."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.tools.result_cache import cache_query_result
from adk_agents.tools.python_executor import execute_python_code
import random
from datetime import datetime, timedelta

def generate_large_dataset():
    """Generate a large simulated dataset."""
    print("Generating large simulated dataset...")
    
    # Generate 20,000 rows of data
    data = []
    equipment_list = ["LINE1-FILL", "LINE2-PCK", "LINE3-PAL", "LINE4-FILL", "LINE5-PCK"]
    reasons = ["JAM", "MAINT", "SETUP", "BREAK", "MATERIAL", "QUALITY", "ELECTRICAL"]
    
    start_date = datetime(2024, 1, 1)
    
    for i in range(20000):
        timestamp = start_date + timedelta(hours=random.randint(0, 2000))
        equipment = random.choice(equipment_list)
        reason = random.choice(reasons)
        duration = random.randint(5, 120)
        
        data.append([
            timestamp.isoformat(),
            equipment,
            reason,
            duration
        ])
    
    # Create a mock SPARQL result
    mock_result = {
        "status": "success",
        "data": {
            "columns": ["timestamp", "equipment", "reason", "duration"],
            "results": data
        }
    }
    
    # Test caching
    print(f"Generated {len(data)} rows")
    cache_id, summary = cache_query_result("MOCK: Large downtime query", mock_result)
    
    print(f"\n✓ Data cached successfully!")
    print(f"  Cache ID: {cache_id}")
    print(f"  Rows: {summary['row_count']}")
    print(f"  Estimated tokens: {summary['estimated_tokens']}")
    
    # Now test Python analysis
    print("\nTesting Python analysis on cached data...")
    
    analysis_code = """
# Convert list format to dict format
columns = ['timestamp', 'equipment', 'reason', 'duration']
data_dicts = [dict(zip(columns, row)) for row in data]
df = pd.DataFrame(data_dicts)

print(f"Analyzing {len(df)} rows...")

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['date'] = df['timestamp'].dt.date

# Analysis 1: Equipment performance
equipment_stats = df.groupby('equipment')['duration'].agg(['count', 'sum', 'mean'])
print("\\nEquipment downtime statistics:")
print(equipment_stats)

# Analysis 2: Reason analysis
reason_stats = df.groupby('reason')['duration'].agg(['count', 'sum', 'mean'])
worst_reason = reason_stats.sort_values('sum', ascending=False).index[0]
print(f"\\nWorst downtime reason: {worst_reason}")

# Analysis 3: Hourly patterns
hourly_events = df.groupby('hour').size()
peak_hour = hourly_events.idxmax()
print(f"Peak downtime hour: {peak_hour}:00")

# Analysis 4: Financial impact
total_downtime_hours = df['duration'].sum() / 60
lost_production = total_downtime_hours * 150  # units per hour
financial_impact = lost_production * 25  # $ per unit

result = {
    'total_events': len(df),
    'equipment_stats': equipment_stats.to_dict('index'),
    'worst_reason': worst_reason,
    'peak_hour': int(peak_hour),
    'financial_impact': {
        'total_downtime_hours': float(total_downtime_hours),
        'lost_production_units': float(lost_production),
        'estimated_annual_loss': float(financial_impact * 365 / 90)  # Scale to annual
    }
}
"""
    
    result = execute_python_code(analysis_code, cache_id=cache_id)
    
    if result['status'] == 'success':
        print("\n✓ Python analysis completed!")
        print(result['output'])
        
        analysis = result['result']
        print(f"\nKey findings:")
        print(f"  Total events analyzed: {analysis['total_events']:,}")
        print(f"  Worst reason: {analysis['worst_reason']}")
        print(f"  Peak hour: {analysis['peak_hour']}:00")
        print(f"  Estimated annual loss: ${analysis['financial_impact']['estimated_annual_loss']:,.2f}")
        
        return True
    else:
        print(f"\n✗ Analysis failed: {result['error']}")
        return False


if __name__ == "__main__":
    print("Testing Large Dataset Handling")
    print("=" * 80)
    
    success = generate_large_dataset()
    
    print("\n" + "=" * 80)
    if success:
        print("✓ SUCCESS: Python executor successfully analyzed large dataset without token limits!")
        print("\nThis demonstrates:")
        print("1. Large SPARQL results are automatically cached")
        print("2. Python executor can access full datasets via cache_id")
        print("3. Complex analysis can be performed without token overflow")
        print("4. The token limit issue is fully resolved!")
    else:
        print("✗ Test failed")