"""
Lightweight context loader for agent system prompts.
Loads ontology structure, SPARQL reference, and learned patterns.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ContextLoader:
    """Dynamically loads and manages context for agent prompts."""
    
    def __init__(self, context_dir: Path, ontology_dir: Path):
        self.context_dir = context_dir
        self.ontology_dir = ontology_dir
        self.contexts = {}
        self.data_catalogue = {}
        self.load_core_contexts()
        self.load_data_catalogue()
    
    def load_core_contexts(self):
        """Load essential context files."""
        # Load full TTL mindmap
        mindmap_file = self.context_dir / "mes_ontology_mindmap.ttl"
        if mindmap_file.exists():
            with open(mindmap_file, 'r') as f:
                self.contexts['ontology_mindmap'] = f.read()
        
        # Load full SPARQL master reference
        sparql_ref_file = self.context_dir / "owlready2_sparql_master_reference.md"
        if sparql_ref_file.exists():
            with open(sparql_ref_file, 'r') as f:
                self.contexts['sparql_reference'] = f.read()
        
        # Load learned patterns if exists
        patterns_file = self.context_dir / "learned_patterns.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                self.contexts['learned_patterns'] = json.load(f)
        else:
            self.contexts['learned_patterns'] = {
                "successful_queries": [],
                "error_fixes": {},
                "value_patterns": []
            }
    
    def load_data_catalogue(self):
        """Load the data catalogue for quick reference."""
        catalogue_file = self.context_dir / "mes_data_catalogue.json"
        if catalogue_file.exists():
            with open(catalogue_file, 'r') as f:
                self.data_catalogue = json.load(f)
        else:
            self.data_catalogue = {
                "metadata": {"error": "Data catalogue not found"},
                "equipment": {},
                "products": {}
            }
    
    def add_learned_pattern(self, pattern_type: str, pattern: Dict[str, Any]):
        """Add a newly learned pattern."""
        if pattern_type in self.contexts['learned_patterns']:
            self.contexts['learned_patterns'][pattern_type].append(pattern)
            self._save_learned_patterns()
    
    def _save_learned_patterns(self):
        """Persist learned patterns."""
        patterns_file = self.context_dir / "learned_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(self.contexts['learned_patterns'], f, indent=2)
    
    def get_data_catalogue_summary(self) -> str:
        """Get a concise summary of available data."""
        if not self.data_catalogue:
            return "Data catalogue not available"
        
        summary = []
        
        # Metadata
        if 'metadata' in self.data_catalogue:
            meta = self.data_catalogue['metadata']
            if 'data_range' in meta:
                summary.append(f"Data Range: {meta['data_range']['start']} to {meta['data_range']['end']}")
                summary.append(f"Total Records: {meta.get('total_records', 'unknown'):,}")
        
        # Equipment summary
        if 'equipment' in self.data_catalogue:
            eq = self.data_catalogue['equipment']
            summary.append(f"\nEquipment: {eq.get('count', 0)} total")
            if 'by_type' in eq:
                for eq_type, items in eq['by_type'].items():
                    summary.append(f"  - {eq_type}: {len(items)} units")
        
        # Products summary
        if 'products' in self.data_catalogue:
            prod = self.data_catalogue['products']
            summary.append(f"\nProducts: {prod.get('count', 0)} SKUs")
            if 'catalog' in prod:
                for p in prod['catalog'][:3]:  # Show first 3
                    summary.append(f"  - {p['id']}: {p['name']} (margin: {p.get('margin_percent', 0)}%)")
                if len(prod['catalog']) > 3:
                    summary.append(f"  ... and {len(prod['catalog']) - 3} more")
        
        # Metrics summary
        if 'metrics' in self.data_catalogue:
            summary.append("\nKey Metrics Available:")
            for metric, data in self.data_catalogue['metrics'].items():
                summary.append(f"  - {metric}: {data.get('typical_range', 'N/A')} (typical)")
        
        return "\n".join(summary)
    
    def get_full_context(self) -> str:
        """Get complete context for system prompts."""
        return f"""
## Quick Data Overview
{self.get_data_catalogue_summary()}

## Ontology Structure and Business Context
{self.contexts.get('ontology_mindmap', 'Ontology structure not loaded')}

## SPARQL Query Reference and Rules
{self.contexts.get('sparql_reference', 'SPARQL reference not loaded')}

## Learned Patterns and Examples
{json.dumps(self.contexts.get('learned_patterns', {}), indent=2)}
"""
    
    def get_equipment_list(self) -> Dict[str, Any]:
        """Get quick access to equipment information."""
        return self.data_catalogue.get('equipment', {})
    
    def get_product_catalog(self) -> Dict[str, Any]:
        """Get quick access to product information."""
        return self.data_catalogue.get('products', {})
    
    def validate_entity(self, entity_type: str, entity_id: str) -> bool:
        """Validate if an entity exists in the data."""
        if entity_type == 'equipment':
            all_equipment = []
            for eq_list in self.data_catalogue.get('equipment', {}).get('by_type', {}).values():
                all_equipment.extend([e['id'] for e in eq_list])
            return entity_id in all_equipment
        elif entity_type == 'product':
            products = self.data_catalogue.get('products', {}).get('catalog', [])
            return entity_id in [p['id'] for p in products]
        return False