"""
Ontology Explorer Tool for Google ADK - discovers structure and business context.
"""
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from ..config.settings import MINDMAP_FILE, ONTOLOGY_NAMESPACE, OWLREADY2_SPARQL_GUIDE


class OntologyExplorationParams(BaseModel):
    """Parameters for ontology exploration."""
    entity_type: Optional[str] = Field(None, description="Type of entity to explore (e.g., Equipment, Product)")
    relationship: Optional[str] = Field(None, description="Specific relationship to trace")
    include_annotations: bool = Field(True, description="Include business context annotations")
    depth: int = Field(1, description="Depth of relationship exploration")


class OntologyExplorer:
    """Explores ontology structure and extracts business context."""
    
    def __init__(self):
        self.namespace = ONTOLOGY_NAMESPACE
        self.entities = {}
        self.relationships = {}
        self.annotations = {}
        self.sparql_reference = {}
        self._load_mindmap()
        self._load_sparql_reference()
    
    def _load_mindmap(self):
        """Load and parse the ontology mindmap."""
        if not MINDMAP_FILE.exists():
            print(f"Warning: Mindmap file not found at {MINDMAP_FILE}")
            return
        
        try:
            with open(MINDMAP_FILE, 'r') as f:
                content = f.read()
            
            # Parse entities, relationships, and annotations
            self._parse_classes(content)
            self._parse_properties(content)
            self._parse_annotations(content)
            
        except Exception as e:
            print(f"Error loading mindmap: {e}")
    
    def _parse_classes(self, content: str):
        """Parse class definitions from mindmap."""
        # Pattern for class definitions
        class_pattern = r':(\w+)\s+a\s+owl:Class\s*;?\s*(?:;\s*rdfs:comment\s+"([^"]+)")?'
        
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            comment = match.group(2) or ""
            
            self.entities[class_name] = {
                'type': 'Class',
                'description': comment,
                'properties': [],
                'relationships': []
            }
    
    def _parse_properties(self, content: str):
        """Parse property definitions from mindmap."""
        # Pattern for data properties
        data_prop_pattern = r':(\w+)\s+a\s+owl:DatatypeProperty\s*;?\s*(?:;\s*rdfs:comment\s+"([^"]+)")?'
        
        for match in re.finditer(data_prop_pattern, content):
            prop_name = match.group(1)
            comment = match.group(2) or ""
            
            self.entities[prop_name] = {
                'type': 'DataProperty',
                'description': comment
            }
        
        # Pattern for object properties (relationships)
        obj_prop_pattern = r':(\w+)\s+a\s+owl:ObjectProperty\s*;?\s*(?:;\s*rdfs:comment\s+"([^"]+)")?'
        
        for match in re.finditer(obj_prop_pattern, content):
            prop_name = match.group(1)
            comment = match.group(2) or ""
            
            self.relationships[prop_name] = {
                'type': 'ObjectProperty',
                'description': comment
            }
    
    def _parse_annotations(self, content: str):
        """Parse business context annotations."""
        # Pattern for custom annotations
        annotation_pattern = r':(\w+)\s+:businessContext\s+"([^"]+)"'
        
        for match in re.finditer(annotation_pattern, content):
            entity = match.group(1)
            context = match.group(2)
            
            if entity not in self.annotations:
                self.annotations[entity] = []
            self.annotations[entity].append(context)
    
    def _load_sparql_reference(self):
        """Load SPARQL reference guide."""
        if not OWLREADY2_SPARQL_GUIDE.exists():
            print(f"Warning: SPARQL reference file not found at {OWLREADY2_SPARQL_GUIDE}")
            return
        
        try:
            with open(OWLREADY2_SPARQL_GUIDE, 'r') as f:
                content = f.read()
            
            # Parse key sections
            self.sparql_reference = {
                'rules': self._extract_rules(content),
                'patterns': self._extract_patterns(content),
                'examples': self._extract_examples(content)
            }
            
        except Exception as e:
            print(f"Error loading SPARQL reference: {e}")
    
    def _extract_rules(self, content: str) -> List[str]:
        """Extract key rules from SPARQL reference."""
        rules = []
        # Find rules section
        rules_match = re.search(r'## Key Rules.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
        if rules_match:
            rules_text = rules_match.group(1)
            # Extract numbered rules
            rule_pattern = r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|\Z)'
            for match in re.finditer(rule_pattern, rules_text, re.DOTALL):
                rules.append(match.group(1).strip())
        return rules
    
    def _extract_patterns(self, content: str) -> Dict[str, str]:
        """Extract SPARQL patterns from reference."""
        patterns = {}
        # Find pattern sections
        pattern_matches = re.finditer(r'### (.+?)\n```sparql\n(.*?)\n```', content, re.DOTALL)
        for match in pattern_matches:
            pattern_name = match.group(1).strip()
            pattern_query = match.group(2).strip()
            patterns[pattern_name] = pattern_query
        return patterns
    
    def _extract_examples(self, content: str) -> List[Dict[str, str]]:
        """Extract example queries from reference."""
        examples = []
        # Find example sections
        example_matches = re.finditer(r'Example: (.+?)\n```sparql\n(.*?)\n```', content, re.DOTALL)
        for match in example_matches:
            examples.append({
                'description': match.group(1).strip(),
                'query': match.group(2).strip()
            })
        return examples
    
    def explore_entity(self, entity_name: str) -> Dict[str, Any]:
        """Explore a specific entity and its context."""
        result = {
            'entity': entity_name,
            'found': False,
            'details': {},
            'business_context': []
        }
        
        # Check if entity exists
        if entity_name in self.entities:
            result['found'] = True
            result['details'] = self.entities[entity_name]
            
            # Add business context
            if entity_name in self.annotations:
                result['business_context'] = self.annotations[entity_name]
        
        return result
    
    def list_entities_by_type(self, entity_type: str) -> List[str]:
        """List all entities of a specific type."""
        return [name for name, info in self.entities.items() 
                if info.get('type', '').lower() == entity_type.lower()]
    
    def get_relationships(self) -> Dict[str, Any]:
        """Get all defined relationships."""
        return self.relationships
    
    def get_business_context(self, entity: str) -> List[str]:
        """Get business context annotations for an entity."""
        return self.annotations.get(entity, [])


# Create singleton explorer
explorer = OntologyExplorer()


async def explore_ontology_structure(
    entity_type: Optional[str] = None,
    relationship: Optional[str] = None,
    include_annotations: bool = True,
    depth: int = 1
) -> Dict[str, Any]:
    """
    Discover ontology structure, relationships, and business context.
    
    Args:
        entity_type: Type of entity to explore (e.g., Equipment, Product)
        relationship: Specific relationship to trace
        include_annotations: Include business context annotations
        depth: Depth of relationship exploration
    
    Returns:
        Dictionary containing discovered structure and context
    """
    result = {
        'success': True,
        'discoveries': {}
    }
    
    try:
        # If entity_type specified, list all entities of that type
        if entity_type:
            entities = explorer.list_entities_by_type(entity_type)
            result['discoveries']['entities'] = {
                'type': entity_type,
                'count': len(entities),
                'list': entities[:10]  # Limit to first 10
            }
            
            # Include sample business context
            if include_annotations and entities:
                sample_contexts = {}
                for entity in entities[:3]:  # Sample first 3
                    context = explorer.get_business_context(entity)
                    if context:
                        sample_contexts[entity] = context
                
                if sample_contexts:
                    result['discoveries']['business_contexts'] = sample_contexts
        
        # If relationship specified, show relationship info
        if relationship:
            rel_info = explorer.relationships.get(relationship, {})
            result['discoveries']['relationship'] = {
                'name': relationship,
                'info': rel_info
            }
        
        # If neither specified, return overview
        if not entity_type and not relationship:
            result['discoveries']['overview'] = {
                'total_entities': len(explorer.entities),
                'total_relationships': len(explorer.relationships),
                'entity_types': list(set(e.get('type', '') for e in explorer.entities.values())),
                'key_relationships': list(explorer.relationships.keys())[:10],
                'annotated_entities': len(explorer.annotations)
            }
        
    except Exception as e:
        result['success'] = False
        result['error'] = f"Exploration failed: {str(e)}"
    
    return result


async def get_business_context(entity: str) -> Dict[str, Any]:
    """
    Extract business context annotations for an entity.
    
    Args:
        entity: Name of the entity
    
    Returns:
        Dictionary containing business context information
    """
    try:
        contexts = explorer.get_business_context(entity)
        entity_info = explorer.explore_entity(entity)
        
        return {
            'success': True,
            'entity': entity,
            'exists': entity_info['found'],
            'type': entity_info['details'].get('type') if entity_info['found'] else None,
            'description': entity_info['details'].get('description') if entity_info['found'] else None,
            'business_contexts': contexts,
            'context_count': len(contexts)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to get business context: {str(e)}"
        }


# Create ADK tools
# FunctionTool automatically extracts metadata from the function's docstring
ontology_explorer_tool = FunctionTool(explore_ontology_structure)

get_context_tool = FunctionTool(get_business_context)