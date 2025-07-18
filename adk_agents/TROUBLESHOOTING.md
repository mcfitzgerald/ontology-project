# ADK Agents Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with the ADK Manufacturing Analytics Agents system. It includes tools for log analysis, performance monitoring, and error recovery.

## Quick Diagnostics

### 1. Analyze Recent Session

```bash
# Parse and analyze the most recent log
python adk_agents/utils/log_analyzer.py adk_web.log

# View detailed analysis
cat adk_web.analysis.json
```

### 2. Check System Status

```bash
# Verify SPARQL API is running
curl http://localhost:8000/health

# Check ADK web UI
curl http://localhost:8001/

# Monitor real-time logs
tail -f adk_web.log | grep -E "ERROR|WARN|429"
```

## Common Issues

### 1. Rate Limit Errors (429 RESOURCE_EXHAUSTED)

**Symptoms:**
- Error: "429 RESOURCE_EXHAUSTED"
- Session terminates unexpectedly
- Multiple queries fail in succession

**Diagnosis:**
```bash
# Check request rate
python adk_agents/utils/log_analyzer.py adk_web.log | grep "Rate Limit"
```

**Solutions:**

1. **Enable Rate Limiting** (Already configured by default)
   ```bash
   # Edit .env file
   RATE_LIMIT_ENABLED=TRUE
   RATE_LIMIT_RPM=48  # 80% of Vertex AI limit
   RATE_LIMIT_THROTTLE_MS=1250
   ```

2. **Reduce Request Frequency**
   - Add delays between queries
   - Batch related queries
   - Use query caching

3. **Monitor Rate Limits**
   ```python
   from adk_agents.utils.rate_limiter import print_rate_limit_stats
   print_rate_limit_stats()
   ```

### 2. SPARQL Query Failures

**Symptoms:**
- Low query success rate (<50%)
- "Unknown prefix" errors
- "Lexing error" messages

**Diagnosis:**
```bash
# Extract failed queries
python -c "
from adk_agents.utils.log_parser import ADKLogParser
from pathlib import Path
parser = ADKLogParser()
sessions = parser.parse_log_file(Path('adk_web.log'))
for s in sessions.values():
    for q in s.sparql_queries:
        if not q.success:
            print(f'Error: {q.error}')
            print(f'Query: {q.query[:100]}...')
            print('---')
"
```

**Common Fixes:**

1. **Prefix Issues**
   ```sparql
   # ❌ WRONG
   ?equipment mes:hasOEEScore ?score
   
   # ✅ CORRECT
   ?equipment mes_ontology_populated:hasOEEScore ?score
   ```

2. **Angle Brackets**
   ```sparql
   # ❌ WRONG
   ?equipment a <http://example.com/Equipment>
   
   # ✅ CORRECT
   ?equipment a mes_ontology_populated:Equipment
   ```

3. **Missing FILTER**
   ```sparql
   # Add for entity variables
   FILTER(ISIRI(?equipment))
   ```

### 3. High Token Usage

**Symptoms:**
- Rapid token consumption
- Context window errors
- Truncated responses

**Diagnosis:**
```bash
# Check token usage
grep "totalTokenCount" adk_web.log | tail -20
```

**Solutions:**

1. **Reduce Context Size**
   - Truncate large query results
   - Limit conversation history
   - Remove redundant context

2. **Configure Result Truncation**
   ```python
   # In log_parser.py
   parser = ADKLogParser(
       max_result_rows=10,  # Limit SPARQL results
       max_content_length=1000  # Truncate long content
   )
   ```

### 4. Memory/Performance Issues

**Symptoms:**
- Slow response times
- High memory usage
- Timeout errors

**Solutions:**

1. **Enable Query Caching**
   - Cached queries execute instantly
   - Reduces API calls

2. **Optimize Queries**
   ```sparql
   # Add LIMIT clauses
   SELECT ?x WHERE {...} LIMIT 100
   
   # Use specific predicates
   ?equipment mes_ontology_populated:hasEquipmentID ?id
   ```

3. **Monitor Performance**
   ```python
   # Track query execution time
   from time import time
   start = time()
   # ... execute query ...
   print(f"Query took {time()-start:.2f}s")
   ```

## Log Analysis Tools

### Parse Logs

```python
from adk_agents.utils.log_parser import ADKLogParser
from pathlib import Path

parser = ADKLogParser()
sessions = parser.parse_log_file(Path('adk_web.log'))

# Get summary
summary = parser.generate_summary(sessions)
print(f"Total requests: {summary['total_requests']}")
print(f"Request rate: {summary['requests_per_minute']:.2f} RPM")
print(f"Query success rate: {summary['query_success_rate']:.1%}")
```

### Analyze Patterns

```python
from adk_agents.utils.log_analyzer import ADKLogAnalyzer

analyzer = ADKLogAnalyzer()
for session in sessions.values():
    analysis = analyzer.analyze_session(session)
    report = analyzer.generate_report(analysis)
    print(report)
```

### Extract Specific Events

```bash
# Find all errors
grep -n "ERROR" adk_web.log

# Extract SPARQL queries
grep -A5 "execute_sparql_query" adk_web.log

# Find rate limit hits
grep "429\|RESOURCE_EXHAUSTED" adk_web.log
```

## Prevention Strategies

### 1. Pre-Flight Checks

Before running analysis:
```bash
# Check API health
curl http://localhost:8000/health

# Verify rate limits configured
grep RATE_LIMIT adk_agents/.env

# Test with simple query
python -m adk_agents.test_simple
```

### 2. Monitoring During Execution

```bash
# Watch for errors in real-time
tail -f adk_web.log | grep -E "ERROR|429|failed"

# Monitor request rate
watch -n 5 'grep "Sending out request" adk_web.log | tail -20 | wc -l'
```

### 3. Post-Analysis Review

```bash
# Generate analysis report
python adk_agents/utils/log_analyzer.py adk_web.log > analysis_report.txt

# Check for warnings
grep "WARNING\|CRITICAL" analysis_report.txt
```

## Configuration Reference

### Environment Variables (.env)

```bash
# Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east1

# Rate Limiting
RATE_LIMIT_ENABLED=TRUE
RATE_LIMIT_RPM=48  # Requests per minute
RATE_LIMIT_THROTTLE_MS=1250  # Min time between requests
RATE_LIMIT_BURST_SIZE=5  # Allow small bursts

# SPARQL Configuration
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30
```

### Key Files

- `adk_web.log` - Main application log
- `adk_web.analysis.json` - Analyzed session data
- `learned_patterns.json` - Cached successful queries
- `query_cache.json` - Query result cache

## Recovery Procedures

### After Rate Limit Hit

1. Wait for quota reset (usually 1 minute)
2. Reduce request rate in configuration
3. Enable more aggressive throttling
4. Consider upgrading API quota

### After Query Failures

1. Review error patterns in analysis
2. Fix common issues (prefixes, brackets)
3. Test queries directly against SPARQL endpoint
4. Update agent prompts if needed

### After System Crash

1. Check last session state in logs
2. Identify error that caused crash
3. Clear corrupted cache files if needed
4. Restart with reduced load

## Getting Help

1. **Check Logs First**
   - Most issues are evident in logs
   - Use analysis tools for patterns

2. **Test Components Individually**
   - SPARQL API: `curl http://localhost:8000/health`
   - ADK Agents: `python -m adk_agents.test_simple`
   - Rate Limiter: `python adk_agents/utils/rate_limiter.py`

3. **Enable Debug Mode**
   - Add debug prints to critical paths
   - Increase log verbosity
   - Save intermediate results

4. **Report Issues**
   - Include relevant log excerpts
   - Provide analysis report
   - Share configuration (remove secrets)

## Best Practices

1. **Always Use Rate Limiting**
   - Prevents service disruption
   - Maintains stable performance
   - Avoids quota exhaustion

2. **Monitor Resource Usage**
   - Track token consumption
   - Watch query complexity
   - Limit result sizes

3. **Regular Maintenance**
   - Clean old logs periodically
   - Update cached patterns
   - Review error trends

4. **Incremental Testing**
   - Start with simple queries
   - Build complexity gradually
   - Test rate limits early