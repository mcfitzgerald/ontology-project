### **Objective**

This document outlines the structure for the manufacturing MES ontology, aligned with the raw data that includes inline KPI calculations. The design focuses on representing the core entities, relationships, and data fields from the mes_data_with_kpis.csv file.

### **TBox (The Classes)**

The class hierarchy represents the core manufacturing concepts:

* **Process**  
  * ProductionOrder  
* **Resource**  
  * Equipment (A general machine)  
    * Filler  
    * Packer  
    * Palletizer  
  * ProductionLine (The container for a set of equipment)  
  * Product (The final SKU being produced)  
* **Event** (A point-in-time happening on the factory floor)  
  * ProductionLog (An event that records production and KPIs)  
  * DowntimeLog (An event that records a machine stoppage)  
* **Reason** (The cause of an event)  
  * DowntimeReason  
    * PlannedDowntime  
      * Changeover (e.g., PLN-CO)  
      * Cleaning (e.g., PLN-CLN)  
      * PreventiveMaintenance (e.g., PLN-PM)  
    * UnplannedDowntime  
      * MechanicalFailure (e.g., UNP-MECH)  
      * MaterialJam (e.g., UNP-JAM)  
      * MaterialStarvation (e.g., UNP-MAT)  
      * ElectricalFailure (e.g., UNP-ELEC)  
      * QualityCheck (e.g., UNP-QC)  
      * OperatorError (e.g., UNP-OPR)  
      * SensorFailure (e.g., UNP-SENS)

### **RBox (The Properties)**

The properties map the raw data fields and relationships between entities.

#### **Object Properties (linking individuals to other individuals)**

| Property Name | Domain | Range | Description & Purpose |
| :---- | :---- | :---- | :---- |
| isUpstreamOf | Equipment | Equipment | Defines process flow. e.g., A Filler isUpstreamOf a Packer. |
| isDownstreamOf | Equipment | Equipment | Inverse of isUpstreamOf. |
| belongsToLine | Equipment | ProductionLine | Connects a specific machine to its parent line. |
| hasEquipment | ProductionLine | Equipment | The inverse of belongsToLine. |
| executesOrder | Equipment | ProductionOrder | Links a machine to the current order. |
| producesProduct | ProductionOrder | Product | Specifies which product an order produces. |
| logsEvent | Equipment | Event | Connects a machine to log entries. |
| hasDowntimeReason | DowntimeLog | DowntimeReason | Explains why a downtime occurred. |

#### **Data Properties (linking individuals to literal values)**

This section maps to every column in mes_data_with_kpis.csv:

| Property Name | Domain | Range | Maps to Raw Data Column |
| :---- | :---- | :---- | :---- |
| hasTimestamp | Event | string | Timestamp |
| hasOrderID | ProductionOrder | string | ProductionOrderID |
| hasLineID | ProductionLine | integer | LineID |
| hasEquipmentID | Equipment | string | EquipmentID |
| hasEquipmentType | Equipment | string | EquipmentType |
| hasProductID | Product | string | ProductID |
| hasProductName | Product | string | ProductName |
| hasMachineStatus | Event | string | MachineStatus |
| hasDowntimeReasonCode | DowntimeLog | string | DowntimeReason |
| hasGoodUnits | ProductionLog | integer | GoodUnitsProduced |
| hasScrapUnits | ProductionLog | integer | ScrapUnitsProduced |
| hasTargetRate | Product | float | TargetRate_units_per_5min |
| hasStandardCost | Product | float | StandardCost_per_unit |
| hasSalePrice | Product | float | SalePrice_per_unit |
| hasAvailabilityScore | Event | float | Availability_Score |
| hasPerformanceScore | Event | float | Performance_Score |
| hasQualityScore | Event | float | Quality_Score |
| hasOEEScore | Event | float | OEE_Score |

### **Implementation Notes**

1. **KPIs are now data properties of Events**: Since KPIs are pre-calculated in the raw data, they are simple data properties rather than separate metric individuals.

2. **Process Flow Relationships**: The isUpstreamOf/isDownstreamOf relationships must be established based on the configuration during ontology population.

3. **Event Classification**: Events are classified as either ProductionLog (when MachineStatus = "Running") or DowntimeLog (when MachineStatus = "Stopped").

### **Simplified Ontology Benefits**

This streamlined ontology:
- Directly mirrors the raw data structure
- Eliminates the need for KPI calculation in the ontology layer
- Provides all metrics readily available for LLM analysis
- Maintains core relationships for semantic reasoning
- Reduces complexity while preserving analytical capability

The LLM can now directly query KPIs and identify patterns without needing to calculate metrics, making the analysis more efficient and scalable.