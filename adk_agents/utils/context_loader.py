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
        self.load_core_contexts()
    
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
    
    def get_full_context(self) -> str:
        """Get complete context for system prompts."""
        return f"""
## Ontology Structure and Business Context
{self.contexts.get('ontology_mindmap', 'Ontology structure not loaded')}

## SPARQL Query Reference and Rules
{self.contexts.get('sparql_reference', 'SPARQL reference not loaded')}

## Learned Patterns and Examples
{json.dumps(self.contexts.get('learned_patterns', {}), indent=2)}
"""