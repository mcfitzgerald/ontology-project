# MES Ontology Detailed Reference

Generated: 2025-07-30T19:59:46.588566

This document provides complete details about the MES ontology including business contexts.

## Classes (TBox)

### Process
- **Parent**: None
- **Description**: Manufacturing workflow that transforms raw materials into finished products through defined operations
- **Business Context**: Manufacturing workflow that transforms raw materials into finished products through defined operations.

### ProductionOrder
- **Parent**: Process
- **Description**: Customer-driven manufacturing request
- **Business Context**: Customer-driven manufacturing request specifying product type, quantity, and schedule. Typical duration: 4-12 hours.

### Resource
- **Parent**: None
- **Description**: Assets required for production
- **Business Context**: Assets required for production including equipment, production lines, and product specifications.

### Equipment
- **Parent**: Resource
- **Description**: Physical machines that transform raw materials
- **Business Context**: Physical machines that transform raw materials into finished products. Performance tracked in 5-minute intervals.

### Filler
- **Parent**: Equipment
- **Description**: First stage in bottling line
- **Business Context**: First stage in bottling line. Fills containers with product. Critical for volume accuracy and product quality. Common issues: incorrect fill levels, foaming, contamination.
- **Equipment Type**: Filler

### Packer
- **Parent**: Equipment
- **Description**: Groups individual containers
- **Business Context**: Groups individual containers into cases/multipacks. Common issues: material jams, label misalignment, case damage.
- **Equipment Type**: Packer

### Palletizer
- **Parent**: Equipment
- **Description**: Stacks cases onto pallets
- **Business Context**: Stacks cases onto pallets for shipping. End of production line. Common issues: unstable stacks, stretch wrap failures.
- **Equipment Type**: Palletizer

### ProductionLine
- **Parent**: Resource
- **Description**: Complete set of equipment working together
- **Business Context**: Complete set of equipment working together. Throughput limited by slowest equipment (bottleneck).

### Product
- **Parent**: Resource
- **Description**: Items manufactured for sale
- **Business Context**: Items manufactured for sale. Each has target rates, costs, and quality specifications.

### Event
- **Parent**: None
- **Description**: Time-stamped production occurrence
- **Business Context**: Time-stamped production occurrence captured every 5 minutes. Foundation for all KPI calculations.

### ProductionLog
- **Parent**: Event
- **Description**: 5-minute snapshot when equipment is running
- **Business Context**: 5-minute snapshot of production metrics when equipment is running. Core data for OEE calculation.
- **Condition**: MachineStatus == 'Running'

### DowntimeLog
- **Parent**: Event
- **Description**: Equipment stoppage event
- **Business Context**: Equipment stoppage event with reason code. Critical for availability calculation and improvement initiatives.
- **Condition**: MachineStatus == 'Stopped'

### Reason
- **Parent**: None
- **Description**: Categorized explanation for production events
- **Business Context**: Categorized explanation for production events, especially equipment stoppages. Critical for root cause analysis.

### DowntimeReason
- **Parent**: Reason
- **Description**: Coded explanation for equipment stoppage
- **Business Context**: Coded explanation for equipment stoppage. Primary driver of availability losses in OEE.

### PlannedDowntime
- **Parent**: DowntimeReason
- **Description**: Scheduled production interruptions
- **Business Context**: Scheduled production interruptions. Predictable but still impacts availability score.

### Changeover
- **Parent**: PlannedDowntime
- **Description**: Product switch requiring reconfiguration
- **Business Context**: Product switch requiring equipment reconfiguration. Typical duration: 30-60 minutes. Code: PLN-CO.
- **Code**: PLN-CO

### Cleaning
- **Parent**: PlannedDowntime
- **Description**: Mandatory sanitation cycle
- **Business Context**: Mandatory sanitation cycle every 8 hours for food safety. Duration: 30 minutes. Code: PLN-CLN.
- **Code**: PLN-CLN

### PreventiveMaintenance
- **Parent**: PlannedDowntime
- **Description**: Scheduled equipment service
- **Business Context**: Scheduled equipment service to prevent breakdowns. Weekly/monthly cycles. Code: PLN-PM.
- **Code**: PLN-PM

### UnplannedDowntime
- **Parent**: DowntimeReason
- **Description**: Unexpected production stoppages
- **Business Context**: Unexpected production stoppages. Major focus area for continuous improvement.

### MechanicalFailure
- **Parent**: UnplannedDowntime
- **Description**: Equipment breakdown requiring repair
- **Business Context**: Equipment breakdown requiring repair. Major impact on availability. Can exceed 5 hours. Code: UNP-MECH.
- **Code**: UNP-MECH

### MaterialJam
- **Parent**: UnplannedDowntime
- **Description**: Product blockage in equipment
- **Business Context**: Product blockage in equipment. Most frequent unplanned stop (35% probability on LINE2-PCK). Duration: 0.5-2 minutes. Code: UNP-JAM.
- **Code**: UNP-JAM

### MaterialStarvation
- **Parent**: UnplannedDowntime
- **Description**: Upstream supply shortage
- **Business Context**: Upstream supply shortage. Peak times: 10-12am and 3-5pm. Also caused by cascade failures from upstream equipment after 10-minute delay. Code: UNP-MAT.
- **Code**: UNP-MAT

### ElectricalFailure
- **Parent**: UnplannedDowntime
- **Description**: Power or control system malfunction
- **Business Context**: Power or control system malfunction. Can cascade to entire line. Code: UNP-ELEC.
- **Code**: UNP-ELEC

### QualityCheck
- **Parent**: UnplannedDowntime
- **Description**: Production halt for quality inspection
- **Business Context**: Production halt for quality inspection. Protects brand reputation. Code: UNP-QC.
- **Code**: UNP-QC

### OperatorError
- **Parent**: UnplannedDowntime
- **Description**: Human-caused stoppage
- **Business Context**: Human-caused stoppage. 12% probability on night shift (10pm-6am). Code: UNP-OPR.
- **Code**: UNP-OPR

### SensorFailure
- **Parent**: UnplannedDowntime
- **Description**: Misaligned or faulty sensors
- **Business Context**: Misaligned or faulty sensors. Quick fix but 15% probability on LINE1-FIL. Code: UNP-SENS.
- **Code**: UNP-SENS

## Object Properties (RBox)

### isUpstreamOf
- **Domain**: Equipment
- **Range**: Equipment
- **Description**: Defines process flow direction
- **Business Context**: Material flow direction. Upstream equipment problems cascade downstream after 10-minute delay with 80% probability. Critical for root cause analysis.
- **Inverse Property**: isDownstreamOf

### isDownstreamOf
- **Domain**: Equipment
- **Range**: Equipment
- **Description**: Inverse of isUpstreamOf
- **Business Context**: Inverse material flow. Downstream blockages can starve upstream equipment.

### belongsToLine
- **Domain**: Equipment
- **Range**: ProductionLine
- **Description**: Connects equipment to its parent line
- **Business Context**: Links equipment to its production line. Lines operate independently but share resources.
- **Inverse Property**: hasEquipment

### hasEquipment
- **Domain**: ProductionLine
- **Range**: Equipment
- **Description**: Inverse of belongsToLine
- **Business Context**: Inverse of belongsToLine. Each line has 3 equipment: Filler → Packer → Palletizer.

### executesOrder
- **Domain**: Equipment
- **Range**: ProductionOrder
- **Description**: Links equipment to current order
- **Business Context**: Links equipment to current production order. Equipment can execute multiple orders per day.

### producesProduct
- **Domain**: ProductionOrder
- **Range**: Product
- **Description**: Specifies which product an order produces
- **Business Context**: Links orders to products. Each order produces one product type.

### logsEvent
- **Domain**: Equipment
- **Range**: Event
- **Description**: Connects equipment to log entries
- **Business Context**: Links equipment to its 5-minute event logs. Each equipment generates ~4,000 events over 2 weeks.

### hasDowntimeReason
- **Domain**: DowntimeLog
- **Range**: DowntimeReason
- **Description**: Explains why downtime occurred
- **Business Context**: Links downtime events to specific reason codes. Essential for Pareto analysis.

## Data Properties (RBox)

### hasTimestamp
- **Domain**: Event
- **Range**: string
- **CSV Column**: Timestamp
- **Description**: Event timestamp
- **Data Context**: 5-minute interval timestamp for production events
- **Example Value**: 2025-06-01 00:00:00

### hasOrderID
- **Domain**: ProductionOrder
- **Range**: string
- **CSV Column**: ProductionOrderID
- **Description**: Order identifier
- **Data Context**: Unique identifier for production order

### hasLineID
- **Domain**: ProductionLine
- **Range**: integer
- **CSV Column**: LineID
- **Description**: Line identifier
- **Data Context**: Production line identifier (1-3)

### hasEquipmentID
- **Domain**: Equipment
- **Range**: string
- **CSV Column**: EquipmentID
- **Description**: Equipment identifier
- **Data Context**: Unique equipment identifier (e.g., LINE1-FIL)
- **Example Value**: LINE1-FIL

### hasEquipmentType
- **Domain**: Equipment
- **Range**: string
- **CSV Column**: EquipmentType
- **Description**: Type of equipment
- **Data Context**: Type of equipment (Filler, Packer, Palletizer)

### hasProductID
- **Domain**: Product
- **Range**: string
- **CSV Column**: ProductID
- **Description**: Product SKU
- **Data Context**: Product SKU identifier
- **Example Value**: SKU-1001

### hasProductName
- **Domain**: Product
- **Range**: string
- **CSV Column**: ProductName
- **Description**: Product name
- **Data Context**: Human-readable product name

### hasMachineStatus
- **Domain**: Event
- **Range**: string
- **CSV Column**: MachineStatus
- **Description**: Equipment state
- **Data Context**: Current equipment state (Running/Stopped)

### hasDowntimeReasonCode
- **Domain**: DowntimeLog
- **Range**: string
- **CSV Column**: DowntimeReason
- **Description**: Downtime reason code
- **Data Context**: Reason code for equipment stoppage

### hasGoodUnits
- **Domain**: ProductionLog
- **Range**: integer
- **CSV Column**: GoodUnitsProduced
- **Description**: Good units produced
- **Data Context**: Count of sellable units produced in 5-min interval

### hasScrapUnits
- **Domain**: ProductionLog
- **Range**: integer
- **CSV Column**: ScrapUnitsProduced
- **Description**: Scrap units produced
- **Data Context**: Count of defective units in 5-min interval

### hasTargetRate
- **Domain**: Product
- **Range**: float
- **CSV Column**: TargetRate_units_per_5min
- **Description**: Target production rate
- **Data Context**: Expected production rate per 5-minute interval

### hasStandardCost
- **Domain**: Product
- **Range**: float
- **CSV Column**: StandardCost_per_unit
- **Description**: Manufacturing cost
- **Data Context**: Manufacturing cost per unit

### hasSalePrice
- **Domain**: Product
- **Range**: float
- **CSV Column**: SalePrice_per_unit
- **Description**: Selling price
- **Data Context**: Selling price per unit

### hasAvailabilityScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: Availability_Score
- **Description**: Equipment availability
- **Data Context**: Equipment availability percentage (0-100)
- **Business Context**: % of scheduled time equipment was available. Current average: 69%. Lost to all downtime types including frequent micro-stops.
- **Typical Value**: World-class: >90%, Current avg: 69%

### hasPerformanceScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: Performance_Score
- **Description**: Production speed efficiency
- **Data Context**: Production speed efficiency (0-100)
- **Business Context**: % of ideal cycle time achieved. Current average: 50%. Lost to slow cycles, minor stops, and performance degradation.
- **Typical Value**: World-class: >95%, Current avg: 50%

### hasQualityScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: Quality_Score
- **Description**: Product quality percentage
- **Data Context**: Product quality percentage (0-100)
- **Business Context**: % of total units that are sellable. Current average: 64%. Lost to normal variations (5% probability), startup scrap (first 30 min), and end-of-run degradation (last 2 hours).
- **Typical Value**: World-class: >99%, Current avg: 64%

### hasOEEScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: OEE_Score
- **Description**: Overall Equipment Effectiveness
- **Data Context**: Overall Equipment Effectiveness (0-100)
- **Business Context**: Overall Equipment Effectiveness (0-100%). Current average: 46%. World-class: >85%, Typical: 60-75%. Impacted by micro-stops, quality variations, and cascade failures.
- **Typical Value**: World-class: >85%, Good: 60-75%, Current avg: 46%
- **Calculation Method**: Availability × Performance × Quality

## Entity Contexts

Business contexts for specific equipment and product instances:

### SKU-1001
12oz Sparkling Water - High volume, low margin product. Simple to produce with minimal issues.

### SKU-1002
32oz Premium Juice - High margin product with elevated quality requirements. Shows 6-8% scrap rate due to quality issues.

### SKU-2001
12oz Soda - Standard carbonated beverage. Stable production across all lines.

### SKU-2002
16oz Energy Drink - Complex formulation. Runs 65-80% speed on LINE1 and LINE3 due to foaming issues.

### SKU-3001
8oz Kids Drink - Small format, high speed production. Popular in school channels.

### LINE1-FIL
Filler with sensor calibration issues (15% micro-stops). Night shift operator issues add 12% stops. Prone to 0.5-1.5 minute jams (10% probability).

### LINE2-FIL
Standard filler with typical 10% micro-stop rate. Duration: 0.5-1.5 minutes per stop.

### LINE3-FIL
Older filler prone to failures. Major breakdown on June 8 (2:00-7:30 AM) caused 5.5 hour downtime. Also has 10% micro-stop rate.

### LINE1-PCK
Packer with 12% micro-stop probability. Typical duration: 0.5-2 minutes per jam.

### LINE2-PCK
Packer with chronic micro-stops. 35% chance of 0.5-2 minute jams each period. Top maintenance priority.

### LINE3-PCK
Standard packer with 12% micro-stop rate. Duration: 0.5-2 minutes.

### LINE1-PAL
Palletizer with 8% micro-stop rate. Typical duration: 1-2 minutes for stack adjustments.

### LINE2-PAL
Standard palletizer. 8% micro-stop probability, 1-2 minute duration.

### LINE3-PAL
Palletizer at end of problematic LINE3. 8% micro-stops plus cascade effects from upstream.

### QualityVariation
Normal production experiences 5% probability of minor quality issues per 5-minute interval.

### ChangeoverQuality
First 30 minutes after product changeover shows 2x normal scrap rate due to equipment adjustment.

### EndOfRunQuality
Last 2 hours before changeover experiences 1.5x scrap rate due to material depletion and operator fatigue.

### CascadeFailure
Downstream equipment starves 10 minutes after upstream stoppage. 80% probability of propagation. Major cause of line-wide OEE loss.

### UpstreamDependency
Filler stoppages cascade to Packer then Palletizer. Each stage adds 10-minute buffer before starvation.

## Downtime Code Mappings

- **PLN-CO**: Changeover
- **PLN-CLN**: Cleaning
- **PLN-PM**: PreventiveMaintenance
- **UNP-MECH**: MechanicalFailure
- **UNP-JAM**: MaterialJam
- **UNP-MAT**: MaterialStarvation
- **UNP-ELEC**: ElectricalFailure
- **UNP-QC**: QualityCheck
- **UNP-OPR**: OperatorError
- **UNP-SENS**: SensorFailure
