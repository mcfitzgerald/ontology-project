"""
Financial calculation utilities for manufacturing analytics.
"""
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np


class FinancialCalculator:
    """Handles financial calculations for manufacturing metrics."""
    
    @staticmethod
    def calculate_oee_impact(
        current_oee: float,
        target_oee: float,
        daily_production: float,
        unit_margin: float,
        days_per_year: int = 365
    ) -> Dict[str, float]:
        """
        Calculate financial impact of OEE improvement.
        
        Args:
            current_oee: Current OEE percentage (0-100)
            target_oee: Target OEE percentage (0-100)
            daily_production: Current daily production units
            unit_margin: Profit margin per unit
            days_per_year: Operating days per year
        
        Returns:
            Dictionary with financial metrics
        """
        oee_gap = target_oee - current_oee
        capacity_increase_pct = oee_gap / 100
        
        # Additional units from OEE improvement
        daily_unit_increase = daily_production * capacity_increase_pct
        annual_unit_increase = daily_unit_increase * days_per_year
        
        # Financial impact
        annual_value = annual_unit_increase * unit_margin
        monthly_value = annual_value / 12
        daily_value = annual_value / days_per_year
        
        return {
            'oee_gap': oee_gap,
            'capacity_increase_pct': capacity_increase_pct * 100,
            'daily_unit_increase': daily_unit_increase,
            'annual_unit_increase': annual_unit_increase,
            'annual_value': annual_value,
            'monthly_value': monthly_value,
            'daily_value': daily_value
        }
    
    @staticmethod
    def calculate_downtime_cost(
        downtime_minutes: float,
        units_per_minute: float,
        unit_margin: float,
        fixed_cost_per_hour: float = 0
    ) -> Dict[str, float]:
        """
        Calculate cost of equipment downtime.
        
        Args:
            downtime_minutes: Total downtime in minutes
            units_per_minute: Production rate when running
            unit_margin: Profit margin per unit
            fixed_cost_per_hour: Fixed costs during downtime
        
        Returns:
            Dictionary with downtime costs
        """
        lost_units = downtime_minutes * units_per_minute
        lost_margin = lost_units * unit_margin
        fixed_costs = (downtime_minutes / 60) * fixed_cost_per_hour
        total_cost = lost_margin + fixed_costs
        
        return {
            'downtime_hours': downtime_minutes / 60,
            'lost_units': lost_units,
            'lost_margin': lost_margin,
            'fixed_costs': fixed_costs,
            'total_cost': total_cost
        }
    
    @staticmethod
    def calculate_quality_impact(
        total_units: float,
        scrap_units: float,
        unit_cost: float,
        rework_cost_per_unit: float = 0
    ) -> Dict[str, float]:
        """
        Calculate financial impact of quality issues.
        
        Args:
            total_units: Total units produced
            scrap_units: Units scrapped
            unit_cost: Cost per unit
            rework_cost_per_unit: Additional cost for rework
        
        Returns:
            Dictionary with quality costs
        """
        scrap_rate = scrap_units / total_units if total_units > 0 else 0
        scrap_cost = scrap_units * unit_cost
        rework_cost = scrap_units * rework_cost_per_unit
        total_quality_cost = scrap_cost + rework_cost
        
        # Cost per good unit impact
        good_units = total_units - scrap_units
        quality_burden_per_unit = total_quality_cost / good_units if good_units > 0 else 0
        
        return {
            'scrap_rate': scrap_rate * 100,
            'scrap_units': scrap_units,
            'scrap_cost': scrap_cost,
            'rework_cost': rework_cost,
            'total_quality_cost': total_quality_cost,
            'quality_burden_per_unit': quality_burden_per_unit
        }
    
    @staticmethod
    def calculate_roi_scenarios(
        annual_opportunity: float,
        improvement_levels: List[float] = None
    ) -> List[Dict[str, float]]:
        """
        Calculate ROI for different improvement scenarios.
        
        Args:
            annual_opportunity: Total annual opportunity value
            improvement_levels: List of improvement percentages (0-1)
        
        Returns:
            List of ROI scenarios
        """
        if improvement_levels is None:
            improvement_levels = [0.1, 0.25, 0.5, 0.75, 1.0]
        
        scenarios = []
        
        for level in improvement_levels:
            value = annual_opportunity * level
            
            # Estimate investment based on improvement level
            if level <= 0.25:
                investment = value * 0.2  # 20% of first year value
                payback_months = 3
            elif level <= 0.5:
                investment = value * 0.4  # 40% of first year value
                payback_months = 6
            else:
                investment = value * 0.6  # 60% of first year value
                payback_months = 9
            
            roi = ((value - investment) / investment * 100) if investment > 0 else 0
            
            scenarios.append({
                'improvement_pct': level * 100,
                'annual_value': value,
                'estimated_investment': investment,
                'roi_pct': roi,
                'payback_months': payback_months
            })
        
        return scenarios
    
    @staticmethod
    def aggregate_opportunities(
        opportunities: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Aggregate multiple improvement opportunities.
        
        Args:
            opportunities: List of opportunity dictionaries
        
        Returns:
            Aggregated opportunity summary
        """
        total_annual = sum(opp.get('annual_value', 0) for opp in opportunities)
        total_monthly = sum(opp.get('monthly_value', 0) for opp in opportunities)
        
        # Categorize by size
        small = [opp for opp in opportunities if opp.get('annual_value', 0) < 100000]
        medium = [opp for opp in opportunities if 100000 <= opp.get('annual_value', 0) < 500000]
        large = [opp for opp in opportunities if opp.get('annual_value', 0) >= 500000]
        
        return {
            'total_annual_opportunity': total_annual,
            'total_monthly_opportunity': total_monthly,
            'opportunity_count': len(opportunities),
            'large_opportunities': len(large),
            'medium_opportunities': len(medium),
            'small_opportunities': len(small),
            'largest_opportunity': max(opp.get('annual_value', 0) for opp in opportunities) if opportunities else 0
        }


# Convenience functions
def calculate_oee_opportunity(
    current_oee: float,
    benchmark_oee: float,
    production_data: pd.DataFrame
) -> Dict[str, float]:
    """Calculate OEE improvement opportunity from production data."""
    
    # Get average production metrics
    avg_daily_production = production_data['good_units'].sum() / production_data['timestamp'].nunique()
    avg_margin = (production_data['sale_price'] - production_data['unit_cost']).mean()
    
    calculator = FinancialCalculator()
    return calculator.calculate_oee_impact(
        current_oee=current_oee,
        target_oee=benchmark_oee,
        daily_production=avg_daily_production,
        unit_margin=avg_margin
    )


def estimate_micro_stop_impact(
    stop_frequency: float,
    avg_stop_duration: float,
    units_per_minute: float,
    unit_margin: float,
    operating_hours_per_day: int = 24
) -> Dict[str, float]:
    """Estimate impact of micro-stops on production."""
    
    # Daily impact
    stops_per_day = stop_frequency * operating_hours_per_day
    daily_downtime_minutes = stops_per_day * avg_stop_duration
    
    calculator = FinancialCalculator()
    daily_impact = calculator.calculate_downtime_cost(
        downtime_minutes=daily_downtime_minutes,
        units_per_minute=units_per_minute,
        unit_margin=unit_margin
    )
    
    # Annualize
    annual_impact = {
        key: value * 365 if key != 'downtime_hours' else value
        for key, value in daily_impact.items()
    }
    
    return annual_impact