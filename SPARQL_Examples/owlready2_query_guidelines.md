# Owlready2 SPARQL Query Guidelines

## Key Learnings from API Testing

### 1. **No Angle Brackets**
- ❌ DON'T: `?equipment rdf:type <http://mes-ontology.org/factory.owl#Equipment>`
- ✅ DO: `?equipment a ?type . FILTER(ISIRI(?type))`

### 2. **PREFIX Declarations Don't Work as Expected**
- Owlready2 auto-creates prefixes from ontology names
- The ontology file `mes_ontology_populated.owl` creates prefix `mes_ontology_populated`
- Standard prefixes (rdf, rdfs, owl, xsd) are pre-defined
- Custom PREFIX declarations in queries are ignored

### 3. **Use FILTER(ISIRI()) for Type Checking**
- Essential for filtering out literals and blank nodes
- Combine multiple conditions: `FILTER(ISIRI(?s) && ISIRI(?p) && ISIRI(?o))`

### 4. **Property Access Patterns**
- Use `?x a ?type` instead of `?x rdf:type ?type`
- The predicate `a` is universally recognized
- For specific types, filter results afterwards

### 5. **Avoid Complex Expressions**
- Datetime arithmetic doesn't work: `xsd:dateTime(?t1) - xsd:dateTime(?t2)`
- Complex calculations in SELECT may fail
- Move calculations to post-processing

### 6. **Simplify Aggregations**
- Basic aggregations work: COUNT, SUM, AVG, MIN, MAX
- HAVING clauses may cause issues
- GROUP BY works but keep it simple

### 7. **Property Paths Have Limitations**
- Simple paths work: `rdfs:subClassOf*`
- Avoid nested paths: `(a/p*)*`
- Avoid sequences in repeats: `(p1/p2)*`

### 8. **Integer Predicates**
Owlready2 uses integer IDs for common predicates:
- 6 = rdf:type
- 7 = rdfs:domain
- 8 = rdfs:range
- 9 = rdfs:subClassOf

### 9. **Important: regex() and str() Functions NOT Supported**
- ❌ DON'T: `FILTER(regex(str(?type), "Equipment"))`
- ✅ DO: Use the patterns that actually work (see below)

### 10. **Working Query Patterns That Actually Work**

#### Pattern 1: Get All Instances of a Type
```sparql
SELECT ?x ?type WHERE {
    ?x a ?type .
    FILTER(ISIRI(?x))
} LIMIT 20
```

#### Pattern 2: Count Entities
```sparql
SELECT ?type (COUNT(?x) AS ?count) WHERE {
    ?x a ?type .
    FILTER(ISIRI(?type))
} GROUP BY ?type
ORDER BY DESC(?count)
```

#### Pattern 3: Get Properties with Parameters
```sparql
SELECT ?prop ?value WHERE {
    ?? ?prop ?value .
    FILTER(ISIRI(?prop))
} LIMIT 30
```

#### Pattern 4: Find Relationships
```sparql
SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(ISIRI(?s) && ISIRI(?p) && ISIRI(?o))
} LIMIT 50
```

### 10. **Query Optimization Tips**
- Always use LIMIT for exploratory queries
- Filter early to reduce result set
- Use parameters (??) for repeated queries
- Test with small limits first

### 11. **Common Pitfalls to Avoid**
- Don't use DESCRIBE, CONSTRUCT, ASK
- Don't use FROM or FROM NAMED
- Don't use SERVICE (federated queries)
- Don't use MINUS operator
- Don't use INSERT DATA or DELETE DATA

### 12. **Error Handling**
- "Unknown prefix" → Use full URIs or rely on auto-prefixes
- "Lexing error" → Check for angle brackets
- "COMPARATOR" errors → Simplify FILTERs
- Serialization errors → Check for Python type objects in results