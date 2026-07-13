"""pipeline.py

Main ETL pipeline orchestrator for the N100 Financial Intelligence Platform.

Coordinates the entire ETL workflow from extraction to loading.

This module is part of the production-grade ETL architecture and must remain
backwards compatible with existing entrypoints (e.g. run_etl.py).
"""

import logging
from datetime import datetime
from typing import Any, Dict

from src.config.logging_config import get_logger
from src.etl.data_quality import DataQualityReporter
from src.etl.extract import DataExtractor
from src.etl.load import DataLoader
from src.etl.normalizer import DataNormalizer
from src.etl.transform import DataTransformer
from src.etl.validator import DataValidator

logger = get_logger(__name__)


class ETLPipeline:
    """Orchestrates the complete ETL pipeline.

    Responsibilities:
    1. Coordinate extraction, validation, transformation, and loading
    2. Track pipeline execution status
    3. Generate data quality reports
    4. Handle errors and logging
    """

    def __init__(self) -> None:
        self.extractor = DataExtractor()
        self.validator = DataValidator()
        self.normalizer = DataNormalizer()
        self.transformer = DataTransformer()
        self.loader = DataLoader()
        self.reporter = DataQualityReporter()

        self.pipeline_stats: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "datasets_processed": 0,
            "datasets_failed": 0,
            "errors": [],
        }

    def run(
        self,
        validate: bool = True,
        normalize: bool = True,
        transform: bool = True,
        load: bool = True,
        generate_reports: bool = True,
    ) -> Dict[str, Any]:
        """Run the complete ETL pipeline."""

        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        self.pipeline_stats["status"] = "running"

        logger.info("=" * 80)
        logger.info("STARTING ETL PIPELINE")
        logger.info("=" * 80)

        try:
            # Step 1: Extract
            logger.info("\n[STEP 1/5] EXTRACTION")
            logger.info("-" * 40)
            raw_datasets = self._extract()

            if not raw_datasets:
                raise ValueError("No datasets extracted. Pipeline aborted.")

            # Step 2: Validate
            validation_results: Dict[str, Any] = {}
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
            load_stats: Dict[str, Any] = {}
            if load:
                logger.info("\n[STEP 5/5] LOADING")
                logger.info("-" * 40)
                load_stats = self._load(transformed_datasets)

            # Generate reports
            if generate_reports:
                logger.info("\n[REPORTING]")
                logger.info("-" * 40)
                self._generate_reports(validation_results, load_stats)

            self.pipeline_stats["status"] = "completed"
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            self.pipeline_stats["datasets_processed"] = len(raw_datasets)

            logger.info("\n" + "=" * 80)
            logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

            return self._get_pipeline_results(validation_results, load_stats)

        except Exception as exc:
            self.pipeline_stats["status"] = "failed"
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            self.pipeline_stats["errors"].append(str(exc))

            logger.error("\n" + "=" * 80)
            logger.error("ETL PIPELINE FAILED")
            logger.error("Error: %s", str(exc))
            logger.error("=" * 80)
            raise

    def _extract(self) -> Dict[str, Any]:
        logger.info("Extracting data from Excel files...")

        if not self.extractor.validate_raw_files():
            raise FileNotFoundError("Some required raw data files are missing")

        datasets = self.extractor.extract_all_datasets()
        logger.info("Extracted %s datasets", len(datasets))
        return datasets

    def _validate(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Validating datasets...")

        for dataset_name, df in datasets.items():
            logger.info("Validating: %s", dataset_name)

            required_columns = self._get_required_columns(dataset_name)
            expected_types = self._get_expected_types(dataset_name)

            self.validator.validate_dataset(
                df=df,
                dataset_name=dataset_name,
                required_columns=required_columns,
                expected_types=expected_types,
                missing_threshold=None,
                duplicate_subset=required_columns[:2] if len(required_columns) >= 2 else None,
            )

        summary = self.validator.get_validation_summary()
        logger.info("Validation complete: %s/%s passed", summary["passed"], summary["total_datasets"])
        return summary

    def _normalize(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Normalizing datasets...")

        normalized_datasets: Dict[str, Any] = {}

        for dataset_name, df in datasets.items():
            logger.info("Normalizing: %s", dataset_name)

            date_cols = self._get_date_columns(dataset_name)
            numeric_cols = self._get_numeric_columns(dataset_name)

            normalized_df = self.normalizer.normalize_dataframe(
                df=df,
                company_id_col="company_id",
                date_cols=date_cols,
                numeric_cols=numeric_cols,
            )

            subset = self._get_duplicate_subset(dataset_name)
            if subset:
                normalized_df = self.normalizer.remove_duplicates(normalized_df, subset=subset)

            normalized_datasets[dataset_name] = normalized_df

        logger.info("Normalized %s datasets", len(normalized_datasets))
        return normalized_datasets

    def _transform(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Transforming datasets...")

        transformed_datasets: Dict[str, Any] = {}

        for dataset_name, df in datasets.items():
            logger.info("Transforming: %s", dataset_name)

            transformed_df = self.transformer.transform_dataset(
                dataset_name=dataset_name,
                df=df,
            )

            transformed_datasets[dataset_name] = transformed_df

        logger.info("Transformed %s datasets", len(transformed_datasets))
        return transformed_datasets

    def _load(self, datasets: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Loading datasets into database...")

        if not self.loader.create_tables():
            raise RuntimeError("Failed to create database tables")

        load_stats = self.loader.load_all_datasets(datasets)

        expected_counts = {
            table: stats["rows_loaded"]
            for table, stats in load_stats.get("tables", {}).items()
            if stats.get("success")
        }

        if expected_counts:
            verification = self.loader.verify_table_counts(expected_counts)
            load_stats["verification"] = verification

        logger.info("Loaded %s total rows", load_stats.get("total_rows_loaded", 0))
        return load_stats

    def _generate_reports(self, validation_results: Dict[str, Any], load_stats: Dict[str, Any]) -> None:
        logger.info("Generating data quality reports...")

        self.reporter.set_validation_results(validation_results)
        self.reporter.set_normalization_log(self.normalizer.get_normalization_log())
        self.reporter.set_transformation_log(self.transformer.get_transformation_log())
        self.reporter.set_load_stats(load_stats)

        json_path = self.reporter.save_json_report()
        html_path = self.reporter.save_html_report()

        self.reporter.print_summary()
        logger.info("Reports generated: %s, %s", json_path, html_path)

    def _get_required_columns(self, dataset_name: str) -> list:
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
            "peer_groups": ["company_id", "peer_company_id"],
        }
        return required_columns_map.get(dataset_name, [])

    def _get_expected_types(self, dataset_name: str) -> Dict[str, str]:
        return {}

    def _get_date_columns(self, dataset_name: str) -> list:
        date_columns_map = {
            "companies": ["listed_date"],
            "documents": ["upload_date"],
            "stock_prices": ["date"],
            "market_cap": ["date"],
        }
        return date_columns_map.get(dataset_name, [])

    def _get_numeric_columns(self, dataset_name: str) -> list:
        numeric_columns_map = {
            "profit_loss": ["revenue", "gross_profit", "operating_profit", "net_profit", "eps"],
            "balance_sheet": ["total_assets", "total_liabilities", "total_equity", "current_assets", "current_liabilities"],
            "cash_flow": ["operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "free_cash_flow"],
            "financial_ratios": [
                "pe_ratio",
                "pb_ratio",
                "ps_ratio",
                "roe",
                "roa",
                "debt_to_equity",
                "current_ratio",
                "quick_ratio",
                "dividend_yield",
            ],
            "stock_prices": ["open_price", "high_price", "low_price", "close_price", "volume"],
            "market_cap": ["market_cap", "enterprise_value", "shares_outstanding"],
        }
        return numeric_columns_map.get(dataset_name, [])

    def _get_duplicate_subset(self, dataset_name: str) -> Optional[list]:
        duplicate_subset_map = {
            "profit_loss": ["company_id", "period"],
            "balance_sheet": ["company_id", "period"],
            "cash_flow": ["company_id", "period"],
            "analysis": ["company_id", "period"],
            "stock_prices": ["company_id", "date"],
            "market_cap": ["company_id", "date"],
            "financial_ratios": ["company_id", "period"],
            "pros_cons": ["company_id", "analysis_period"],
            "peer_groups": ["company_id", "peer_company_id"],
        }
        return duplicate_subset_map.get(dataset_name)

    def _get_pipeline_results(self, validation_results: Dict[str, Any], load_stats: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "pipeline_stats": self.pipeline_stats,
            "validation_summary": validation_results.get("summary", validation_results) if validation_results else {},
            "load_stats": load_stats,
            "normalization_log": self.normalizer.get_normalization_log(),
            "transformation_log": self.transformer.get_transformation_log(),
        }


def run_etl_pipeline(
    validate: bool = True,
    normalize: bool = True,
    transform: bool = True,
    load: bool = True,
    generate_reports: bool = True,
) -> Dict[str, Any]:
    """Backwards-compatible entrypoint used by run_etl.py."""

    pipeline = ETLPipeline()
    return pipeline.run(
        validate=validate,
        normalize=normalize,
        transform=transform,
        load=load,
        generate_reports=generate_reports,
    )

