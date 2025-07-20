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

## Essential Query Patterns

### 0. Discovery Pattern (ALWAYS START HERE!)
```sparql
# First discover what lines exist
SELECT DISTINCT ?line WHERE { 
    ?equipment mes_ontology_populated:belongsToLine ?line 
}

# First discover what equipment exists
SELECT DISTINCT ?equipment WHERE {
    { ?equipment a mes_ontology_populated:Filler } UNION
    { ?equipment a mes_ontology_populated:Packer } UNION
    { ?equipment a mes_ontology_populated:Palletizer }
}

# First discover what types exist
SELECT DISTINCT ?type WHERE { 
    ?entity a ?type .
    FILTER(ISIRI(?type))
}
```

### 1. Query Equipment (Concrete Types)
```sparql
# Equipment is abstract - query its concrete subclasses
SELECT ?equipment WHERE {
    { ?equipment a mes_ontology_populated:Filler } UNION
    { ?equipment a mes_ontology_populated:Packer } UNION
    { ?equipment a mes_ontology_populated:Palletizer }
    FILTER(ISIRI(?equipment))
}
```

### 2. Get Properties
```sparql
SELECT ?property ?value WHERE {
    mes_ontology_populated:LINE1-FIL ?property ?value .
    FILTER(ISIRI(?property))
}
```

### 3. Filter Numeric Values
```sparql
SELECT ?equipment ?oee WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(?oee < 85.0)
    FILTER(ISIRI(?equipment))
}
```

### 4. Aggregations
```sparql
SELECT ?equipment (AVG(?oee) AS ?avgOEE) WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
}
GROUP BY ?equipment
```

### 5. Time Series
```sparql
SELECT ?equipment ?oee ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment))
}
ORDER BY ?timestamp
LIMIT 100
```

### 6. Relationships
```sparql
SELECT ?upstream ?downstream WHERE {
    ?upstream mes_ontology_populated:isUpstreamOf ?downstream .
    FILTER(ISIRI(?upstream) && ISIRI(?downstream))
}
```

### 7. Optional Properties
```sparql
SELECT ?equipment ?id WHERE {
    { ?equipment a mes_ontology_populated:Filler } UNION
    { ?equipment a mes_ontology_populated:Packer } UNION
    { ?equipment a mes_ontology_populated:Palletizer }
    OPTIONAL { ?equipment mes_ontology_populated:hasEquipmentID ?id }
    FILTER(ISIRI(?equipment))
}
```

### 8. Count by Type
```sparql
SELECT ?type (COUNT(?x) AS ?count) WHERE {
    ?x a ?type .
    FILTER(ISIRI(?type))
}
GROUP BY ?type
ORDER BY DESC(?count)
```

### 9. Product Analysis
```sparql
SELECT ?product ?name ?price ?cost WHERE {
    ?product a mes_ontology_populated:Product .
    ?product mes_ontology_populated:hasProductName ?name .
    ?product mes_ontology_populated:hasSalePrice ?price .
    ?product mes_ontology_populated:hasStandardCost ?cost .
}
```

### 10. Downtime Events
```sparql
SELECT ?equipment ?timestamp ?reason WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    OPTIONAL { ?event mes_ontology_populated:hasDowntimeReasonCode ?reason }
    FILTER(ISIRI(?equipment))
} 
ORDER BY DESC(?timestamp) 
LIMIT 100
```

### 11. Production Quality Issues
```sparql
SELECT ?equipment ?goodUnits ?scrapUnits ?qualityScore WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasGoodUnits ?goodUnits .
    ?event mes_ontology_populated:hasScrapUnits ?scrapUnits .
    ?event mes_ontology_populated:hasQualityScore ?qualityScore .
    FILTER(?qualityScore < 98.0)
    FILTER(ISIRI(?equipment))
} 
LIMIT 100
```

### 12. Equipment Chain
```sparql
SELECT ?filler ?packer ?palletizer WHERE {
    ?filler a mes_ontology_populated:Filler .
    ?packer a mes_ontology_populated:Packer .
    ?palletizer a mes_ontology_populated:Palletizer .
    ?filler mes_ontology_populated:isUpstreamOf ?packer .
    ?packer mes_ontology_populated:isUpstreamOf ?palletizer .
} 
LIMIT 20
```

### 13. IRI Filtering Patterns (CRITICAL!)
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

#### Problem: COUNT returns IRI instead of number
```sparql
# WRONG - May return IRI in some contexts
SELECT (COUNT(?event) AS ?count) WHERE { ... }

# CORRECT - Ensure proper aggregation
SELECT (COUNT(DISTINCT ?event) AS ?count) WHERE { ... }
```

#### Problem: Variable not found error
```sparql
# WRONG - ?timestamp not bound in WHERE clause
SELECT ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
}

# CORRECT - Bind the variable in WHERE clause
SELECT ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
}
```

#### Problem: Complex queries failing
```sparql
# Start simple and test incrementally
# Step 1: Test basic pattern
SELECT * WHERE {
    ?equipment a mes_ontology_populated:Filler .
} LIMIT 10

# Step 2: Add relationships
SELECT * WHERE {
    ?equipment a mes_ontology_populated:Filler .
    ?equipment mes_ontology_populated:belongsToLine ?line .
} LIMIT 10

# Step 3: Add filters and aggregations only after basic pattern works
```

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