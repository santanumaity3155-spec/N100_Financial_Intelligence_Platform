"""
calculator.py

Main KPI calculator orchestrator for the N100 Financial Intelligence Platform.

This module provides the central KPIEngine class that coordinates all KPI calculations
across different categories and manages the overall KPI computation workflow.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

from src.kpi_engine.profitability import ProfitabilityCalculator
from src.kpi_engine.liquidity import LiquidityCalculator
from src.kpi_engine.leverage import LeverageCalculator
from src.kpi_engine.efficiency import EfficiencyCalculator
from src.kpi_engine.cashflow import CashFlowCalculator
from src.kpi_engine.valuation import ValuationCalculator
from src.kpi_engine.growth import GrowthCalculator
from src.kpi_engine.validator import KPIValidator
from src.kpi_engine.formatter import KPIFormatter

logger = get_logger(__name__)


class KPIEngine:
    """
    Main orchestrator for KPI calculations.
    
    This class coordinates all KPI calculators and provides a unified interface
    for calculating financial KPIs from SQLite database data.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the KPIEngine.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        
        # Initialize all calculators
        self.profitability_calc = ProfitabilityCalculator(db_path)
        self.liquidity_calc = LiquidityCalculator(db_path)
        self.leverage_calc = LeverageCalculator(db_path)
        self.efficiency_calc = EfficiencyCalculator(db_path)
        self.cashflow_calc = CashFlowCalculator(db_path)
        self.valuation_calc = ValuationCalculator(db_path)
        self.growth_calc = GrowthCalculator(db_path)
        
        # Initialize validator and formatter
        self.validator = KPIValidator()
        self.formatter = KPIFormatter()
        
        logger.info("KPIEngine initialized with all calculators")

    def calculate_all_kpis(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated KPIs
        """
        logger.info(f"Calculating all KPIs for {company_id}, period {period}")
        
        # Calculate KPIs from all categories
        results = {
            "company_id": company_id,
            "period": period,
        }
        
        # Profitability KPIs
        profitability_kpis = self.profitability_calc.calculate_all(company_id, period)
        results.update(profitability_kpis)
        
        # Liquidity KPIs
        liquidity_kpis = self.liquidity_calc.calculate_all(company_id, period)
        results.update(liquidity_kpis)
        
        # Leverage KPIs
        leverage_kpis = self.leverage_calc.calculate_all(company_id, period)
        results.update(leverage_kpis)
        
        # Efficiency KPIs
        efficiency_kpis = self.efficiency_calc.calculate_all(company_id, period)
        results.update(efficiency_kpis)
        
        # Cash Flow KPIs
        cashflow_kpis = self.cashflow_calc.calculate_all(company_id, period)
        results.update(cashflow_kpis)
        
        # Valuation KPIs
        valuation_kpis = self.valuation_calc.calculate_all(company_id, period)
        results.update(valuation_kpis)
        
        # Note: Growth KPIs require multiple periods, so we skip them here
        # They can be calculated separately using calculate_growth_kpis()
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} total KPIs")
        return results

    def calculate_growth_kpis(self, company_id: str, periods: List[str]) -> Dict[str, Any]:
        """
        Calculate growth KPIs for a company across multiple periods.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        periods : List[str]
            List of financial periods (e.g., ['2022-Q1', '2023-Q1', '2024-Q1'])
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing growth KPIs
        """
        logger.info(f"Calculating growth KPIs for {company_id} across {len(periods)} periods")
        
        growth_kpis = self.growth_calc.calculate_all(company_id, periods)
        
        return growth_kpis

    def calculate_kpis_for_company(self, company_id: str, periods: List[str]) -> List[Dict[str, Any]]:
        """
        Calculate all KPIs for a company across multiple periods.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        periods : List[str]
            List of financial periods
            
        Returns
        -------
        List[Dict[str, Any]]
            List of KPI results for each period
        """
        logger.info(f"Calculating KPIs for {company_id} across {len(periods)} periods")
        
        results = []
        
        for period in periods:
            kpi_results = self.calculate_all_kpis(company_id, period)
            results.append(kpi_results)
        
        # Add growth KPIs if we have multiple periods
        if len(periods) >= 2:
            growth_kpis = self.calculate_growth_kpis(company_id, periods)
            # Add growth KPIs to the latest period
            if growth_kpis:
                results[-1].update(growth_kpis)
        
        logger.info(f"Calculated KPIs for {len(results)} periods")
        return results

    def calculate_kpis_for_all_companies(self, company_ids: List[str], period: str) -> List[Dict[str, Any]]:
        """
        Calculate all KPIs for multiple companies in a specific period.
        
        Parameters
        ----------
        company_ids : List[str]
            List of company identifiers
        period : str
            Financial period
            
        Returns
        -------
        List[Dict[str, Any]]
            List of KPI results for each company
        """
        logger.info(f"Calculating KPIs for {len(company_ids)} companies, period {period}")
        
        results = []
        
        for company_id in company_ids:
            try:
                kpi_results = self.calculate_all_kpis(company_id, period)
                results.append(kpi_results)
            except Exception as e:
                logger.error(f"Failed to calculate KPIs for {company_id}: {str(e)}")
                continue
        
        logger.info(f"Successfully calculated KPIs for {len(results)}/{len(company_ids)} companies")
        return results

    def validate_kpi_results(self, kpi_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of KPI results.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        Dict[str, Any]
            Validation results
        """
        logger.info(f"Validating {len(kpi_batch)} KPI results")
        
        validation_results = self.validator.validate_kpi_batch(kpi_batch)
        
        logger.info(f"Validation complete: {validation_results['valid_kpis']}/{validation_results['total_kpis']} KPIs valid")
        return validation_results

    def format_kpi_results(self, kpi_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format a batch of KPI results.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        List[Dict[str, Any]]
            Formatted KPI results
        """
        logger.info(f"Formatting {len(kpi_batch)} KPI results")
        
        formatted_results = [self.formatter.format_kpi_results(kpi) for kpi in kpi_batch]
        
        logger.info(f"Formatted {len(formatted_results)} KPI results")
        return formatted_results

    def save_kpi_results(self, kpi_batch: List[Dict[str, Any]], output_dir: str) -> Dict[str, bool]:
        """
        Save KPI results to files.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
        output_dir : str
            Directory to save output files
            
        Returns
        -------
        Dict[str, bool]
            Dictionary indicating success/failure for each file type
        """
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Save to JSON
        json_path = output_path / "kpi_results.json"
        results["json"] = self.formatter.save_kpi_results_to_json(kpi_batch, str(json_path))
        
        # Save to CSV
        csv_path = output_path / "kpi_results.csv"
        results["csv"] = self.formatter.save_kpi_results_to_csv(kpi_batch, str(csv_path))
        
        logger.info(f"Saved KPI results to {output_dir}")
        return results

    def get_kpi_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for all available KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        descriptions = {}
        
        # Collect descriptions from all calculators
        descriptions.update(self.profitability_calc.get_kpi_descriptions())
        descriptions.update(self.liquidity_calc.get_kpi_descriptions())
        descriptions.update(self.leverage_calc.get_kpi_descriptions())
        descriptions.update(self.efficiency_calc.get_kpi_descriptions())
        descriptions.update(self.cashflow_calc.get_kpi_descriptions())
        descriptions.update(self.valuation_calc.get_kpi_descriptions())
        descriptions.update(self.growth_calc.get_kpi_descriptions())
        
        return descriptions

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all available KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        formulas = {}
        
        # Collect formulas from all calculators
        formulas.update(self.profitability_calc.get_kpi_formulas())
        formulas.update(self.liquidity_calc.get_kpi_formulas())
        formulas.update(self.leverage_calc.get_kpi_formulas())
        formulas.update(self.efficiency_calc.get_kpi_formulas())
        formulas.update(self.cashflow_calc.get_kpi_formulas())
        formulas.update(self.valuation_calc.get_kpi_formulas())
        formulas.update(self.growth_calc.get_kpi_formulas())
        
        return formulas

    def get_available_companies(self) -> List[str]:
        """
        Get list of companies available in the database.
        
        Returns
        -------
        List[str]
            List of company IDs
        """
        try:
            conn = get_connection()
            query = "SELECT DISTINCT company_id FROM companies ORDER BY company_id"
            df = pd.read_sql_query(query, conn)
            companies = df['company_id'].tolist()
            logger.info(f"Found {len(companies)} companies in database")
            return companies
        except Exception as e:
            logger.error(f"Failed to fetch companies: {str(e)}")
            return []

    def get_available_periods(self, company_id: str) -> List[str]:
        """
        Get list of available periods for a company.
        
        Parameters
        ----------
        company_id : str
            Company identifier
            
        Returns
        -------
        List[str]
            List of available periods
        """
        try:
            conn = get_connection()
            query = """
                SELECT DISTINCT period FROM profit_loss 
                WHERE company_id = ? 
                ORDER BY period
            """
            df = pd.read_sql_query(query, conn, params=(company_id,))
            periods = df['period'].tolist()
            logger.info(f"Found {len(periods)} periods for {company_id}")
            return periods
        except Exception as e:
            logger.error(f"Failed to fetch periods for {company_id}: {str(e)}")
            return []

    def generate_kpi_report(self, kpi_batch: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive KPI report.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        str
            Formatted report string
        """
        return self.formatter.generate_kpi_summary_report(kpi_batch)

    def get_kpi_statistics(self, kpi_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics across a batch of KPI results.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        Dict[str, Any]
            Statistical summary
        """
        return self.formatter.get_kpi_statistics(kpi_batch)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def calculate_kpis(company_id: str, period: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to calculate all KPIs for a company and period.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    period : str
        Financial period
    db_path : str, optional
        Path to SQLite database
        
    Returns
    -------
    Dict[str, Any]
        KPI results
    """
    engine = KPIEngine(db_path)
    return engine.calculate_all_kpis(company_id, period)


def calculate_kpis_batch(company_ids: List[str], period: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to calculate KPIs for multiple companies.
    
    Parameters
    ----------
    company_ids : List[str]
        List of company identifiers
    period : str
        Financial period
    db_path : str, optional
        Path to SQLite database
        
    Returns
    -------
    List[Dict[str, Any]]
        List of KPI results
    """
    engine = KPIEngine(db_path)
    return engine.calculate_kpis_for_all_companies(company_ids, period)


# =============================================================================
# SCRIPT TEST
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize KPI Engine
    engine = KPIEngine()
    
    # Get available companies
    companies = engine.get_available_companies()
    print(f"Found {len(companies)} companies")
    
    if companies:
        # Test with first company
        test_company = companies[0]
        periods = engine.get_available_periods(test_company)
        
        if periods:
            print(f"\nTesting KPI calculation for {test_company}, period {periods[0]}")
            kpi_results = engine.calculate_all_kpis(test_company, periods[0])
            
            # Print results
            engine.formatter.print_kpi_results(kpi_results)
            
            # Validate results
            validation = engine.validate_kpi_results([kpi_results])
            print(f"\nValidation: {validation['valid_kpis']}/{validation['total_kpis']} KPIs valid")
        else:
            print(f"No periods found for {test_company}")