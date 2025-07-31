#!/usr/bin/env python3
"""
Ontology Configuration Parser
Loads and parses YAML ontology specification for dynamic ontology generation
"""

import yaml
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class OntologyConfigParser:
    """Parser for ontology specification YAML files"""
    
    def __init__(self, config_path: str = None):
        """Initialize parser with config file path"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "ontology_spec.yaml")
        
        self.config_path = Path(config_path)
        self.config = None
        self._load_config()
        
    def _load_config(self):
        """Load and parse YAML configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Validate basic structure
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration structure"""
        required_sections = ['ontology', 'classes', 'object_properties', 'data_properties']
        missing = [s for s in required_sections if s not in self.config]
        
        if missing:
            raise ValueError(f"Missing required sections in config: {missing}")
        
        # Validate ontology metadata
        ont_meta = self.config.get('ontology', {})
        required_meta = ['name', 'version', 'iri']
        missing_meta = [m for m in required_meta if m not in ont_meta]
        
        if missing_meta:
            raise ValueError(f"Missing required ontology metadata: {missing_meta}")
    
    def get_ontology_metadata(self) -> Dict[str, str]:
        """Get ontology metadata (name, version, IRI)"""
        return self.config.get('ontology', {})
    
    def get_classes(self) -> Dict[str, Any]:
        """Get all class definitions"""
        return self.config.get('classes', {})
    
    def get_class_hierarchy(self, parent_name: str = None) -> List[Tuple[str, Dict]]:
        """Get classes in hierarchical order for creation
        
        Returns list of (class_name, class_info) tuples in order suitable for creation
        """
        classes = self.get_classes()
        result = []
        
        def process_class(name: str, info: Dict, parent: str = None):
            """Recursively process class and its subclasses"""
            # Add parent info for creation
            class_info = info.copy()
            class_info['parent'] = parent
            result.append((name, class_info))
            
            # Process subclasses
            subclasses = info.get('subclasses', {})
            for subclass_name, subclass_info in subclasses.items():
                process_class(subclass_name, subclass_info, name)
        
        # Process top-level classes
        if parent_name:
            if parent_name in classes:
                process_class(parent_name, classes[parent_name])
        else:
            for class_name, class_info in classes.items():
                process_class(class_name, class_info)
        
        return result
    
    def get_object_properties(self) -> Dict[str, Dict]:
        """Get all object property definitions"""
        return self.config.get('object_properties', {})
    
    def get_data_properties(self) -> Dict[str, Dict]:
        """Get all data property definitions"""
        return self.config.get('data_properties', {})
    
    def get_downtime_mappings(self) -> Dict[str, str]:
        """Get downtime reason code to class mappings"""
        return self.config.get('downtime_mappings', {})
    
    def get_entity_context(self, entity_name: str) -> Optional[str]:
        """Get business context for a specific entity"""
        contexts = self.config.get('entity_contexts', {})
        return contexts.get(entity_name)
    
    def get_equipment_type_mapping(self) -> Dict[str, str]:
        """Build equipment type to class name mapping"""
        mapping = {}
        classes = self.get_class_hierarchy()
        
        for class_name, class_info in classes:
            if 'equipment_type' in class_info:
                mapping[class_info['equipment_type']] = class_name
        
        return mapping
    
    def get_class_by_code(self, code: str) -> Optional[str]:
        """Find class name by its code (e.g., PLN-CO -> Changeover)"""
        classes = self.get_class_hierarchy()
        
        for class_name, class_info in classes:
            if class_info.get('code') == code:
                return class_name
        
        # Fallback to downtime mappings
        return self.get_downtime_mappings().get(code)
    
    def get_property_column_mapping(self) -> Dict[str, str]:
        """Get mapping of property names to CSV columns"""
        mapping = {}
        
        for prop_name, prop_info in self.get_data_properties().items():
            if 'csv_column' in prop_info:
                mapping[prop_name] = prop_info['csv_column']
        
        return mapping
    
    def get_inverse_properties(self) -> Dict[str, str]:
        """Get mapping of properties to their inverses"""
        mapping = {}
        
        for prop_name, prop_info in self.get_object_properties().items():
            if 'inverse' in prop_info:
                mapping[prop_name] = prop_info['inverse']
                # Also add the reverse mapping
                mapping[prop_info['inverse']] = prop_name
        
        return mapping
    
    def validate_domain_range(self, property_name: str, domain_class: str, range_class: str) -> bool:
        """Validate that domain and range classes exist"""
        all_classes = {name for name, _ in self.get_class_hierarchy()}
        
        # Check if domain exists
        if domain_class not in all_classes:
            print(f"Warning: Domain class '{domain_class}' not found for property '{property_name}'")
            return False
        
        # Check if range exists (for object properties)
        obj_props = self.get_object_properties()
        if property_name in obj_props and range_class not in all_classes:
            print(f"Warning: Range class '{range_class}' not found for property '{property_name}'")
            return False
        
        return True
    
    def get_kpi_properties(self) -> List[str]:
        """Get list of KPI-related properties"""
        kpi_props = []
        
        for prop_name, prop_info in self.get_data_properties().items():
            if 'Score' in prop_name or prop_name in ['hasOEEScore', 'hasAvailabilityScore', 
                                                      'hasPerformanceScore', 'hasQualityScore']:
                kpi_props.append(prop_name)
        
        return kpi_props
    
    def get_type_mapping(self, range_type: str) -> str:
        """Map YAML range types to owlready2 types"""
        type_map = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'datetime': str  # Store as ISO string
        }
        return type_map.get(range_type, str)


def load_ontology_config(config_path: str = None) -> OntologyConfigParser:
    """Convenience function to load configuration"""
    return OntologyConfigParser(config_path)


# Helper functions for ontology creation
def create_class_from_config(onto, class_name: str, class_info: Dict, parent_class=None):
    """Create an owlready2 class from configuration
    
    Args:
        onto: The ontology object
        class_name: Name of the class to create
        class_info: Dictionary with class information
        parent_class: Parent class object (default: Thing)
    
    Returns:
        The created class
    """
    if parent_class is None:
        parent_class = onto.Thing
    
    # Create the class dynamically
    with onto:
        new_class = type(class_name, (parent_class,), {})
        
        # Add description as comment if available
        if 'description' in class_info:
            new_class.comment = [class_info['description']]
        
        # Add label
        new_class.label = [class_name]
    
    return new_class


def create_object_property_from_config(onto, prop_name: str, prop_info: Dict, class_map: Dict):
    """Create an owlready2 object property from configuration
    
    Args:
        onto: The ontology object
        prop_name: Name of the property
        prop_info: Dictionary with property information
        class_map: Dictionary mapping class names to class objects
    
    Returns:
        The created property
    """
    with onto:
        # Get domain and range classes
        domain_name = prop_info.get('domain')
        range_name = prop_info.get('range')
        
        domain_class = class_map.get(domain_name, onto.Thing)
        range_class = class_map.get(range_name, onto.Thing)
        
        # Create the property
        new_prop = type(prop_name, (domain_class >> range_class,), {})
        
        # Add metadata
        if 'description' in prop_info:
            new_prop.comment = [prop_info['description']]
        
        new_prop.label = [prop_name]
        
        # Handle inverse property
        if 'inverse' in prop_info:
            inverse_name = prop_info['inverse']
            # The inverse will be set up when processing the inverse property
    
    return new_prop


def create_data_property_from_config(onto, prop_name: str, prop_info: Dict, class_map: Dict):
    """Create an owlready2 data property from configuration
    
    Args:
        onto: The ontology object
        prop_name: Name of the property
        prop_info: Dictionary with property information
        class_map: Dictionary mapping class names to class objects
    
    Returns:
        The created property
    """
    from owlready2 import DataProperty
    
    with onto:
        # Create base data property using DataProperty class directly
        new_prop = type(prop_name, (DataProperty,), {"namespace": onto})
        
        # Set domain
        domain_name = prop_info.get('domain')
        if domain_name and domain_name in class_map:
            new_prop.domain = [class_map[domain_name]]
        
        # Set range
        range_type = prop_info.get('range', 'string')
        type_mapping = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'datetime': str
        }
        new_prop.range = [type_mapping.get(range_type, str)]
        
        # Add metadata
        if 'description' in prop_info:
            new_prop.comment = [prop_info['description']]
        
        new_prop.label = [prop_name]
    
    return new_prop


if __name__ == "__main__":
    # Test the parser
    parser = OntologyConfigParser()
    
    print("Ontology Metadata:")
    print(parser.get_ontology_metadata())
    
    print("\nClass Hierarchy:")
    for class_name, class_info in parser.get_class_hierarchy()[:5]:
        parent = class_info.get('parent', 'Thing')
        print(f"  {class_name} (parent: {parent})")
    
    print("\nObject Properties:")
    for prop_name, prop_info in list(parser.get_object_properties().items())[:3]:
        print(f"  {prop_name}: {prop_info.get('domain')} -> {prop_info.get('range')}")
    
    print("\nData Properties:")
    for prop_name, prop_info in list(parser.get_data_properties().items())[:3]:
        print(f"  {prop_name}: {prop_info.get('domain')} -> {prop_info.get('range')}")