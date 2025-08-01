#!/usr/bin/env python3
"""
Extract Ontology Structure to Turtle (TTL) Format
Creates a reference file of the ontology structure for query generation.
Configuration-driven from ontology_spec.yaml
"""

import os
import json
import datetime
from owlready2 import *
from ontology_config_parser import load_ontology_config




def get_business_context(entity_name, ontology_parser):
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
    ontology_meta = ontology_parser.get_ontology_metadata()

    with open(output_ttl_path, "w") as f:
        # Write header
        f.write(
            f"""# Ontology Structure Reference
# Generated: {datetime.datetime.now().isoformat()}
# Purpose: Ontology structure for query construction

# Note: When using SPARQL with Owlready2, the prefix is derived from the OWL filename.

# Standard prefixes:
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Base namespace:
@prefix : <{onto.base_iri}> .

# Annotation properties
:businessContext a owl:AnnotationProperty ;
    rdfs:label "Business Context" ;
    rdfs:comment "Explains the business meaning and operational significance" .

:typicalValue a owl:AnnotationProperty ;
    rdfs:label "Typical Value" ;
    rdfs:comment "Common or expected values in production" .

:calculationMethod a owl:AnnotationProperty ;
    rdfs:label "Calculation Method" ;
    rdfs:comment "How this metric is calculated" .

:mapsToColumn a owl:AnnotationProperty ;
    rdfs:label "Maps to Column" ;
    rdfs:comment "The CSV column name this property maps to" .

:dataContext a owl:AnnotationProperty ;
    rdfs:label "Data Context" ;
    rdfs:comment "Describes the type and meaning of the data" .

:exampleValue a owl:AnnotationProperty ;
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
                f.write(f":{cls.name} a owl:Class")

                # Add superclasses
                superclasses = [
                    sc for sc in cls.is_a if hasattr(sc, "name") and sc != Thing
                ]
                if superclasses:
                    for sc in superclasses:
                        f.write(f" ;\n    rdfs:subClassOf :{sc.name}")

                # Add label and comment
                label = cls.label[0] if cls.label else cls.name
                f.write(f' ;\n    rdfs:label "{label}"')

                if cls.comment:
                    f.write(f' ;\n    rdfs:comment "{cls.comment[0]}"')

                # Add business context from configuration
                context = get_business_context(cls.name, ontology_parser)
                if context:
                    f.write(f' ;\n    :businessContext "{context}"')

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
                f.write(f":{prop.name} a owl:ObjectProperty")

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
                        f.write(f" ;\n    rdfs:domain :{domains[0]}")

                if prop.range:
                    ranges = [r.name for r in prop.range if hasattr(r, "name")]
                    if ranges:
                        f.write(f" ;\n    rdfs:range :{ranges[0]}")

                # Label and comment
                label = prop.label[0] if prop.label else prop.name
                f.write(f' ;\n    rdfs:label "{label}"')

                if prop.comment:
                    f.write(f' ;\n    rdfs:comment "{prop.comment[0]}"')

                # Business context from configuration
                context = get_business_context(prop.name, ontology_parser)
                if context:
                    f.write(f' ;\n    :businessContext "{context}"')

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
                f.write(f":{prop.name} a owl:DatatypeProperty")

                # Add characteristics
                if FunctionalProperty in prop.is_a:
                    f.write(", owl:FunctionalProperty")

                # Domain and range
                if prop.domain:
                    domains = [d.name for d in prop.domain if hasattr(d, "name")]
                    if domains:
                        f.write(f" ;\n    rdfs:domain :{domains[0]}")

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
                    f.write(f' ;\n    :mapsToColumn "{mapping["column"]}"')
                    f.write(f' ;\n    :dataContext "{mapping["context"]}"')

                # Add example values from configuration
                prop_config = ontology_parser.get_data_properties().get(prop.name, {})
                if 'example_value' in prop_config:
                    f.write(f' ;\n    :exampleValue "{prop_config["example_value"]}"')

                # Business context
                context = get_business_context(prop.name, ontology_parser)
                if context:
                    f.write(f' ;\n    :businessContext "{context}"')

                # Add typical values for KPIs
                if 'typical_value' in prop_config:
                    f.write(f' ;\n    :typicalValue "{prop_config["typical_value"]}"')
                if 'calculation_method' in prop_config:
                    f.write(f' ;\n    :calculationMethod "{prop_config["calculation_method"]}"')

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