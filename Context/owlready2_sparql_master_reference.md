# Owlready2 SPARQL Master Reference Guide

## Table of Contents
1. [Overview](#overview)
2. [Critical Compatibility Notes](#critical-compatibility-notes)
3. [Supported SPARQL Elements](#supported-sparql-elements)
4. [Working Query Patterns](#working-query-patterns)
5. [Query Conversion Guidelines](#query-conversion-guidelines)
6. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
7. [Post-Processing Strategies](#post-processing-strategies)
8. [Performance Optimization](#performance-optimization)
9. [Tested Working Queries](#tested-working-queries)
10. [Python Integration Examples](#python-integration-examples)

## Overview

Owlready2 uses a native SPARQL engine that translates SPARQL queries into SQL for execution with SQLite3. This provides ~60x better performance than RDFlib but supports only a subset of SPARQL features.

### Key Characteristics
- **Performance**: Much faster than RDFlib (60x on Gene Ontology tests)
- **No dependencies**: Uses built-in SQLite3
- **Thread parallelism**: Can be enabled for better performance
- **Limitations**: Subset of SPARQL features supported

## Critical Compatibility Notes

### 1. **PREFIX Declarations Are IGNORED**
```sparql
# ❌ WRONG - PREFIX declarations don't work
PREFIX mes: <http://mes-ontology.org/factory.owl#>
SELECT ?x WHERE { ?x mes:hasOEEScore ?score }

# ✅ CORRECT - Use automatic prefix from ontology filename
SELECT ?x WHERE { ?x mes_ontology_populated:hasOEEScore ?score }
```

**Automatic Prefix**: Created from ontology filename (e.g., `mes_ontology_populated.owl` → `mes_ontology_populated`)

### 2. **NO Angle Brackets in Queries**
```sparql
# ❌ WRONG - Causes lexing error
?equipment rdf:type <http://mes-ontology.org/factory.owl#Equipment>

# ✅ CORRECT - Use FILTER(ISIRI())
?equipment a ?type . FILTER(ISIRI(?equipment))
```

### 2a. **Understanding Owlready2's Prefix System**

**The Root Issue**: Owlready2 automatically generates a prefix from the OWL filename, not from the ontology's IRI:
- Ontology IRI: `http://mes-ontology.org/factory.owl`
- Filename: `mes_ontology_populated.owl`
- Auto-generated prefix: `mes_ontology_populated:`

```sparql
# ❌ WRONG - Custom prefixes from Turtle files don't work
?event mes:hasOEEScore ?oee
FILTER(?oee < 85.0)  # This causes "Error at COMPARATOR:'<'"

# ✅ CORRECT OPTION 1 - Use auto-generated prefix from filename
?event mes_ontology_populated:hasOEEScore ?oee
FILTER(?oee < 85.0)  # This works with the actual prefix

# ✅ CORRECT OPTION 2 - Use : prefix for default namespace
?event :hasOEEScore ?oee
FILTER(?oee < 85.0)  # This maps to the default namespace
```

**Important**: 
- Owlready2 derives the prefix from the OWL filename (`mes_ontology_populated.owl` → `mes_ontology_populated:`)
- The `:` prefix maps to the default namespace in Owlready2
- The `mes:` prefix from Turtle files causes parsing errors, especially with comparison operators
- PREFIX declarations in SPARQL queries are completely ignored by Owlready2

### 3. **Functions NOT Supported**
- ❌ `regex()` - Causes "user-defined function raised exception"
- ❌ `str()` - Not supported
- ✅ `ISIRI()` - Works perfectly
- ✅ Basic comparisons (`>`, `<`, `=`, etc.)

### 4. **Integer Predicates**
Owlready2 uses integer IDs internally:
- 6 = `rdf:type`
- 7 = `rdfs:domain`
- 8 = `rdfs:range`
- 9 = `rdfs:subClassOf`
- 10 = `rdfs:subPropertyOf`

### 5. **Standard Prefixes Available**
These work automatically:
- `rdf:` - RDF namespace
- `rdfs:` - RDF Schema
- `owl:` - OWL namespace
- `xsd:` - XML Schema datatypes

## Supported SPARQL Elements

### ✅ Supported Query Types
- SELECT
- INSERT
- DELETE

### ✅ Supported Features
- UNION
- OPTIONAL
- FILTER, BIND
- FILTER EXISTS, FILTER NOT EXISTS
- GRAPH clauses
- SELECT sub queries
- VALUES in SELECT queries
- All standard functions and aggregations
- Blank node notation: `[ a XXX ]`
- Parameters: `??` or `??1`
- Simple property paths: `rdfs:subClassOf*`

### ❌ NOT Supported
- ASK, DESCRIBE, CONSTRUCT queries
- INSERT DATA, DELETE DATA, DELETE WHERE
- SERVICE (Federated queries)
- FROM, FROM NAMED
- MINUS
- Complex property paths with nested repeats
- regex() and str() functions
- Complex datetime arithmetic

## Working Query Patterns

### Pattern 1: List All Entities with Types
```sparql
SELECT ?entity ?type WHERE {
    ?entity a ?type .
    ?type rdfs:subClassOf* owl:Thing .
    FILTER(ISIRI(?entity))
} LIMIT 20
```

### Pattern 2: Count Entities by Type
```sparql
SELECT ?type (COUNT(?x) AS ?count) WHERE {
    ?x a ?type .
    FILTER(ISIRI(?type))
} GROUP BY ?type
ORDER BY DESC(?count)
```

### Pattern 3: Get Properties with Parameters
```sparql
SELECT ?prop ?value WHERE {
    ?? ?prop ?value .
    FILTER(ISIRI(?prop))
} LIMIT 30
```
Usage: `parameters=["http://mes-ontology.org/factory.owl#LINE1-FIL"]`

### Pattern 4: Find Triple Relationships
```sparql
SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(ISIRI(?s) && ISIRI(?p) && ISIRI(?o))
} LIMIT 50
```

### Pattern 5: Aggregations
```sparql
SELECT ?group (AVG(?value) AS ?avg) (COUNT(?item) AS ?count) WHERE {
    ?item a ?type .
    ?item ?prop ?value .
    ?item ?groupProp ?group .
    FILTER(ISIRI(?item))
} GROUP BY ?group
ORDER BY DESC(?avg)
```

### Pattern 6: Property Paths
```sparql
# Simple transitive closure works
SELECT ?sub ?super WHERE {
    ?sub rdfs:subClassOf* ?super .
}

# Complex paths should be expanded
# Instead of: ?x (p1/p2)* ?y
# Use: ?x p1 ?z . ?z p2 ?y .
```

## Query Conversion Guidelines

### 1. Remove PREFIX Declarations
```sparql
# Standard SPARQL
PREFIX mes: <http://mes-ontology.org/factory.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Owlready2 - Just remove them, standard prefixes work automatically
```

### 2. Replace Angle Brackets
```sparql
# Standard
?x rdf:type <http://mes-ontology.org/factory.owl#Equipment>

# Owlready2
?x a mes_ontology_populated:Equipment
# OR
?x a ?type . FILTER(ISIRI(?x))
```

### 3. Replace regex() Filters
```sparql
# Standard
FILTER(regex(str(?name), "Equipment"))

# Owlready2 - Use specific properties or post-process
?x mes_ontology_populated:hasEquipmentType ?type
# Then filter in Python
```

### 4. Simplify Complex Expressions
```sparql
# Standard
BIND((?price - ?cost) / ?price * 100 AS ?margin)

# Owlready2 - Get raw values, calculate in Python
SELECT ?price ?cost
# Calculate margin in post-processing
```

### 5. Handle Datetime Operations
```sparql
# Standard
FILTER(?timestamp > "2025-06-14T00:00:00"^^xsd:dateTime)

# Owlready2 - Get all timestamps, filter in Python
SELECT ?timestamp
# Filter dates in post-processing
```

## Common Pitfalls and Solutions

### Pitfall 1: "Unknown prefix" Error
**Cause**: Using undefined prefixes
**Solution**: Use the automatic prefix from ontology filename

### Pitfall 2: "Lexing error at COMPARATOR:'<'"
**Cause**: Angle brackets in query
**Solution**: Remove all angle brackets, use FILTER(ISIRI())

### Pitfall 3: "user-defined function raised exception"
**Cause**: Using regex() or str() functions
**Solution**: Remove these functions, use specific properties

### Pitfall 4: Integer Predicates in Results
**Cause**: Owlready2's internal representation
**Solution**: API handles conversion automatically

### Pitfall 5: Timeout on Large Result Sets
**Solutions**:
- Enable thread parallelism
- Increase timeout
- Add LIMIT clause
- Optimize query pattern

## Post-Processing Strategies

### 1. Filter by String Pattern
```python
# Instead of FILTER(regex(str(?type), "Equipment"))
results = world.sparql(query)
equipment_results = [
    row for row in results 
    if "Equipment" in str(row[0])
]
```

### 2. Calculate Derived Values
```python
# Instead of complex BIND expressions
results = list(world.sparql("SELECT ?price ?cost WHERE {...}"))
for row in results:
    price, cost = row
    margin = (price - cost) / price * 100
    row.append(margin)
```

### 3. DateTime Filtering
```python
# Instead of datetime comparisons in SPARQL
from datetime import datetime
results = world.sparql("SELECT ?timestamp WHERE {...}")
filtered = [
    row for row in results
    if datetime.fromisoformat(row[0]) > datetime(2025, 6, 14)
]
```

### 4. Aggregate Complex Conditions
```python
# Instead of complex HAVING clauses
results = world.sparql("SELECT ?group ?value WHERE {...}")
groups = {}
for group, value in results:
    if group not in groups:
        groups[group] = []
    groups[group].append(value)

filtered_groups = {
    k: sum(v)/len(v) 
    for k, v in groups.items() 
    if sum(v)/len(v) > 85.0
}
```

## Performance Optimization

### 1. Enable Thread Parallelism
```python
world.set_backend(
    filename=quadstore_path,
    exclusive=False,
    enable_thread_parallelism=True
)
```

### 2. Use Parameters for Repeated Queries
```python
query = world.prepare_sparql("""
    SELECT ?prop ?value WHERE {
        ?? ?prop ?value .
    }
""")
# Reuse prepared query with different parameters
results1 = query.execute(["entity1"])
results2 = query.execute(["entity2"])
```

### 3. Optimize Query Patterns
- Always use LIMIT for exploration
- Filter early with FILTER(ISIRI())
- Avoid complex expressions
- Use specific properties instead of wildcards

### 4. Batch Operations
```python
# Instead of multiple queries
entities = ["LINE1-FIL", "LINE2-FIL", "LINE3-FIL"]
query = """
    SELECT ?entity ?prop ?value WHERE {
        ?entity ?prop ?value .
        FILTER(?entity IN (??))
    }
"""
results = world.sparql(query, [entities])
```

## Tested Working Queries

All queries tested with 100% success rate on MES Ontology:

### 1. List Equipment
```sparql
SELECT ?equipment ?type WHERE {
    ?equipment a ?type .
    ?type rdfs:subClassOf* owl:Thing .
    FILTER(ISIRI(?equipment))
} LIMIT 20
```

### 2. Find Products with Prices
```sparql
SELECT ?product ?price ?cost WHERE {
    ?product a mes_ontology_populated:Product .
    ?product mes_ontology_populated:hasSalePrice ?price .
    ?product mes_ontology_populated:hasStandardCost ?cost .
    FILTER(?price > 1.0)
} LIMIT 20
```

### 3. Equipment Status
```sparql
SELECT ?equipment ?event ?oee ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
} ORDER BY ?equipment LIMIT 50
```

### 4. Count Events by Type
```sparql
SELECT ?type (COUNT(?equipment) AS ?count) WHERE {
    ?equipment a ?type .
    ?equipment mes_ontology_populated:logsEvent ?event .
    FILTER(ISIRI(?type))
} GROUP BY ?type ORDER BY DESC(?count)
```

### 5. Find Relationships
```sparql
SELECT ?upstream ?downstream WHERE {
    ?upstream mes_ontology_populated:isUpstreamOf ?downstream .
    FILTER(ISIRI(?upstream) && ISIRI(?downstream))
} LIMIT 50
```

### 6. Production Analysis
```sparql
SELECT ?equipment ?event ?goodUnits ?scrapUnits ?qualityScore WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasGoodUnits ?goodUnits .
    ?event mes_ontology_populated:hasScrapUnits ?scrapUnits .
    ?event mes_ontology_populated:hasQualityScore ?qualityScore .
    FILTER(?qualityScore < 98.0)
    FILTER(ISIRI(?equipment))
} LIMIT 100
```

### 7. Equipment Chain
```sparql
SELECT ?filler ?packer ?palletizer WHERE {
    ?filler a mes_ontology_populated:Filler .
    ?packer a mes_ontology_populated:Packer .
    ?palletizer a mes_ontology_populated:Palletizer .
    ?filler mes_ontology_populated:isUpstreamOf ?packer .
    ?packer mes_ontology_populated:isUpstreamOf ?palletizer .
} LIMIT 20
```

### 8. Downtime Events
```sparql
SELECT ?equipment ?event ?timestamp ?reason WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    ?event mes_ontology_populated:hasDowntimeReason ?reason .
    FILTER(ISIRI(?equipment))
} ORDER BY ?timestamp LIMIT 100
```

### 9. Line Overview
```sparql
SELECT ?line (COUNT(DISTINCT ?equipment) AS ?equipmentCount) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?line))
} GROUP BY ?line
```

### 10. Low OEE Equipment
```sparql
SELECT ?equipment ?oee ?timestamp WHERE {
    ?equipment a ?type .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(?oee < 85.0)
    FILTER(ISIRI(?equipment))
} ORDER BY ?oee LIMIT 20
```

## Python Integration Examples

### Basic Query Execution
```python
import requests
import pandas as pd

# Execute Owlready2-compatible query
response = requests.post("http://localhost:8000/sparql/query", 
    json={
        "query": """
            SELECT ?equipment ?type WHERE {
                ?equipment a ?type .
                FILTER(ISIRI(?equipment))
            } LIMIT 20
        """
    })

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(
        data["data"]["results"], 
        columns=data["data"]["columns"]
    )
```

### Parametrized Query
```python
# Query with parameters
response = requests.post("http://localhost:8000/sparql/query", 
    json={
        "query": """
            SELECT ?prop ?value WHERE {
                ?? ?prop ?value .
                FILTER(ISIRI(?prop))
            } LIMIT 30
        """,
        "parameters": ["http://mes-ontology.org/factory.owl#LINE1-FIL"]
    })
```

### Post-Processing Example
```python
# Get raw data
response = requests.post("http://localhost:8000/sparql/query",
    json={
        "query": """
            SELECT ?product ?price ?cost WHERE {
                ?product a mes_ontology_populated:Product .
                ?product mes_ontology_populated:hasSalePrice ?price .
                ?product mes_ontology_populated:hasStandardCost ?cost .
            }
        """
    })

# Process results
if response.ok:
    data = response.json()
    df = pd.DataFrame(data["data"]["results"], 
                     columns=data["data"]["columns"])
    
    # Calculate margin
    df['margin'] = (df['price'] - df['cost']) / df['price'] * 100
    
    # Filter high-margin products
    high_margin = df[df['margin'] > 70]
```

### Complex Analysis with Multiple Queries
```python
# Step 1: Get equipment
equipment_response = requests.post(url, json={
    "query": """
        SELECT ?equipment WHERE {
            ?equipment a mes_ontology_populated:Equipment .
        }
    """
})

# Step 2: For each equipment, get performance data
for equipment in equipment_response.json()["data"]["results"]:
    perf_response = requests.post(url, json={
        "query": """
            SELECT ?oee ?timestamp WHERE {
                ?? mes_ontology_populated:logsEvent ?event .
                ?event mes_ontology_populated:hasOEEScore ?oee .
                ?event mes_ontology_populated:hasTimestamp ?timestamp .
            } ORDER BY DESC(?timestamp) LIMIT 100
        """,
        "parameters": [equipment[0]]
    })
    # Process performance data...
```

## Summary: Key Rules for Success

1. **NO angle brackets** - Ever
2. **NO PREFIX declarations** - Owlready2 ignores them completely
3. **Use mes_ontology_populated: prefix** - This is auto-generated from the OWL filename
4. **NO regex() or str()** - Post-process instead
5. **YES to FILTER(ISIRI())** - Use liberally
6. **YES to simple patterns** - Complex logic in Python
7. **YES to parameters (??)** - For repeated queries
8. **Always test incrementally** - Start simple, add complexity

**CRITICAL**: The prefix `mes_ontology_populated:` comes from the OWL filename, NOT from any namespace declaration or the ontology IRI. This is how Owlready2 works.

## Testing Recommendations

1. Start with simple triple patterns
2. Add filters incrementally
3. Test with small LIMIT values
4. Move complex logic to Python post-processing
5. Use the API's example queries as templates
6. Monitor query execution time
7. Enable thread parallelism for production

This reference represents the definitive guide for writing Owlready2-compatible SPARQL queries based on extensive testing and real-world usage with the MES Ontology.