# MES Ontology SPARQL Query API

A FastAPI-based REST API for executing SPARQL queries against the MES manufacturing ontology using Owlready2's native SPARQL engine.

## Features

- **Async/Await Pattern**: All endpoints are fully async with thread pool management for Owlready2 operations
- **Thread Pool Safety**: Dedicated thread pool prevents blocking the event loop
- **Comprehensive Metadata**: Query results include column names and execution metrics for easy DataFrame construction
- **Error Handling**: Detailed error messages with helpful hints
- **Query Validation**: Lightweight validation that respects Owlready2's capabilities
- **Health Monitoring**: Health check endpoint with ontology statistics

## Installation

1. Install dependencies:
```bash
cd API
pip install -r requirements.txt
```

2. Ensure the ontology is populated:
```bash
cd ..
python Ontology_Generation/mes_ontology_population.py
```

## Running the API

### Basic Usage

```bash
cd API
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Production Usage

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

The API can be configured via environment variables or a `.env` file:

```env
# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Thread Pool Configuration
THREAD_POOL_SIZE=4
QUERY_TIMEOUT=30

# Query Limits
MAX_QUERY_LENGTH=10240
MAX_RESULT_ROWS=10000

# Ontology Path
ONTOLOGY_PATH=/path/to/mes_ontology_populated.owl

# CORS
CORS_ENABLED=true
CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### 1. Health Check
```bash
GET /health
```

Returns the health status of the API and ontology.

### 2. Execute SPARQL Query
```bash
POST /sparql/query
Content-Type: application/json

{
  "query": "SELECT ?equipment ?oee WHERE { ?equipment :hasOEEScore ?oee } LIMIT 10",
  "parameters": null,
  "timeout": 30
}
```

Response format:
```json
{
  "status": "success",
  "data": {
    "columns": ["equipment", "oee"],
    "results": [
      ["http://mes-ontology.org/factory.owl#LINE1-FIL", 99.2],
      ["http://mes-ontology.org/factory.owl#LINE1-PCK", 98.5]
    ],
    "row_count": 2,
    "truncated": false
  },
  "metadata": {
    "query_time_ms": 125,
    "query_type": "select",
    "ontology_version": "1.0.0",
    "timestamp": "2025-07-11T10:30:00Z",
    "prepared_query": false
  }
}
```

### 3. Get Ontology Information
```bash
GET /ontology/info
```

Returns information about the loaded ontology including statistics.

### 4. Get Example Queries
```bash
GET /sparql/examples
```

Returns example SPARQL queries for the MES ontology.

## Client Examples

### Python with Pandas

```python
import requests
import pandas as pd

# Execute query
response = requests.post("http://localhost:8000/sparql/query", 
    json={
        "query": """
            SELECT ?equipment ?oee ?timestamp WHERE {
                ?equipment a :Equipment .
                ?equipment :logsEvent ?event .
                ?event :hasOEEScore ?oee .
                ?event :hasTimestamp ?timestamp .
            } ORDER BY DESC(?timestamp) LIMIT 100
        """
    })

# Check response
if response.status_code == 200:
    data = response.json()
    
    # Create DataFrame
    df = pd.DataFrame(
        data["data"]["results"], 
        columns=data["data"]["columns"]
    )
    
    print(f"Query executed in {data['metadata']['query_time_ms']}ms")
    print(f"Retrieved {data['data']['row_count']} rows")
    print(df.head())
else:
    error = response.json()
    print(f"Error: {error['error']['message']}")
    if error['error'].get('hint'):
        print(f"Hint: {error['error']['hint']}")
```

### Using Parameters

```python
# Query with parameters (for prepared statements)
response = requests.post("http://localhost:8000/sparql/query", 
    json={
        "query": """
            SELECT ?timestamp ?oee WHERE {
                ?? :logsEvent ?event .
                ?event :hasTimestamp ?timestamp .
                ?event :hasOEEScore ?oee .
            } ORDER BY DESC(?timestamp) LIMIT 10
        """,
        "parameters": ["LINE1-FIL"]
    })
```

### JavaScript/TypeScript

```javascript
const response = await fetch('http://localhost:8000/sparql/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'SELECT * WHERE { ?s ?p ?o } LIMIT 10'
  })
});

const data = await response.json();

if (response.ok) {
  console.log(`Found ${data.data.row_count} results`);
  console.log('Columns:', data.data.columns);
  console.log('Results:', data.data.results);
} else {
  console.error('Error:', data.error.message);
}
```

## Supported SPARQL Features

Based on Owlready2's native SPARQL engine, the API supports:

### Supported:
- Query types: SELECT, INSERT, DELETE
- Operators: UNION, OPTIONAL, FILTER, BIND, EXISTS, NOT EXISTS
- Aggregations: COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING
- Property paths: Simple expressions like `rdfs:subClassOf*`
- Parameters: `??` and `??1` style parameters
- Blank nodes: `[ a :Class ]` notation

### Not Supported:
- Query types: ASK, DESCRIBE, CONSTRUCT
- Clauses: FROM, FROM NAMED, SERVICE, MINUS
- Commands: INSERT DATA, DELETE DATA, DELETE WHERE
- Complex property paths with nested repeats

## Error Handling

The API provides detailed error messages with helpful hints:

```json
{
  "status": "error",
  "error": {
    "type": "invalid_sparql",
    "message": "Unknown prefix: 'foaf'",
    "hint": "Check prefix definitions. Owlready2 auto-defines common prefixes (rdf, rdfs, owl, xsd) and ontology prefixes."
  },
  "request_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Performance Tips

1. **Use Prepared Queries**: For repeated queries with different parameters, use parameterized queries
2. **Limit Results**: Always use LIMIT for exploratory queries
3. **Index Consideration**: Owlready2 uses SQLite, so query performance depends on the underlying indices
4. **Thread Pool Size**: Adjust `THREAD_POOL_SIZE` based on your concurrent query load

## Monitoring

The API logs all requests and errors. Configure logging level via `LOG_LEVEL` environment variable.

Key metrics to monitor:
- Query execution time (in response metadata)
- Health check status
- Thread pool utilization
- Error rates by type

## Security Considerations

1. **Input Validation**: Queries are sanitized and length-limited
2. **Timeout Protection**: All queries have configurable timeouts
3. **CORS**: Configure allowed origins for production
4. **Rate Limiting**: Consider adding rate limiting for production use

## Troubleshooting

### Ontology Not Loading
- Check the `ONTOLOGY_PATH` is correct
- Ensure the ontology file exists and is readable
- Check logs for specific error messages

### Slow Queries
- Use LIMIT to restrict result size
- Simplify complex queries
- Check if the query is using efficient patterns
- Increase `QUERY_TIMEOUT` if needed

### Memory Issues
- Reduce `MAX_RESULT_ROWS` to limit memory usage
- Use pagination for large result sets
- Monitor thread pool size

## License

MIT License - See parent project LICENSE file