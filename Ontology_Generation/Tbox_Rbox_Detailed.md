# MES Ontology Detailed Reference

Generated: 2025-07-31T20:10:49.971611

This document provides complete details about the MES ontology including business contexts.

## Classes (TBox)

### Process
- **Parent**: None
- **Description**: Manufacturing workflow that transforms raw materials into finished products through defined operations

### ProductionOrder
- **Parent**: Process
- **Description**: Customer-driven manufacturing request specifying product type, quantity, and schedule

### Resource
- **Parent**: None
- **Description**: Assets required for production including equipment, production lines, and product specifications

### Equipment
- **Parent**: Resource
- **Description**: Physical machines that transform raw materials into finished products

### Filler
- **Parent**: Equipment
- **Description**: First stage in bottling line that fills containers with product
- **Equipment Type**: Filler

### Packer
- **Parent**: Equipment
- **Description**: Groups individual containers into cases or multipacks
- **Equipment Type**: Packer

### Palletizer
- **Parent**: Equipment
- **Description**: Stacks cases onto pallets for shipping
- **Equipment Type**: Palletizer

### ProductionLine
- **Parent**: Resource
- **Description**: Complete set of equipment working together in sequence

### Product
- **Parent**: Resource
- **Description**: Items manufactured for sale with defined specifications

### Event
- **Parent**: None
- **Description**: Time-stamped production occurrence captured at regular intervals

### ProductionLog
- **Parent**: Event
- **Description**: Snapshot of production metrics when equipment is running
- **Condition**: MachineStatus == 'Running'

### DowntimeLog
- **Parent**: Event
- **Description**: Equipment stoppage event with associated reason code
- **Condition**: MachineStatus == 'Stopped'

### Reason
- **Parent**: None
- **Description**: Categorized explanation for production events

### DowntimeReason
- **Parent**: Reason
- **Description**: Coded explanation for equipment stoppage

### PlannedDowntime
- **Parent**: DowntimeReason
- **Description**: Scheduled production interruptions

### Changeover
- **Parent**: PlannedDowntime
- **Description**: Product switch requiring equipment reconfiguration
- **Code**: PLN-CO

### Cleaning
- **Parent**: PlannedDowntime
- **Description**: Mandatory sanitation cycle for hygiene and safety
- **Code**: PLN-CLN

### PreventiveMaintenance
- **Parent**: PlannedDowntime
- **Description**: Scheduled equipment service to prevent breakdowns
- **Code**: PLN-PM

### UnplannedDowntime
- **Parent**: DowntimeReason
- **Description**: Unexpected production stoppages

### MechanicalFailure
- **Parent**: UnplannedDowntime
- **Description**: Equipment breakdown requiring repair
- **Code**: UNP-MECH

### MaterialJam
- **Parent**: UnplannedDowntime
- **Description**: Product blockage in equipment causing temporary stoppage
- **Code**: UNP-JAM

### MaterialStarvation
- **Parent**: UnplannedDowntime
- **Description**: Upstream supply shortage preventing equipment operation
- **Code**: UNP-MAT

### ElectricalFailure
- **Parent**: UnplannedDowntime
- **Description**: Power or control system malfunction
- **Code**: UNP-ELEC

### QualityCheck
- **Parent**: UnplannedDowntime
- **Description**: Production halt for quality inspection
- **Code**: UNP-QC

### OperatorError
- **Parent**: UnplannedDowntime
- **Description**: Production stoppage caused by human error or intervention
- **Code**: UNP-OPR

### SensorFailure
- **Parent**: UnplannedDowntime
- **Description**: Misaligned or faulty sensors requiring adjustment
- **Code**: UNP-SENS

## Object Properties (RBox)

### isUpstreamOf
- **Domain**: Equipment
- **Range**: Equipment
- **Description**: Defines material flow direction from upstream to downstream equipment
- **Inverse Property**: isDownstreamOf

### isDownstreamOf
- **Domain**: Equipment
- **Range**: Equipment
- **Description**: Inverse of isUpstreamOf - defines equipment receiving material flow

### belongsToLine
- **Domain**: Equipment
- **Range**: ProductionLine
- **Description**: Connects equipment to its parent production line
- **Inverse Property**: hasEquipment

### hasEquipment
- **Domain**: ProductionLine
- **Range**: Equipment
- **Description**: Lists equipment belonging to a production line

### executesOrder
- **Domain**: Equipment
- **Range**: ProductionOrder
- **Description**: Links equipment to the production order it is currently executing

### producesProduct
- **Domain**: ProductionOrder
- **Range**: Product
- **Description**: Specifies which product type a production order produces

### logsEvent
- **Domain**: Equipment
- **Range**: Event
- **Description**: Connects equipment to its time-stamped event log entries

### hasDowntimeReason
- **Domain**: DowntimeLog
- **Range**: DowntimeReason
- **Description**: Links downtime events to their specific reason codes

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
- **Description**: Percentage of scheduled time equipment was available for production
- **Data Context**: Equipment availability percentage (0-100)
- **Typical Value**: World-class: >90%

### hasPerformanceScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: Performance_Score
- **Description**: Percentage of ideal cycle time achieved during production
- **Data Context**: Production speed efficiency (0-100)
- **Typical Value**: World-class: >95%

### hasQualityScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: Quality_Score
- **Description**: Percentage of total units produced that meet quality standards
- **Data Context**: Product quality percentage (0-100)
- **Typical Value**: World-class: >99%

### hasOEEScore
- **Domain**: Event
- **Range**: float
- **CSV Column**: OEE_Score
- **Description**: Overall Equipment Effectiveness - composite measure of availability, performance, and quality
- **Data Context**: Overall Equipment Effectiveness (0-100)
- **Typical Value**: World-class: >85%, Good: 60-75%
- **Calculation Method**: Availability × Performance × Quality

## Entity Contexts

Business contexts for specific equipment and product instances:

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
