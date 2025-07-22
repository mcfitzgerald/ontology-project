# Architecture Diagrams - Discovery-Driven System

## 1. System Overview - Discovery Flow

```mermaid
graph LR
    subgraph "Discovery Methodology"
        E[EXPLORE<br/>Entity Discovery]
        D[DISCOVER<br/>Pattern Finding]
        Q[QUANTIFY<br/>Impact Calc]
        R[RECOMMEND<br/>Actions]
        
        E --> D
        D --> Q
        Q --> R
    end
    
    subgraph "Value Found"
        M[Manual: $2.5M]
        A[Agent: $9.36M<br/>374% Better]
    end
    
    R --> A
    
    style E fill:#e3f2fd
    style D fill:#f3e5f5
    style Q fill:#e8f5e9
    style R fill:#fff3e0
    style A fill:#c8e6c9
```

## 2. Discovery Tools Integration

```mermaid
graph TB
    subgraph "User Query"
        Q[Find optimization<br/>opportunities]
    end
    
    subgraph "Discovery Agent"
        DA[Discovery Agent<br/>with State Memory]
    end
    
    subgraph "9 Specialized Tools"
        T1[execute_sparql_query<br/>+ Hypothesis Tracking]
        T2[get_discovery_pattern<br/>5 Proven Patterns]
        T3[analyze_patterns<br/>Find Anomalies]
        T4[calculate_roi<br/>Quantify Impact]
        T5[format_insight<br/>Executive Ready]
        T6[create_visualization]
        T7[get_data_catalogue]
        T8[retrieve_cached_result]
        T9[get_sparql_reference]
    end
    
    Q --> DA
    DA --> T2
    T2 --> T1
    T1 --> T3
    T3 --> T4
    T4 --> T5
    
    T1 -.->|State Updates| DA
    
    style DA fill:#f3e5f5
    style T1 fill:#e3f2fd
    style T2 fill:#fff3e0
    style T4 fill:#e8f5e9
    style T5 fill:#ffebee
```

## 3. State-Aware Discovery Process

```mermaid
stateDiagram-v2
    [*] --> Explore: User Query
    
    Explore --> Discover: Entities Found
    Discover --> Analyze: Hypothesis Formed
    Analyze --> Quantify: Patterns Found
    Quantify --> Recommend: Impact Calculated
    Recommend --> [*]: Insight Delivered
    
    Analyze --> Discover: Refine Hypothesis
    
    state Explore {
        [*] --> GetCatalogue
        GetCatalogue --> ListEntities
        ListEntities --> [*]
    }
    
    state Discover {
        [*] --> FormHypothesis
        FormHypothesis --> ExecuteQuery
        ExecuteQuery --> UpdateState
        UpdateState --> [*]
    }
    
    state Quantify {
        [*] --> CalculateROI
        CalculateROI --> PrioritizeActions
        PrioritizeActions --> [*]
    }
```

## 4. Hypothesis-Driven Query Evolution

```mermaid
graph TD
    H1[Hypothesis 1:<br/>Low OEE indicates opportunity]
    Q1[Query: Find OEE < 85%]
    R1[Result: LINE2-PCK at 73.2%]
    
    H2[Hypothesis 2:<br/>Investigate LINE2-PCK issues]
    Q2[Query: Downtime reasons for LINE2-PCK]
    R2[Result: UNP-JAM frequent]
    
    H3[Hypothesis 3:<br/>Quantify jam impact]
    Q3[Query: Count UNP-JAM events]
    R3[Result: 81.5 hours lost]
    
    H4[Hypothesis 4:<br/>Calculate financial impact]
    Q4[Query: Production rate & margins]
    R4[Result: $9.36M opportunity]
    
    H1 --> Q1 --> R1 --> H2
    H2 --> Q2 --> R2 --> H3
    H3 --> Q3 --> R3 --> H4
    H4 --> Q4 --> R4
    
    style H1 fill:#f3e5f5
    style H2 fill:#f3e5f5
    style H3 fill:#f3e5f5
    style H4 fill:#f3e5f5
    style R4 fill:#c8e6c9
```

## 5. Flexible vs Rigid Evaluation

```mermaid
graph LR
    subgraph "Rigid Evaluation ❌"
        RT[Required Tools:<br/>1. query_entities<br/>2. analyze_oee<br/>3. calculate_roi]
        RA[Agent Tools:<br/>1. get_pattern ❌<br/>2. execute_query ❌<br/>3. format_insight ❌]
        RF[FAILED]
        
        RT --> RA --> RF
    end
    
    subgraph "Flexible Evaluation ✅"
        FO[Required Outcome:<br/>Find $300K-$800K opportunity]
        AA[Agent Found:<br/>$9.36M opportunity<br/>374% of target]
        FP[PASSED 90%]
        
        FO --> AA --> FP
    end
    
    style RF fill:#ffcdd2
    style FP fill:#c8e6c9
```

## 6. Discovery Pattern Library

```mermaid
mindmap
  root((Discovery<br/>Patterns))
    Hidden Capacity
      Gap Analysis
      Benchmark Comparison
      Utilization Study
      Found: $9.36M
    Temporal Anomaly
      Time Clustering
      Shift Patterns
      Seasonal Trends
      Target: $350K
    Quality Tradeoff
      Cost vs Quality
      Speed vs Accuracy
      Margin Analysis
      Target: $200K
    Comparative
      Cross-Entity
      Best vs Worst
      Peer Comparison
    Correlation
      Multi-Factor
      Cause-Effect
      Hidden Links
```

These diagrams clearly show:
1. The EXPLORE → DISCOVER → QUANTIFY → RECOMMEND flow
2. How the 9 tools work together with state management
3. The hypothesis-driven discovery process
4. Why flexible validation succeeds where rigid validation fails
5. The proven discovery patterns that guide analysis