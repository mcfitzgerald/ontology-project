# SPARQL Query Conversion Examples: Standard to Owlready2

This document shows how to convert standard SPARQL queries to Owlready2-compatible versions.

## Critical Note on Prefixes

**IMPORTANT**: The `mes:` prefix causes parsing errors in Owlready2, especially with comparison operators. Always use the `:` prefix instead:
- ❌ `mes:hasOEEScore` - Causes "Error at COMPARATOR:'<'" 
- ✅ `:hasOEEScore` - Works correctly

The ADK agents automatically convert `mes:` to `:` using the owlready2_adapter.

## Example 1: Basic Type Query

### Standard SPARQL:
```sparql
PREFIX mes: <http://mes-ontology.org/factory.owl#>
SELECT ?equipment 
WHERE {
    ?equipment rdf:type mes:Equipment .
}
```

### Owlready2 Compatible:
```sparql
SELECT ?equipment ?type
WHERE {
    ?equipment a ?type .
    FILTER(ISIRI(?equipment))
    FILTER(regex(str(?type), "Equipment"))
}
```

**Changes Made:**
- Removed PREFIX declaration
- Removed angle brackets
- Used `a` instead of `rdf:type`
- Added FILTER(ISIRI()) for safety
- Used regex to match type name

---

## Example 2: Property Query with PREFIX

### Standard SPARQL:
```sparql
PREFIX mes: <http://mes-ontology.org/factory.owl#>
SELECT ?equipment ?oee
WHERE {
    ?equipment mes:hasOEEScore ?oee .
}
```

### Owlready2 Compatible:
```sparql
SELECT ?equipment ?oee
WHERE {
    ?equipment :hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
}
```

**Changes Made:**
- Removed PREFIX declaration
- Changed `mes:hasOEEScore` to `:hasOEEScore`
- Added FILTER(ISIRI()) for entity variable
- No PREFIX needed

---

## Example 3: Complex Filter with Comparisons

### Standard SPARQL:
```sparql
PREFIX mes: <http://mes-ontology.org/factory.owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?product ?price
WHERE {
    ?product mes:hasSalePrice ?price .
    FILTER(?price > "1.0"^^xsd:decimal)
}
```

### Owlready2 Compatible:
```sparql
SELECT ?product ?price
WHERE {
    ?product :hasSalePrice ?price .
    FILTER(ISIRI(?product))
    FILTER(?price > 1.0)
}
```

**Changes Made:**
- Simplified numeric comparison
- Removed typed literal notation
- Added ISIRI filter

---

## Example 4: Datetime Handling

### Standard SPARQL:
```sparql
PREFIX mes: <http://mes-ontology.org/factory.owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?event ?timestamp
WHERE {
    ?event mes:hasTimestamp ?timestamp .
    FILTER(?timestamp > "2025-06-14T00:00:00"^^xsd:dateTime)
}
```

### Owlready2 Compatible:
```sparql
SELECT ?event ?timestamp
WHERE {
    ?event :hasTimestamp ?timestamp .
    FILTER(ISIRI(?event))
}
# Filter timestamps in Python post-processing
```

**Changes Made:**
- Removed datetime comparison from SPARQL
- Will filter in post-processing
- Simpler query structure

---

## Example 5: Aggregation Query

### Standard SPARQL:
```sparql
PREFIX mes: <http://mes-ontology.org/factory.owl#>
SELECT ?type (AVG(?oee) AS ?avgOEE) (COUNT(*) AS ?count)
WHERE {
    ?equipment rdf:type ?type .
    ?equipment mes:hasOEEScore ?oee .
}
GROUP BY ?type
HAVING (AVG(?oee) > 85.0)
```

### Owlready2 Compatible:
```sparql
SELECT ?type (AVG(?oee) AS ?avgOEE) (COUNT(?equipment) AS ?count)
WHERE {
    ?equipment a ?type .
    ?equipment :hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
}
GROUP BY ?type
ORDER BY ?avgOEE
```

**Changes Made:**
- Removed HAVING clause
- Changed COUNT(*) to COUNT(?equipment)
- Added ORDER BY instead
- Filter results in post-processing

---

## Example 6: Path Queries

### Standard SPARQL:
```sparql
PREFIX mes: <http://mes-ontology.org/factory.owl#>
SELECT ?start ?end
WHERE {
    ?start mes:isUpstreamOf+ ?end .
}
```

### Owlready2 Compatible:
```sparql
SELECT ?start ?middle ?end
WHERE {
    ?start :isUpstreamOf ?middle .
    ?middle :isUpstreamOf ?end .
    FILTER(ISIRI(?start) && ISIRI(?middle) && ISIRI(?end))
}
```

**Changes Made:**
- Expanded property path to explicit triples
- Added intermediate variables
- Used regex for relationship matching

---

## General Conversion Rules

1. **Remove all PREFIX declarations** - They don't work in Owlready2
2. **Remove angle brackets** - Never use `<URI>` syntax
3. **Replace namespace:name with regex matching** - Use `regex(str(?var), "name")`
4. **Add FILTER(ISIRI())** - Ensure you're getting IRIs not literals
5. **Simplify complex expressions** - Move to post-processing
6. **Avoid HAVING clauses** - Use ORDER BY and filter in code
7. **Expand property paths** - Make them explicit
8. **Remove datatype annotations** - Just use simple values
9. **Use `a` for rdf:type** - It's universally recognized
10. **Keep it simple** - Complex SPARQL often fails in Owlready2

## Post-Processing in Python

After getting results from Owlready2:

```python
# Example: Filter by datetime
results = list(world.sparql(query))
filtered_results = [
    row for row in results 
    if row[1] > datetime(2025, 6, 14)  # timestamp column
]

# Example: Calculate derived values
for row in results:
    price = row[2]
    cost = row[3]
    profit_margin = (price - cost) / price * 100
    row.append(profit_margin)

# Example: Filter by HAVING condition
grouped_results = {}
for row in results:
    key = row[0]
    if key not in grouped_results:
        grouped_results[key] = []
    grouped_results[key].append(row[1])

filtered_groups = {
    k: sum(v)/len(v) 
    for k, v in grouped_results.items() 
    if sum(v)/len(v) > 85.0
}
```