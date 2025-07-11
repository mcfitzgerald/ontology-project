#!/usr/bin/env python3
"""
Simple test script for the MES Ontology SPARQL API

Run this after starting the API to verify it's working correctly.
"""

import requests
import sys
import time
from typing import Dict, Any


def test_endpoint(name: str, method: str, url: str, json_data: Any = None) -> bool:
    """Test a single endpoint"""
    print(f"\nTesting {name}...")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200:
            print(f"✓ {name} - OK")
            
            # Print some response info
            data = response.json()
            if isinstance(data, dict):
                if "status" in data:
                    print(f"  Status: {data['status']}")
                if "data" in data and "row_count" in data["data"]:
                    print(f"  Rows returned: {data['data']['row_count']}")
                if "metadata" in data and "query_time_ms" in data["metadata"]:
                    print(f"  Query time: {data['metadata']['query_time_ms']}ms")
            
            return True
        else:
            print(f"✗ {name} - Failed (Status: {response.status_code})")
            try:
                error_data = response.json()
                if "error" in error_data:
                    print(f"  Error: {error_data['error']['message']}")
            except:
                print(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ {name} - Failed (Connection error - is the API running?)")
        return False
    except Exception as e:
        print(f"✗ {name} - Failed ({type(e).__name__}: {e})")
        return False


def main():
    """Run all tests"""
    base_url = "http://localhost:8000"
    
    print("=== MES Ontology SPARQL API Tests ===")
    print(f"Testing API at: {base_url}")
    
    # Wait a moment for API to be ready
    print("\nWaiting for API to be ready...")
    time.sleep(2)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Root endpoint
    tests_total += 1
    if test_endpoint("Root endpoint", "GET", f"{base_url}/"):
        tests_passed += 1
    
    # Test 2: Health check
    tests_total += 1
    if test_endpoint("Health check", "GET", f"{base_url}/health"):
        tests_passed += 1
    
    # Test 3: Ontology info
    tests_total += 1
    if test_endpoint("Ontology info", "GET", f"{base_url}/ontology/info"):
        tests_passed += 1
    
    # Test 4: Example queries
    tests_total += 1
    if test_endpoint("Example queries", "GET", f"{base_url}/sparql/examples"):
        tests_passed += 1
    
    # Test 5: Simple SELECT query
    tests_total += 1
    simple_query = {
        "query": "SELECT ?s WHERE { ?s a :Equipment } LIMIT 5"
    }
    if test_endpoint("Simple SELECT query", "POST", f"{base_url}/sparql/query", simple_query):
        tests_passed += 1
    
    # Test 6: Query with aggregation
    tests_total += 1
    agg_query = {
        "query": """
            SELECT (COUNT(?e) as ?count) WHERE { 
                ?e a :Equipment 
            }
        """
    }
    if test_endpoint("Aggregation query", "POST", f"{base_url}/sparql/query", agg_query):
        tests_passed += 1
    
    # Test 7: Invalid query (should fail gracefully)
    tests_total += 1
    invalid_query = {
        "query": "THIS IS NOT VALID SPARQL"
    }
    print("\nTesting invalid query (should fail gracefully)...")
    response = requests.post(f"{base_url}/sparql/query", json=invalid_query)
    if response.status_code == 400:
        print("✓ Invalid query - Correctly rejected")
        error_data = response.json()
        if "error" in error_data:
            print(f"  Error type: {error_data['error']['type']}")
        tests_passed += 1
    else:
        print("✗ Invalid query - Should have been rejected")
    
    # Test 8: Parametrized query
    tests_total += 1
    param_query = {
        "query": "SELECT ?event WHERE { ?? :logsEvent ?event } LIMIT 3",
        "parameters": ["LINE1-FIL"]
    }
    if test_endpoint("Parametrized query", "POST", f"{base_url}/sparql/query", param_query):
        tests_passed += 1
    
    # Test 9: Query with timeout
    tests_total += 1
    timeout_query = {
        "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
        "timeout": 5
    }
    if test_endpoint("Query with timeout", "POST", f"{base_url}/sparql/query", timeout_query):
        tests_passed += 1
    
    # Summary
    print("\n" + "="*50)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✓ All tests passed! The API is working correctly.")
        return 0
    else:
        print(f"\n✗ {tests_total - tests_passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())