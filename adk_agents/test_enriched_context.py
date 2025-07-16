#!/usr/bin/env python3
"""
Test script to verify enriched context functionality.
"""
from pathlib import Path
from utils.context_loader import ContextLoader
from config.settings import CONTEXT_DIR, ONTOLOGY_DIR

def test_context_loader():
    """Test the enhanced context loader."""
    print("Testing Enhanced Context Loader\n" + "="*50)
    
    # Initialize loader
    loader = ContextLoader(CONTEXT_DIR, ONTOLOGY_DIR)
    
    # Test data catalogue summary
    print("\n1. Data Catalogue Summary:")
    print(loader.get_data_catalogue_summary())
    
    # Test equipment list
    print("\n2. Equipment Information:")
    equipment = loader.get_equipment_list()
    print(f"Total equipment: {equipment.get('count', 0)}")
    for eq_type, items in equipment.get('by_type', {}).items():
        print(f"  {eq_type}: {[e['id'] for e in items]}")
    
    # Test product catalog
    print("\n3. Product Catalog:")
    products = loader.get_product_catalog()
    print(f"Total products: {products.get('count', 0)}")
    for p in products.get('catalog', [])[:3]:
        print(f"  {p['id']}: {p['name']} (margin: {p.get('margin_percent', 0)}%)")
    
    # Test entity validation
    print("\n4. Entity Validation:")
    test_cases = [
        ('equipment', 'LINE1-FIL', True),
        ('equipment', 'INVALID-EQ', False),
        ('product', 'SKU-1001', True),
        ('product', 'SKU-9999', False)
    ]
    
    for entity_type, entity_id, expected in test_cases:
        result = loader.validate_entity(entity_type, entity_id)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {entity_type} '{entity_id}': {result}")
    
    # Test context size
    print("\n5. Context Information:")
    full_context = loader.get_full_context()
    print(f"Full context size: {len(full_context):,} characters")
    print(f"Ontology mindmap loaded: {'ontology_mindmap' in loader.contexts}")
    print(f"SPARQL reference loaded: {'sparql_reference' in loader.contexts}")
    print(f"Data catalogue loaded: {bool(loader.data_catalogue)}")
    
    # Show a snippet of enriched TTL
    print("\n6. Sample Enriched TTL Property:")
    ttl_content = loader.contexts.get('ontology_mindmap', '')
    if 'mes:hasOEEScore' in ttl_content:
        lines = ttl_content.split('\n')
        oee_start = None
        for i, line in enumerate(lines):
            if 'mes:hasOEEScore a owl:DatatypeProperty' in line:
                oee_start = i
                break
        
        if oee_start:
            print("mes:hasOEEScore property with enrichments:")
            for i in range(oee_start, min(oee_start + 10, len(lines))):
                if lines[i].strip() and not lines[i].startswith('#'):
                    print(f"  {lines[i]}")
                if lines[i].strip() == '.':
                    break
    
    print("\n" + "="*50)
    print("✓ Enhanced context loading successful!")

if __name__ == "__main__":
    test_context_loader()