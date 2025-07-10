# MES Ontology Project

## An Ontology-Augmented Generation System for Manufacturing Analytics

This project demonstrates how ontologies can serve as a semantic layer between raw manufacturing data and Large Language Models (LLMs), enabling more accurate and contextual analysis of industrial operations. By combining structured knowledge representation with LLM capabilities, we create a "Palantir Lite" system for manufacturing execution system (MES) data.

## 🎯 Project Goals

1. **Semantic Layer for Industrial Data**: Create an ontology that provides semantic context for complex manufacturing data
2. **LLM-Ready Data Pipeline**: Pre-calculate KPIs and structure data for efficient LLM analysis
3. **Hybrid Intelligence**: Combine deterministic validation with flexible LLM reasoning
4. **Realistic Test Environment**: Generate synthetic but realistic manufacturing data with known anomalies

## 🏭 System Overview

We simulate a three-line bottling plant with:
- **3 Production Lines**: Each with Filler → Packer → Palletizer equipment
- **5 Products**: Various beverages with different production characteristics
- **Embedded Anomalies**: Quality issues, equipment failures, micro-stops, and performance bottlenecks
- **Pre-calculated KPIs**: OEE, Availability, Performance, and Quality scores

## 📁 Project Structure

```
ontology-project/
├── Data_Generation/
│   └── mes_data_generation.py      # Generates synthetic MES data with inline KPIs
├── Ontology_Specification/
│   └── Tbox_Rbox.md               # Ontology schema (classes and properties)
├── mes_data_config.json           # Configuration for data generation and ontology
├── mes_ontology_population.py     # Populates ontology from CSV data
├── mes_llm_validation.py          # Validation tool for LLM analysis
├── llm_query_interface.py         # Natural language to SPARQL interface
└── project_idea.md               # Original project concept
```

## 🚀 Quick Start

### 1. Generate Manufacturing Data
```bash
cd Data_Generation
python mes_data_generation.py
```
This creates `mes_data_with_kpis.csv` with 2 weeks of minute-by-minute factory data including:
- Production events with good/scrap units
- Equipment downtime with reasons
- Pre-calculated KPIs (OEE, Availability, Performance, Quality)

### 2. Populate the Ontology
```bash
cd ..
python mes_ontology_population.py
```
This creates `mes_ontology_populated.owl` containing:
- Equipment hierarchy and relationships
- Production orders and products
- Events with embedded KPIs
- Process flow connections (upstream/downstream)

### 3. Validate the Data
```bash
python mes_llm_validation.py
```
This generates `validation_report.json` with:
- Data integrity checks
- KPI validation
- Known pattern detection
- Statistical anomaly detection

### 4. Query with Natural Language (Optional)
```bash
python llm_query_interface.py
```
Demonstrates natural language to SPARQL translation for queries like:
- "What is the current OEE for each line?"
- "Which equipment has the most downtime?"
- "Show quality trends for premium juice"

## 🔧 Configuration

The `mes_data_config.json` file controls:

### Equipment Configuration
- 3 production lines with equipment sequences
- Process flow relationships (upstream/downstream)

### Product Master
- 5 products with target rates, costs, and quality parameters
- Product-specific anomalies (e.g., energy drinks have performance issues on LINE1)

### Anomaly Injection
- **Major Mechanical Failure**: LINE3-FIL fails for 5.5 hours on June 8
- **Frequent Micro-stops**: LINE2-PCK has 5% probability of 1-5 minute stops
- **Quality Issues**: 32oz Premium Juice has elevated scrap rate
- **Performance Bottleneck**: Energy drinks run 75-85% speed on LINE1
- **Changeover Scrap**: Double scrap rate for first hour after changeovers

## 📊 Data Schema

### Raw Data (CSV)
```
Timestamp, EquipmentID, MachineStatus, GoodUnitsProduced, ScrapUnitsProduced,
Availability_Score, Performance_Score, Quality_Score, OEE_Score
```

### Ontology Structure
- **Classes**: Equipment, Product, ProductionOrder, Event (ProductionLog/DowntimeLog)
- **Object Properties**: isUpstreamOf, belongsToLine, executesOrder, logsEvent
- **Data Properties**: hasTimestamp, hasOEEScore, hasGoodUnits, etc.

## 🧠 Ontology-Augmented Generation

This architecture enables:

1. **Grounded Analysis**: LLMs can't hallucinate equipment that doesn't exist
2. **Pre-computed Metrics**: KPIs are readily available, no calculation needed
3. **Semantic Relationships**: Process flow and dependencies are explicit
4. **Validation Framework**: Deterministic checks verify LLM insights

## 🔍 Example Insights

The system can detect:
- Bottlenecks (equipment constraining downstream flow)
- Cascade failures (problems propagating through the line)
- Quality patterns (scrap spikes after changeovers)
- Performance degradation (specific product-line combinations)

## 🛠️ Technical Stack

- **Python 3.8+**: Data generation and processing
- **Owlready2**: OWL ontology management
- **Pandas**: Data manipulation
- **NumPy**: Statistical calculations
- **JSON**: Configuration management

## 📈 Next Steps

1. **LLM Integration**: Connect to GPT-4/Claude for natural language analysis
2. **Real-time Updates**: Stream live data into the ontology
3. **Predictive Analytics**: Use patterns to predict future issues
4. **Visualization**: Add dashboards for insights
5. **Scale Testing**: Expand to larger, more complex manufacturing scenarios

## 🤝 Contributing

This project serves as a template for ontology-augmented manufacturing analytics. Feel free to:
- Add new anomaly patterns
- Extend the ontology schema
- Improve LLM query capabilities
- Test with real manufacturing data

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Inspired by semantic layer approaches in platforms like Palantir Foundry, this project demonstrates how ontologies can bridge the gap between raw industrial data and AI-powered analysis.