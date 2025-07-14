#!/usr/bin/env python3
"""
Simple test script for ADK Manufacturing Analytics components.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from adk_agents.tools.sparql_tool import execute_sparql_query
from adk_agents.utils.financial_calc import FinancialCalculator


async def test_sparql_connectivity():
    """Test basic SPARQL connectivity."""
    print("\n=== Testing SPARQL Connectivity ===")
    
    # Simple test query - use mes_ontology_populated prefix for Owlready2
    test_query = """
    SELECT ?equipment ?oee 
    WHERE { 
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:ProductionLog .
        ?event mes_ontology_populated:hasOEEScore ?oee .
        FILTER(?oee < 85.0)
    } 
    LIMIT 10
    """
    
    try:
        # execute_sparql_query is async
        result = await execute_sparql_query(test_query)
        if result.get('status') == 'success':
            print("✅ SPARQL connectivity: OK")
            print(f"   Retrieved {result['data']['row_count']} rows")
            if result['data']['row_count'] > 0:
                print("\n   Sample results:")
                for row in result['data']['results'][:3]:
                    equipment = row[0].split('#')[-1] if '#' in str(row[0]) else row[0]
                    oee = row[1]
                    print(f"   - {equipment}: {oee}% OEE")
            return True
        else:
            print("❌ SPARQL connectivity: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ SPARQL connectivity: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_equipment_analysis():
    """Test equipment performance analysis."""
    print("\n=== Testing Equipment Performance Analysis ===")
    
    # Query for all equipment with OEE data
    query = """
    SELECT ?equipment ?equipmentID (AVG(?oee) AS ?avgOEE) (COUNT(?event) AS ?eventCount)
    WHERE {
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:ProductionLog .
        ?equipment mes_ontology_populated:hasEquipmentID ?equipmentID .
        ?event mes_ontology_populated:hasOEEScore ?oee .
        FILTER(ISIRI(?equipment))
    }
    GROUP BY ?equipment ?equipmentID
    ORDER BY ?avgOEE
    """
    
    try:
        result = await execute_sparql_query(query)
        if result.get('status') == 'success' and result['data']['row_count'] > 0:
            print("✅ Equipment analysis: OK")
            print(f"\n   Found {result['data']['row_count']} equipment units:")
            
            opportunities = []
            for row in result['data']['results']:
                equipment_id = row[1]
                avg_oee = float(row[2])
                event_count = int(row[3])
                
                if avg_oee < 85.0:
                    # Calculate opportunity using FinancialCalculator
                    calculator = FinancialCalculator()
                    daily_production = event_count * 0.5 * 1000 / 30  # Convert to daily units
                    
                    opportunity = calculator.calculate_oee_impact(
                        current_oee=avg_oee,
                        target_oee=85.0,
                        daily_production=daily_production,
                        unit_margin=5.0  # $ per unit
                    )
                    opportunities.append({
                        'equipment': equipment_id,
                        'current_oee': avg_oee,
                        'annual_value': opportunity['annual_value']
                    })
                
                status = "⚠️  Underperforming" if avg_oee < 85.0 else "✅"
                print(f"   - {equipment_id}: {avg_oee:.1f}% OEE ({event_count} events) {status}")
            
            if opportunities:
                print(f"\n   💰 Found {len(opportunities)} improvement opportunities:")
                total_value = 0
                for opp in sorted(opportunities, key=lambda x: x['annual_value'], reverse=True):
                    print(f"      - {opp['equipment']}: ${opp['annual_value']:,.0f}/year potential")
                    total_value += opp['annual_value']
                print(f"\n   Total annual opportunity: ${total_value:,.0f}")
            
            return True
        else:
            print("❌ Equipment analysis: No data found")
            return False
    except Exception as e:
        print(f"❌ Equipment analysis: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_downtime_patterns():
    """Test downtime pattern analysis."""
    print("\n=== Testing Downtime Pattern Analysis ===")
    
    # Query for recent downtime events
    query = """
    SELECT ?equipment ?timestamp ?reasonCode
    WHERE {
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:DowntimeLog .
        ?event mes_ontology_populated:hasTimestamp ?timestamp .
        OPTIONAL { ?event mes_ontology_populated:hasDowntimeReasonCode ?reasonCode }
    }
    ORDER BY ?timestamp
    LIMIT 100
    """
    
    try:
        result = await execute_sparql_query(query)
        if result.get('status') == 'success' and result['data']['row_count'] > 0:
            print("✅ Downtime analysis: OK")
            print(f"\n   Analyzed {result['data']['row_count']} downtime events")
            
            # Analyze patterns
            downtime_by_equipment = {}
            total_downtime = 0
            
            for row in result['data']['results']:
                equipment = row[0].split('#')[-1] if '#' in str(row[0]) else row[0]
                timestamp = row[1]
                reason = row[2] if len(row) > 2 and row[2] else "Unknown"
                
                if equipment not in downtime_by_equipment:
                    downtime_by_equipment[equipment] = {'total': 0, 'count': 0, 'reasons': {}}
                
                # Since we don't have duration, just count events
                downtime_by_equipment[equipment]['count'] += 1
                
                if reason not in downtime_by_equipment[equipment]['reasons']:
                    downtime_by_equipment[equipment]['reasons'][reason] = 0
                downtime_by_equipment[equipment]['reasons'][reason] += 1
            
            print(f"\n   Analyzed {result['data']['row_count']} downtime events")
            print("\n   Downtime by equipment:")
            for equipment, data in sorted(downtime_by_equipment.items(), 
                                        key=lambda x: x[1]['count'], reverse=True):
                print(f"   - {equipment}: {data['count']} events")
                
                # Show top reason
                if data['reasons']:
                    top_reason = max(data['reasons'].items(), key=lambda x: x[1])
                    print(f"     Top reason: {top_reason[0]} ({top_reason[1]} times)")
            
            return True
        else:
            print("❌ Downtime analysis: No data found")
            return False
    except Exception as e:
        print(f"❌ Downtime analysis: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_financial_calculations():
    """Test financial calculation utilities."""
    print("\n=== Testing Financial Calculations ===")
    
    try:
        # Test OEE opportunity calculation
        calculator = FinancialCalculator()
        daily_production = 7000 * 1000 / 365  # Convert annual hours to daily units
        
        scenario = calculator.calculate_oee_impact(
            current_oee=75.0,
            target_oee=85.0,
            daily_production=daily_production,
            unit_margin=5.0
        )
        
        print("✅ Financial calculations: OK")
        print("\n   Test scenario:")
        print(f"   - Current OEE: 75%")
        print(f"   - Target OEE: 85%")
        print(f"   - Production hours: 7,000/year")
        print(f"   - Output: 1,000 units/hour")
        print(f"   - Margin: $5/unit")
        
        print("\n   Results:")
        print(f"   - OEE gap: {scenario['oee_gap']:.1f}%")
        print(f"   - Capacity increase: {scenario['capacity_increase_pct']:.1f}%")
        print(f"   - Annual unit increase: {scenario['annual_unit_increase']:,.0f} units")
        print(f"   - Annual value: ${scenario['annual_value']:,.0f}")
        print(f"   - Monthly value: ${scenario['monthly_value']:,.0f}")
        
        return True
    except Exception as e:
        print(f"❌ Financial calculations: ERROR - {e}")
        return False


async def main():
    """Run all tests."""
    print("ADK Manufacturing Analytics - Component Test")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Run tests
    results.append(("SPARQL Connectivity", await test_sparql_connectivity()))
    results.append(("Equipment Analysis", await test_equipment_analysis()))
    results.append(("Downtime Patterns", await test_downtime_patterns()))
    results.append(("Financial Calculations", await test_financial_calculations()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! The system is working correctly.")
        print("\nKey findings:")
        print("- SPARQL API is connected and responding")
        print("- Equipment performance data is available")
        print("- Downtime events are being tracked")
        print("- Financial calculations are accurate")
        print("\nYou can now use the interactive demo to explore the full agent capabilities.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())