# Owlready2 SPARQL Query Guide for LLM-Generated Business Insights

## Overview
This guide captures best practices for generating Owlready2-compatible SPARQL queries that provide meaningful business insights from the MES ontology. It's designed to be a living document that evolves as we discover new patterns and techniques.

## Core Principles

### 1. Strict Syntax Requirements
- **NO PREFIX declarations** - Owlready2 ignores them completely
- **NO angle brackets** (`< >`) - Causes immediate lexing errors
- **Always use automatic prefix** - Derived from ontology filename (e.g., `mes_ontology_populated:`)
- **Liberal use of FILTER(ISIRI())** - Prevents type errors and improves reliability

### 2. Understanding the Ontology Structure
Before writing queries:
- Review the ontology mindmap (`Context/mes_ontology_mindmap.ttl`) for:
  - Class hierarchies (e.g., `MaterialJam` → `UnplannedDowntime` → `DowntimeReason`)
  - Property domains and ranges
  - Business context annotations
- Identify key relationships:
  - `belongsToLine`: Links equipment to production lines
  - `logsEvent`: Links equipment to events (production, downtime)
  - `hasDowntimeReason`: Links downtime events to specific reasons

### 3. Query Pattern Templates

#### Basic Entity Discovery
```sparql
SELECT ?entity ?type WHERE {
    ?entity a ?type .
    ?type rdfs:subClassOf* owl:Thing .
    FILTER(ISIRI(?entity))
} LIMIT 20
```

#### Downtime Analysis Pattern
```sparql
SELECT ?equipment ?line ?timestamp ?reason WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    ?event mes_ontology_populated:hasDowntimeReason ?reason .
    FILTER(ISIRI(?equipment) && ISIRI(?line))
} ORDER BY ?line ?timestamp LIMIT 100
```

#### Performance Metrics Pattern
```sparql
SELECT ?equipment ?oee ?availability ?performance ?quality ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasAvailabilityScore ?availability .
    ?event mes_ontology_populated:hasPerformanceScore ?performance .
    ?event mes_ontology_populated:hasQualityScore ?quality .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(?oee < 85.0)
    FILTER(ISIRI(?equipment))
} ORDER BY ?oee LIMIT 50
```

#### Equipment Relationship Pattern
```sparql
SELECT ?upstream ?downstream ?line WHERE {
    ?upstream mes_ontology_populated:isUpstreamOf ?downstream .
    ?upstream mes_ontology_populated:belongsToLine ?line .
    FILTER(ISIRI(?upstream) && ISIRI(?downstream) && ISIRI(?line))
} ORDER BY ?line
```

### 4. Handling Aggregations

#### Working Aggregations
- `MIN()` and `MAX()` - Reliable for timestamps and numeric values
- Simple `GROUP BY` clauses

```sparql
SELECT ?equipment ?line (MIN(?timestamp) AS ?firstEvent) (MAX(?timestamp) AS ?lastEvent) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment))
} GROUP BY ?equipment ?line
```

#### Problematic Aggregations
- `COUNT()` often returns URIs instead of numbers
- Complex `HAVING` clauses may fail
- String operations in aggregations

**Solution**: Use post-processing in Python/application layer for complex calculations

### 5. Business Insight Patterns

#### Trend Analysis
Focus on time-based patterns:
```sparql
# Downtime frequency over time
SELECT ?equipment ?date ?reason WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    ?event mes_ontology_populated:hasDowntimeReason ?reason .
    BIND(SUBSTR(?timestamp, 1, 10) AS ?date)
    FILTER(ISIRI(?equipment))
} ORDER BY ?equipment ?date
```

#### Root Cause Analysis
Leverage equipment relationships:
```sparql
# Find cascading failures
SELECT ?upstream ?downstream ?upstreamEvent ?downstreamEvent ?timestamp WHERE {
    ?upstream mes_ontology_populated:isUpstreamOf ?downstream .
    ?upstream mes_ontology_populated:logsEvent ?upstreamEvent .
    ?downstream mes_ontology_populated:logsEvent ?downstreamEvent .
    ?upstreamEvent a mes_ontology_populated:DowntimeLog .
    ?downstreamEvent a mes_ontology_populated:DowntimeLog .
    ?upstreamEvent mes_ontology_populated:hasTimestamp ?timestamp .
    ?downstreamEvent mes_ontology_populated:hasTimestamp ?timestamp .
} LIMIT 50
```

#### Performance Benchmarking
Compare against business thresholds:
```sparql
# Equipment below world-class OEE (85%)
SELECT ?equipment ?oee ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(?oee < 85.0)
    FILTER(ISIRI(?equipment))
} ORDER BY ?oee LIMIT 100
```

### 6. Common Pitfalls and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Angle brackets | "Lexing error at COMPARATOR:'<'" | Remove all `< >`, use prefixes |
| Unknown prefix | "Unknown prefix: 'mes'" | Use `mes_ontology_populated:` |
| regex() function | "user-defined function raised exception" | Post-process in application |
| Complex COUNT | Returns URIs instead of numbers | Use simple patterns or post-process |
| No results | Empty result set | Check class/property names against mindmap |

### 7. Query Optimization Tips

1. **Always use LIMIT** during development
2. **Filter early** with FILTER(ISIRI()) 
3. **Order results** for meaningful analysis
4. **Avoid complex expressions** - calculate in post-processing
5. **Use indexed properties** when possible (timestamps, IDs)

### 8. Business Context Integration

When generating queries, consider:
- **Equipment characteristics** from mindmap (e.g., "LINE2-PCK: 25% micro-stops")
- **Industry standards** (OEE >85% is world-class)
- **Operational patterns** (5-minute logging intervals)
- **Business impact** (downstream effects, production targets)

### 9. Testing Approach

1. Start with simple triple patterns
2. Add one constraint at a time
3. Verify results match business expectations
4. Check against known data patterns in mindmap

### 10. Future Enhancements

Areas to explore:
- [ ] Parametrized queries for repeated analysis
- [ ] Complex event correlation patterns
- [ ] Integration with external data sources
- [ ] Real-time alerting queries
- [ ] Predictive maintenance patterns

## Example Analysis Workflow

1. **Identify business question**: "Which equipment has chronic downtime issues?"
2. **Map to ontology concepts**: Equipment → DowntimeLog → DowntimeReason
3. **Build query incrementally**:
   - Start: Find all downtime events
   - Add: Group by equipment
   - Add: Time range filters
   - Add: Reason categorization
4. **Validate results** against known issues (e.g., LINE2-PCK micro-stops)
5. **Refine for insights**: Add trend analysis, impact assessment

## Query Library

### Production Analysis
```sparql
# High-scrap products
SELECT ?product ?equipment ?scrapUnits ?goodUnits ?qualityScore WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasScrapUnits ?scrapUnits .
    ?event mes_ontology_populated:hasGoodUnits ?goodUnits .
    ?event mes_ontology_populated:hasQualityScore ?qualityScore .
    ?order mes_ontology_populated:producesProduct ?product .
    ?equipment mes_ontology_populated:executesOrder ?order .
    FILTER(?qualityScore < 98.0)
    FILTER(ISIRI(?product) && ISIRI(?equipment))
} LIMIT 100
```

### Line Performance Comparison
```sparql
# Compare lines by equipment count and types
SELECT ?line (COUNT(DISTINCT ?equipment) AS ?equipmentCount) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    FILTER(ISIRI(?equipment) && ISIRI(?line))
} GROUP BY ?line
```

### Maintenance Priority
```sparql
# Equipment with frequent downtime
SELECT ?equipment (MIN(?firstDowntime) AS ?earliest) (MAX(?lastDowntime) AS ?latest) WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    BIND(?timestamp AS ?firstDowntime)
    BIND(?timestamp AS ?lastDowntime)
    FILTER(ISIRI(?equipment))
} GROUP BY ?equipment
ORDER BY ?equipment
```

---

*Last Updated: 2025-07-13*
*Version: 1.0*