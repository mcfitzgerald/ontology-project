# Owlready2 SPARQL Quick Reference

## Critical Rules

### 1. Prefix Usage
```sparql
# WRONG: PREFIX declarations are IGNORED
PREFIX mes: <http://...>  # This will not work

# CORRECT: Use the auto-generated prefix from OWL filename
mes_ontology_populated:hasOEEScore  # Correct for mes_ontology_populated.owl
```

### 2. No Angle Brackets
```sparql
# WRONG: Angle brackets cause errors
?x a <http://example.org/Equipment>  # FAILS

# CORRECT: Use prefixed names
?x a mes_ontology_populated:Equipment
```

### 3. Unsupported Functions
- regex() - Not supported
- str() - Not supported
- BIND() - Not supported
- Complex datetime operations - Not supported
- ISIRI() - Supported and recommended
- Basic comparisons (<, >, =, !=) - Fully supported
- **COUNT() with GROUP BY - Known issue**: Returns IRIs instead of numeric counts

## IRI Filtering Patterns (CRITICAL!)
```sparql
# WRONG - Treating IRI as string
FILTER (?line = "LINE2")  # This will NEVER match!

# CORRECT - Using full IRI
FILTER (?line = mes_ontology_populated:LINE2)

# CORRECT - String matching on IRI ending
FILTER (STRENDS(STR(?line), "LINE2"))

# Example: Get OEE for specific line
# Step 1: Discover lines
SELECT DISTINCT ?line WHERE { 
    ?equipment mes_ontology_populated:belongsToLine ?line 
}

# Step 2: Use discovered IRI in filter
SELECT ?equipment (AVG(?oee) AS ?avgOEE) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER (?line = mes_ontology_populated:LINE2)  # Use actual IRI!
    FILTER(ISIRI(?equipment))
}
GROUP BY ?equipment
```

## Troubleshooting

### Empty Results
1. Verify prefix is exactly: mes_ontology_populated:
2. Add FILTER(ISIRI(?var)) for all entity variables
3. Check property names match exactly (case-sensitive)
4. Ensure no angle brackets in query

### Query Errors
1. Remove all PREFIX declarations
2. Replace <URI> with prefixed names
3. Remove regex(), str(), or BIND() functions
4. Simplify complex expressions

### Common Query Debugging Patterns

**COUNT returns IRI instead of number**: When using COUNT with GROUP BY, Owlready2 may return IRIs. Use the fallback query approach - fetch raw data and aggregate with Python.

**Recommended Pattern for COUNT/GROUP BY**:
```sparql
# Instead of this (returns IRIs):
SELECT ?reason (COUNT(?reason) AS ?count) WHERE {
  ?equipment mes_ontology_populated:logsEvent ?event .
  ?event mes_ontology_populated:hasDowntimeReasonCode ?reason .
} GROUP BY ?reason

# Do this (fetch raw data):
SELECT ?reason WHERE {
  ?equipment mes_ontology_populated:logsEvent ?event .
  ?event mes_ontology_populated:hasDowntimeReasonCode ?reason .
}
# Then aggregate in Python using pandas value_counts() or similar
```

**Variable not found**: Ensure all variables in SELECT are bound in the WHERE clause.

**Complex queries failing**: Build incrementally - start with simple patterns and add complexity step by step.

#### Debugging Strategy
1. Always test with LIMIT 10 first
2. Use SELECT * to see all variables before narrowing
3. Build queries incrementally
4. Check each variable is properly bound
5. Verify IRIs match exactly (case-sensitive)

## Key Points

1. **Prefix**: Always use mes_ontology_populated: (from OWL filename)
2. **No Angle Brackets**: Never use <URI> syntax
3. **FILTER(ISIRI())**: Use for all entity variables
4. **Equipment**: Query concrete types (Filler, Packer, Palletizer)
5. **Unsupported**: No BIND(), regex(), or str() functions
6. **Performance**: Always use LIMIT for large result sets
7. **Optional**: Use OPTIONAL for properties that may not exist

## Quick Checklist

- Using mes_ontology_populated: prefix?
- No angle brackets in query?
- No PREFIX declarations?
- FILTER(ISIRI()) for all entities?
- No regex(), str(), or BIND()?
- LIMIT clause for large results?

## Additional Technical Notes

### Query Formatting Requirements
- **CRITICAL**: Format queries as single-line strings when executing (no newlines)
- Use proper spacing between clauses
- Ensure all brackets are balanced
- Test with simple queries before complex ones

### Large Result Handling
- Results over 10k tokens are automatically cached
- Use `retrieve_cached_result(cache_id)` to access full data
- Summary is provided with key statistics

### Supported Functions
**Working:**
- Basic comparisons: <, >, =, !=
- ISIRI()
- String functions: STRENDS(), CONTAINS() (limited)
- Aggregations: SUM(), AVG(), MIN(), MAX()
- COUNT() (but returns IRIs with GROUP BY - see workaround above)

**Not Supported:**
- regex()
- str() 
- BIND()
- Complex datetime operations
- IN clause for types (use UNION instead)

### Performance Considerations
- Start with LIMIT for exploration
- Use filters to reduce result size
- Aggregate at query level when possible
- Cache prevents redundant executions

### Common Pitfalls to Avoid
- Don't use string matching on properties - use direct predicates
- Don't assume reverse relationships exist in the ontology
- Don't use complex datetime operations
- Don't use BIND() function - not supported
- Always include proper GROUP BY when using aggregations