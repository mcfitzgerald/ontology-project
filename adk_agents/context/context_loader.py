"""Context loader for Manufacturing Analyst Agent."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from ..config.settings import PROJECT_ROOT

logger = logging.getLogger(__name__)

class ContextLoader:
    """Loads and formats context for the Manufacturing Analyst Agent."""
    
    def __init__(self):
        self.context_dir = PROJECT_ROOT.parent / "Context"
        self.cache_dir = PROJECT_ROOT / "cache"
        
        # Define all context file mappings
        self.files = {
            'mindmap': 'mes_ontology_mindmap.ttl',
            'sparql_ref': 'owlready2_sparql_lean_reference.md',
            'data_catalogue': 'mes_data_catalogue.json',
            'query_patterns': 'query_patterns.json',
            'python_analysis': 'python_analysis_guide.md',
            'system_prompt': 'system_prompt.md'
        }
    
    def load_file(self, file_key: str, format_as_section: bool = True) -> str:
        """Generic file loader with error handling.
        
        Args:
            file_key: Key from self.files dict
            format_as_section: Whether to format with section header
            
        Returns:
            File contents or error message
        """
        if file_key not in self.files:
            logger.warning(f"Unknown file key: {file_key}")
            return f"### {file_key}: Unknown file key\n"
            
        file_name = self.files[file_key]
        file_path = self.context_dir / file_name
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if format_as_section:
                    # Format with section header based on file type
                    section_headers = {
                        'mindmap': "### Ontology Structure:",
                        'sparql_ref': "### SPARQL Reference:",
                        'data_catalogue': "### Data Catalogue:",
                        'sparql_rules': "### SPARQL Rules:",
                        'query_patterns': "### Query Patterns:",
                        'discovery_methodology': "### Discovery Methodology:",
                        'python_analysis': "### Python Analysis Guide:",
                        'collaborative_patterns': "### Collaborative Patterns:",
                        'best_practices': "### Analysis Best Practices:",
                        'technical_notes': "### Technical Notes:"
                    }
                    header = section_headers.get(file_key, f"### {file_key.replace('_', ' ').title()}:")
                    return f"{header}\n{content}\n"
                else:
                    return content
            else:
                logger.warning(f"File not found: {file_path}")
                return f"### {file_key}: File not found at {file_path}\n"
        except Exception as e:
            logger.error(f"Failed to load {file_key}: {e}")
            return f"### {file_key}: Error loading - {e}\n"
        
    def load_ontology_context(self) -> str:
        """Load complete ontology mindmap for context."""
        return self.load_file('mindmap')
    
    def load_sparql_reference(self) -> str:
        """Load SPARQL reference guide for Owlready2."""
        return self.load_file('sparql_ref')
    
    def load_successful_queries(self) -> str:
        """Load examples of successful queries."""
        # Try to load query patterns file
        patterns_content = self.load_file('query_patterns', format_as_section=False)
        
        try:
            # If it's JSON, parse and format it
            if patterns_content and not patterns_content.startswith("###"):
                patterns_data = json.loads(patterns_content)
                query_text = "### Successful Query Examples:\n"
                
                if "patterns" in patterns_data:
                    for i, pattern in enumerate(patterns_data["patterns"][:8], 1):  # First 8 examples
                        query_text += f"\n{i}. {pattern['purpose']}:\n```sparql\n{pattern['query']}\n```\n"
                        if pattern.get('notes'):
                            query_text += f"*Note: {pattern['notes']}*\n"
                
                return query_text
        except Exception as e:
            logger.warning(f"Failed to parse query patterns: {e}")
        
        # Fallback to loading as-is
        return self.load_file('query_patterns')
    
    def load_data_catalogue(self) -> str:
        """Load MES data catalogue information."""
        try:
            catalogue_path = self.context_dir / self.files['data_catalogue']
            if catalogue_path.exists():
                with open(catalogue_path, 'r') as f:
                    catalogue = json.load(f)
                
                info = "### Data Catalogue:\n"
                
                # Metadata summary
                if "metadata" in catalogue:
                    meta = catalogue["metadata"]
                    info += f"- Data range: {meta['data_range']['start']} to {meta['data_range']['end']} ({meta['data_range']['days_covered']} days)\n"
                    info += f"- Total records: {meta['total_records']:,}\n"
                    info += f"- Update frequency: {meta['update_frequency']}\n\n"
                
                # Equipment summary
                if "equipment" in catalogue:
                    equipment = catalogue["equipment"]
                    info += f"- Equipment: {equipment['count']} units\n"
                    # Group by type
                    for eq_type, items in equipment.get("by_type", {}).items():
                        ids = [item["id"] for item in items]
                        info += f"  - {eq_type}: {', '.join(ids)}\n"
                    info += "\n"
                
                # Products summary
                if "products" in catalogue:
                    products = catalogue["products"]
                    info += f"- Products: {products['count']} SKUs\n"
                    for prod in products.get("catalog", [])[:5]:  # First 5 products
                        info += f"  - {prod['id']}: {prod['name']} (margin: {prod['margin_percent']}%)\n"
                    info += "\n"
                
                # Metrics summary
                if "metrics" in catalogue:
                    info += "- Key Metrics:\n"
                    for metric, values in catalogue["metrics"].items():
                        info += f"  - {metric}: mean={values['mean']}, typical={values['typical_range']}, benchmark={values['world_class']}\n"
                    info += "\n"
                
                # Downtime summary
                if "downtime_reasons" in catalogue:
                    downtime = catalogue["downtime_reasons"]
                    info += f"- Total downtime: {downtime['total_downtime_hours']} hours\n"
                    if downtime.get("unplanned"):
                        info += "  - Top unplanned reasons:\n"
                        for reason in downtime["unplanned"][:3]:
                            info += f"    - {reason['code']}: {reason['total_hours']} hours\n"
                
                return info
            else:
                return "### Data Catalogue: Not found\n"
        except Exception as e:
            logger.error(f"Failed to load data catalogue: {e}")
            return f"### Data Catalogue: Error loading - {e}\n"
    
# Legacy methods removed - use get_comprehensive_agent_context() and get_minimal_agent_context() instead
    
    def get_essential_sparql_rules(self) -> str:
        """Get just the essential SPARQL rules."""
        return self.load_file('sparql_ref')
    
    def get_discovery_context(self) -> str:
        """Get focused context for discovery methodology."""
        # Discovery methodology is now part of system_prompt
        return self.load_file('system_prompt')
    
    def get_python_analysis_context(self) -> str:
        """Get context for Python analysis capabilities."""
        return self.load_file('python_analysis')
    
    def get_comprehensive_agent_context(self) -> str:
        """Get complete context for ADK agents.
        
        This centralizes the context file selection for all agents,
        providing a single source of truth for what context is loaded.
        """
        context_parts = []
        
        # Load context files in order of importance
        context_files = [
            'system_prompt',      # Agent behavior and methodology
            'data_catalogue',     # Available data inventory
            'sparql_ref',        # SPARQL syntax rules
            'query_patterns',    # Working query examples
            'python_analysis',   # Python analysis capabilities
            'mindmap'           # Ontology structure (last due to size)
        ]
        
        for file_key in context_files:
            content = self.load_file(file_key)
            if content and not content.startswith("### File not found"):
                context_parts.append(content)
        
        return "\n".join(context_parts)
    
    def get_minimal_agent_context(self) -> str:
        """Get minimal context for testing or lightweight operations.
        
        Includes only essential components for basic functionality.
        """
        context_parts = []
        
        # Minimal context for testing
        context_files = [
            'system_prompt',    # Core behavior
            'sparql_ref'       # Essential SPARQL rules
        ]
        
        for file_key in context_files:
            content = self.load_file(file_key)
            if content and not content.startswith("### File not found"):
                context_parts.append(content)
        
        return "\n".join(context_parts)
    
    def get_initial_context(self) -> str:
        """Get initial conversation context.
        
        This provides the essential context for starting a conversation,
        including system behavior, available data, and ontology structure.
        """
        context_parts = []
        
        # Essential context for initial conversation
        context_files = [
            'system_prompt',      # Agent behavior and methodology
            'data_catalogue',     # Available data inventory
            'mindmap'            # Ontology structure overview
        ]
        
        for file_key in context_files:
            content = self.load_file(file_key)
            if content and not content.startswith("### File not found"):
                context_parts.append(content)
        
        return "\n".join(context_parts)
    
    def get_sparql_context(self) -> str:
        """Get context for SPARQL query construction.
        
        Builds on initial context by adding SPARQL-specific information.
        """
        # Start with current context (assuming it builds on initial)
        base_context = self.get_initial_context()
        
        # Add SPARQL-specific context
        sparql_parts = []
        sparql_files = [
            'sparql_ref',        # SPARQL syntax rules
            'query_patterns'     # Working query examples
        ]
        
        for file_key in sparql_files:
            content = self.load_file(file_key)
            if content and not content.startswith("### File not found"):
                sparql_parts.append(content)
        
        return base_context + "\n" + "\n".join(sparql_parts)
    
    def get_python_context(self) -> str:
        """Get context for Python code generation.
        
        Builds on initial context by adding Python analysis guidance.
        """
        # Start with current context
        base_context = self.get_initial_context()
        
        # Add Python-specific context
        python_content = self.load_file('python_analysis')
        
        if python_content and not python_content.startswith("### File not found"):
            return base_context + "\n" + python_content
        
        return base_context

# Create singleton instance
context_loader = ContextLoader()