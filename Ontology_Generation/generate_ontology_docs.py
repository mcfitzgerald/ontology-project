#!/usr/bin/env python3
"""
Generate Ontology Documentation from YAML Configuration
Creates human-readable markdown documentation from ontology_spec.yaml
"""

import os
from datetime import datetime
from ontology_config_parser import load_ontology_config


def generate_class_hierarchy_markdown(classes, indent=0):
    """Generate markdown for class hierarchy"""
    result = []
    indent_str = "  " * indent
    
    for class_name, class_info in classes.items():
        # Add class with description
        desc = class_info.get('description', '')
        code = class_info.get('code', '')
        
        if code:
            result.append(f"{indent_str}* {class_name} (e.g., {code})")
        else:
            result.append(f"{indent_str}* {class_name}")
        
        # Add subclasses recursively
        if 'subclasses' in class_info:
            result.extend(generate_class_hierarchy_markdown(class_info['subclasses'], indent + 1))
    
    return result


def generate_ontology_docs(output_path: str = None):
    """Generate markdown documentation from YAML configuration"""
    
    # Load configuration
    parser = load_ontology_config()
    metadata = parser.get_ontology_metadata()
    
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "Tbox_Rbox.md")
    
    print(f"Generating ontology documentation...")
    
    with open(output_path, 'w') as f:
        # Header
        f.write("### **Objective**\n\n")
        f.write(f"{metadata.get('description', 'Manufacturing MES ontology')}\n\n")
        
        # TBox Section
        f.write("### **TBox (The Classes)**\n\n")
        f.write("The class hierarchy represents the core manufacturing concepts:\n\n")
        
        # Generate class hierarchy
        classes = parser.get_classes()
        hierarchy_lines = generate_class_hierarchy_markdown(classes)
        f.write("\n".join(hierarchy_lines))
        f.write("\n\n")
        
        # RBox Section
        f.write("### **RBox (The Properties)**\n\n")
        f.write("The properties map the raw data fields and relationships between entities.\n\n")
        
        # Object Properties Table
        f.write("#### **Object Properties (linking individuals to other individuals)**\n\n")
        f.write("| Property Name | Domain | Range | Description & Purpose |\n")
        f.write("| :---- | :---- | :---- | :---- |\n")
        
        obj_props = parser.get_object_properties()
        for prop_name, prop_info in obj_props.items():
            domain = prop_info.get('domain', '')
            range_val = prop_info.get('range', '')
            desc = prop_info.get('description', '')
            
            # Add inverse info if present
            if 'inverse' in prop_info:
                desc += f" Inverse of {prop_info['inverse']}."
            
            f.write(f"| {prop_name} | {domain} | {range_val} | {desc} |\n")
        
        f.write("\n")
        
        # Data Properties Table
        f.write("#### **Data Properties (linking individuals to literal values)**\n\n")
        f.write("This section maps to every column in mes_data_with_kpis.csv:\n\n")
        f.write("| Property Name | Domain | Range | Maps to Raw Data Column |\n")
        f.write("| :---- | :---- | :---- | :---- |\n")
        
        data_props = parser.get_data_properties()
        for prop_name, prop_info in data_props.items():
            domain = prop_info.get('domain', '')
            range_val = prop_info.get('range', '')
            csv_col = prop_info.get('csv_column', '')
            
            f.write(f"| {prop_name} | {domain} | {range_val} | {csv_col} |\n")
        
        f.write("\n")
        
        # Implementation Notes
        f.write("### **Implementation Notes**\n\n")
        f.write("1. **KPIs are now data properties of Events**: Since KPIs are pre-calculated in the raw data, they are simple data properties rather than separate metric individuals.\n\n")
        f.write("2. **Process Flow Relationships**: The isUpstreamOf/isDownstreamOf relationships must be established based on the configuration during ontology population.\n\n")
        f.write('3. **Event Classification**: Events are classified as either ProductionLog (when MachineStatus = "Running") or DowntimeLog (when MachineStatus = "Stopped").\n\n')
        
        # Benefits
        f.write("### **Simplified Ontology Benefits**\n\n")
        f.write("This streamlined ontology:\n")
        f.write("- Directly mirrors the raw data structure\n")
        f.write("- Eliminates the need for KPI calculation in the ontology layer\n")
        f.write("- Provides all metrics readily available for LLM analysis\n")
        f.write("- Maintains core relationships for semantic reasoning\n")
        f.write("- Reduces complexity while preserving analytical capability\n\n")
        f.write("The LLM can now directly query KPIs and identify patterns without needing to calculate metrics, making the analysis more efficient and scalable.\n")
    
    print(f"Documentation generated: {output_path}")
    
    # Also generate a detailed reference with business contexts
    generate_detailed_reference(parser)


def generate_detailed_reference(parser):
    """Generate a detailed reference document with all business contexts"""
    
    output_path = os.path.join(os.path.dirname(__file__), "Tbox_Rbox_Detailed.md")
    
    print(f"Generating detailed reference documentation...")
    
    with open(output_path, 'w') as f:
        # Header
        f.write("# MES Ontology Detailed Reference\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("This document provides complete details about the MES ontology including business contexts.\n\n")
        
        # Classes with full details
        f.write("## Classes (TBox)\n\n")
        
        for class_name, class_info in parser.get_class_hierarchy():
            parent = class_info.get('parent', 'Thing')
            f.write(f"### {class_name}\n")
            f.write(f"- **Parent**: {parent}\n")
            f.write(f"- **Description**: {class_info.get('description', '')}\n")
            
            if 'business_context' in class_info:
                f.write(f"- **Business Context**: {class_info['business_context']}\n")
            
            if 'code' in class_info:
                f.write(f"- **Code**: {class_info['code']}\n")
            
            if 'equipment_type' in class_info:
                f.write(f"- **Equipment Type**: {class_info['equipment_type']}\n")
            
            if 'condition' in class_info:
                f.write(f"- **Condition**: {class_info['condition']}\n")
            
            f.write("\n")
        
        # Object Properties with full details
        f.write("## Object Properties (RBox)\n\n")
        
        for prop_name, prop_info in parser.get_object_properties().items():
            f.write(f"### {prop_name}\n")
            f.write(f"- **Domain**: {prop_info.get('domain', '')}\n")
            f.write(f"- **Range**: {prop_info.get('range', '')}\n")
            f.write(f"- **Description**: {prop_info.get('description', '')}\n")
            
            if 'business_context' in prop_info:
                f.write(f"- **Business Context**: {prop_info['business_context']}\n")
            
            if 'inverse' in prop_info:
                f.write(f"- **Inverse Property**: {prop_info['inverse']}\n")
            
            f.write("\n")
        
        # Data Properties with full details
        f.write("## Data Properties (RBox)\n\n")
        
        for prop_name, prop_info in parser.get_data_properties().items():
            f.write(f"### {prop_name}\n")
            f.write(f"- **Domain**: {prop_info.get('domain', '')}\n")
            f.write(f"- **Range**: {prop_info.get('range', '')}\n")
            f.write(f"- **CSV Column**: {prop_info.get('csv_column', '')}\n")
            f.write(f"- **Description**: {prop_info.get('description', '')}\n")
            
            if 'data_context' in prop_info:
                f.write(f"- **Data Context**: {prop_info['data_context']}\n")
            
            if 'business_context' in prop_info:
                f.write(f"- **Business Context**: {prop_info['business_context']}\n")
            
            if 'example_value' in prop_info:
                f.write(f"- **Example Value**: {prop_info['example_value']}\n")
            
            if 'typical_value' in prop_info:
                f.write(f"- **Typical Value**: {prop_info['typical_value']}\n")
            
            if 'calculation_method' in prop_info:
                f.write(f"- **Calculation Method**: {prop_info['calculation_method']}\n")
            
            f.write("\n")
        
        # Entity Contexts
        f.write("## Entity Contexts\n\n")
        f.write("Business contexts for specific equipment and product instances:\n\n")
        
        entity_contexts = parser.config.get('entity_contexts', {})
        for entity_name, context in entity_contexts.items():
            f.write(f"### {entity_name}\n")
            f.write(f"{context}\n\n")
        
        # Downtime Mappings
        f.write("## Downtime Code Mappings\n\n")
        
        mappings = parser.get_downtime_mappings()
        for code, class_name in mappings.items():
            f.write(f"- **{code}**: {class_name}\n")
    
    print(f"Detailed reference generated: {output_path}")


def main():
    """Main execution function"""
    # Generate standard Tbox_Rbox.md
    generate_ontology_docs()
    
    print("\nDocumentation generation complete!")
    print("Files generated:")
    print("- Tbox_Rbox.md (standard format)")
    print("- Tbox_Rbox_Detailed.md (detailed reference)")


if __name__ == "__main__":
    main()