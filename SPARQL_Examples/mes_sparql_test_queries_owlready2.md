# MES Ontology SPARQL Test Queries - Owlready2 Compatible

This document contains 10 SPARQL queries updated to work with Owlready2's native SPARQL engine.
All angle brackets have been removed and queries simplified for compatibility.

## Important Compatibility Notes

When using Owlready2's native SPARQL engine:
- No angle brackets around URIs
- PREFIX declarations are ignored (use built-in prefixes)
- Complex expressions need simplification
- Datetime arithmetic not supported
- Use FILTER(ISIRI()) to ensure proper type filtering

---

## Query 1: List All Equipment with Types (Basic)

**Purpose**: Get a complete inventory of all equipment in the factory with their types and IDs.

**Original Issues**: Used angle brackets and assumed PREFIX works

```sparql
SELECT ?equipment ?equipmentType ?equipmentID
WHERE {
    ?equipment a ?type .
    ?equipment ?hasType ?equipmentType .
    ?equipment ?hasID ?equipmentID .
    FILTER(ISIRI(?equipment))
    FILTER(regex(str(?type), "Equipment"))
    FILTER(regex(str(?hasType), "hasEquipmentType"))
    FILTER(regex(str(?hasID), "hasEquipmentID"))
}
ORDER BY ?equipmentID
LIMIT 20
```

**Note**: Property names must be discovered through exploration as prefixes don't work as expected.

---

## Query 2: Find Products with Prices (Simplified)

**Purpose**: Find products and their prices, avoiding complex calculations.

```sparql
SELECT ?product ?productName ?salePrice ?standardCost
WHERE {
    ?product a ?type .
    ?product ?nameProp ?productName .
    ?product ?priceProp ?salePrice .
    ?product ?costProp ?standardCost .
    FILTER(ISIRI(?product))
    FILTER(regex(str(?type), "Product"))
    FILTER(?salePrice > 1.0)
}
LIMIT 20
```

**Note**: Profit margin calculation should be done in post-processing, not in SPARQL.

---

## Query 3: Equipment Status Check (Simplified Timestamp)

**Purpose**: Get recent equipment status without complex date filtering.

```sparql
SELECT ?equipment ?equipmentID ?status ?timestamp ?oeeScore
WHERE {
    ?equipment a ?type .
    ?equipment ?hasID ?equipmentID .
    ?equipment ?logsEvent ?event .
    ?event ?hasStatus ?status .
    ?event ?hasTime ?timestamp .
    ?event ?hasOEE ?oeeScore .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
    FILTER(regex(str(?type), "Equipment"))
}
ORDER BY ?equipmentID
LIMIT 50
```

**Note**: Timestamp filtering should be done in post-processing.

---

## Query 4: Count Events by Equipment Type (Basic Aggregation)

**Purpose**: Count events grouped by equipment type using simple aggregation.

```sparql
SELECT ?equipmentType (COUNT(?event) AS ?eventCount)
WHERE {
    ?equipment a ?type .
    ?equipment ?hasType ?equipmentType .
    ?equipment ?logsEvent ?event .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
    FILTER(regex(str(?type), "Equipment"))
}
GROUP BY ?equipmentType
ORDER BY DESC(?eventCount)
LIMIT 10
```

---

## Query 5: Find Equipment Relationships (Simplified)

**Purpose**: Find upstream/downstream relationships between equipment.

```sparql
SELECT ?upstreamEquip ?downstreamEquip
WHERE {
    ?upstreamEquip ?relationship ?downstreamEquip .
    FILTER(ISIRI(?upstreamEquip))
    FILTER(ISIRI(?downstreamEquip))
    FILTER(regex(str(?relationship), "isUpstreamOf"))
}
LIMIT 50
```

**Note**: OEE comparison and timestamp matching should be done in post-processing.

---

## Query 6: Production Events Analysis (Simplified)

**Purpose**: Find production events with basic filtering.

```sparql
SELECT ?equipment ?event ?goodUnits ?scrapUnits ?qualityScore
WHERE {
    ?equipment a ?equipType .
    ?equipment ?logsEvent ?event .
    ?event a ?eventType .
    ?event ?hasGood ?goodUnits .
    ?event ?hasScrap ?scrapUnits .
    ?event ?hasQuality ?qualityScore .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
    FILTER(regex(str(?eventType), "ProductionLog"))
    FILTER(?qualityScore < 98.0)
}
LIMIT 100
```

**Note**: Scrap rate calculations should be done in post-processing.

---

## Query 7: Equipment Chain Query (Simple Path)

**Purpose**: Find equipment connected through relationships.

```sparql
SELECT ?equipment1 ?equipment2 ?equipment3
WHERE {
    ?equipment1 a ?type1 .
    ?equipment2 a ?type2 .
    ?equipment3 a ?type3 .
    ?equipment1 ?rel1 ?equipment2 .
    ?equipment2 ?rel2 ?equipment3 .
    FILTER(ISIRI(?equipment1) && ISIRI(?equipment2) && ISIRI(?equipment3))
    FILTER(regex(str(?type1), "Filler"))
    FILTER(regex(str(?type3), "Palletizer"))
}
LIMIT 20
```

**Note**: Transitive property paths (*) may not work as expected.

---

## Query 8: Find Downtime Events (Simple Pattern)

**Purpose**: Find downtime events without complex time calculations.

```sparql
SELECT ?equipment ?event ?timestamp ?reason
WHERE {
    ?equipment a ?equipType .
    ?equipment ?logsEvent ?event .
    ?event a ?eventType .
    ?event ?hasTime ?timestamp .
    ?event ?hasReason ?reason .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
    FILTER(regex(str(?eventType), "DowntimeLog"))
}
ORDER BY ?timestamp
LIMIT 100
```

**Note**: Time difference calculations must be done outside SPARQL.

---

## Query 9: Equipment Performance Data (Basic Aggregation)

**Purpose**: Get performance scores with simple grouping.

```sparql
SELECT ?equipment (AVG(?performanceScore) AS ?avgPerformance) (COUNT(?event) AS ?count)
WHERE {
    ?equipment a ?type .
    ?equipment ?logsEvent ?event .
    ?event ?hasPerf ?performanceScore .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
    FILTER(?performanceScore < 90.0)
}
GROUP BY ?equipment
ORDER BY ?avgPerformance
LIMIT 20
```

**Note**: Complex grouping by multiple variables may cause issues.

---

## Query 10: Simple Line Overview (Basic Counts)

**Purpose**: Get basic counts per production line.

```sparql
SELECT ?line (COUNT(DISTINCT ?equipment) AS ?equipmentCount) (COUNT(?event) AS ?eventCount)
WHERE {
    ?equipment ?belongsTo ?line .
    ?equipment ?logsEvent ?event .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?line))
    FILTER(regex(str(?belongsTo), "belongsToLine"))
}
GROUP BY ?line
LIMIT 10
```

**Note**: Complex OPTIONAL patterns should be avoided.

---

## General Query Pattern for Owlready2

The most reliable pattern for Owlready2 queries:

```sparql
SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object .
    FILTER(ISIRI(?subject))
    # Add more filters as needed
}
LIMIT 100
```

Then process results in Python to:
- Filter by specific types
- Calculate derived values
- Handle datetime operations
- Apply complex business logic

## Testing Approach

1. Start with simple triple patterns
2. Add filters incrementally
3. Test with small LIMIT values
4. Move complex logic to Python post-processing
5. Use regex for property matching when prefixes fail