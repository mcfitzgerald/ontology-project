#!/usr/bin/env python3
"""
MES Ontology Population Script
Populates the ontology from CSV data with inline KPIs
"""

from owlready2 import *
import pandas as pd
import datetime as dt
import json
import os


def load_config(config_file="mes_data_config.json"):
    """Load configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data_Generation", config_file)
    with open(config_path, "r") as f:
        return json.load(f)


def create_ontology_structure(onto, config):
    """Create the TBox classes and RBox properties based on specification."""

    with onto:
        # TBox - Classes

        # Process
        class Process(Thing):
            pass

        class ProductionOrder(Process):
            pass

        # Resource
        class Resource(Thing):
            pass

        class Equipment(Resource):
            pass

        class Filler(Equipment):
            pass

        class Packer(Equipment):
            pass

        class Palletizer(Equipment):
            pass

        class ProductionLine(Resource):
            pass

        class Product(Resource):
            pass

        # Event
        class Event(Thing):
            pass

        class ProductionLog(Event):
            """Event when equipment is running and producing"""

            pass

        class DowntimeLog(Event):
            """Event when equipment is stopped"""

            pass

        # Reason
        class Reason(Thing):
            pass

        class DowntimeReason(Reason):
            pass

        class PlannedDowntime(DowntimeReason):
            pass

        class Changeover(PlannedDowntime):
            pass

        class Cleaning(PlannedDowntime):
            pass

        class UnplannedDowntime(DowntimeReason):
            pass

        class MechanicalFailure(UnplannedDowntime):
            pass

        class MaterialJam(UnplannedDowntime):
            pass

        class MaterialStarvation(UnplannedDowntime):
            pass

        # RBox - Object Properties

        class isUpstreamOf(Equipment >> Equipment):
            pass

        class isDownstreamOf(Equipment >> Equipment):
            inverse_property = isUpstreamOf

        class belongsToLine(Equipment >> ProductionLine):
            pass

        class hasEquipment(ProductionLine >> Equipment):
            inverse_property = belongsToLine

        class executesOrder(Equipment >> ProductionOrder):
            pass

        class producesProduct(ProductionOrder >> Product):
            pass

        class logsEvent(Equipment >> Event):
            pass

        class hasDowntimeReason(DowntimeLog >> DowntimeReason):
            pass

        # RBox - Data Properties

        # Event properties
        class hasTimestamp(DataProperty):
            domain = [Event]
            range = [str]  # Store as ISO string

        # Order properties
        class hasOrderID(DataProperty):
            domain = [ProductionOrder]
            range = [str]

        # Line properties
        class hasLineID(DataProperty):
            domain = [ProductionLine]
            range = [int]

        # Equipment properties
        class hasEquipmentID(DataProperty):
            domain = [Equipment]
            range = [str]

        class hasEquipmentType(DataProperty):
            domain = [Equipment]
            range = [str]

        # Product properties
        class hasProductID(DataProperty):
            domain = [Product]
            range = [str]

        class hasProductName(DataProperty):
            domain = [Product]
            range = [str]

        class hasTargetRate(DataProperty):
            domain = [Product]
            range = [float]  # Units per 5 minutes

        class hasStandardCost(DataProperty):
            domain = [Product]
            range = [float]

        class hasSalePrice(DataProperty):
            domain = [Product]
            range = [float]

        # Event data properties
        class hasMachineStatus(DataProperty):
            domain = [Event]
            range = [str]

        class hasDowntimeReasonCode(DataProperty):
            domain = [DowntimeLog]
            range = [str]

        # Production metrics
        class hasGoodUnits(DataProperty):
            domain = [ProductionLog]
            range = [int]

        class hasScrapUnits(DataProperty):
            domain = [ProductionLog]
            range = [int]

        # KPI properties (pre-calculated in data)
        class hasAvailabilityScore(DataProperty):
            domain = [Event]
            range = [float]

        class hasPerformanceScore(DataProperty):
            domain = [Event]
            range = [float]

        class hasQualityScore(DataProperty):
            domain = [Event]
            range = [float]

        class hasOEEScore(DataProperty):
            domain = [Event]
            range = [float]


def get_or_create_individual(onto, cls, iri_suffix, **kwargs):
    """Get existing individual or create new one."""
    individual = onto.search_one(iri=f"*{iri_suffix}")
    if not individual:
        individual = cls(iri_suffix, namespace=onto, **kwargs)
    return individual


def populate_from_csv(onto, csv_file, config):
    """Populate the ontology from CSV data."""

    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"  Found {len(df)} records")

    # Create master data individuals first
    print("Creating master data individuals...")

    # Production Lines
    unique_lines = df["LineID"].unique()
    lines = {}
    for line_id in unique_lines:
        line_iri = f"LINE{line_id}"
        line = get_or_create_individual(onto, onto.ProductionLine, line_iri)
        line.hasLineID = [int(line_id)]
        lines[line_id] = line
    print(f"  Created {len(lines)} production lines")

    # Equipment
    equipment_df = df[["EquipmentID", "EquipmentType", "LineID"]].drop_duplicates()
    equipment_map = {}

    for _, row in equipment_df.iterrows():
        equip_type = row["EquipmentType"]

        # Map to specific equipment class
        if equip_type == "Filler":
            equip_class = onto.Filler
        elif equip_type == "Packer":
            equip_class = onto.Packer
        elif equip_type == "Palletizer":
            equip_class = onto.Palletizer
        else:
            equip_class = onto.Equipment

        equipment = get_or_create_individual(onto, equip_class, row["EquipmentID"])
        equipment.hasEquipmentID = [row["EquipmentID"]]
        equipment.hasEquipmentType = [equip_type]
        equipment.belongsToLine = [lines[row["LineID"]]]
        equipment_map[row["EquipmentID"]] = equipment

    print(f"  Created {len(equipment_map)} equipment")

    # Set up equipment process flow from configuration
    print("Setting up process flow relationships...")
    for line_id, line_config in config["equipment_configuration"]["lines"].items():
        for eq_id, flow in line_config["process_flow"].items():
            equipment = equipment_map.get(eq_id)
            if equipment and flow["downstream"]:
                downstream_eq = equipment_map.get(flow["downstream"])
                if downstream_eq:
                    equipment.isUpstreamOf.append(downstream_eq)

    # Products
    product_df = df[
        [
            "ProductID",
            "ProductName",
            "TargetRate_units_per_5min",
            "StandardCost_per_unit",
            "SalePrice_per_unit",
        ]
    ].drop_duplicates()
    products = {}

    for _, row in product_df.iterrows():
        product = get_or_create_individual(onto, onto.Product, row["ProductID"])
        product.hasProductID = [row["ProductID"]]
        product.hasProductName = [row["ProductName"]]
        product.hasTargetRate = [float(row["TargetRate_units_per_5min"])]
        product.hasStandardCost = [float(row["StandardCost_per_unit"])]
        product.hasSalePrice = [float(row["SalePrice_per_unit"])]
        products[row["ProductID"]] = product

    print(f"  Created {len(products)} products")

    # Production Orders
    order_df = df[["ProductionOrderID", "ProductID"]].drop_duplicates()
    orders = {}

    for _, row in order_df.iterrows():
        order = get_or_create_individual(
            onto, onto.ProductionOrder, row["ProductionOrderID"]
        )
        order.hasOrderID = [row["ProductionOrderID"]]
        order.producesProduct = [products[row["ProductID"]]]
        orders[row["ProductionOrderID"]] = order

    print(f"  Created {len(orders)} production orders")

    # Downtime Reasons from configuration
    downtime_reasons = {}
    for code, info in config["downtime_reason_mapping"].items():
        reason_class = info["class"]

        # Map to specific downtime reason class
        if reason_class == "Changeover":
            cls = onto.Changeover
        elif reason_class == "Cleaning":
            cls = onto.Cleaning
        elif reason_class == "MechanicalFailure":
            cls = onto.MechanicalFailure
        elif reason_class == "MaterialJam":
            cls = onto.MaterialJam
        elif reason_class == "MaterialStarvation":
            cls = onto.MaterialStarvation
        else:
            cls = onto.DowntimeReason

        reason = get_or_create_individual(onto, cls, f"REASON-{code}")
        reason.hasDowntimeReasonCode = [code]
        downtime_reasons[code] = reason

    print(f"  Created {len(downtime_reasons)} downtime reasons")

    # Process events
    print("Processing events...")
    events_created = 0

    # Process in chunks for memory efficiency
    chunk_size = 10000
    for chunk_start in range(0, len(df), chunk_size):
        chunk_end = min(chunk_start + chunk_size, len(df))
        chunk_df = df.iloc[chunk_start:chunk_end]

        for idx, row in chunk_df.iterrows():
            # Create event based on machine status
            timestamp_str = str(row["Timestamp"])
            event_iri = f"EVENT-{row['EquipmentID']}-{timestamp_str.replace(' ', 'T').replace(':', '-')}"

            if row["MachineStatus"] == "Running":
                event = get_or_create_individual(onto, onto.ProductionLog, event_iri)
                event.hasGoodUnits = [int(row["GoodUnitsProduced"])]
                event.hasScrapUnits = [int(row["ScrapUnitsProduced"])]
            else:
                event = get_or_create_individual(onto, onto.DowntimeLog, event_iri)
                if pd.notna(row["DowntimeReason"]):
                    reason = downtime_reasons.get(row["DowntimeReason"])
                    if reason:
                        event.hasDowntimeReason = [reason]
                    event.hasDowntimeReasonCode = [row["DowntimeReason"]]

            # Common event properties
            event.hasTimestamp = [timestamp_str]
            event.hasMachineStatus = [row["MachineStatus"]]

            # KPI scores
            event.hasAvailabilityScore = [float(row["Availability_Score"])]
            event.hasPerformanceScore = [float(row["Performance_Score"])]
            event.hasQualityScore = [float(row["Quality_Score"])]
            event.hasOEEScore = [float(row["OEE_Score"])]

            # Link event to equipment
            equipment = equipment_map[row["EquipmentID"]]
            equipment.logsEvent.append(event)

            # Link equipment to order
            order = orders[row["ProductionOrderID"]]
            if order not in equipment.executesOrder:
                equipment.executesOrder.append(order)

            events_created += 1

        if chunk_end < len(df):
            print(f"  Processed {chunk_end}/{len(df)} events...")

    print(f"  Created {events_created} events")


def main():
    """Main execution function."""
    # Load configuration
    config = load_config()

    print(
        f"Creating MES Ontology: {config['ontology']['name']} v{config['ontology']['version']}"
    )
    print("-" * 60)

    # Create ontology
    onto = get_ontology(config["ontology"]["iri"])

    # Create TBox/RBox structure
    print("Creating ontology structure...")
    create_ontology_structure(onto, config)

    # Populate from CSV
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "mes_data_with_kpis.csv")
    if os.path.exists(csv_file):
        populate_from_csv(onto, csv_file, config)
    else:
        print(
            f"Warning: {csv_file} not found. Please run mes_data_generation.py first."
        )
        return

    # Save ontology to Ontology directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Ontology")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "mes_ontology_populated.owl")
    onto.save(file=output_file, format="rdfxml")
    print(f"\nOntology saved to {output_file}")

    # Print summary statistics
    print("\nOntology Summary:")
    print(f"  Equipment: {len(list(onto.Equipment.instances()))}")
    print(f"  Products: {len(list(onto.Product.instances()))}")
    print(f"  Production Orders: {len(list(onto.ProductionOrder.instances()))}")
    print(f"  Events: {len(list(onto.Event.instances()))}")
    print(f"    - Production Logs: {len(list(onto.ProductionLog.instances()))}")
    print(f"    - Downtime Logs: {len(list(onto.DowntimeLog.instances()))}")


if __name__ == "__main__":
    main()
