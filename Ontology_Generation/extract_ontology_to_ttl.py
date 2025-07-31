#!/usr/bin/env python3
"""
Extract Ontology Structure to Turtle (TTL) Format
Creates a comprehensive mind map of the MES ontology for LLM-based SPARQL query generation.
Includes business context annotations to help LLMs understand the manufacturing domain.
Now configuration-driven from ontology_spec.yaml
"""

import os
import json
import datetime
from owlready2 import *
from ontology_config_parser import load_ontology_config


def load_data_config():
    """Load the MES data configuration for anomaly context."""
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "Data_Generation", "mes_data_config.json"
    )
    with open(config_path, "r") as f:
        return json.load(f)


def get_business_context(entity_name, ontology_parser, data_config):
    """Get business context for specific entities from configuration."""
    # First check entity contexts in the ontology configuration
    base_context = ontology_parser.get_entity_context(entity_name) or ""
    
    # For classes, check the class hierarchy for business_context
    if not base_context:
        for class_name, class_info in ontology_parser.get_class_hierarchy():
            if class_name == entity_name:
                base_context = class_info.get('business_context', class_info.get('description', ''))
                break
    
    # For properties, check property definitions
    if not base_context:
        # Check object properties
        obj_props = ontology_parser.get_object_properties()
        if entity_name in obj_props:
            base_context = obj_props[entity_name].get('business_context', obj_props[entity_name].get('description', ''))
        
        # Check data properties
        data_props = ontology_parser.get_data_properties()
        if entity_name in data_props:
            base_context = data_props[entity_name].get('business_context', data_props[entity_name].get('description', ''))
    
    # Add anomaly information if applicable
    if (
        entity_name == "LINE3-FIL"
        and data_config["anomaly_injection"]["major_mechanical_failure"]["enabled"]
    ):
        failure = data_config["anomaly_injection"]["major_mechanical_failure"]
        base_context += (
            f" Major failure: {failure['start_datetime']} to {failure['end_datetime']}."
        )

    if (
        entity_name == "LINE2-PCK"
        and data_config["anomaly_injection"]["frequent_micro_stops"]["enabled"]
    ):
        stops = data_config["anomaly_injection"]["frequent_micro_stops"]
        base_context += f" Micro-stops: {int(stops['probability_per_5min']*100)}% probability per period, 0.5-2 minute duration."

    # Add dynamic context for new equipment patterns
    if entity_name.startswith("LINE") and "-" in entity_name:
        line_num = entity_name.split("-")[0][-1]
        eq_type = entity_name.split("-")[1]
        
        # Check filler micro-stops
        if eq_type == "FIL" and data_config.get("anomaly_injection", {}).get("filler_micro_stops", {}).get("enabled", False):
            for pattern in data_config["anomaly_injection"]["filler_micro_stops"]["equipment_patterns"]:
                if pattern["equipment_id"] == entity_name:
                    if base_context:
                        base_context += f" Filler micro-stops: {int(pattern['probability_per_5min']*100)}% probability, {pattern['duration_range_minutes']['min']}-{pattern['duration_range_minutes']['max']} minute duration."
        
        # Check palletizer micro-stops
        elif eq_type == "PAL" and data_config.get("anomaly_injection", {}).get("palletizer_micro_stops", {}).get("enabled", False):
            for pattern in data_config["anomaly_injection"]["palletizer_micro_stops"]["equipment_patterns"]:
                if pattern["equipment_id"] == entity_name:
                    if base_context:
                        base_context += f" Palletizer micro-stops: {int(pattern['probability_per_5min']*100)}% probability, {pattern['duration_range_minutes']['min']}-{pattern['duration_range_minutes']['max']} minute duration."
    
    return base_context


def get_column_mapping(ontology_parser):
    """Get mapping from ontology properties to CSV columns from configuration."""
    mapping = {}
    
    for prop_name, prop_info in ontology_parser.get_data_properties().items():
        if 'csv_column' in prop_info:
            mapping[prop_name] = {
                "column": prop_info["csv_column"],
                "context": prop_info.get("data_context", prop_info.get("description", ""))
            }
    
    return mapping


def extract_ontology_to_ttl(owl_file_path, output_ttl_path):
    """Extract ontology structure and write to Turtle format with business context."""

    print(f"Loading ontology from {owl_file_path}...")
    onto = get_ontology(f"file://{owl_file_path}").load()
    
    # Load configurations
    ontology_parser = load_ontology_config()
    data_config = load_data_config()
    ontology_meta = ontology_parser.get_ontology_metadata()

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

# CRITICAL PREFIX INFORMATION FOR SPARQL QUERIES:
# ============================================
# Owlready2 IGNORES all PREFIX declarations and creates its own prefix from the OWL filename.
# 
# PREFIX MAPPING:
#   - Turtle format (this file): mes:hasOEEScore
#   - OWL filename: mes_ontology_populated.owl
#   - Owlready2 auto-prefix: mes_ontology_populated:hasOEEScore
#   - SPARQL queries MUST use: mes_ontology_populated:hasOEEScore
#
# IMPORTANT: The 'mes:' prefix shown in this file will NOT work in SPARQL queries!
# You MUST use 'mes_ontology_populated:' as the prefix in all SPARQL queries.
#
# Example SPARQL query:
#   SELECT ?equipment ?oee WHERE {{
#     ?equipment mes_ontology_populated:logsEvent ?event .
#     ?event a mes_ontology_populated:ProductionLog .
#     ?event mes_ontology_populated:hasOEEScore ?oee .
#     FILTER(?oee < 85.0)
#   }}

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

mes:mapsToColumn a owl:AnnotationProperty ;
    rdfs:label "Maps to Column" ;
    rdfs:comment "The CSV column name this property maps to" .

mes:dataContext a owl:AnnotationProperty ;
    rdfs:label "Data Context" ;
    rdfs:comment "Describes the type and meaning of the data" .

mes:exampleValue a owl:AnnotationProperty ;
    rdfs:label "Example Value" ;
    rdfs:comment "Example value from the dataset" .

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

                # Add business context from configuration
                context = get_business_context(cls.name, ontology_parser, data_config)
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

                # Business context from configuration
                context = get_business_context(prop.name, ontology_parser, data_config)
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
        column_mappings = get_column_mapping(ontology_parser)

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

                # Add column mapping if available
                if prop.name in column_mappings:
                    mapping = column_mappings[prop.name]
                    f.write(f' ;\n    mes:mapsToColumn "{mapping["column"]}"')
                    f.write(f' ;\n    mes:dataContext "{mapping["context"]}"')

                # Add example values from configuration
                prop_config = ontology_parser.get_data_properties().get(prop.name, {})
                if 'example_value' in prop_config:
                    f.write(f' ;\n    mes:exampleValue "{prop_config["example_value"]}"')

                # Business context
                context = get_business_context(prop.name, ontology_parser, data_config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                # Add typical values for KPIs
                if 'typical_value' in prop_config:
                    f.write(f' ;\n    mes:typicalValue "{prop_config["typical_value"]}"')
                if 'calculation_method' in prop_config:
                    f.write(f' ;\n    mes:calculationMethod "{prop_config["calculation_method"]}"')

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

                # Add business context from configuration
                context = get_business_context(ind.name, ontology_parser, data_config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                f.write(" .\n\n")

        # Production Order examples (needed for executesOrder -> producesProduct queries)
        print("Extracting production order examples...")
        order_examples = ["ORD-1000", "ORD-1001", "ORD-1037", "ORD-1038", "ORD-1080"]
        for order_id in order_examples:
            individuals = onto.search(iri=f"*{order_id}")
            if individuals:
                ind = individuals[0]
                f.write(f"mes:{ind.name} a mes:ProductionOrder")
                f.write(f' ;\n    rdfs:label "{ind.name}"')
                
                # Add properties, especially producesProduct
                for prop in ind.get_properties():
                    if prop.namespace == onto:
                        values = prop[ind]
                        if values:
                            if prop.name == "producesProduct":
                                if isinstance(values, list) and values:
                                    f.write(f" ;\n    mes:producesProduct mes:{values[0].name}")
                                elif hasattr(values, "name"):
                                    f.write(f" ;\n    mes:producesProduct mes:{values.name}")
                            elif prop.name == "hasOrderID":
                                if isinstance(values, list) and values:
                                    f.write(f' ;\n    mes:hasOrderID "{values[0]}"')
                                else:
                                    f.write(f' ;\n    mes:hasOrderID "{values}"')
                
                f.write(" .\n\n")

        # Product examples
        product_examples = ["SKU-1001", "SKU-1002", "SKU-2001", "SKU-2002", "SKU-3001"]
        for sku in product_examples:
            individuals = onto.search(iri=f"*{sku}")
            if individuals:
                ind = individuals[0]
                f.write(f"mes:{ind.name} a mes:Product")

                # Get product info from data config
                if sku in data_config["product_master"]:
                    prod_info = data_config["product_master"][sku]
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

                # Add business context from configuration
                context = get_business_context(sku, ontology_parser, data_config)
                if context:
                    f.write(f' ;\n    mes:businessContext "{context}"')

                f.write(" .\n\n")

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