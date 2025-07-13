# Summary: Working SPARQL Patterns for Owlready2

Based on extensive testing with the MES Ontology API, here are the SPARQL patterns that **actually work** with Owlready2.

## ✅ Confirmed Working Patterns

### 1. List All Entities with Types
```sparql
SELECT ?equipment ?type WHERE {
    ?equipment a ?type .
    ?type rdfs:subClassOf* owl:Thing .
    FILTER(ISIRI(?equipment))
} LIMIT 20
```

### 2. Count Entity Types
```sparql
SELECT ?type (COUNT(?x) AS ?count) WHERE {
    ?x a ?type .
    FILTER(ISIRI(?type))
} GROUP BY ?type
ORDER BY DESC(?count)
LIMIT 10
```

### 3. Get Properties with Parameters
```sparql
SELECT ?prop ?value WHERE {
    ?? ?prop ?value .
    FILTER(ISIRI(?prop))
} LIMIT 30
```
Usage: Pass parameter like `["http://mes-ontology.org/factory.owl#LINE1-FIL"]`

### 4. Get All Classes
```sparql
SELECT DISTINCT ?class WHERE {
    ?x a ?class .
    ?class a owl:Class .
} LIMIT 20
```

### 5. Find Triple Relationships
```sparql
SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(ISIRI(?s) && ISIRI(?p) && ISIRI(?o))
} LIMIT 50
```

### 6. Find Datatype Properties
```sparql
SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(ISIRI(?s))
    FILTER(ISIRI(?p))
    FILTER(!ISIRI(?o))
} LIMIT 50
```

### 7. Simple Test Query
```sparql
SELECT ?x WHERE {
    ?x a owl:Thing .
} LIMIT 5
```

## ❌ Confirmed NOT Working

1. **regex() function** - Causes "user-defined function raised exception"
2. **str() function** - Not supported
3. **Complex datetime operations** - Use post-processing
4. **PREFIX declarations** - Ignored by Owlready2
5. **Angle brackets** - Cause lexing errors
6. **HAVING clauses** - May cause issues
7. **Complex property paths** - Use simple paths only

## 🔑 Key Success Factors

1. **Use FILTER(ISIRI())** - Essential for avoiding type errors
2. **Keep it simple** - Complex queries often fail
3. **Use parameters (??)** - For repeated queries
4. **Post-process results** - Don't try to do everything in SPARQL
5. **Test incrementally** - Add complexity gradually

## 📊 Real Results from Testing

From our test suite:
- ✅ 13/13 tests passing (100% success rate)
- All 7 example queries work reliably
- Query execution times: 0-2ms for most queries
- Thread parallelism enabled for better performance

## 🎯 Recommended Approach

1. Start with these working patterns
2. Modify incrementally for your needs
3. Test each change
4. Move complex logic to Python
5. Use the API's example queries as templates

## 🐍 Python Post-Processing Example

```python
# Get results from simple query
results = requests.post("http://localhost:8000/sparql/query", 
    json={"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o . FILTER(ISIRI(?s)) } LIMIT 1000"})

# Filter in Python
equipment_results = [
    row for row in results.json()["data"]["results"]
    if "Equipment" in row[0]  # Subject contains "Equipment"
]

# Calculate derived values
for row in equipment_results:
    if "hasOEEScore" in row[1]:  # Predicate
        oee_score = row[2]  # Object
        # Do calculations here
```

This approach is more reliable than trying to force Owlready2 to handle complex SPARQL.