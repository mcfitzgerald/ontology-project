#!/usr/bin/env python3
"""
Generate a lightweight data catalogue from the MES dataset.
Creates a JSON file with metadata about available data for agent context.
"""

import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict


def analyze_csv_data(csv_path):
    """Analyze the CSV data and extract metadata."""
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    print(f"Loaded {len(df)} records")
    return df


def generate_catalogue(df):
    """Generate comprehensive data catalogue from DataFrame."""
    catalogue = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_range": {
                "start": df['Timestamp'].min().isoformat(),
                "end": df['Timestamp'].max().isoformat(),
                "days_covered": (df['Timestamp'].max() - df['Timestamp'].min()).days + 1
            },
            "total_records": len(df),
            "update_frequency": "5 minutes",
            "columns": list(df.columns)
        },
        "equipment": {},
        "products": {},
        "production_lines": {},
        "metrics": {},
        "downtime_reasons": {},
        "data_quality": {}
    }
    
    # Equipment analysis
    equipment_data = defaultdict(list)
    for _, row in df[['EquipmentID', 'EquipmentType', 'LineID']].drop_duplicates().iterrows():
        equipment_data[row['EquipmentType']].append({
            "id": row['EquipmentID'],
            "line": f"LINE{row['LineID']}"
        })
    
    catalogue["equipment"] = {
        "count": df['EquipmentID'].nunique(),
        "by_type": dict(equipment_data),
        "by_line": {}
    }
    
    # Group equipment by line
    for line_id in sorted(df['LineID'].unique()):
        line_equipment = df[df['LineID'] == line_id]['EquipmentID'].unique().tolist()
        catalogue["equipment"]["by_line"][f"LINE{line_id}"] = sorted(line_equipment)
    
    # Products analysis
    products = []
    product_groups = df.groupby(['ProductID', 'ProductName']).agg({
        'TargetRate_units_per_5min': 'first',
        'StandardCost_per_unit': 'first',
        'SalePrice_per_unit': 'first',
        'GoodUnitsProduced': 'sum',
        'ScrapUnitsProduced': 'sum'
    }).reset_index()
    
    for _, prod in product_groups.iterrows():
        margin = ((prod['SalePrice_per_unit'] - prod['StandardCost_per_unit']) / 
                  prod['SalePrice_per_unit'] * 100)
        total_units = prod['GoodUnitsProduced'] + prod['ScrapUnitsProduced']
        scrap_rate = (prod['ScrapUnitsProduced'] / total_units * 100) if total_units > 0 else 0
        
        products.append({
            "id": prod['ProductID'],
            "name": prod['ProductName'],
            "target_rate_per_5min": int(prod['TargetRate_units_per_5min']),
            "standard_cost": float(prod['StandardCost_per_unit']),
            "sale_price": float(prod['SalePrice_per_unit']),
            "margin_percent": round(margin, 1),
            "total_produced": int(prod['GoodUnitsProduced']),
            "actual_scrap_rate": round(scrap_rate, 2)
        })
    
    catalogue["products"] = {
        "count": len(products),
        "catalog": sorted(products, key=lambda x: x['id'])
    }
    
    # Production lines summary
    for line_id in sorted(df['LineID'].unique()):
        line_df = df[df['LineID'] == line_id]
        catalogue["production_lines"][f"LINE{line_id}"] = {
            "orders_executed": line_df['ProductionOrderID'].nunique(),
            "products_made": line_df['ProductID'].unique().tolist(),
            "total_runtime_hours": len(line_df[line_df['MachineStatus'] == 'Running']) * 5 / 60
        }
    
    # Metrics analysis (KPIs)
    kpi_columns = ['OEE_Score', 'Availability_Score', 'Performance_Score', 'Quality_Score']
    for kpi in kpi_columns:
        if kpi in df.columns:
            kpi_name = kpi.replace('_Score', '').replace('_', ' ')
            catalogue["metrics"][kpi_name] = {
                "min": round(df[kpi].min(), 1),
                "max": round(df[kpi].max(), 1),
                "mean": round(df[kpi].mean(), 1),
                "median": round(df[kpi].median(), 1),
                "typical_range": f"{round(df[kpi].quantile(0.25), 1)}-{round(df[kpi].quantile(0.75), 1)}",
                "world_class": "85-95" if kpi != 'Quality_Score' else "98-99.5"
            }
    
    # Downtime analysis
    downtime_df = df[df['MachineStatus'] == 'Stopped']
    if len(downtime_df) > 0:
        downtime_counts = downtime_df['DowntimeReason'].value_counts()
        
        planned_reasons = []
        unplanned_reasons = []
        
        for reason, count in downtime_counts.items():
            if pd.notna(reason):
                minutes = count * 5
                hours = round(minutes / 60, 1)
                reason_info = {
                    "code": reason,
                    "occurrences": int(count),
                    "total_minutes": minutes,
                    "total_hours": hours
                }
                
                if reason.startswith('PLN'):
                    planned_reasons.append(reason_info)
                else:
                    unplanned_reasons.append(reason_info)
        
        catalogue["downtime_reasons"] = {
            "total_downtime_hours": round(len(downtime_df) * 5 / 60, 1),
            "planned": sorted(planned_reasons, key=lambda x: x['total_hours'], reverse=True),
            "unplanned": sorted(unplanned_reasons, key=lambda x: x['total_hours'], reverse=True)
        }
    
    # Data quality indicators
    catalogue["data_quality"] = {
        "null_values": {col: int(df[col].isnull().sum()) for col in df.columns if df[col].isnull().sum() > 0},
        "update_consistency": "5-minute intervals" if len(df['Timestamp'].diff().dropna().unique()) <= 2 else "Variable",
        "equipment_coverage": f"{df['EquipmentID'].nunique()} unique equipment tracked"
    }
    
    # Column descriptions for quick reference
    catalogue["column_descriptions"] = {
        "Timestamp": "5-minute interval timestamp",
        "ProductionOrderID": "Unique production order identifier",
        "LineID": "Production line number (1-3)",
        "EquipmentID": "Unique equipment identifier (e.g., LINE1-FIL)",
        "EquipmentType": "Type of equipment (Filler/Packer/Palletizer)",
        "ProductID": "Product SKU identifier",
        "ProductName": "Human-readable product name",
        "MachineStatus": "Equipment state (Running/Stopped)",
        "DowntimeReason": "Reason code for stops (PLN-*/UNP-*)",
        "GoodUnitsProduced": "Sellable units in 5-min interval",
        "ScrapUnitsProduced": "Defective units in 5-min interval",
        "TargetRate_units_per_5min": "Expected production rate",
        "StandardCost_per_unit": "Manufacturing cost per unit",
        "SalePrice_per_unit": "Selling price per unit",
        "Availability_Score": "Equipment availability % (0-100)",
        "Performance_Score": "Production speed efficiency % (0-100)",
        "Quality_Score": "Product quality % (0-100)",
        "OEE_Score": "Overall Equipment Effectiveness % (0-100)"
    }
    
    return catalogue


def main():
    """Main execution function."""
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    csv_path = os.path.join(project_root, "Data", "mes_data_with_kpis.csv")
    output_path = os.path.join(project_root, "Context", "mes_data_catalogue.json")
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please run mes_data_generation.py first to generate the data.")
        return
    
    # Analyze data
    df = analyze_csv_data(csv_path)
    
    # Generate catalogue
    print("Generating data catalogue...")
    catalogue = generate_catalogue(df)
    
    # Save catalogue
    print(f"Saving catalogue to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(catalogue, f, indent=2)
    
    # Print summary
    print("\nCatalogue Summary:")
    print(f"- Date range: {catalogue['metadata']['data_range']['days_covered']} days")
    print(f"- Total records: {catalogue['metadata']['total_records']:,}")
    print(f"- Equipment tracked: {catalogue['equipment']['count']}")
    print(f"- Products manufactured: {catalogue['products']['count']}")
    print(f"- Total downtime: {catalogue['downtime_reasons']['total_downtime_hours']:.1f} hours")
    
    print("\nCatalogue saved successfully!")
    print("Use this file as context for ADK agents to understand available data.")


if __name__ == "__main__":
    main()