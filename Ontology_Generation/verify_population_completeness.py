#!/usr/bin/env python3
"""
Verify that the ontology population captures all data from CSV
"""

import pandas as pd
import os
from owlready2 import *

def verify_csv_coverage():
    """Check that all CSV columns are mapped in the population script."""
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "mes_data_with_kpis.csv")
    df = pd.read_csv(csv_file)
    
    csv_columns = list(df.columns)
    print("CSV Columns to verify:")
    for col in csv_columns:
        print(f"  - {col}")
    
    # Read the population script to check mappings
    script_file = os.path.join(os.path.dirname(__file__), "mes_ontology_population.py")
    with open(script_file, 'r') as f:
        script_content = f.read()
    
    print("\nColumn mapping verification:")
    missing_columns = []
    for col in csv_columns:
        if col in script_content:
            print(f"  ✓ {col} - Found in script")
        else:
            print(f"  ✗ {col} - NOT FOUND in script")
            missing_columns.append(col)
    
    return missing_columns

def verify_ontology_completeness():
    """Verify the populated ontology contains expected data."""
    onto_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Ontology", "mes_ontology_populated.owl")
    
    if not os.path.exists(onto_file):
        print("\nERROR: Ontology file not found. Run mes_ontology_population.py first.")
        return
    
    onto = get_ontology(f"file://{onto_file}").load()
    
    print("\n\nOntology content verification:")
    
    # Check classes exist
    print("\n1. Class verification:")
    expected_classes = [
        "Process", "ProductionOrder", "Resource", "Equipment", 
        "Filler", "Packer", "Palletizer", "ProductionLine", "Product",
        "Event", "ProductionLog", "DowntimeLog", "Reason", "DowntimeReason",
        "PlannedDowntime", "Changeover", "Cleaning", "PreventiveMaintenance",
        "UnplannedDowntime", "MechanicalFailure", "MaterialJam", "MaterialStarvation",
        "ElectricalFailure", "QualityCheck", "OperatorError", "SensorFailure"
    ]
    
    for cls_name in expected_classes:
        cls = getattr(onto, cls_name, None)
        if cls:
            count = len(list(cls.instances()))
            print(f"  ✓ {cls_name}: {count} instances")
        else:
            print(f"  ✗ {cls_name}: NOT FOUND")
    
    # Check properties exist
    print("\n2. Property verification:")
    expected_properties = [
        # Object properties
        "isUpstreamOf", "isDownstreamOf", "belongsToLine", "hasEquipment",
        "executesOrder", "producesProduct", "logsEvent", "hasDowntimeReason",
        # Data properties
        "hasTimestamp", "hasOrderID", "hasLineID", "hasEquipmentID", "hasEquipmentType",
        "hasProductID", "hasProductName", "hasMachineStatus", "hasDowntimeReasonCode",
        "hasGoodUnits", "hasScrapUnits", "hasTargetRate", "hasStandardCost", "hasSalePrice",
        "hasAvailabilityScore", "hasPerformanceScore", "hasQualityScore", "hasOEEScore"
    ]
    
    for prop_name in expected_properties:
        prop = getattr(onto, prop_name, None)
        if prop:
            print(f"  ✓ {prop_name}")
        else:
            print(f"  ✗ {prop_name}: NOT FOUND")
    
    # Sample data verification
    print("\n3. Sample data verification:")
    
    # Check a few events have all expected properties
    events = list(onto.Event.instances())[:5]
    print(f"\nChecking first 5 events (of {len(list(onto.Event.instances()))}):")
    
    for event in events:
        print(f"\n  Event: {event.name}")
        print(f"    - hasTimestamp: {event.hasTimestamp}")
        print(f"    - hasMachineStatus: {event.hasMachineStatus}")
        print(f"    - hasOEEScore: {event.hasOEEScore}")
        
        if isinstance(event, onto.ProductionLog):
            print(f"    - hasGoodUnits: {event.hasGoodUnits}")
            print(f"    - hasScrapUnits: {event.hasScrapUnits}")
        elif isinstance(event, onto.DowntimeLog):
            print(f"    - hasDowntimeReasonCode: {event.hasDowntimeReasonCode}")
            if event.hasDowntimeReason:
                print(f"    - hasDowntimeReason: {event.hasDowntimeReason[0].name}")
    
    # Check equipment relationships
    print("\n4. Equipment relationship verification:")
    equipment = list(onto.Equipment.instances())[:3]
    for eq in equipment:
        print(f"\n  Equipment: {eq.name}")
        print(f"    - belongsToLine: {eq.belongsToLine}")
        print(f"    - executesOrder: {len(eq.executesOrder)} orders")
        print(f"    - logsEvent: {len(eq.logsEvent)} events")
        if eq.isUpstreamOf:
            print(f"    - isUpstreamOf: {[e.name for e in eq.isUpstreamOf]}")
        if eq.isDownstreamOf:
            print(f"    - isDownstreamOf: {[e.name for e in eq.isDownstreamOf]}")

def verify_edge_cases():
    """Check edge cases in the CSV data."""
    csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "mes_data_with_kpis.csv")
    df = pd.read_csv(csv_file)
    
    print("\n\n5. Edge case verification:")
    
    # Check for nulls
    print("\nNull value counts:")
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            print(f"  - {col}: {count} nulls")
    
    # Check changeover periods
    changeover_df = df[df['MachineStatus'] == 'Stopped']
    changeover_with_pln_co = changeover_df[changeover_df['DowntimeReason'] == 'PLN-CO']
    print(f"\nChangeover verification:")
    print(f"  - Total stopped events: {len(changeover_df)}")
    print(f"  - PLN-CO (changeover) events: {len(changeover_with_pln_co)}")
    print(f"  - Events with null ProductionOrderID: {df['ProductionOrderID'].isnull().sum()}")
    
    # Check all downtime reasons are present
    print("\nDowntime reason coverage:")
    downtime_reasons = df[df['DowntimeReason'].notna()]['DowntimeReason'].unique()
    for reason in sorted(downtime_reasons):
        count = len(df[df['DowntimeReason'] == reason])
        print(f"  - {reason}: {count} events")

def main():
    print("MES Ontology Population Completeness Verification")
    print("=" * 60)
    
    # 1. Verify CSV columns are mapped
    missing_columns = verify_csv_coverage()
    
    # 2. Verify ontology content
    verify_ontology_completeness()
    
    # 3. Verify edge cases
    verify_edge_cases()
    
    print("\n\nSUMMARY:")
    if missing_columns:
        print(f"WARNING: {len(missing_columns)} columns not found in script: {missing_columns}")
    else:
        print("✓ All CSV columns are mapped in the population script")

if __name__ == "__main__":
    main()