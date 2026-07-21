"""
engine.py

Core Investment Screener Engine (Module 6) for the N100 Financial Intelligence Platform.

This module provides comprehensive screening, filtering, sorting, and ranking
capabilities for Nifty 100 companies using financial KPIs from previous modules.

Responsibilities:
1. Load data from multiple tables (financial_ratios, financial_health_scores, market_cap, balance_sheet)
2. Apply multiple filter conditions with AND/OR logic
3. Sort results by multiple fields
4. Rank companies by selected metrics
5. Export results to CSV
6. Comprehensive logging and error handling
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import sqlite3

from src.config.logging_config import get_logger
from src.config.constants import OUTPUT_DIR
from src.database.connection import get_connection
from src.screener.constants import (
    DEFAULT_OUTPUT_COLUMNS,
    MAX_RECORDS_LIMIT,
    SCREENER_CSV_PATH,
    VALID_SCREEN_FIELDS,
    SUPPORTED_RANK_FIELDS,
)
from src.screener.filters import FilterCondition, FilterGroup, FilterOperator, FilterValidator
from src.screener.exporter import ScreenerExporter
from src.screener.templates import ScreenTemplateManager

logger = get_logger(__name__)


# =============================================================================
# SCREENER ENGINE
# =============================================================================

class ScreenerEngine:
    """
    Investment Screener Engine for filtering, sorting, and ranking Nifty 100 companies.

    This engine loads financial data from the database and applies user-defined
    filters to screen companies based on various financial KPIs.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the Screener Engine.

        Parameters
        ----------
        output_dir : Path, optional
            Output directory for CSV exports, by default uses OUTPUT_DIR
        """
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.data: Optional[pd.DataFrame] = None
        self.filtered_data: Optional[pd.DataFrame] = None
        self.results: List[Dict[str, Any]] = []

        self.pipeline_stats: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "total_companies": 0,
            "records_after_filtering": 0,
            "filters_applied": 0,
            "execution_time": 0,
            "errors": [],
            "warnings": [],
        }

        self.exporter = ScreenerExporter(output_dir=self.output_dir)
        self.template_manager = ScreenTemplateManager()
        self.filter_validator = FilterValidator(VALID_SCREEN_FIELDS)

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------

    def load_data(self) -> pd.DataFrame:
        """
        Load financial data from multiple tables for screening.

        Joins data from:
        - companies (basic info)
        - financial_ratios (profitability, growth, cash flow, leverage)
        - financial_health_scores (health scores and ratings)
        - market_cap (valuation metrics, dividend yield)
        - balance_sheet (liquidity ratios)

        Returns
        -------
        pd.DataFrame
            Combined DataFrame with all screening data
        """
        logger.info("Loading data for screening...")
        start_time = time.time()

        try:
            conn = get_connection()

            # Build comprehensive query joining all relevant tables
            query = """
                SELECT
                    -- Company Info
                    c.company_id,
                    c.company_name,
                    c.sector,
                    c.industry,
                    
                    -- Financial Ratios
                    fr.period,
                    fr.roe,
                    fr.roa,
                    fr.roce,
                    fr.net_profit_margin,
                    fr.operating_profit_margin,
                    fr.revenue_cagr_3yr,
                    fr.revenue_cagr_5yr,
                    fr.pat_cagr_3yr,
                    fr.pat_cagr_5yr,
                    fr.eps_cagr_3yr,
                    fr.eps_cagr_5yr,
                    fr.free_cash_flow,
                    fr.fcf_margin,
                    fr.cash_conversion,
                    fr.cash_return_on_assets,
                    fr.debt_to_equity,
                    fr.interest_coverage,
                    
                    -- Financial Health Scores
                    fhs.overall_score,
                    fhs.rating,
                    fhs.profitability_score,
                    fhs.growth_score,
                    fhs.cashflow_score,
                    fhs.leverage_score,
                    fhs.efficiency_score,
                    
                    -- Market Cap (Valuation & Dividend)
                    mc.pe_ratio,
                    mc.pb_ratio,
                    mc.dividend_yield,
                    
                    -- Balance Sheet (Liquidity)
                    bs.current_ratio,
                    bs.quick_ratio
                    
                FROM companies c
                LEFT JOIN financial_ratios fr ON c.company_id = fr.company_id
                LEFT JOIN financial_health_scores fhs ON c.company_id = fhs.company_id 
                    AND fr.period = fhs.period
                LEFT JOIN market_cap mc ON c.company_id = mc.company_id 
                    AND fr.period = mc.period
                LEFT JOIN balance_sheet bs ON c.company_id = bs.company_id 
                    AND fr.period = bs.period
                
                WHERE fr.period IS NOT NULL
                
                ORDER BY c.company_id, fr.period
            """

            self.data = pd.read_sql_query(query, conn)

            # Clean up NaN values for easier processing
            self.data = self.data.replace({pd.NA: None, pd.NaT: None})

            execution_time = time.time() - start_time
            logger.info(
                f"Loaded {len(self.data)} company-period records in {execution_time:.2f}s"
            )

            self.pipeline_stats["total_companies"] = len(self.data)
            return self.data

        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            self.pipeline_stats["errors"].append(f"Data loading failed: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # FILTERING
    # ------------------------------------------------------------------

    def apply_filters(
        self,
        filters: Union[List[Dict[str, Any]], FilterGroup, List[FilterCondition]],
        logic: str = "AND",
    ) -> pd.DataFrame:
        """
        Apply filters to the loaded data.

        Parameters
        ----------
        filters : Union[List[Dict[str, Any]], FilterGroup, List[FilterCondition]]
            Filter conditions to apply. Can be:
            - List of filter dictionaries
            - FilterGroup object
            - List of FilterCondition objects
        logic : str, optional
            Logic for combining filters: "AND" or "OR", by default "AND"

        Returns
        -------
        pd.DataFrame
            Filtered DataFrame

        Raises
        ------
        ValueError
            If data is not loaded or filters are invalid
        """
        if self.data is None or self.data.empty:
            raise ValueError("No data loaded. Call load_data() first.")

        start_time = time.time()
        logger.info(f"Applying {len(filters)} filters with {logic} logic...")

        # Normalize filters to FilterCondition objects
        conditions = self._normalize_filters(filters)

        # Validate filters
        errors = self.filter_validator.validate_filter_group(
            FilterGroup(conditions=conditions, logic=logic)
        )
        if errors:
            error_msg = f"Filter validation errors: {'; '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Apply filters
        try:
            mask = self._build_filter_mask(conditions, logic)
            self.filtered_data = self.data[mask].copy()

            execution_time = time.time() - start_time
            records_after = len(self.filtered_data)
            records_removed = len(self.data) - records_after

            logger.info(
                f"Filtering complete: {records_after} records remaining "
                f"({records_removed} removed) in {execution_time:.2f}s"
            )

            self.pipeline_stats["filters_applied"] = len(conditions)
            self.pipeline_stats["records_after_filtering"] = records_after

            return self.filtered_data

        except Exception as e:
            error_msg = f"Failed to apply filters: {str(e)}"
            logger.error(error_msg)
            self.pipeline_stats["errors"].append(error_msg)
            raise

    def _normalize_filters(
        self, filters: Union[List[Dict[str, Any]], FilterGroup, List[FilterCondition]]
    ) -> List[FilterCondition]:
        """
        Normalize filters to a list of FilterCondition objects.

        Parameters
        ----------
        filters : Union[List[Dict[str, Any]], FilterGroup, List[FilterCondition]]
            Filters to normalize

        Returns
        -------
        List[FilterCondition]
            List of FilterCondition objects
        """
        conditions = []

        if isinstance(filters, FilterGroup):
            # Flatten FilterGroup
            for cond in filters.conditions:
                if isinstance(cond, FilterCondition):
                    conditions.append(cond)
                elif isinstance(cond, FilterGroup):
                    conditions.extend(self._normalize_filters(cond))
        elif isinstance(filters, list):
            for item in filters:
                if isinstance(item, FilterCondition):
                    conditions.append(item)
                elif isinstance(item, dict):
                    conditions.append(FilterCondition.from_dict(item))
                elif isinstance(item, FilterGroup):
                    conditions.extend(self._normalize_filters(item))

        return conditions

    def _build_filter_mask(
        self, conditions: List[FilterCondition], logic: str
    ) -> pd.Series:
        """
        Build a boolean mask for filtering.

        Parameters
        ----------
        conditions : List[FilterCondition]
            List of filter conditions
        logic : str
            Logic for combining conditions: "AND" or "OR"

        Returns
        -------
        pd.Series
            Boolean mask for filtering
        """
        if not conditions:
            return pd.Series([True] * len(self.data), index=self.data.index)

        masks = []
        for condition in conditions:
            mask = self._evaluate_condition(condition)
            masks.append(mask)

        if logic == "AND":
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask = combined_mask & mask
        else:  # OR
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask = combined_mask | mask

        return combined_mask

    def _evaluate_condition(self, condition: FilterCondition) -> pd.Series:
        """
        Evaluate a single filter condition.

        Parameters
        ----------
        condition : FilterCondition
            Filter condition to evaluate

        Returns
        -------
        pd.Series
            Boolean mask for the condition
        """
        field = condition.field
        operator = condition.operator
        value = condition.value
        value2 = condition.value2

        # Get the column data
        if field not in self.data.columns:
            logger.warning(f"Field '{field}' not found in data, returning all False")
            return pd.Series([False] * len(self.data), index=self.data.index)

        col_data = self.data[field]

        # Evaluate based on operator
        if operator == FilterOperator.GREATER_THAN:
            return col_data > value
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return col_data >= value
        elif operator == FilterOperator.LESS_THAN:
            return col_data < value
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return col_data <= value
        elif operator == FilterOperator.EQUAL:
            return col_data == value
        elif operator == FilterOperator.NOT_EQUAL:
            return col_data != value
        elif operator == FilterOperator.BETWEEN:
            return (col_data >= value) & (col_data <= value2)
        elif operator == FilterOperator.IN:
            return col_data.isin(value)
        elif operator == FilterOperator.NOT_IN:
            return ~col_data.isin(value)
        elif operator == FilterOperator.IS_NULL:
            return col_data.isna() | (col_data == "")
        elif operator == FilterOperator.IS_NOT_NULL:
            return col_data.notna() & (col_data != "")
        else:
            logger.warning(f"Unsupported operator: {operator}")
            return pd.Series([False] * len(self.data), index=self.data.index)

    # ------------------------------------------------------------------
    # SORTING
    # ------------------------------------------------------------------

    def sort_results(
        self,
        data: Optional[pd.DataFrame] = None,
        sort_by: Union[str, List[str]] = None,
        ascending: Union[bool, List[bool]] = True,
    ) -> pd.DataFrame:
        """
        Sort results by one or more fields.

        Parameters
        ----------
        data : pd.DataFrame, optional
            DataFrame to sort, by default uses filtered_data
        sort_by : Union[str, List[str]]
            Field(s) to sort by
        ascending : Union[bool, List[bool]]
            Sort order(s), by default True

        Returns
        -------
        pd.DataFrame
            Sorted DataFrame
        """
        if data is None:
            data = self.filtered_data

        if data is None or data.empty:
            logger.warning("No data to sort")
            return data

        if not sort_by:
            logger.warning("No sort field specified")
            return data

        try:
            # Normalize to list
            if isinstance(sort_by, str):
                sort_by = [sort_by]
            if isinstance(ascending, bool):
                ascending = [ascending] * len(sort_by)

            # Validate sort fields exist
            valid_sort_fields = [f for f in sort_by if f in data.columns]
            if not valid_sort_fields:
                logger.warning(f"No valid sort fields found in {sort_by}")
                return data

            # Sort
            sorted_data = data.sort_values(
                by=valid_sort_fields,
                ascending=ascending[: len(valid_sort_fields)],
                na_position="last",
            )

            logger.info(f"Sorted results by {valid_sort_fields}")
            return sorted_data

        except Exception as e:
            logger.error(f"Failed to sort results: {str(e)}")
            return data

    # ------------------------------------------------------------------
    # RANKING
    # ------------------------------------------------------------------

    def rank_companies(
        self,
        data: Optional[pd.DataFrame] = None,
        rank_by: str = "overall_score",
        ascending: bool = False,
    ) -> pd.DataFrame:
        """
        Rank companies by a specific field.

        Parameters
        ----------
        data : pd.DataFrame, optional
            DataFrame to rank, by default uses filtered_data
        rank_by : str
            Field to rank by, by default "overall_score"
        ascending : bool
            Sort order, by default False (descending)

        Returns
        -------
        pd.DataFrame
            DataFrame with 'rank' column added
        """
        if data is None:
            data = self.filtered_data

        if data is None or data.empty:
            logger.warning("No data to rank")
            return data

        if rank_by not in data.columns:
            logger.warning(f"Rank field '{rank_by}' not found in data")
            return data

        try:
            # Sort by rank field
            ranked_data = data.sort_values(by=rank_by, ascending=ascending, na_position="last")

            # Add rank column (1-based)
            ranked_data = ranked_data.copy()
            ranked_data["rank"] = range(1, len(ranked_data) + 1)

            logger.info(
                f"Ranked {len(ranked_data)} companies by '{rank_by}' "
                f"({'ascending' if ascending else 'descending'})"
            )

            return ranked_data

        except Exception as e:
            logger.error(f"Failed to rank companies: {str(e)}")
            return data

    # ------------------------------------------------------------------
    # SCREENING PIPELINE
    # ------------------------------------------------------------------

    def screen_companies(
        self,
        filters: Optional[Union[List[Dict[str, Any]], FilterGroup]] = None,
        filter_logic: str = "AND",
        sort_by: Optional[Union[str, List[str]]] = None,
        sort_ascending: Union[bool, List[bool]] = True,
        rank_by: Optional[str] = None,
        rank_ascending: bool = False,
        preset_id: Optional[str] = None,
        custom_screen_name: Optional[str] = None,
        output_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run complete screening pipeline.

        This is the main entry point for screening companies.

        Parameters
        ----------
        filters : Optional[Union[List[Dict[str, Any]], FilterGroup]]
            Filter conditions to apply
        filter_logic : str, optional
            Logic for combining filters: "AND" or "OR", by default "AND"
        sort_by : Optional[Union[str, List[str]]]
            Field(s) to sort by
        sort_ascending : Union[bool, List[bool]]
            Sort order(s), by default True
        rank_by : Optional[str]
            Field to rank by, by default None (no ranking)
        rank_ascending : bool
            Rank order, by default False (descending)
        preset_id : Optional[str]
            Preset screener ID to use
        custom_screen_name : Optional[str]
            Name of custom screen template to load
        output_columns : Optional[List[str]]
            Columns to include in output

        Returns
        -------
        Dict[str, Any]
            Screening results with metadata
        """
        start_time = time.time()
        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        self.pipeline_stats["status"] = "running"

        logger.info("=" * 80)
        logger.info("INVESTMENT SCREENER - STARTING")
        logger.info("=" * 80)

        try:
            # Step 1: Load data
            if self.data is None:
                self.load_data()

            if self.data.empty:
                logger.warning("No data available for screening")
                self.pipeline_stats["status"] = "completed_no_data"
                return self._build_response([])

            # Step 2: Load preset or custom screen if specified
            if preset_id:
                from src.screener.presets import get_preset_screener
                preset = get_preset_screener(preset_id)
                filters = preset.get("filters", [])
                filter_logic = "AND"
                if not sort_by:
                    sort_by = preset.get("sort_by")
                if not rank_by:
                    rank_by = preset.get("rank_by")
                logger.info(f"Using preset screener: {preset_id}")

            if custom_screen_name:
                template = self.template_manager.load_screen(custom_screen_name)
                if not template:
                    raise ValueError(f"Custom screen '{custom_screen_name}' not found")
                filters = template.get("filters", [])
                filter_logic = "AND"
                if not sort_by:
                    sort_by = template.get("sort_by")
                if not rank_by:
                    rank_by = template.get("rank_by")
                logger.info(f"Using custom screen: {custom_screen_name}")

            # Step 3: Apply filters
            if filters:
                self.apply_filters(filters, logic=filter_logic)
            else:
                self.filtered_data = self.data.copy()
                logger.info("No filters applied, using all data")

            # Step 4: Sort results
            if sort_by:
                self.filtered_data = self.sort_results(
                    self.filtered_data, sort_by=sort_by, ascending=sort_ascending
                )

            # Step 5: Rank results
            if rank_by:
                self.filtered_data = self.rank_companies(
                    self.filtered_data, rank_by=rank_by, ascending=rank_ascending
                )

            # Step 6: Convert to list of dicts
            self.results = self.filtered_data.to_dict("records")

            # Step 7: Select output columns
            if output_columns:
                available_cols = set(self.results[0].keys()) if self.results else set()
                selected_cols = [col for col in output_columns if col in available_cols]
                self.results = [
                    {k: record.get(k, "") for k in selected_cols}
                    for record in self.results
                ]

            # Update stats
            execution_time = time.time() - start_time
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            self.pipeline_stats["execution_time"] = execution_time
            self.pipeline_stats["status"] = "completed"

            logger.info(
                f"Screening complete: {len(self.results)} results in {execution_time:.2f}s"
            )

            return self._build_response(self.results)

        except Exception as e:
            self.pipeline_stats["status"] = "failed"
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            error_msg = f"Screening failed: {str(e)}"
            logger.error(error_msg)
            self.pipeline_stats["errors"].append(error_msg)
            return self._build_response([])

    def _build_response(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build response dictionary with results and metadata.

        Parameters
        ----------
        results : List[Dict[str, Any]]
            Screening results

        Returns
        -------
        Dict[str, Any]
            Response with results and metadata
        """
        return {
            "results": results,
            "count": len(results),
            "stats": self.pipeline_stats,
            "success": self.pipeline_stats["status"] == "completed",
        }

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------

    def export_results(
        self,
        results: Optional[List[Dict[str, Any]]] = None,
        filename: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ) -> Optional[Path]:
        """
        Export screening results to CSV.

        Parameters
        ----------
        results : Optional[List[Dict[str, Any]]]
            Results to export, by default uses self.results
        filename : Optional[str]
            Custom filename
        columns : Optional[List[str]]
            Columns to export

        Returns
        -------
        Optional[Path]
            Path to exported CSV file
        """
        if results is None:
            results = self.results

        if not results:
            logger.warning("No results to export")
            return None

        return self.exporter.export_results(
            results=results,
            filename=filename,
            columns=columns,
        )

    # ------------------------------------------------------------------
    # CONVENIENCE METHODS
    # ------------------------------------------------------------------

    def screen_by_preset(
        self,
        preset_id: str,
        sort_by: Optional[str] = None,
        rank_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Screen companies using a preset screener.

        Parameters
        ----------
        preset_id : str
            Preset screener ID
        sort_by : Optional[str]
            Field to sort by
        rank_by : Optional[str]
            Field to rank by

        Returns
        -------
        Dict[str, Any]
            Screening results
        """
        return self.screen_companies(
            preset_id=preset_id,
            sort_by=sort_by,
            rank_by=rank_by,
        )

    def screen_by_custom(
        self,
        screen_name: str,
        sort_by: Optional[str] = None,
        rank_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Screen companies using a custom screen template.

        Parameters
        ----------
        screen_name : str
            Custom screen template name
        sort_by : Optional[str]
            Field to sort by
        rank_by : Optional[str]
            Field to rank by

        Returns
        -------
        Dict[str, Any]
            Screening results
        """
        return self.screen_companies(
            custom_screen_name=screen_name,
            sort_by=sort_by,
            rank_by=rank_by,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get screening statistics.

        Returns
        -------
        Dict[str, Any]
            Screening statistics
        """
        return self.pipeline_stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def screen_companies(
    filters: Optional[Union[List[Dict[str, Any]], FilterGroup]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to screen companies.

    Parameters
    ----------
    filters : Optional[Union[List[Dict[str, Any]], FilterGroup]]
        Filter conditions
    **kwargs
        Additional arguments passed to ScreenerEngine.screen_companies()

    Returns
    -------
    Dict[str, Any]
        Screening results
    """
    engine = ScreenerEngine()
    return engine.screen_companies(filters=filters, **kwargs)


def run_preset_screener(preset_id: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to run a preset screener.

    Parameters
    ----------
    preset_id : str
        Preset screener ID
    **kwargs
        Additional arguments passed to ScreenerEngine.screen_companies()

    Returns
    -------
    Dict[str, Any]
        Screening results
    """
    engine = ScreenerEngine()
    return engine.screen_by_preset(preset_id, **kwargs)


def run_custom_screener(screen_name: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to run a custom screener.

    Parameters
    ----------
    screen_name : str
        Custom screen template name
    **kwargs
        Additional arguments passed to ScreenerEngine.screen_companies()

    Returns
    -------
    Dict[str, Any]
        Screening results
    """
    engine = ScreenerEngine()
    return engine.screen_by_custom(screen_name, **kwargs)