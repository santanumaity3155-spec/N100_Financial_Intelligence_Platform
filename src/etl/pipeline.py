"""
pipeline.py

Main ETL pipeline orchestrator for the N100 Financial Intelligence Platform.
Coordinates the entire ETL workflow from extraction to loading.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.logging_config import get_logger
from src.etl.extract import DataExtractor
from src.etl.validator import DataValidator
from src.etl.normalizer import DataNormalizer
from src.etl.transform import DataTransformer
from src.etl.load import DataLoader
from src.etl.data_quality import DataQualityReporter

logger = get_logger(__name__)


class ETLPipeline:
    """
    Orchestrates the complete ETL pipeline.
    
    Responsibilities:
    1. Coordinate extraction, validation, transformation, and loading
    2. Track pipeline execution status
    3. Generate data quality reports
    4. Handle errors and logging
    """

    def __init__(self):
        """Initialize the ETL Pipeline."""
        self.extractor = DataExtractor()
        self.validator = DataValidator()
        self.normalizer = DataNormalizer()
        self.transformer = DataTransformer()
        self.loader = DataLoader()
        self.reporter = DataQualityReporter()
        
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "datasets_processed": 0,
            "datasets_failed": 0,
            "errors": []
        }

    def run(
        self,
        validate: bool = True,
        normalize: bool = True,
        transform: bool = True,
        load: bool = True,
        generate_reports: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete ETL pipeline.
        
        Parameters
        ----------
        validate : bool, default True
            Whether to validate datasets
        normalize : bool, default True
            Whether to normalize datasets
        transform : bool, default True
            Whether to transform datasets
        load : bool, default True
            Whether to load datasets into database
        generate_reports : bool, default True
            Whether to generate data quality reports
            
        Returns
        -------
        Dict[str, Any]
            Pipeline execution results
        """
        from datetime import datetime
        
        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        self.pipeline_stats["status"] = "running"
        
        logger.info("="*80)
        logger.info("STARTING ETL PIPELINE")
        logger.info("="*80)

        try:
            # Step 1: Extract
            logger.info("\n[STEP 1/5] EXTRACTION")
            logger.info("-" * 40)
            raw_datasets = self._extract()
            
            if not raw_datasets:
                raise ValueError("No datasets extracted. Pipeline aborted.")

            # Step 2: Validate
            validation_results = {}
            if validate:
                logger.info("\n[STEP 2/5] VALIDATION")
                logger.info("-" * 40)
                validation_results = self._validate(raw_datasets)

            # Step 3: Normalize
            normalized_datasets = raw_datasets
            if normalize:
                logger.info("\n[STEP 3/5] NORMALIZATION")
                logger.info("-" * 40)
                normalized_datasets = self._normalize(raw_datasets)

            # Step 4: Transform
            transformed_datasets = normalized_datasets
            if transform:
                logger.info("\n[STEP 4/5] TRANSFORMATION")
                logger.info("-" * 40)
                transformed_datasets = self._transform(normalized_datasets)

            # Step 5: Load
            load_stats = {}
            if load:
                logger.info("\n[STEP 5/5] LOADING")
                logger.info("-" * 40)
                load_stats = self._load(transformed_datasets)

            # Generate reports
            if generate_reports:
                logger.info("\n[REPORTING]")
                logger.info("-" * 40)
                self._generate_reports(validation_results, load_stats)

            # Update pipeline stats
            self.pipeline_stats["status"] = "completed"
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            self.pipeline_stats["datasets_processed"] = len(raw_datasets)

            logger.info("\n" + "="*80)
            logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("="*80)

            return self._get_pipeline_results(validation_results, load_stats)

        except Exception as e:
            self.pipeline_stats["status"] = "failed"
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            self.pipeline_stats["errors"].append(str(e))
            
            logger.error("\n" + "="*80)
            logger.error("ETL PIPELINE FAILED")
            logger.error(f"Error: {str(e)}")
            logger.error("="*80)
            
            raise

    def _extract(self) -> Dict[str, Any]:
        """
        Extract data from Excel files.
        
        Returns
        -------
        Dict[str, Any]
            Extracted datasets
        """
        logger.info("Extracting data from Excel files...")
        
        # Validate raw files exist
        if not self.extractor.validate_raw_files():
            raise FileNotFoundError("Some required raw data files are missing")

        # Extract all datasets
        datasets = self.extractor.extract_all_datasets()
        
        logger.info(f"Extracted {len(datasets)} datasets")
        return datasets

    def _validate(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all datasets.
        
        Parameters
        ----------
        datasets : Dict[str, Any]
            Datasets to validate
            
        Returns
        -------
        Dict[str, Any]
            Validation results
        """
        logger.info("Validating datasets...")
        
        for dataset_name, df in datasets.items():
            logger.info(f"Validating: {dataset_name}")
            
            # Define validation rules per dataset
            required_columns = self._get_required_columns(dataset_name)
            expected_types = self._get_expected_types(dataset_name)
            
            # Run validation
            self.validator.validate_dataset(
                df=df,
                dataset_name=dataset_name,
                required_columns=required_columns,
                expected_types=expected_types,
                missing_threshold=30.0,
                duplicate_subset=required_columns[:2] if len(required_columns) >= 2 else None
            )

        # Get summary
        summary = self.validator.get_validation_summary()
        logger.info(f"Validation complete: {summary['passed']}/{summary['total_datasets']} passed")
        
        return summary

    def _normalize(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all datasets.
        
        Parameters
        ----------
        datasets : Dict[str, Any]
            Datasets to normalize
            
        Returns
        -------
        Dict[str, Any]
            Normalized datasets
        """
        logger.info("Normalizing datasets...")
        
        normalized_datasets = {}
        
        for dataset_name, df in datasets.items():
            logger.info(f"Normalizing: {dataset_name}")
            
            # Get date columns for this dataset
            date_cols = self._get_date_columns(dataset_name)
            numeric_cols = self._get_numeric_columns(dataset_name)
            
            # Normalize
            normalized_df = self.normalizer.normalize_dataframe(
                df=df,
                company_id_col="company_id",
                date_cols=date_cols,
                numeric_cols=numeric_cols
            )
            
            # Remove duplicates
            subset = self._get_duplicate_subset(dataset_name)
            if subset:
                normalized_df = self.normalizer.remove_duplicates(
                    normalized_df, subset=subset
                )
            
            normalized_datasets[dataset_name] = normalized_df

        logger.info(f"Normalized {len(normalized_datasets)} datasets")
        return normalized_datasets

    def _transform(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform all datasets.
        
        Parameters
        ----------
        datasets : Dict[str, Any]
            Datasets to transform
            
        Returns
        -------
        Dict[str, Any]
            Transformed datasets
        """
        logger.info("Transforming datasets...")
        
        transformed_datasets = {}
        
        for dataset_name, df in datasets.items():
            logger.info(f"Transforming: {dataset_name}")
            
            transformed_df = self.transformer.transform_dataset(
                dataset_name=dataset_name,
                df=df
            )
            
            transformed_datasets[dataset_name] = transformed_df

        logger.info(f"Transformed {len(transformed_datasets)} datasets")
        return transformed_datasets

    def _load(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load all datasets into database.
        
        Parameters
        ----------
        datasets : Dict[str, Any]
            Datasets to load
            
        Returns
        -------
        Dict[str, Any]
            Load statistics
        """
        logger.info("Loading datasets into database...")
        
        # Create tables
        if not self.loader.create_tables():
            raise RuntimeError("Failed to create database tables")

        # Load all datasets
        load_stats = self.loader.load_all_datasets(datasets)
        
        # Verify counts
        expected_counts = {
            table: stats["rows_loaded"] 
            for table, stats in load_stats.get("tables", {}).items()
            if stats.get("success")
        }
        
        if expected_counts:
            verification = self.loader.verify_table_counts(expected_counts)
            load_stats["verification"] = verification

        logger.info(f"Loaded {load_stats['total_rows_loaded']} total rows")
        return load_stats

    def _generate_reports(
        self,
        validation_results: Dict[str, Any],
        load_stats: Dict[str, Any]
    ):
        """
        Generate data quality reports.
        
        Parameters
        ----------
        validation_results : Dict[str, Any]
            Validation results
        load_stats : Dict[str, Any]
            Load statistics
        """
        logger.info("Generating data quality reports...")
        
        # Set data for reporter
        self.reporter.set_validation_results(validation_results)
        self.reporter.set_normalization_log(self.normalizer.get_normalization_log())
        self.reporter.set_transformation_log(self.transformer.get_transformation_log())
        self.reporter.set_load_stats(load_stats)
        
        # Generate reports
        json_path = self.reporter.save_json_report()
        html_path = self.reporter.save_html_report()
        
        # Print summary
        self.reporter.print_summary()
        
        logger.info(f"Reports generated: {json_path}, {html_path}")

    def _get_required_columns(self, dataset_name: str) -> list:
        """
        Get required columns for a dataset.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset
            
        Returns
        -------
        list
            List of required columns
        """
        required_columns_map = {
            "companies": ["company_id", "company_name"],
            "profit_loss": ["company_id", "period"],
            "balance_sheet": ["company_id", "period"],
            "cash_flow": ["company_id", "period"],
            "analysis": ["company_id", "period"],
            "documents": ["company_id"],
            "pros_cons": ["company_id"],
            "sectors": ["sector_id"],
            "stock_prices": ["company_id", "date"],
            "market_cap": ["company_id", "date"],
            "financial_ratios": ["company_id", "period"],
            "peer_groups": ["company_id", "peer_company_id"]
        }
        
        return required_columns_map.get(dataset_name, [])

    def _get_expected_types(self, dataset_name: str) -> Dict[str, str]:
        """
        Get expected data types for a dataset.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset
            
        Returns
        -------
        Dict[str, str]
            Expected data types
        """
        # Simplified - can be extended based on actual data
        return {}

    def _get_date_columns(self, dataset_name: str) -> list:
        """
        Get date columns for a dataset.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset
            
        Returns
        -------
        list
            List of date columns
        """
        date_columns_map = {
            "companies": ["listed_date"],
            "documents": ["upload_date"],
            "stock_prices": ["date"],
            "market_cap": ["date"]
        }
        
        return date_columns_map.get(dataset_name, [])

    def _get_numeric_columns(self, dataset_name: str) -> list:
        """
        Get numeric columns for a dataset.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset
            
        Returns
        -------
        list
            List of numeric columns
        """
