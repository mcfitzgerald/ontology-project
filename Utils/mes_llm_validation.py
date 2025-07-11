#!/usr/bin/env python3
"""
MES LLM Validation Script
Provides deterministic validation and sanity checks for LLM-generated insights
"""

from owlready2 import *
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import json

import os

def load_config(config_file='mes_data_config.json'):
    """Load configuration from JSON file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data_Generation", config_file)
    with open(config_path, 'r') as f:
        return json.load(f)

class OntologyValidator:
    """Validates ontology data and provides ground truth for LLM analysis."""
    
    def __init__(self, ontology_file, config):
        self.onto = get_ontology(f"file://{ontology_file}").load()
        self.config = config
        self.validation_results = {
            'data_integrity': {},
            'kpi_validation': {},
            'known_patterns': {},
            'statistical_anomalies': {},
            'relationship_consistency': {}
        }
    
    def validate_all(self):
        """Run all validation checks."""
        print("Running MES Ontology Validation")
        print("=" * 60)
        
        self.validate_data_integrity()
        self.validate_kpi_calculations()
        self.detect_known_patterns()
        self.check_statistical_anomalies()
        self.validate_relationships()
        
        return self.validation_results
    
    def validate_data_integrity(self):
        """Check basic data integrity and completeness."""
        print("\n1. Data Integrity Checks")
        print("-" * 40)
        
        # Count entities
        equipment_count = len(list(self.onto.Equipment.instances()))
        product_count = len(list(self.onto.Product.instances()))
        order_count = len(list(self.onto.ProductionOrder.instances()))
        event_count = len(list(self.onto.Event.instances()))
        production_log_count = len(list(self.onto.ProductionLog.instances()))
        downtime_log_count = len(list(self.onto.DowntimeLog.instances()))
        
        self.validation_results['data_integrity'] = {
            'equipment_count': equipment_count,
            'product_count': product_count,
            'order_count': order_count,
            'total_events': event_count,
            'production_events': production_log_count,
            'downtime_events': downtime_log_count,
            'completeness_check': 'PASS' if event_count > 0 else 'FAIL'
        }
        
        print(f"  Equipment: {equipment_count}")
        print(f"  Products: {product_count}")
        print(f"  Orders: {order_count}")
        print(f"  Total Events: {event_count:,}")
        print(f"    - Production: {production_log_count:,}")
        print(f"    - Downtime: {downtime_log_count:,}")
        
        # Check for missing KPI data
        events_with_kpis = 0
        events_missing_kpis = 0
        
        for event in self.onto.Event.instances():
            if hasattr(event, 'hasOEEScore') and event.hasOEEScore:
                events_with_kpis += 1
            else:
                events_missing_kpis += 1
        
        self.validation_results['data_integrity']['kpi_coverage'] = {
            'events_with_kpis': events_with_kpis,
            'events_missing_kpis': events_missing_kpis,
            'coverage_percentage': (events_with_kpis / event_count * 100) if event_count > 0 else 0
        }
        
        print(f"  KPI Coverage: {events_with_kpis}/{event_count} events ({events_with_kpis/event_count*100:.1f}%)")
    
    def validate_kpi_calculations(self):
        """Validate KPI values are within expected ranges."""
        print("\n2. KPI Validation")
        print("-" * 40)
        
        kpi_issues = []
        
        # Collect all KPI values
        availability_scores = []
        performance_scores = []
        quality_scores = []
        oee_scores = []
        
        for event in self.onto.Event.instances():
            if hasattr(event, 'hasAvailabilityScore') and event.hasAvailabilityScore:
                avail = event.hasAvailabilityScore[0]
                perf = event.hasPerformanceScore[0] if event.hasPerformanceScore else 0
                qual = event.hasQualityScore[0] if event.hasQualityScore else 0
                oee = event.hasOEEScore[0] if event.hasOEEScore else 0
                
                availability_scores.append(avail)
                performance_scores.append(perf)
                quality_scores.append(qual)
                oee_scores.append(oee)
                
                # Validate ranges (0-100)
                if not (0 <= avail <= 100):
                    kpi_issues.append(f"Availability out of range: {avail}")
                if not (0 <= perf <= 100):
                    kpi_issues.append(f"Performance out of range: {perf}")
                if not (0 <= qual <= 100):
                    kpi_issues.append(f"Quality out of range: {qual}")
                if not (0 <= oee <= 100):
                    kpi_issues.append(f"OEE out of range: {oee}")
                
                # Validate OEE calculation (allowing for rounding)
                calculated_oee = (avail * perf * qual) / 10000
                if abs(oee - calculated_oee) > 0.5:  # 0.5% tolerance
                    kpi_issues.append(f"OEE calculation mismatch: {oee} vs {calculated_oee:.1f}")
        
        # Calculate statistics
        if availability_scores:
            self.validation_results['kpi_validation'] = {
                'availability': {
                    'mean': np.mean(availability_scores),
                    'std': np.std(availability_scores),
                    'min': np.min(availability_scores),
                    'max': np.max(availability_scores)
                },
                'performance': {
                    'mean': np.mean(performance_scores),
                    'std': np.std(performance_scores),
                    'min': np.min(performance_scores),
                    'max': np.max(performance_scores)
                },
                'quality': {
                    'mean': np.mean(quality_scores),
                    'std': np.std(quality_scores),
                    'min': np.min(quality_scores),
                    'max': np.max(quality_scores)
                },
                'oee': {
                    'mean': np.mean(oee_scores),
                    'std': np.std(oee_scores),
                    'min': np.min(oee_scores),
                    'max': np.max(oee_scores)
                },
                'validation_issues': kpi_issues[:10],  # First 10 issues
                'total_issues': len(kpi_issues)
            }
            
            print(f"  Availability: μ={np.mean(availability_scores):.1f}%, σ={np.std(availability_scores):.1f}%")
            print(f"  Performance: μ={np.mean(performance_scores):.1f}%, σ={np.std(performance_scores):.1f}%")
            print(f"  Quality: μ={np.mean(quality_scores):.1f}%, σ={np.std(quality_scores):.1f}%")
            print(f"  OEE: μ={np.mean(oee_scores):.1f}%, σ={np.std(oee_scores):.1f}%")
            print(f"  Validation Issues: {len(kpi_issues)}")
    
    def detect_known_patterns(self):
        """Detect patterns that match configured anomalies."""
        print("\n3. Known Pattern Detection")
        print("-" * 40)
        
        patterns_found = {}
        
        # Check for major mechanical failure
        if self.config['anomaly_injection']['major_mechanical_failure']['enabled']:
            failure_config = self.config['anomaly_injection']['major_mechanical_failure']
            equipment_id = failure_config['equipment_id']
            reason_code = failure_config['downtime_reason']
            
            # Find the equipment
            equipment = self.onto.search_one(hasEquipmentID=equipment_id)
            if equipment:
                failure_events = []
                for event in equipment.logsEvent:
                    if (isinstance(event, self.onto.DowntimeLog) and 
                        hasattr(event, 'hasDowntimeReasonCode') and
                        reason_code in event.hasDowntimeReasonCode):
                        failure_events.append(event)
                
                patterns_found['major_mechanical_failure'] = {
                    'equipment': equipment_id,
                    'events_found': len(failure_events),
                    'expected': True,
                    'confidence': 1.0 if len(failure_events) > 0 else 0.0
                }
                
                print(f"  Major Mechanical Failure ({equipment_id}): {len(failure_events)} events")
        
        # Check for frequent micro-stops
        if self.config['anomaly_injection']['frequent_micro_stops']['enabled']:
            micro_config = self.config['anomaly_injection']['frequent_micro_stops']
            equipment_id = micro_config['equipment_id']
            reason_code = micro_config['downtime_reason']
            
            equipment = self.onto.search_one(hasEquipmentID=equipment_id)
            if equipment:
                micro_events = []
                for event in equipment.logsEvent:
                    if (isinstance(event, self.onto.DowntimeLog) and
                        hasattr(event, 'hasDowntimeReasonCode') and
                        reason_code in event.hasDowntimeReasonCode):
                        micro_events.append(event)
                
                patterns_found['frequent_micro_stops'] = {
                    'equipment': equipment_id,
                    'events_found': len(micro_events),
                    'expected': True,
                    'confidence': 1.0 if len(micro_events) > 5 else 0.5
                }
                
                print(f"  Frequent Micro-stops ({equipment_id}): {len(micro_events)} events")
        
        # Check for quality issues
        quality_issues = []
        for product_id, product_info in self.config['product_master'].items():
            if 'quality_issue_scrap_rate' in product_info:
                product = self.onto.search_one(hasProductID=product_id)
                if product:
                    # Find all production events for this product
                    low_quality_events = 0
                    total_events = 0
                    
                    for order in self.onto.ProductionOrder.instances():
                        if product in order.producesProduct:
                            for equipment in self.onto.Equipment.instances():
                                if order in equipment.executesOrder:
                                    for event in equipment.logsEvent:
                                        if isinstance(event, self.onto.ProductionLog):
                                            total_events += 1
                                            if hasattr(event, 'hasQualityScore'):
                                                quality = event.hasQualityScore[0]
                                                if quality < 96:  # Below 96% indicates quality issue
                                                    low_quality_events += 1
                    
                    if total_events > 0:
                        quality_issues.append({
                            'product': product_id,
                            'low_quality_events': low_quality_events,
                            'total_events': total_events,
                            'percentage': low_quality_events / total_events * 100
                        })
                        
                        print(f"  Quality Issues ({product_info['name']}): {low_quality_events}/{total_events} events")
        
        patterns_found['quality_issues'] = quality_issues
        self.validation_results['known_patterns'] = patterns_found
    
    def check_statistical_anomalies(self):
        """Check for statistical anomalies in the data."""
        print("\n4. Statistical Anomaly Detection")
        print("-" * 40)
        
        anomalies = {}
        
        # Check for sustained high OEE (unlikely in real world)
        high_oee_equipment = []
        for equipment in self.onto.Equipment.instances():
            oee_values = []
            for event in equipment.logsEvent:
                if hasattr(event, 'hasOEEScore') and event.hasOEEScore:
                    oee_values.append(event.hasOEEScore[0])
            
            if oee_values and len(oee_values) > 100:  # Need sufficient data
                avg_oee = np.mean(oee_values)
                if avg_oee > 95:  # Suspiciously high
                    high_oee_equipment.append({
                        'equipment': equipment.hasEquipmentID[0] if equipment.hasEquipmentID else 'Unknown',
                        'avg_oee': avg_oee,
                        'sample_size': len(oee_values)
                    })
        
        anomalies['high_oee_equipment'] = high_oee_equipment
        
        # Check for zero-variance metrics (indicates potential data issues)
        zero_variance_metrics = []
        for equipment in self.onto.Equipment.instances():
            metrics = {'availability': [], 'performance': [], 'quality': []}
            
            for event in equipment.logsEvent:
                if hasattr(event, 'hasAvailabilityScore'):
                    metrics['availability'].append(event.hasAvailabilityScore[0])
                if hasattr(event, 'hasPerformanceScore'):
                    metrics['performance'].append(event.hasPerformanceScore[0])
                if hasattr(event, 'hasQualityScore'):
                    metrics['quality'].append(event.hasQualityScore[0])
            
            for metric_name, values in metrics.items():
                if len(values) > 10:  # Need sufficient data
                    variance = np.var(values)
                    if variance < 0.1:  # Very low variance
                        zero_variance_metrics.append({
                            'equipment': equipment.hasEquipmentID[0] if equipment.hasEquipmentID else 'Unknown',
                            'metric': metric_name,
                            'variance': variance,
                            'mean': np.mean(values)
                        })
        
        anomalies['zero_variance_metrics'] = zero_variance_metrics[:5]  # Top 5
        
        if high_oee_equipment:
            print(f"  Found {len(high_oee_equipment)} equipment with suspiciously high OEE")
        if zero_variance_metrics:
            print(f"  Found {len(zero_variance_metrics)} metrics with near-zero variance")
        
        self.validation_results['statistical_anomalies'] = anomalies
    
    def validate_relationships(self):
        """Validate ontology relationships are consistent."""
        print("\n5. Relationship Consistency")
        print("-" * 40)
        
        issues = []
        
        # Check upstream/downstream consistency
        for equipment in self.onto.Equipment.instances():
            # Check if upstream relationships have matching downstream
            for upstream in equipment.isUpstreamOf:
                if equipment not in upstream.isDownstreamOf:
                    issues.append(f"Inconsistent upstream/downstream: {equipment.hasEquipmentID[0]} -> {upstream.hasEquipmentID[0]}")
        
        # Check that all equipment belongs to a line
        orphan_equipment = []
        for equipment in self.onto.Equipment.instances():
            if not equipment.belongsToLine:
                orphan_equipment.append(equipment.hasEquipmentID[0] if equipment.hasEquipmentID else 'Unknown')
        
        # Check that all events have timestamps
        events_without_timestamp = 0
        for event in self.onto.Event.instances():
            if not hasattr(event, 'hasTimestamp') or not event.hasTimestamp:
                events_without_timestamp += 1
        
        self.validation_results['relationship_consistency'] = {
            'upstream_downstream_issues': len(issues),
            'orphan_equipment': orphan_equipment,
            'events_without_timestamp': events_without_timestamp,
            'validation_status': 'PASS' if len(issues) == 0 and len(orphan_equipment) == 0 else 'FAIL'
        }
        
        print(f"  Upstream/Downstream Issues: {len(issues)}")
        print(f"  Orphan Equipment: {len(orphan_equipment)}")
        print(f"  Events without Timestamp: {events_without_timestamp}")
    
    def generate_validation_report(self):
        """Generate a comprehensive validation report."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        # Overall health score
        total_issues = 0
        total_issues += self.validation_results['kpi_validation'].get('total_issues', 0)
        total_issues += len(self.validation_results['relationship_consistency']['orphan_equipment'])
        total_issues += self.validation_results['relationship_consistency']['upstream_downstream_issues']
        
        health_score = max(0, 100 - (total_issues / 10))  # Lose 10 points per 100 issues
        
        print(f"\nOverall Health Score: {health_score:.1f}%")
        
        # Key findings
        print("\nKey Findings:")
        
        # Data completeness
        coverage = self.validation_results['data_integrity']['kpi_coverage']['coverage_percentage']
        print(f"  ✓ Data Completeness: {coverage:.1f}% events have KPIs")
        
        # KPI accuracy
        kpi_issues = self.validation_results['kpi_validation'].get('total_issues', 0)
        if kpi_issues == 0:
            print("  ✓ KPI Calculations: All within valid ranges")
        else:
            print(f"  ⚠ KPI Calculations: {kpi_issues} validation issues found")
        
        # Known patterns
        patterns = self.validation_results['known_patterns']
        patterns_detected = sum(1 for p in patterns.values() if isinstance(p, dict) and p.get('confidence', 0) > 0.5)
        print(f"  ✓ Pattern Detection: {patterns_detected} known patterns confirmed")
        
        # Anomalies
        anomalies = self.validation_results['statistical_anomalies']
        anomaly_count = sum(len(v) for v in anomalies.values() if isinstance(v, list))
        if anomaly_count > 0:
            print(f"  ⚠ Statistical Anomalies: {anomaly_count} potential issues")
        
        # Save detailed report to project root
        report_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "validation_report.json")
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return health_score

def main():
    """Main execution function."""
    # Load configuration
    config = load_config()
    
    print(f"MES LLM Validation Tool v1.0")
    print(f"Configuration: {config['ontology']['name']} v{config['ontology']['version']}")
    print("-" * 60)
    
    # Run validation on ontology file
    ontology_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Ontology", "mes_ontology_populated.owl")
    validator = OntologyValidator(ontology_file, config)
    validator.validate_all()
    health_score = validator.generate_validation_report()
    
    print("\n" + "=" * 60)
    if health_score > 90:
        print("✓ Ontology validation PASSED - Ready for LLM analysis")
    elif health_score > 70:
        print("⚠ Ontology validation PASSED with warnings - Review issues before LLM analysis")
    else:
        print("✗ Ontology validation FAILED - Address critical issues before proceeding")

if __name__ == "__main__":
    main()