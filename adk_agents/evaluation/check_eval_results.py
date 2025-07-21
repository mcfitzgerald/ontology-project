#!/usr/bin/env python3
"""Check evaluation results to understand what's happening"""
import json

# Sample result from the evaluation
result = {
    "discovery_first": {
        "actual": {
            "tool_uses": [
                {
                    "name": "execute_sparql_query",
                    "args": {"query": "SELECT DISTINCT ?line WHERE { ?equipment mes_ontology_populated:belongsToLine ?line . FILTER(ISIRI(?line)) }"}
                },
                {
                    "name": "execute_sparql_query", 
                    "args": {"query": "SELECT ?equipment ?reason WHERE { ?equipment mes_ontology_populated:logsEvent ?event . ?event a mes_ontology_populated:DowntimeLog . ?event mes_ontology_populated:hasDowntimeReasonCode ?reason . FILTER(ISIRI(?equipment)) FILTER(ISIRI(?event)) }"}
                }
            ],
            "final_response": None
        },
        "expected": {
            "tool_uses": [
                {
                    "name": "execute_sparql_query",
                    "args": {"query": "SELECT DISTINCT ?line WHERE { ?line a mes_ontology_populated:Line } ORDER BY ?line"}
                },
                {
                    "name": "execute_sparql_query",
                    "args": {"query": "SELECT ?equipment ?line WHERE { ?equipment mes_ontology_populated:belongsToLine ?line . FILTER(ISIRI(?equipment) && ISIRI(?line)) } ORDER BY ?line ?equipment"}
                },
                {
                    "name": "execute_sparql_query", 
                    "args": {"query": "SELECT ?equipment ?line ?event ?timestamp WHERE { ?equipment mes_ontology_populated:belongsToLine ?line . ?equipment mes_ontology_populated:logsEvent ?event . ?event a mes_ontology_populated:DowntimeLog . ?event mes_ontology_populated:hasTimestamp ?timestamp . FILTER(ISIRI(?equipment) && ISIRI(?line)) } ORDER BY ?line ?timestamp LIMIT 50"}
                }
            ],
            "final_response": "I'll analyze downtime trends across your production lines. Let me start by discovering what lines and equipment exist in the system, then analyze their downtime patterns."
        }
    }
}

print("ANALYSIS OF EVALUATION RESULTS")
print("=" * 80)
print("\n1. Tool Execution Status:")
print("   - Agent IS executing tools ✅")
print("   - Agent executed 2 SPARQL queries")
print("   - BUT: final_response is null, suggesting an error occurred")

print("\n2. Discovery Pattern Comparison:")
print("   Expected first query:")
print("   - SELECT DISTINCT ?line WHERE { ?line a mes_ontology_populated:Line }")
print("   Actual first query:")  
print("   - SELECT DISTINCT ?line WHERE { ?equipment mes_ontology_populated:belongsToLine ?line }")
print("   Issue: Different discovery approach")

print("\n3. Key Issues:")
print("   - Agent is not following the exact pattern expected")
print("   - Agent appears to be erroring out (no final response)")
print("   - Need to check logs for the actual error")

print("\n4. Recommendations:")
print("   - Check agent logs for errors during execution")
print("   - Update test expectations to be more flexible")
print("   - Or update agent prompt to follow exact pattern")