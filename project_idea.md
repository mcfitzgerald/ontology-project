## Project Summary: An Ontology as a Semantic Layer for MES Data

### Goal:

Our primary goal was to explore how an ontology can serve as a semantic compatibility layer for interacting with complex industrial data, using Large Language Models (LLMs) for context-aware analysis. To achieve this, we needed a safe and realistic testbed. We created a high-fidelity, synthetic Manufacturing Execution System (MES) dataset for a fictional bottling plant, intentionally embedding common operational problems like bottlenecks, equipment failures, and quality issues to serve as a rich sandbox for analysis.

Our primary goal was to explore how an ontology can serve as a semantic compatibility layer for interacting with complex industrial data, potentially using Large Language Models (LLMs). To achieve this, we needed a safe and realistic testbed. We created a high-fidelity, synthetic Manufacturing Execution System (MES) dataset for a fictional bottling plant, intentionally embedding common operational problems like bottlenecks, equipment failures, and quality issues to serve as a rich sandbox for analysis.

### Technical Approach:

We followed a data-first methodology to create the knowledge graph:

1. **System & Data First:** (done) We began by defining a fictional three-line bottling plant and then used a Python script to generate two weeks of minute-by-minute factory data. This synthetic MES dataset was built to conform to a realistic structure and was intentionally embedded with pre-planned anomalies to create a rich sandbox for analysis.
2. **Ontology Design:** (done) With the data structure established, we designed a formal OWL ontology to serve as a semantic model. This involved defining the classes of objects in our factory (the **TBox**, e.g., `Filler`, `ProductionOrder`) and the rich, contextual relationships between them (the **RBox**, e.g., `isUpstreamOf`, `executesOrder`).
3. **Knowledge Graph Creation:** (todo), map the generated data onto the ontology structure, using a Python-based approach with `owlready2` to populate the ontology with individuals and create the final, queryable knowledge graph (the **ABox**).
4. **LLM-powered Analysis:** (todo) use LLMs to form an analysis plan around a natural language business question (input), generate SPARQL queries and retreive data, and then conduct LLM-based analyses and LLM-directed python analyses, and then synthesize and surface actionable insights.

