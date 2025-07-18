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