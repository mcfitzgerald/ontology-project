### **Objective**

Manufacturing MES ontology aligned with raw data including inline KPI calculations

### **TBox (The Classes)**

The class hierarchy represents the core manufacturing concepts:

* Process
  * ProductionOrder
* Resource
  * Equipment
    * Filler
    * Packer
    * Palletizer
  * ProductionLine
  * Product
* Event
  * ProductionLog
  * DowntimeLog
* Reason
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
| isUpstreamOf | Equipment | Equipment | Defines material flow direction from upstream to downstream equipment Inverse of isDownstreamOf. |
| isDownstreamOf | Equipment | Equipment | Inverse of isUpstreamOf - defines equipment receiving material flow |
| belongsToLine | Equipment | ProductionLine | Connects equipment to its parent production line Inverse of hasEquipment. |
| hasEquipment | ProductionLine | Equipment | Lists equipment belonging to a production line |
| executesOrder | Equipment | ProductionOrder | Links equipment to the production order it is currently executing |
| producesProduct | ProductionOrder | Product | Specifies which product type a production order produces |
| logsEvent | Equipment | Event | Connects equipment to its time-stamped event log entries |
| hasDowntimeReason | DowntimeLog | DowntimeReason | Links downtime events to their specific reason codes |

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
