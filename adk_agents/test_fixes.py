"""
Test script to verify ADK fixes work correctly.
Tests the same queries that worked in Claude Code.
"""
import asyncio
import logging
from rich import print
from rich.console import Console
from rich.table import Table

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from tools.sparql_tool import (
    execute_sparql_query,
    discover_classes,
    discover_equipment_instances,
    discover_properties_for_class
)
from agents.orchestrator import shared_context
from utils.owlready2_adapter import adapt_sparql_for_owlready2

console = Console()

async def test_discovery_queries():
    """Test basic discovery queries."""
    console.print("\n[bold blue]Testing Discovery Queries[/bold blue]")
    
    # Test 1: Discover classes
    console.print("\n[yellow]Test 1: Discovering classes...[/yellow]")
    result = await discover_classes()
    if result.get('success'):
        console.print(f"✓ Found {result['row_count']} classes")
        if result['results']:
            for row in result['results'][:5]:
                console.print(f"  - {row[0]}")
    else:
        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")
    
    # Test 2: Discover equipment
    console.print("\n[yellow]Test 2: Discovering equipment instances...[/yellow]")
    result = await discover_equipment_instances()
    if result.get('success'):
        console.print(f"✓ Found {result['row_count']} equipment instances")
        if result['results']:
            for row in result['results'][:5]:
                console.print(f"  - {row[0]} (type: {row[1]})")
    else:
        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")
    
    # Test 3: Discover properties for ProductionLog
    console.print("\n[yellow]Test 3: Discovering ProductionLog properties...[/yellow]")
    result = await discover_properties_for_class("ProductionLog")
    if result.get('success'):
        console.print(f"✓ Found {result['row_count']} properties")
        if result['results']:
            for row in result['results'][:10]:
                console.print(f"  - {row[0]}")
    else:
        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


async def test_analysis_queries():
    """Test the analysis queries from Claude Code session."""
    console.print("\n[bold blue]Testing Analysis Queries[/bold blue]")
    
    # Test 1: Equipment OEE query (corrected)
    console.print("\n[yellow]Test 1: Equipment OEE analysis...[/yellow]")
    query = """
    SELECT ?equipment ?oee ?timestamp WHERE {
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:ProductionLog .
        ?event mes_ontology_populated:hasOEEScore ?oee .
        ?event mes_ontology_populated:hasTimestamp ?timestamp .
        FILTER(?oee < 85.0)
        FILTER(ISIRI(?equipment))
    } 
    ORDER BY ?oee
    LIMIT 10
    """
    
    result = await execute_sparql_query(query)
    if result.get('success'):
        console.print(f"✓ Found {result['row_count']} underperforming equipment entries")
        if result['results']:
            table = Table(title="Underperforming Equipment")
            table.add_column("Equipment", style="cyan")
            table.add_column("OEE", style="red")
            table.add_column("Timestamp", style="green")
            
            for row in result['results'][:5]:
                equipment = str(row[0]).split('#')[-1] if '#' in str(row[0]) else str(row[0])
                table.add_row(equipment, f"{row[1]:.1f}%", str(row[2]))
            
            console.print(table)
    else:
        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")
    
    # Test 2: Downtime events
    console.print("\n[yellow]Test 2: Downtime events analysis...[/yellow]")
    query = """
    SELECT ?equipment ?timestamp ?reason WHERE {
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:DowntimeLog .
        ?event mes_ontology_populated:hasTimestamp ?timestamp .
        OPTIONAL { ?event mes_ontology_populated:hasDowntimeReason ?reason }
        FILTER(ISIRI(?equipment))
    }
    ORDER BY DESC(?timestamp)
    LIMIT 10
    """
    
    result = await execute_sparql_query(query)
    if result.get('success'):
        console.print(f"✓ Found {result['row_count']} downtime events")
    else:
        console.print(f"[red]✗ Failed: {result.get('error')}[/red]")


async def test_prefix_conversion():
    """Test that prefix conversion works correctly."""
    console.print("\n[bold blue]Testing Prefix Conversion[/bold blue]")
    
    test_queries = [
        ("mes: prefix", "SELECT ?x WHERE { ?x mes:hasOEEScore ?score }"),
        (": prefix", "SELECT ?x WHERE { ?x :hasOEEScore ?score }"),
        ("Mixed prefixes", "SELECT ?x WHERE { ?x a mes:Equipment . ?x :logsEvent ?e }")
    ]
    
    for desc, query in test_queries:
        console.print(f"\n[yellow]Testing {desc}:[/yellow]")
        console.print(f"Original: {query}")
        adapted = adapt_sparql_for_owlready2(query)
        console.print(f"Adapted:  {adapted}")
        
        # Verify conversion
        if "mes_ontology_populated:" in adapted and "mes:" not in adapted:
            console.print("✓ Prefix conversion successful")
        else:
            console.print("[red]✗ Prefix conversion failed[/red]")


async def main():
    """Run all tests."""
    console.print("[bold green]ADK Fix Verification Tests[/bold green]")
    console.print("=" * 50)
    
    # Test prefix conversion
    await test_prefix_conversion()
    
    # Test discovery queries
    await test_discovery_queries()
    
    # Test analysis queries
    await test_analysis_queries()
    
    # Show shared context summary
    console.print("\n[bold blue]Shared Context Summary[/bold blue]")
    summary = shared_context.get_context_summary()
    console.print(f"Entities discovered: {summary['entities_discovered']}")
    console.print(f"Successful queries: {summary['successful_queries']}")
    console.print(f"Failed queries: {summary['failed_queries']}")
    
    if summary['sample_entities']:
        console.print("\nSample discovered entities:")
        for entity_type, entities in summary['sample_entities'].items():
            console.print(f"  {entity_type}: {entities}")


if __name__ == "__main__":
    asyncio.run(main())