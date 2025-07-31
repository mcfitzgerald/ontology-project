#!/usr/bin/env python3
"""
MES Ontology Population Script
Populates the ontology from CSV data with inline KPIs
Now configuration-driven from ontology_spec.yaml
"""

from owlready2 import *
import pandas as pd
import datetime as dt
import json
import os
from ontology_config_parser import (
    load_ontology_config, 
    create_class_from_config,
    create_object_property_from_config,
    create_data_property_from_config
)


def load_config(config_file="mes_data_config.json"):
    """Load configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data_Generation", config_file)
    with open(config_path, "r") as f:
        return json.load(f)


def create_ontology_structure(onto, ontology_parser):
    """Create the TBox classes and RBox properties from configuration."""
    
    print("Creating ontology structure from configuration...")
    
    # Store created classes for reference
    class_map = {}
    
    with onto:
        # Create classes in hierarchical order
        print("  Creating classes...")
        for class_name, class_info in ontology_parser.get_class_hierarchy():
            parent_name = class_info.get('parent')
            parent_class = class_map.get(parent_name, Thing) if parent_name else Thing
            
            # Create the class
            new_class = create_class_from_config(onto, class_name, class_info, parent_class)
            class_map[class_name] = new_class
            
            # Store reference in onto namespace for backward compatibility
            setattr(onto, class_name, new_class)
        
        print(f"    Created {len(class_map)} classes")
        
        # Create object properties
        print("  Creating object properties...")
        
        # First pass: Create all properties
        for prop_name, prop_info in ontology_parser.get_object_properties().items():
            # Create the property
            new_prop = create_object_property_from_config(onto, prop_name, prop_info, class_map)
            # Store reference
            setattr(onto, prop_name, new_prop)
        
        # Second pass: Set up inverse relationships
        inverse_mappings = ontology_parser.get_inverse_properties()
        for prop_name, inverse_name in inverse_mappings.items():
            if hasattr(onto, prop_name) and hasattr(onto, inverse_name):
                prop = getattr(onto, prop_name)
                inverse_prop = getattr(onto, inverse_name)
                # Only set if not already set
                if not hasattr(prop, '_inverse_property') or prop._inverse_property is None:
                    prop.inverse_property = inverse_prop
        
        print(f"    Created {len(ontology_parser.get_object_properties())} object properties")
        
        # Create data properties
        print("  Creating data properties...")
        for prop_name, prop_info in ontology_parser.get_data_properties().items():
            new_prop = create_data_property_from_config(onto, prop_name, prop_info, class_map)
            setattr(onto, prop_name, new_prop)
        
        print(f"    Created {len(ontology_parser.get_data_properties())} data properties")
    
    return class_map


def get_or_create_individual(onto, cls, iri_suffix, **kwargs):
    """Get existing individual or create new one."""
    individual = onto.search_one(iri=f"*{iri_suffix}")
    if not individual:
        individual = cls(iri_suffix, namespace=onto, **kwargs)
    return individual


def populate_from_csv(onto, csv_file, config, ontology_parser):
    """Populate the ontology from CSV data."""
    
    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"  Found {len(df)} records")
    
    # Get equipment type mapping from configuration
    equipment_type_mapping = ontology_parser.get_equipment_type_mapping()
    
    # Get downtime mappings
    downtime_mappings = ontology_parser.get_downtime_mappings()
    
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
        
        # Map to specific equipment class using configuration
        if equip_type in equipment_type_mapping:
            equip_class_name = equipment_type_mapping[equip_type]
            equip_class = getattr(onto, equip_class_name, onto.Equipment)
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
    ].dropna().drop_duplicates()
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
    order_df = df[["ProductionOrderID", "ProductID"]].dropna().drop_duplicates()
    orders = {}
    
    for _, row in order_df.iterrows():
        order = get_or_create_individual(
            onto, onto.ProductionOrder, row["ProductionOrderID"]
        )
        order.hasOrderID = [row["ProductionOrderID"]]
        if row["ProductID"] in products:
            order.producesProduct = [products[row["ProductID"]]]
        orders[row["ProductionOrderID"]] = order
    
    print(f"  Created {len(orders)} production orders")
    
    # Downtime Reasons from configuration
    downtime_reasons = {}
    for code, class_name in downtime_mappings.items():
        if hasattr(onto, class_name):
            cls = getattr(onto, class_name)
        else:
            # Try to find the class by code in the configuration
            found_class = ontology_parser.get_class_by_code(code)
            if found_class and hasattr(onto, found_class):
                cls = getattr(onto, found_class)
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
            
            # Link equipment to order (only if order exists - not during changeover)
            if pd.notna(row["ProductionOrderID"]):
                order = orders.get(row["ProductionOrderID"])
                if order and order not in equipment.executesOrder:
                    equipment.executesOrder.append(order)
            
            events_created += 1
        
        if chunk_end < len(df):
            print(f"  Processed {chunk_end}/{len(df)} events...")
    
    print(f"  Created {events_created} events")


def main():
    """Main execution function."""
    # Load data generation configuration
    config = load_config()
    
    # Load ontology configuration
    ontology_parser = load_ontology_config()
    ontology_meta = ontology_parser.get_ontology_metadata()
    
    print(
        f"Creating MES Ontology: {ontology_meta['name']} v{ontology_meta['version']}"
    )
    print("-" * 60)
    
    # Create ontology
    onto = get_ontology(ontology_meta["iri"])
    
    # Create TBox/RBox structure from configuration
    class_map = create_ontology_structure(onto, ontology_parser)
    
    # Populate from CSV
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "mes_data_with_kpis.csv")
    if os.path.exists(csv_file):
        populate_from_csv(onto, csv_file, config, ontology_parser)
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