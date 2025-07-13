#!/usr/bin/env python3
"""
Extract Ontology Structure to Turtle (TTL) Format
Creates a comprehensive mind map of the MES ontology for LLM-based SPARQL query generation.
Includes business context annotations to help LLMs understand the manufacturing domain.
"""

import os
import json
import datetime
from owlready2 import *


def load_config():
    """Load the MES configuration for business context."""
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "Data_Generation", "mes_data_config.json"
    )
    with open(config_path, "r") as f:
        return json.load(f)


def get_business_context(entity_name, config):
    """Get business context for specific entities from configuration."""
    contexts = {
        # Equipment contexts
        "Equipment": "Physical machines that transform raw materials into finished products. Performance tracked in 5-minute intervals.",
        "Filler": "First stage in bottling line. Fills containers with product. Critical for volume accuracy and product quality. Common issues: incorrect fill levels, foaming, contamination.",
        "Packer": "Groups individual containers into cases/multipacks. Common issues: material jams, label misalignment, case damage.",
        "Palletizer": "Stacks cases onto pallets for shipping. End of production line. Common issues: unstable stacks, stretch wrap failures.",
        "ProductionLine": "Complete set of equipment working together. Throughput limited by slowest equipment (bottleneck).",
        # Product contexts
        "Product": "Items manufactured for sale. Each has target rates, costs, and quality specifications.",
        "SKU-1001": "12oz Sparkling Water - High volume, low margin product. Simple to produce with minimal issues.",
        "SKU-1002": "32oz Premium Juice - High margin product with elevated quality requirements. Shows 3-4% scrap rate vs 1% target.",
        "SKU-2001": "12oz Soda - Standard carbonated beverage. Stable production across all lines.",
        "SKU-2002": "16oz Energy Drink - Complex formulation. Runs 75-85% speed on LINE1 due to foaming issues.",
        "SKU-3001": "8oz Kids Drink - Small format, high speed production. Popular in school channels.",
        # Event contexts
        "ProductionEvent": "5-minute snapshot of production metrics. Core data for OEE calculation.",
        "DowntimeEvent": "Equipment stoppage with reason code. Critical for availability calculation and improvement initiatives.",
        # KPI contexts
        "hasOEEScore": "Overall Equipment Effectiveness (0-100%). Industry standard: >85% is world-class, 65-85% is typical, <65% needs improvement.",
        "hasAvailabilityScore": "% of scheduled time equipment was available. Lost to breakdowns, changeovers, and other stops.",
        "hasPerformanceScore": "% of ideal cycle time achieved. Lost to slow cycles, minor stops, and reduced speed.",
        "hasQualityScore": "% of total units that are sellable. Lost to defects, rework, and startup losses.",
        # Anomaly patterns from config
        "LINE3-FIL": "Older filler prone to failures. Major breakdown on June 8 caused 5.5 hour downtime. Scheduled for replacement Q3 2025.",
        "LINE2-PCK": "Packer with chronic micro-stops. 25% chance of 1-5 minute stops each period. Needs preventive maintenance.",
        # Relationship contexts
        "isUpstreamOf": "Material flow direction. Upstream equipment problems cascade downstream. Critical for root cause analysis.",
        "belongsToLine": "Links equipment to its production line. Lines operate independently but share resources.",
        "executesOrder": "Links production events to customer orders. Enables order tracking and profitability analysis.",
    }

    # Check for specific equipment IDs
    base_context = contexts.get(entity_name, "")

    # Add anomaly information if applicable
    if (
        entity_name == "LINE3-FIL"
        and config["anomaly_injection"]["major_mechanical_failure"]["enabled"]
    ):
        failure = config["anomaly_injection"]["major_mechanical_failure"]
        base_context += (
            f" Major failure: {failure['start_datetime']} to {failure['end_datetime']}."
        )

    if (
        entity_name == "LINE2-PCK"
        and config["anomaly_injection"]["frequent_micro_stops"]["enabled"]
    ):
        stops = config["anomaly_injection"]["frequent_micro_stops"]
        base_context += f" Micro-stops: {int(stops['probability_per_5min']*100)}% probability per period."

    return base_context


def extract_ontology_to_ttl(owl_file_path, output_ttl_path):
    """Extract ontology structure and write to Turtle format with business context."""

    print(f"Loading ontology from {owl_file_path}...")
    onto = get_ontology(f"file://{owl_file_path}").load()
    config = load_config()

    with open(output_ttl_path, "w") as f:
        # Write header
        f.write(
            f"""# MES Ontology Mind Map for LLM SPARQL Query Generation
# Generated: {datetime.datetime.now().isoformat()}
# Purpose: Provide ontology structure with business context for accurate SPARQL query construction

# This file contains:
# 1. Complete class hierarchy with business meanings
# 2. All properties with domains, ranges, and operational context  
# 3. Key individuals as real-world examples

#############################################################################
# NAMESPACE INFORMATION
#############################################################################

# Base IRI: {onto.base_iri}
# Ontology filename: mes_ontology_populated.owl
# Automatic Owlready2 prefix: mes_ontology_populated

# Standard prefixes (automatically available):
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Ontology prefix:
@prefix mes: <{onto.base_iri}> .

# Business context annotation property
mes:businessContext a owl:AnnotationProperty ;
    rdfs:label "Business Context" ;
    rdfs:comment "Explains the business meaning and operational significance" .

mes:typicalValue a owl:AnnotationProperty ;
    rdfs:label "Typical Value" ;
    rdfs:comment "Common or expected values in production" .

mes:calculationMethod a owl:AnnotationProperty ;
    rdfs:label "Calculation Method" ;
    rdfs:comment "How this metric is calculated" .

#############################################################################
# CLASSES - Core business entities
#############################################################################

"""
        )

        # Extract and write classes
        print("Extracting classes...")
        classes = list(onto.classes())
        class_dict = {}

        for cls in sorted(classes, key=lambda x: x.name):
            if cls.namespace == onto:  # Only include classes from this ontology
                class_dict[cls.name] = cls
                f.write(f"mes:{cls.name} a owl:Class")

                # Add superclasses
                superclasses = [
                    sc for sc in cls.is_a if hasattr(sc, "name") and sc != Thing
                ]
                if superclasses:
                    for sc in superclasses:
                        f.write(f" ;\n    rdfs:subClassOf mes:{sc.name}")

                # Add label and comment
                label = cls.label[0] if cls.label else cls.name
                f.write(f' ;\n    rdfs:label "{label}"')

                if cls.comment:
                    f.write(f' ;\n    rdfs:comment "{cls.comment[0]}"')

                # Add business context
                context = get_business_context(cls.name, config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                f.write(" .\n\n")

        # Extract and write properties
        f.write(
            """
#############################################################################
# OBJECT PROPERTIES - Relationships between entities
#############################################################################

"""
        )

        print("Extracting object properties...")
        obj_props = list(onto.object_properties())

        for prop in sorted(obj_props, key=lambda x: x.name):
            if prop.namespace == onto:
                f.write(f"mes:{prop.name} a owl:ObjectProperty")

                # Add characteristics
                if prop.is_a:
                    for char in prop.is_a:
                        if char == TransitiveProperty:
                            f.write(", owl:TransitiveProperty")
                        elif char == SymmetricProperty:
                            f.write(", owl:SymmetricProperty")
                        elif char == FunctionalProperty:
                            f.write(", owl:FunctionalProperty")
                        elif char == InverseFunctionalProperty:
                            f.write(", owl:InverseFunctionalProperty")

                # Domain and range
                if prop.domain:
                    domains = [d.name for d in prop.domain if hasattr(d, "name")]
                    if domains:
                        f.write(f" ;\n    rdfs:domain mes:{domains[0]}")

                if prop.range:
                    ranges = [r.name for r in prop.range if hasattr(r, "name")]
                    if ranges:
                        f.write(f" ;\n    rdfs:range mes:{ranges[0]}")

                # Label and comment
                label = prop.label[0] if prop.label else prop.name
                f.write(f' ;\n    rdfs:label "{label}"')

                if prop.comment:
                    f.write(f' ;\n    rdfs:comment "{prop.comment[0]}"')

                # Business context
                context = get_business_context(prop.name, config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                f.write(" .\n\n")

        # Extract and write data properties
        f.write(
            """
#############################################################################
# DATA PROPERTIES - Metrics and attributes
#############################################################################

"""
        )

        print("Extracting data properties...")
        data_props = list(onto.data_properties())

        for prop in sorted(data_props, key=lambda x: x.name):
            if prop.namespace == onto:
                f.write(f"mes:{prop.name} a owl:DatatypeProperty")

                # Add characteristics
                if FunctionalProperty in prop.is_a:
                    f.write(", owl:FunctionalProperty")

                # Domain and range
                if prop.domain:
                    domains = [d.name for d in prop.domain if hasattr(d, "name")]
                    if domains:
                        f.write(f" ;\n    rdfs:domain mes:{domains[0]}")

                if prop.range:
                    range_type = prop.range[0]
                    if range_type == float:
                        f.write(f" ;\n    rdfs:range xsd:float")
                    elif range_type == int:
                        f.write(f" ;\n    rdfs:range xsd:integer")
                    elif range_type == str:
                        f.write(f" ;\n    rdfs:range xsd:string")
                    elif range_type == bool:
                        f.write(f" ;\n    rdfs:range xsd:boolean")
                    elif range_type == datetime:
                        f.write(f" ;\n    rdfs:range xsd:dateTime")

                # Label and comment
                label = prop.label[0] if prop.label else prop.name
                f.write(f' ;\n    rdfs:label "{label}"')

                if prop.comment:
                    f.write(f' ;\n    rdfs:comment "{prop.comment[0]}"')

                # Business context
                context = get_business_context(prop.name, config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                # Add typical values for KPIs
                if "Score" in prop.name:
                    f.write(
                        f' ;\n    mes:typicalValue "85-95% for world-class operations"'
                    )
                    if prop.name == "hasOEEScore":
                        f.write(
                            f' ;\n    mes:calculationMethod "Availability × Performance × Quality"'
                        )

                f.write(" .\n\n")

        # Extract key individuals as examples
        f.write(
            """
#############################################################################
# EXAMPLE INDIVIDUALS - Real instances from the factory
#############################################################################

"""
        )

        print("Extracting example individuals...")

        # Equipment examples
        equipment_examples = ["LINE1-FIL", "LINE1-PCK", "LINE2-PCK", "LINE3-FIL"]
        for eq_id in equipment_examples:
            individuals = onto.search(iri=f"*{eq_id}")
            if individuals:
                ind = individuals[0]
                f.write(f"mes:{ind.name} a mes:{ind.is_a[0].name}")
                f.write(f' ;\n    rdfs:label "{ind.name}"')

                # Add properties
                for prop in ind.get_properties():
                    if prop.namespace == onto:
                        values = prop[ind]
                        if values:
                            if isinstance(values, list):
                                for val in values[:3]:  # Limit to first 3 values
                                    if hasattr(val, "name"):
                                        f.write(
                                            f" ;\n    mes:{prop.name} mes:{val.name}"
                                        )
                            else:
                                if hasattr(values, "name"):
                                    f.write(
                                        f" ;\n    mes:{prop.name} mes:{values.name}"
                                    )

                # Add business context
                context = get_business_context(ind.name, config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                f.write(" .\n\n")

        # Product examples
        product_examples = ["SKU-1001", "SKU-1002", "SKU-2001", "SKU-2002", "SKU-3001"]
        for sku in product_examples:
            individuals = onto.search(iri=f"*{sku}")
            if individuals:
                ind = individuals[0]
                f.write(f"mes:{ind.name} a mes:Product")

                # Get product info from config
                if sku in config["product_master"]:
                    prod_info = config["product_master"][sku]
                    f.write(f" ;\n    rdfs:label \"{prod_info['name']}\"")
                    f.write(
                        f" ;\n    mes:targetRate {prod_info['target_rate_units_per_5min']}"
                    )
                    f.write(
                        f" ;\n    mes:standardCost {prod_info['standard_cost_per_unit']}"
                    )
                    f.write(f" ;\n    mes:salePrice {prod_info['sale_price_per_unit']}")

                    margin = (
                        (
                            prod_info["sale_price_per_unit"]
                            - prod_info["standard_cost_per_unit"]
                        )
                        / prod_info["sale_price_per_unit"]
                        * 100
                    )
                    f.write(f' ;\n    mes:profitMargin "{margin:.1f}%"')

                # Add business context
                context = get_business_context(sku, config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                f.write(" .\n\n")

        # Add example SPARQL queries section
        f.write(
            """

"""
        )

    print(f"Turtle mind map written to {output_ttl_path}")
    print(f"Total classes: {len(classes)}")
    print(f"Total object properties: {len(obj_props)}")
    print(f"Total data properties: {len(data_props)}")


def main():
    """Main execution function."""
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    owl_file = os.path.join(project_root, "Ontology", "mes_ontology_populated.owl")
    output_ttl = os.path.join(project_root, "Context", "mes_ontology_mindmap.ttl")

    # Check if OWL file exists
    if not os.path.exists(owl_file):
        print(f"Error: OWL file not found at {owl_file}")
        print(
            "Please run mes_ontology_population.py first to create the populated ontology."
        )
        return

    # Extract ontology to TTL
    extract_ontology_to_ttl(owl_file, output_ttl)

    print("\nNext steps:")
    print("1. Review the generated TTL file for ontology structure")
    print(
        "2. See SPARQL_Examples/owlready2_sparql_master_reference.md for query guidelines"
    )
    print("3. Use both files as context when prompting LLMs to generate SPARQL queries")
    print(
        "4. Test generated queries with the API at http://localhost:8000/sparql/query"
    )


if __name__ == "__main__":
    main()
