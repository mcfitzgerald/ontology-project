"""
Ontology Knowledge Management System

This module provides static ontology knowledge caching and retrieval functionality.
It parses TTL files to extract equipment types, metrics, properties, and relationships,
caching the results for fast access without requiring SPARQL queries.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime
import re

class OntologyKnowledge:
    """
    Manages static ontology knowledge extracted from TTL files.
    
    This class provides:
    - Parsing of TTL ontology files
    - Caching of parsed data for performance
    - Methods to determine if questions can be answered without SPARQL
    - Summaries of available ontology data
    """
    
    def __init__(self, ttl_file_path: str = None, cache_dir: str = None):
        """
        Initialize the OntologyKnowledge system.
        
        Args:
            ttl_file_path: Path to TTL file (defaults to mes_ontology_mindmap.ttl)
            cache_dir: Directory for cache files (defaults to adk_agents/cache)
        """
        # Set default paths
        project_root = Path(__file__).parent.parent.parent
        self.ttl_file_path = ttl_file_path or str(project_root / "Context" / "mes_ontology_mindmap.ttl")
        self.cache_dir = Path(cache_dir or (project_root / "adk_agents" / "cache"))
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize namespace prefix
        self.MES_NAMESPACE = "http://mes-ontology.org/factory.owl#"
        
        # Storage for parsed ontology data
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.object_properties: Dict[str, Dict[str, Any]] = {}
        self.data_properties: Dict[str, Dict[str, Any]] = {}
        self.individuals: Dict[str, Dict[str, Any]] = {}
        self.annotations: Dict[str, Dict[str, Any]] = {}
        
        # Additional indices for fast lookup
        self.class_hierarchy: Dict[str, List[str]] = {}
        self.property_domains: Dict[str, List[str]] = {}
        self.property_ranges: Dict[str, List[str]] = {}
        self.equipment_types: Set[str] = set()
        self.metrics: Set[str] = set()
        self.csv_mappings: Dict[str, str] = {}
        
        # Load or parse the ontology
        self._load_ontology()
    
    def _get_cache_path(self) -> Path:
        """Get the cache file path based on TTL file hash."""
        # Create hash of TTL file path for unique cache file
        path_hash = hashlib.md5(str(self.ttl_file_path).encode()).hexdigest()[:8]
        return self.cache_dir / f"ontology_knowledge_{path_hash}.json"
    
    def _is_cache_valid(self) -> bool:
        """Check if cache exists and is newer than TTL file."""
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return False
        
        ttl_path = Path(self.ttl_file_path)
        if not ttl_path.exists():
            return False
        
        # Compare modification times
        cache_mtime = cache_path.stat().st_mtime
        ttl_mtime = ttl_path.stat().st_mtime
        
        return cache_mtime > ttl_mtime
    
    def _load_ontology(self):
        """Load ontology from cache or parse TTL file."""
        if self._is_cache_valid():
            self._load_from_cache()
        else:
            self._parse_ttl_file()
            self._save_to_cache()
    
    def _load_from_cache(self):
        """Load parsed ontology data from cache."""
        cache_path = self._get_cache_path()
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Restore data structures
            self.classes = data.get('classes', {})
            self.object_properties = data.get('object_properties', {})
            self.data_properties = data.get('data_properties', {})
            self.individuals = data.get('individuals', {})
            self.annotations = data.get('annotations', {})
            self.class_hierarchy = data.get('class_hierarchy', {})
            self.property_domains = data.get('property_domains', {})
            self.property_ranges = data.get('property_ranges', {})
            self.equipment_types = set(data.get('equipment_types', []))
            self.metrics = set(data.get('metrics', []))
            self.csv_mappings = data.get('csv_mappings', {})
            
            print(f"Loaded ontology knowledge from cache: {cache_path}")
        except Exception as e:
            print(f"Error loading cache, will parse TTL file: {e}")
            self._parse_ttl_file()
            self._save_to_cache()
    
    def _save_to_cache(self):
        """Save parsed ontology data to cache."""
        cache_path = self._get_cache_path()
        
        # Prepare data for JSON serialization
        data = {
            'classes': self.classes,
            'object_properties': self.object_properties,
            'data_properties': self.data_properties,
            'individuals': self.individuals,
            'annotations': self.annotations,
            'class_hierarchy': self.class_hierarchy,
            'property_domains': self.property_domains,
            'property_ranges': self.property_ranges,
            'equipment_types': list(self.equipment_types),
            'metrics': list(self.metrics),
            'csv_mappings': self.csv_mappings,
            'cached_at': datetime.now().isoformat()
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved ontology knowledge to cache: {cache_path}")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _parse_ttl_file(self):
        """Parse the TTL file and extract ontology information using regex."""
        print(f"Parsing TTL file: {self.ttl_file_path}")
        
        # Read the TTL file
        with open(self.ttl_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove comments but preserve annotations
        lines = []
        for line in content.split('\n'):
            # Keep lines that are not just comments
            if line.strip() and not (line.strip().startswith('#') and not line.strip().startswith('##')):
                lines.append(line)
        
        content = '\n'.join(lines)
        
        # Parse classes
        class_pattern = r':(\w+)\s+a\s+owl:Class\s*(?:;|\.)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            self.classes[class_name] = {
                'uri': self.MES_NAMESPACE + class_name,
                'label': class_name,
                'subclass_of': [],
                'annotations': {}
            }
        
        # Parse subclass relationships
        subclass_pattern = r':(\w+)\s+a\s+owl:Class\s*;\s*rdfs:subClassOf\s+:(\w+)'
        for match in re.finditer(subclass_pattern, content):
            child_class = match.group(1)
            parent_class = match.group(2)
            
            if child_class in self.classes:
                self.classes[child_class]['subclass_of'].append(parent_class)
                
                # Build hierarchy index
                if parent_class not in self.class_hierarchy:
                    self.class_hierarchy[parent_class] = []
                self.class_hierarchy[parent_class].append(child_class)
                
                # Check if it's an equipment type
                if parent_class == 'Equipment':
                    self.equipment_types.add(child_class)
        
        # Parse object properties
        obj_prop_pattern = r':(\w+)\s+a\s+owl:ObjectProperty\s*[;.]'
        for match in re.finditer(obj_prop_pattern, content):
            prop_name = match.group(1)
            self.object_properties[prop_name] = {
                'uri': self.MES_NAMESPACE + prop_name,
                'label': prop_name,
                'domain': [],
                'range': [],
                'annotations': {}
            }
        
        # Parse object property domains and ranges
        domain_pattern = r':(\w+)\s+a\s+owl:ObjectProperty\s*;[^.]*rdfs:domain\s+:(\w+)'
        for match in re.finditer(domain_pattern, content, re.DOTALL):
            prop_name = match.group(1)
            domain_class = match.group(2)
            
            if prop_name in self.object_properties:
                self.object_properties[prop_name]['domain'].append(domain_class)
                
                # Build domain index
                if domain_class not in self.property_domains:
                    self.property_domains[domain_class] = []
                self.property_domains[domain_class].append(prop_name)
        
        range_pattern = r':(\w+)\s+a\s+owl:ObjectProperty\s*;[^.]*rdfs:range\s+:(\w+)'
        for match in re.finditer(range_pattern, content, re.DOTALL):
            prop_name = match.group(1)
            range_class = match.group(2)
            
            if prop_name in self.object_properties:
                self.object_properties[prop_name]['range'].append(range_class)
                
                # Build range index
                if range_class not in self.property_ranges:
                    self.property_ranges[range_class] = []
                self.property_ranges[range_class].append(prop_name)
        
        # Parse data properties
        data_prop_pattern = r':(\w+)\s+a\s+owl:DatatypeProperty\s*[;.]'
        for match in re.finditer(data_prop_pattern, content):
            prop_name = match.group(1)
            self.data_properties[prop_name] = {
                'uri': self.MES_NAMESPACE + prop_name,
                'label': prop_name,
                'domain': [],
                'range': [],
                'annotations': {}
            }
            
            # Check if it's a metric
            if 'Score' in prop_name or 'OEE' in prop_name or 'Rate' in prop_name:
                self.metrics.add(prop_name)
        
        # Parse data property domains
        data_domain_pattern = r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*rdfs:domain\s+:(\w+)'
        for match in re.finditer(data_domain_pattern, content, re.DOTALL):
            prop_name = match.group(1)
            domain_class = match.group(2)
            
            if prop_name in self.data_properties:
                self.data_properties[prop_name]['domain'].append(domain_class)
        
        # Parse data property ranges
        data_range_pattern = r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*rdfs:range\s+xsd:(\w+)'
        for match in re.finditer(data_range_pattern, content, re.DOTALL):
            prop_name = match.group(1)
            range_type = match.group(2)
            
            if prop_name in self.data_properties:
                self.data_properties[prop_name]['range'].append(range_type)
        
        # Parse annotations (mapsToColumn, dataContext, etc.)
        annotation_patterns = {
            'mapsToColumn': r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*:mapsToColumn\s+"([^"]+)"',
            'dataContext': r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*:dataContext\s+"([^"]+)"',
            'typicalValue': r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*:typicalValue\s+"([^"]+)"',
            'calculationMethod': r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*:calculationMethod\s+"([^"]+)"',
            'exampleValue': r':(\w+)\s+a\s+owl:DatatypeProperty\s*;[^.]*:exampleValue\s+"([^"]+)"'
        }
        
        for annotation_name, pattern in annotation_patterns.items():
            for match in re.finditer(pattern, content, re.DOTALL):
                prop_name = match.group(1)
                value = match.group(2)
                
                if prop_name in self.data_properties:
                    self.data_properties[prop_name]['annotations'][annotation_name] = value
                    
                    # Build CSV mapping index
                    if annotation_name == 'mapsToColumn':
                        self.csv_mappings[value] = prop_name
        
        # Parse individuals (examples)
        individual_pattern = r':([A-Z][A-Z0-9\-]+)\s+a\s+:(\w+)\s*[;.]'
        for match in re.finditer(individual_pattern, content):
            ind_name = match.group(1)
            type_name = match.group(2)
            
            # Only process if type is a known class
            if type_name in self.classes:
                if ind_name not in self.individuals:
                    self.individuals[ind_name] = {
                        'uri': self.MES_NAMESPACE + ind_name,
                        'label': ind_name,
                        'types': [],
                        'properties': {}
                    }
                
                self.individuals[ind_name]['types'].append(type_name)
        
        # Parse individual properties
        ind_prop_pattern = r':([A-Z][A-Z0-9\-]+)\s+(?:a\s+:\w+\s*;[^.]*)?:(\w+)\s+(?::([A-Z][A-Z0-9\-]+)|"([^"]+)"|\d+(?:\.\d+)?)'
        for match in re.finditer(ind_prop_pattern, content, re.DOTALL):
            ind_name = match.group(1)
            prop_name = match.group(2)
            obj_value = match.group(3)
            lit_value = match.group(4)
            
            if ind_name in self.individuals and prop_name != 'label':
                value = obj_value if obj_value else lit_value if lit_value else match.group(0).split()[-1]
                
                if prop_name not in self.individuals[ind_name]['properties']:
                    self.individuals[ind_name]['properties'][prop_name] = []
                self.individuals[ind_name]['properties'][prop_name].append(value)
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract the local name from a URI."""
        if '#' in uri:
            return uri.split('#')[-1]
        else:
            return uri.split('/')[-1]
    
    def can_answer_without_query(self, question: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if a question can be answered using static ontology knowledge.
        
        Args:
            question: The user's question
            
        Returns:
            Tuple of (can_answer, answer) where answer is provided if can_answer is True
        """
        question_lower = question.lower()
        
        # Check for equipment type questions
        if any(phrase in question_lower for phrase in ['what equipment types', 'types of equipment', 
                                                       'list equipment types', 'kinds of equipment']):
            equipment_list = sorted(list(self.equipment_types))
            answer = f"The ontology defines these equipment types: {', '.join(equipment_list)}"
            if self.class_hierarchy.get('Equipment'):
                answer += f"\n\nAll equipment types are subclasses of Equipment: {', '.join(self.class_hierarchy['Equipment'])}"
            return True, answer
        
        # Check for metric questions
        if any(phrase in question_lower for phrase in ['what metrics', 'available metrics', 
                                                       'list metrics', 'performance metrics']):
            metrics_list = sorted(list(self.metrics))
            answer = f"The ontology defines these metrics: {', '.join(metrics_list)}"
            
            # Add details about OEE if mentioned
            if 'oee' in question_lower and 'hasOEEScore' in self.data_properties:
                oee_info = self.data_properties['hasOEEScore']
                answer += f"\n\nOEE (Overall Equipment Effectiveness):"
                if 'calculationMethod' in oee_info.get('annotations', {}):
                    answer += f"\n- Calculation: {oee_info['annotations']['calculationMethod']}"
                if 'typicalValue' in oee_info.get('annotations', {}):
                    answer += f"\n- Typical value: {oee_info['annotations']['typicalValue']}"
            
            return True, answer
        
        # Check for property questions
        if any(phrase in question_lower for phrase in ['what properties', 'list properties', 
                                                       'available properties']):
            obj_props = sorted(list(self.object_properties.keys()))
            data_props = sorted(list(self.data_properties.keys()))
            
            answer = f"Object Properties (relationships): {', '.join(obj_props[:10])}"
            if len(obj_props) > 10:
                answer += f" (and {len(obj_props) - 10} more)"
            
            answer += f"\n\nData Properties (attributes): {', '.join(data_props[:10])}"
            if len(data_props) > 10:
                answer += f" (and {len(data_props) - 10} more)"
            
            return True, answer
        
        # Check for class hierarchy questions
        if any(phrase in question_lower for phrase in ['class hierarchy', 'subclasses of', 
                                                       'parent class', 'inheritance']):
            # Extract class name from question
            for class_name in self.classes:
                if class_name.lower() in question_lower:
                    if class_name in self.class_hierarchy:
                        subclasses = self.class_hierarchy[class_name]
                        answer = f"Subclasses of {class_name}: {', '.join(subclasses)}"
                    else:
                        answer = f"{class_name} has no subclasses defined."
                    
                    if self.classes[class_name]['subclass_of']:
                        answer += f"\n{class_name} is a subclass of: {', '.join(self.classes[class_name]['subclass_of'])}"
                    
                    return True, answer
        
        # Check for CSV mapping questions
        if any(phrase in question_lower for phrase in ['csv', 'column', 'mapping', 'maps to']):
            # Look for specific property or column mentions
            for csv_col, prop_name in self.csv_mappings.items():
                if csv_col.lower() in question_lower or prop_name.lower() in question_lower:
                    answer = f"CSV column '{csv_col}' maps to property '{prop_name}'"
                    
                    # Add additional context if available
                    if prop_name in self.data_properties:
                        prop_info = self.data_properties[prop_name]
                        if 'dataContext' in prop_info.get('annotations', {}):
                            answer += f"\nContext: {prop_info['annotations']['dataContext']}"
                    
                    return True, answer
        
        # Check for example/individual questions
        if any(phrase in question_lower for phrase in ['example', 'instance', 'individual']):
            # Look for specific class mentions
            for class_name in self.classes:
                if class_name.lower() in question_lower:
                    examples = [ind for ind, info in self.individuals.items() 
                               if class_name in info['types']]
                    if examples:
                        answer = f"Example {class_name} individuals: {', '.join(examples[:5])}"
                        if len(examples) > 5:
                            answer += f" (and {len(examples) - 5} more)"
                        
                        # Show details for first example
                        if examples:
                            first_example = self.individuals[examples[0]]
                            answer += f"\n\nDetails for {examples[0]}:"
                            answer += f"\n- Label: {first_example['label']}"
                            if first_example['properties']:
                                answer += "\n- Properties:"
                                for prop, values in list(first_example['properties'].items())[:5]:
                                    answer += f"\n  - {prop}: {', '.join(values)}"
                        
                        return True, answer
        
        return False, None
    
    def get_available_data_summary(self) -> str:
        """
        Get a comprehensive summary of available ontology data.
        
        Returns:
            String summary of ontology contents
        """
        summary = "=== Ontology Knowledge Summary ===\n\n"
        
        # Classes summary
        summary += f"Classes: {len(self.classes)} total\n"
        summary += f"- Equipment Types: {', '.join(sorted(list(self.equipment_types)))}\n"
        summary += f"- Event Types: {', '.join([c for c in self.classes if 'Event' in c or 'Log' in c])}\n"
        summary += f"- Other Classes: {', '.join([c for c in self.classes if c not in self.equipment_types and 'Event' not in c and 'Log' not in c])}\n\n"
        
        # Properties summary
        summary += f"Object Properties: {len(self.object_properties)} total\n"
        summary += f"- Key relationships: {', '.join(list(self.object_properties.keys())[:10])}\n\n"
        
        summary += f"Data Properties: {len(self.data_properties)} total\n"
        summary += f"- Metrics: {', '.join(sorted(list(self.metrics)))}\n"
        summary += f"- Other attributes: {', '.join([p for p in list(self.data_properties.keys()) if p not in self.metrics][:10])}\n\n"
        
        # CSV mappings summary
        summary += f"CSV Mappings: {len(self.csv_mappings)} columns mapped\n"
        for i, (csv_col, prop) in enumerate(list(self.csv_mappings.items())[:5]):
            summary += f"- {csv_col} → {prop}\n"
        if len(self.csv_mappings) > 5:
            summary += f"- ... and {len(self.csv_mappings) - 5} more\n"
        summary += "\n"
        
        # Individuals summary
        summary += f"Example Individuals: {len(self.individuals)} total\n"
        
        # Group by type
        type_counts = {}
        for ind_info in self.individuals.values():
            for type_name in ind_info['types']:
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        for type_name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            summary += f"- {type_name}: {count} examples\n"
        
        # Add note about SPARQL prefix
        summary += "\n=== Important SPARQL Note ===\n"
        summary += "All SPARQL queries must use the prefix 'mes_ontology_populated:' for ontology terms.\n"
        summary += "Example: mes_ontology_populated:hasOEEScore (not mes:hasOEEScore)\n"
        
        return summary
    
    def get_property_info(self, property_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific property.
        
        Args:
            property_name: Name of the property
            
        Returns:
            Dictionary with property information or None if not found
        """
        # Check data properties first
        if property_name in self.data_properties:
            return {
                'type': 'data_property',
                **self.data_properties[property_name]
            }
        
        # Check object properties
        if property_name in self.object_properties:
            return {
                'type': 'object_property',
                **self.object_properties[property_name]
            }
        
        return None
    
    def get_class_info(self, class_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific class.
        
        Args:
            class_name: Name of the class
            
        Returns:
            Dictionary with class information or None if not found
        """
        if class_name not in self.classes:
            return None
        
        info = self.classes[class_name].copy()
        
        # Add subclasses if any
        if class_name in self.class_hierarchy:
            info['subclasses'] = self.class_hierarchy[class_name]
        
        # Add properties that have this class as domain
        info['properties'] = []
        for prop_name, prop_info in self.data_properties.items():
            if class_name in prop_info['domain']:
                info['properties'].append({
                    'name': prop_name,
                    'type': 'data_property',
                    'range': prop_info['range']
                })
        
        for prop_name, prop_info in self.object_properties.items():
            if class_name in prop_info['domain']:
                info['properties'].append({
                    'name': prop_name,
                    'type': 'object_property',
                    'range': prop_info['range']
                })
        
        # Add example individuals
        info['examples'] = [ind for ind, ind_info in self.individuals.items() 
                           if class_name in ind_info['types']]
        
        return info
    
    def search_ontology(self, search_term: str) -> Dict[str, List[str]]:
        """
        Search for a term across all ontology components.
        
        Args:
            search_term: Term to search for
            
        Returns:
            Dictionary with matches organized by type
        """
        search_lower = search_term.lower()
        results = {
            'classes': [],
            'object_properties': [],
            'data_properties': [],
            'individuals': [],
            'csv_columns': []
        }
        
        # Search classes
        for class_name in self.classes:
            if search_lower in class_name.lower() or search_lower in self.classes[class_name]['label'].lower():
                results['classes'].append(class_name)
        
        # Search object properties
        for prop_name in self.object_properties:
            if search_lower in prop_name.lower() or search_lower in self.object_properties[prop_name]['label'].lower():
                results['object_properties'].append(prop_name)
        
        # Search data properties
        for prop_name in self.data_properties:
            if search_lower in prop_name.lower() or search_lower in self.data_properties[prop_name]['label'].lower():
                results['data_properties'].append(prop_name)
        
        # Search individuals
        for ind_name in self.individuals:
            if search_lower in ind_name.lower() or search_lower in self.individuals[ind_name]['label'].lower():
                results['individuals'].append(ind_name)
        
        # Search CSV columns
        for csv_col in self.csv_mappings:
            if search_lower in csv_col.lower():
                results['csv_columns'].append(csv_col)
        
        return results


# Example usage and testing
if __name__ == "__main__":
    # Initialize the knowledge base
    kb = OntologyKnowledge()
    
    # Print summary
    print(kb.get_available_data_summary())
    
    # Test some queries
    test_questions = [
        "What equipment types are available?",
        "What metrics can I query?",
        "What are the subclasses of Equipment?",
        "What CSV column maps to OEE?",
        "Show me examples of Filler equipment"
    ]
    
    print("\n=== Testing Question Answering ===\n")
    for question in test_questions:
        can_answer, answer = kb.can_answer_without_query(question)
        print(f"Q: {question}")
        print(f"Can answer without SPARQL: {can_answer}")
        if answer:
            print(f"A: {answer}")
        print()
    
    # Test search
    print("\n=== Testing Search ===\n")
    search_results = kb.search_ontology("OEE")
    print(f"Search results for 'OEE':")
    for category, items in search_results.items():
        if items:
            print(f"- {category}: {items}")