#!/usr/bin/env python3
"""
Example client for the MES Ontology SPARQL API

Demonstrates how to use the API to query the ontology and work with results.
"""

import requests
import pandas as pd
import json
from typing import Dict, Any, Optional


class MESQueryClient:
    """Client for interacting with the MES Ontology SPARQL API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def query(
        self, 
        sparql: str, 
        parameters: Optional[list] = None,
        timeout: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute a SPARQL query and return results as a pandas DataFrame.
        
        Args:
            sparql: SPARQL query string
            parameters: Optional query parameters
            timeout: Query timeout in seconds
            
        Returns:
            DataFrame with query results
        """
        payload = {
            "query": sparql,
            "parameters": parameters,
            "timeout": timeout
        }
        
        response = self.session.post(
            f"{self.base_url}/sparql/query",
            json=payload
        )
        
        if response.status_code != 200:
            error_data = response.json()
            error = error_data.get("error", {})
            raise Exception(
                f"Query failed: {error.get('message', 'Unknown error')}\n"
                f"Hint: {error.get('hint', 'No hint available')}"
            )
        
        data = response.json()
        
        # Print metadata
        metadata = data["metadata"]
        print(f"Query executed in {metadata['query_time_ms']}ms")
        print(f"Query type: {metadata['query_type']}")
        
        # Check for warnings
        if data.get("warning"):
            print(f"Warning: {data['warning']}")
        
        # Create DataFrame
        df = pd.DataFrame(
            data["data"]["results"],
            columns=data["data"]["columns"]
        )
        
        if data["data"]["truncated"]:
            print(f"Note: Results were truncated")
        
        return df
    
    def get_examples(self) -> list:
        """Get example queries"""
        response = self.session.get(f"{self.base_url}/sparql/examples")
        response.raise_for_status()
        return response.json()["examples"]


def main():
    """Run example queries"""
    
    # Create client
    client = MESQueryClient()
    
    print("=== MES Ontology SPARQL API Example ===\n")
    
    # 1. Health check
    print("1. Checking API health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Ontology loaded: {health['ontology_loaded']}")
    if health.get('ontology_stats'):
        print(f"   Equipment count: {health['ontology_stats'].get('equipment', 0)}")
        print(f"   Total events: {health['ontology_stats'].get('total_events', 0)}")
    print()
    
    # 2. Current OEE by equipment
    print("2. Getting current OEE scores...")
    query = """
        SELECT ?equipment ?oee ?timestamp WHERE {
            ?equipment a :Equipment .
            ?equipment :logsEvent ?event .
            ?event :hasOEEScore ?oee .
            ?event :hasTimestamp ?timestamp .
        } ORDER BY DESC(?timestamp) LIMIT 20
    """
    
    try:
        df_oee = client.query(query)
        print(f"   Found {len(df_oee)} records")
        print("\n   Latest OEE scores:")
        print(df_oee.head())
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # 3. Equipment with low performance
    print("3. Finding equipment with performance issues...")
    query = """
        SELECT DISTINCT ?equipment ?performance ?timestamp WHERE {
            ?equipment a :Equipment .
            ?equipment :logsEvent ?event .
            ?event :hasPerformanceScore ?performance .
            ?event :hasTimestamp ?timestamp .
            FILTER(?performance < 90.0)
        } ORDER BY ?performance LIMIT 10
    """
    
    try:
        df_perf = client.query(query)
        if len(df_perf) > 0:
            print(f"   Found {len(df_perf)} equipment with low performance")
            print("\n   Low performance equipment:")
            print(df_perf)
        else:
            print("   No equipment with performance below 90%")
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # 4. Production summary by product
    print("4. Getting production summary by product...")
    query = """
        SELECT ?product (SUM(?good) as ?total_good) (SUM(?scrap) as ?total_scrap) WHERE {
            ?order :producesProduct ?product .
            ?equipment :executesOrder ?order .
            ?equipment :logsEvent ?event .
            ?event a :ProductionLog .
            ?event :hasGoodUnits ?good .
            ?event :hasScrapUnits ?scrap .
        } GROUP BY ?product
    """
    
    try:
        df_prod = client.query(query)
        print(f"   Production summary:")
        print(df_prod)
        
        # Calculate scrap rate
        if len(df_prod) > 0:
            df_prod['scrap_rate'] = df_prod['total_scrap'] / (df_prod['total_good'] + df_prod['total_scrap']) * 100
            print("\n   Scrap rates:")
            print(df_prod[['product', 'scrap_rate']].round(2))
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # 5. Parametrized query example
    print("5. Using parametrized query for specific equipment...")
    query = """
        SELECT ?timestamp ?status ?oee WHERE {
            ?? :logsEvent ?event .
            ?event :hasTimestamp ?timestamp .
            ?event :hasMachineStatus ?status .
            ?event :hasOEEScore ?oee .
        } ORDER BY DESC(?timestamp) LIMIT 5
    """
    
    try:
        # Query for specific equipment
        equipment_id = "LINE1-FIL"
        df_equip = client.query(query, parameters=[equipment_id])
        print(f"   Recent events for {equipment_id}:")
        print(df_equip)
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # 6. Show available examples
    print("6. Available example queries:")
    try:
        examples = client.get_examples()
        for i, example in enumerate(examples[:3], 1):
            print(f"   {i}. {example['name']}")
            print(f"      {example['description']}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    main()