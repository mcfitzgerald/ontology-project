#!/usr/bin/env python3
"""
Orchestrate Data Pipeline - Automated workflow for MES ontology data generation

This script orchestrates the complete data generation pipeline:
1. Validates configuration
2. Generates manufacturing data
3. Populates ontology
4. Extracts mindmap
5. Generates data catalogue
6. Validates outputs

Usage:
    python orchestrate_data_pipeline.py                    # Full pipeline
    python orchestrate_data_pipeline.py --dry-run         # Preview without execution
    python orchestrate_data_pipeline.py --validate-config # Validate config only
    python orchestrate_data_pipeline.py --force           # Overwrite existing files
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
import logging
from datetime import datetime
from pathlib import Path
import traceback
from typing import Dict, List, Tuple, Optional
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('orchestration.log')
    ]
)
logger = logging.getLogger(__name__)


class DataPipelineOrchestrator:
    """Orchestrates the complete data generation pipeline"""
    
    def __init__(self, config_path: str = None, dry_run: bool = False, 
                 force: bool = False, skip_backup: bool = False):
        self.project_root = Path(__file__).parent
        self.config_path = config_path or self.project_root / "Data_Generation" / "mes_data_config.json"
        self.dry_run = dry_run
        self.force = force
        self.skip_backup = skip_backup
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Define expected outputs
        self.outputs = {
            'data': self.project_root / "Data" / "mes_data_with_kpis.csv",
            'ontology': self.project_root / "Ontology" / "mes_ontology_populated.owl",
            'mindmap': self.project_root / "Context" / "mes_ontology_mindmap.ttl",
            'catalogue': self.project_root / "Context" / "mes_data_catalogue.json"
        }
        
        # Define scripts
        self.scripts = {
            'data': self.project_root / "Data_Generation" / "mes_data_generation.py",
            'ontology': self.project_root / "Ontology_Generation" / "mes_ontology_population.py",
            'mindmap': self.project_root / "Ontology_Generation" / "extract_ontology_to_ttl.py",
            'catalogue': self.project_root / "Data_Generation" / "generate_data_catalogue.py"
        }
        
        self.config = None
        self.validation_errors = []
        self.validation_warnings = []

    def validate_configuration(self) -> bool:
        """Validate the configuration file structure and values"""
        logger.info(f"Validating configuration: {self.config_path}")
        
        # Check if config exists
        if not self.config_path.exists():
            self.validation_errors.append(f"Configuration file not found: {self.config_path}")
            return False
        
        # Load and parse JSON
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            self.validation_errors.append(f"Invalid JSON in config file: {e}")
            return False
        
        # Validate required sections
        required_sections = [
            'ontology', 'equipment_configuration', 'product_master',
            'downtime_reason_mapping', 'anomaly_injection', 'product_specifications',
            'production_schedule'
        ]
        
        for section in required_sections:
            if section not in self.config:
                self.validation_errors.append(f"Missing required section: {section}")
        
        # Validate ontology section
        if 'ontology' in self.config:
            ont = self.config['ontology']
            if not all(k in ont for k in ['name', 'version', 'iri']):
                self.validation_errors.append("Ontology section missing required fields (name, version, iri)")
        
        # Validate equipment configuration
        if 'equipment_configuration' in self.config:
            equip_config = self.config['equipment_configuration']
            if 'lines' not in equip_config:
                self.validation_errors.append("Equipment configuration missing 'lines' section")
            else:
                # Validate each line
                for line_id, line_config in equip_config['lines'].items():
                    if 'equipment_sequence' not in line_config:
                        self.validation_errors.append(f"{line_id} missing equipment_sequence")
                    if 'process_flow' not in line_config:
                        self.validation_errors.append(f"{line_id} missing process_flow")
                    
                    # Validate process flow references
                    if 'process_flow' in line_config and 'equipment_sequence' in line_config:
                        equip_ids = {eq['id'] for eq in line_config['equipment_sequence']}
                        for eq_id, flow in line_config['process_flow'].items():
                            if eq_id not in equip_ids:
                                self.validation_errors.append(f"Process flow references unknown equipment: {eq_id}")
                            if flow['downstream'] and flow['downstream'] not in equip_ids:
                                self.validation_errors.append(f"Process flow references unknown downstream: {flow['downstream']}")
        
        # Validate products
        if 'product_master' in self.config:
            products = self.config['product_master']
            if len(products) < 1:
                self.validation_errors.append("No products defined in product_master")
            
            for product_id, product in products.items():
                # Check required fields
                required_fields = ['name', 'target_rate_units_per_5min', 
                                 'standard_cost_per_unit', 'sale_price_per_unit']
                for field in required_fields:
                    if field not in product:
                        self.validation_errors.append(f"Product {product_id} missing field: {field}")
                
                # Business rule validations
                if 'standard_cost_per_unit' in product and 'sale_price_per_unit' in product:
                    if product['sale_price_per_unit'] <= product['standard_cost_per_unit']:
                        self.validation_warnings.append(
                            f"Product {product_id} has non-positive margin "
                            f"(cost: {product['standard_cost_per_unit']}, "
                            f"price: {product['sale_price_per_unit']})"
                        )
                
                if 'target_rate_units_per_5min' in product:
                    rate = product['target_rate_units_per_5min']
                    if rate <= 0 or rate > 1000:
                        self.validation_warnings.append(
                            f"Product {product_id} has unusual target rate: {rate} units/5min"
                        )
        
        # Validate downtime reasons
        if 'downtime_reason_mapping' in self.config:
            downtime_reasons = self.config['downtime_reason_mapping']
            valid_classes = [
                'Changeover', 'Cleaning', 'PreventiveMaintenance',
                'MechanicalFailure', 'MaterialJam', 'MaterialStarvation',
                'ElectricalFailure', 'QualityCheck', 'OperatorError', 'SensorFailure'
            ]
            
            for code, reason in downtime_reasons.items():
                if 'class' not in reason:
                    self.validation_errors.append(f"Downtime reason {code} missing 'class' field")
                elif reason['class'] not in valid_classes:
                    self.validation_warnings.append(
                        f"Downtime reason {code} has unrecognized class: {reason['class']}"
                    )
        
        # Validate anomaly injection
        if 'anomaly_injection' in self.config:
            anomalies = self.config['anomaly_injection']
            for anomaly_name, anomaly_config in anomalies.items():
                if isinstance(anomaly_config, dict) and 'enabled' in anomaly_config:
                    # Validate probability fields
                    if 'probability_per_5min' in anomaly_config:
                        prob = anomaly_config['probability_per_5min']
                        if not (0 <= prob <= 1):
                            self.validation_errors.append(
                                f"Anomaly {anomaly_name} has invalid probability: {prob}"
                            )
        
        # Print validation results
        if self.validation_errors:
            logger.error("Configuration validation failed:")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
            return False
        
        if self.validation_warnings:
            logger.warning("Configuration warnings:")
            for warning in self.validation_warnings:
                logger.warning(f"  - {warning}")
        
        logger.info("✓ Configuration validation passed")
        return True

    def print_configuration_summary(self):
        """Print a summary of the configuration"""
        if not self.config:
            return
        
        logger.info("\n" + "="*60)
        logger.info("CONFIGURATION SUMMARY")
        logger.info("="*60)
        
        # Ontology info
        ont = self.config.get('ontology', {})
        logger.info(f"Ontology: {ont.get('name', 'Unknown')} v{ont.get('version', 'Unknown')}")
        logger.info(f"IRI: {ont.get('iri', 'Unknown')}")
        
        # Equipment summary
        equip_config = self.config.get('equipment_configuration', {})
        lines = equip_config.get('lines', {})
        logger.info(f"\nProduction Lines: {len(lines)}")
        for line_id, line_config in lines.items():
            equip_count = len(line_config.get('equipment_sequence', []))
            logger.info(f"  - {line_id}: {equip_count} equipment")
        
        # Product summary
        products = self.config.get('product_master', {})
        logger.info(f"\nProducts: {len(products)} SKUs")
        for product_id, product in products.items():
            logger.info(f"  - {product_id}: {product.get('name', 'Unknown')}")
        
        # Anomaly summary
        anomalies = self.config.get('anomaly_injection', {})
        enabled_anomalies = sum(1 for a in anomalies.values() 
                              if isinstance(a, dict) and a.get('enabled', False))
        logger.info(f"\nAnomalies Enabled: {enabled_anomalies} patterns")
        
        # Expected output
        logger.info(f"\nExpected Output:")
        logger.info(f"  - Date Range: 14 days (2025-06-01 to 2025-06-14)")
        logger.info(f"  - Records: ~36,000 (5-minute intervals)")
        logger.info(f"  - Output Files: 4 (CSV, OWL, TTL, JSON)")
        logger.info("="*60 + "\n")

    def check_dependencies(self) -> bool:
        """Check if all required Python packages are installed"""
        logger.info("Checking Python dependencies...")
        
        required_packages = {
            'pandas': 'pandas',
            'numpy': 'numpy',
            'owlready2': 'owlready2'
        }
        
        missing_packages = []
        for import_name, package_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
        if missing_packages:
            logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            logger.error("Install with: pip install " + ' '.join(missing_packages))
            return False
        
        logger.info("✓ All dependencies satisfied")
        return True

    def backup_existing_data(self):
        """Backup existing output files"""
        if self.skip_backup or self.dry_run:
            return
        
        files_to_backup = []
        for name, path in self.outputs.items():
            if path.exists():
                files_to_backup.append((name, path))
        
        if not files_to_backup:
            logger.info("No existing files to backup")
            return
        
        logger.info(f"Backing up {len(files_to_backup)} existing files to {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)
        
        for name, path in files_to_backup:
            backup_path = self.backup_dir / path.name
            if not self.dry_run:
                shutil.copy2(path, backup_path)
                logger.info(f"  - Backed up {name}: {path.name}")

    def run_script(self, script_name: str, script_path: Path) -> bool:
        """Run a Python script and capture output"""
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
        
        logger.info(f"Running {script_name}...")
        
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would execute: python {script_path}")
            return True
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Log output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    logger.info(f"  {line}")
            
            if result.stderr:
                for line in result.stderr.strip().split('\n'):
                    logger.warning(f"  {line}")
            
            if result.returncode != 0:
                logger.error(f"Script failed with return code: {result.returncode}")
                return False
            
            logger.info(f"✓ {script_name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running script: {e}")
            logger.error(traceback.format_exc())
            return False

    def validate_output(self, output_name: str, output_path: Path) -> bool:
        """Validate that output file exists and has expected content"""
        if self.dry_run:
            return True
        
        if not output_path.exists():
            logger.error(f"Output file not created: {output_path}")
            return False
        
        file_size = output_path.stat().st_size
        if file_size == 0:
            logger.error(f"Output file is empty: {output_path}")
            return False
        
        # Specific validations based on file type
        if output_name == 'data' and output_path.suffix == '.csv':
            try:
                import pandas as pd
                df = pd.read_csv(output_path, nrows=5)
                
                # Check expected columns
                expected_columns = [
                    'Timestamp', 'ProductionOrderID', 'LineID', 'EquipmentID',
                    'MachineStatus', 'GoodUnitsProduced', 'ScrapUnitsProduced',
                    'OEE_Score', 'Availability_Score', 'Performance_Score', 'Quality_Score'
                ]
                
                missing_columns = set(expected_columns) - set(df.columns)
                if missing_columns:
                    logger.error(f"CSV missing columns: {missing_columns}")
                    return False
                
                # Check row count
                row_count = len(pd.read_csv(output_path, usecols=['Timestamp']))
                logger.info(f"  - CSV contains {row_count:,} rows")
                if row_count < 30000:
                    logger.warning(f"CSV has fewer rows than expected: {row_count}")
                
            except Exception as e:
                logger.error(f"Error validating CSV: {e}")
                return False
        
        elif output_name == 'ontology' and output_path.suffix == '.owl':
            # Basic OWL validation - check it's valid XML
            try:
                with open(output_path, 'r') as f:
                    content = f.read(1000)  # Read first 1KB
                    if '<?xml' not in content or 'owl:Ontology' not in content:
                        logger.error("OWL file doesn't appear to be valid")
                        return False
            except Exception as e:
                logger.error(f"Error validating OWL: {e}")
                return False
        
        elif output_name == 'mindmap' and output_path.suffix == '.ttl':
            # Basic Turtle validation
            try:
                with open(output_path, 'r') as f:
                    content = f.read(1000)
                    if '@prefix' not in content:
                        logger.error("TTL file doesn't appear to be valid Turtle format")
                        return False
            except Exception as e:
                logger.error(f"Error validating TTL: {e}")
                return False
        
        elif output_name == 'catalogue' and output_path.suffix == '.json':
            # Validate JSON structure
            try:
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    required_sections = ['metadata', 'equipment', 'products', 'metrics']
                    missing_sections = set(required_sections) - set(data.keys())
                    if missing_sections:
                        logger.error(f"Catalogue missing sections: {missing_sections}")
                        return False
            except Exception as e:
                logger.error(f"Error validating JSON: {e}")
                return False
        
        logger.info(f"✓ Validated {output_name}: {output_path.name} ({file_size:,} bytes)")
        return True

    def generate_summary_report(self):
        """Generate a summary report of the pipeline execution"""
        logger.info("\n" + "="*60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("="*60)
        
        if self.dry_run:
            logger.info("DRY RUN - No files were actually created or modified")
        
        # Check what was created
        logger.info("\nOutput Files:")
        for name, path in self.outputs.items():
            if path.exists():
                size = path.stat().st_size
                modified = datetime.fromtimestamp(path.stat().st_mtime)
                logger.info(f"  ✓ {name}: {path.name} ({size:,} bytes, modified: {modified:%Y-%m-%d %H:%M:%S})")
            else:
                logger.info(f"  ✗ {name}: Not found")
        
        # Configuration summary
        if self.config:
            logger.info("\nConfiguration Used:")
            logger.info(f"  - Ontology: {self.config['ontology']['name']} v{self.config['ontology']['version']}")
            logger.info(f"  - Lines: {len(self.config['equipment_configuration']['lines'])}")
            logger.info(f"  - Products: {len(self.config['product_master'])}")
            
            # Count enabled anomalies
            anomalies = self.config.get('anomaly_injection', {})
            enabled = sum(1 for a in anomalies.values() if isinstance(a, dict) and a.get('enabled', False))
            logger.info(f"  - Anomalies: {enabled} enabled")
        
        logger.info("\nNext Steps:")
        logger.info("  1. Start SPARQL API: python -m uvicorn API.main:app --port 8000")
        logger.info("  2. Start ADK Web UI: cd adk_agents && adk web --port 8001")
        logger.info("  3. Navigate to: http://localhost:8001/dev-ui/")
        logger.info("="*60)

    def run_parallel_steps(self) -> Tuple[bool, bool]:
        """Run mindmap and catalogue generation in parallel"""
        logger.info("Running mindmap and catalogue generation in parallel...")
        
        if self.dry_run:
            logger.info("  [DRY RUN] Would run extract_ontology_to_ttl.py and generate_data_catalogue.py in parallel")
            return True, True
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            mindmap_future = executor.submit(
                self.run_script, 'mindmap extraction', self.scripts['mindmap']
            )
            catalogue_future = executor.submit(
                self.run_script, 'catalogue generation', self.scripts['catalogue']
            )
            
            # Wait for completion
            mindmap_success = mindmap_future.result()
            catalogue_success = catalogue_future.result()
            
        return mindmap_success, catalogue_success

    def orchestrate(self, steps: Optional[List[str]] = None) -> bool:
        """Run the complete orchestration pipeline"""
        all_steps = ['validate', 'backup', 'data', 'ontology', 'mindmap', 'catalogue']
        steps_to_run = steps or all_steps
        
        logger.info("Starting MES Data Pipeline Orchestration")
        logger.info(f"Steps to run: {', '.join(steps_to_run)}")
        
        if self.dry_run:
            logger.info("*** DRY RUN MODE - No changes will be made ***")
        
        try:
            # Step 1: Validate configuration
            if 'validate' in steps_to_run:
                if not self.validate_configuration():
                    return False
                self.print_configuration_summary()
            
            # Check dependencies
            if not self.check_dependencies():
                return False
            
            # Step 2: Backup existing data
            if 'backup' in steps_to_run and not self.skip_backup:
                self.backup_existing_data()
            
            # Step 3: Generate manufacturing data
            if 'data' in steps_to_run:
                if not self.run_script('data generation', self.scripts['data']):
                    logger.error("Data generation failed")
                    return False
                if not self.validate_output('data', self.outputs['data']):
                    return False
            
            # Step 4: Populate ontology
            if 'ontology' in steps_to_run:
                if not self.run_script('ontology population', self.scripts['ontology']):
                    logger.error("Ontology population failed")
                    return False
                if not self.validate_output('ontology', self.outputs['ontology']):
                    return False
            
            # Step 5 & 6: Extract mindmap and generate catalogue (in parallel)
            if 'mindmap' in steps_to_run or 'catalogue' in steps_to_run:
                mindmap_needed = 'mindmap' in steps_to_run
                catalogue_needed = 'catalogue' in steps_to_run
                
                if mindmap_needed and catalogue_needed:
                    # Run in parallel
                    mindmap_success, catalogue_success = self.run_parallel_steps()
                    
                    if mindmap_needed and not mindmap_success:
                        logger.error("Mindmap extraction failed")
                        return False
                    if catalogue_needed and not catalogue_success:
                        logger.error("Catalogue generation failed")
                        return False
                else:
                    # Run individually
                    if mindmap_needed:
                        if not self.run_script('mindmap extraction', self.scripts['mindmap']):
                            logger.error("Mindmap extraction failed")
                            return False
                    if catalogue_needed:
                        if not self.run_script('catalogue generation', self.scripts['catalogue']):
                            logger.error("Catalogue generation failed")
                            return False
                
                # Validate outputs
                if mindmap_needed and not self.validate_output('mindmap', self.outputs['mindmap']):
                    return False
                if catalogue_needed and not self.validate_output('catalogue', self.outputs['catalogue']):
                    return False
            
            # Generate summary report
            self.generate_summary_report()
            
            logger.info("\n✅ Pipeline orchestration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Orchestration failed with error: {e}")
            logger.error(traceback.format_exc())
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Orchestrate MES data generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrate_data_pipeline.py                    # Run full pipeline
  python orchestrate_data_pipeline.py --dry-run         # Preview without execution
  python orchestrate_data_pipeline.py --validate-config # Validate config only
  python orchestrate_data_pipeline.py --force           # Overwrite existing files
  python orchestrate_data_pipeline.py --skip-backup     # Skip backup step
  python orchestrate_data_pipeline.py --steps data,ontology  # Run specific steps only
        """
    )
    
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Preview actions without executing')
    parser.add_argument('--validate-config', action='store_true', help='Validate configuration only')
    parser.add_argument('--force', action='store_true', help='Force regeneration of existing files')
    parser.add_argument('--skip-backup', action='store_true', help='Skip backup of existing files')
    parser.add_argument('--steps', type=str, help='Comma-separated list of steps to run')
    
    args = parser.parse_args()
    
    # Handle validate-only mode
    if args.validate_config:
        orchestrator = DataPipelineOrchestrator(
            config_path=args.config,
            dry_run=True
        )
        success = orchestrator.validate_configuration()
        if success:
            orchestrator.print_configuration_summary()
        sys.exit(0 if success else 1)
    
    # Parse steps if provided
    steps = None
    if args.steps:
        steps = [s.strip() for s in args.steps.split(',')]
        valid_steps = ['validate', 'backup', 'data', 'ontology', 'mindmap', 'catalogue']
        invalid_steps = set(steps) - set(valid_steps)
        if invalid_steps:
            logger.error(f"Invalid steps: {invalid_steps}")
            logger.error(f"Valid steps are: {', '.join(valid_steps)}")
            sys.exit(1)
    
    # Create and run orchestrator
    orchestrator = DataPipelineOrchestrator(
        config_path=args.config,
        dry_run=args.dry_run,
        force=args.force,
        skip_backup=args.skip_backup
    )
    
    success = orchestrator.orchestrate(steps=steps)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()