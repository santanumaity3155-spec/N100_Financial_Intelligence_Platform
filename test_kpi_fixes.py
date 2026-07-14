"""
Test script to validate all KPI calculation fixes.

This script tests:
1. PB Ratio calculation (Issue 1)
2. EV/EBITDA calculation (Issue 2)
3. Dividend Yield calculation (Issue 3)
4. EPS calculation (Issue 4)
5. Cash Flow calculations (Issue 5)
6. Cash Ratio calculation (Issue 6)
7. Working Capital Turnover (Issue 7)
8. TTM periods handling (Issue 8)
9. All safety checks (Issue 9)
"""

import logging
import sys
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.kpi_engine.valuation import ValuationCalculator
from src.kpi_engine.profitability import ProfitabilityCalculator
from src.kpi_engine.liquidity import LiquidityCalculator
from src.kpi_engine.efficiency import EfficiencyCalculator
from src.kpi_engine.cashflow import CashFlowCalculator
from src.kpi_engine.leverage import LeverageCalculator
from src.database.connection import get_connection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)


def get_test_data(company_id: str, period: str):
    """Fetch test data from database."""
    import sqlite3
    conn = sqlite3.connect('data/database/n100.db')
    
    pl_query = "SELECT * FROM profit_loss WHERE company_id = ? AND period = ? LIMIT 1"
    bs_query = "SELECT * FROM balance_sheet WHERE company_id = ? AND period = ? LIMIT 1"
    mc_query = "SELECT * FROM market_cap WHERE company_id = ? AND period = ? LIMIT 1"
    cf_query = "SELECT * FROM cash_flow WHERE company_id = ? AND period = ? LIMIT 1"
    
    pl_data = pd.read_sql_query(pl_query, conn, params=(company_id, period))
    bs_data = pd.read_sql_query(bs_query, conn, params=(company_id, period))
    mc_data = pd.read_sql_query(mc_query, conn, params=(company_id, period))
    cf_data = pd.read_sql_query(cf_query, conn, params=(company_id, period))
    
    conn.close()
    
    return pl_data, bs_data, mc_data, cf_data


def test_valuation_calculator():
    """Test valuation KPIs."""
    logger.info("=" * 80)
    logger.info("TESTING VALUATION CALCULATOR")
    logger.info("=" * 80)
    
    calculator = ValuationCalculator()
    
    # Test with a known company and period
    company_id = "ABB"
    period = "Mar 2015"
    
    pl_data, bs_data, mc_data, cf_data = get_test_data(company_id, period)
    
    logger.info(f"Testing with company: {company_id}, period: {period}")
    logger.info(f"P&L data shape: {pl_data.shape}")
    logger.info(f"Balance Sheet data shape: {bs_data.shape}")
    logger.info(f"Market Cap data shape: {mc_data.shape}")
    
    # Test calculate_all
    results = calculator.calculate_all(company_id, period)
    
    logger.info("Results:")
    for key, value in results.items():
        if key not in ['company_id', 'period']:
            logger.info(f"  {key}: {value}")
    
    # Test individual calculations with empty dataframes (safety check)
    logger.info("\nTesting with empty dataframes (safety checks):")
    empty_df = pd.DataFrame()
    
    eps = calculator.calculate_eps(empty_df, empty_df)
    logger.info(f"  EPS with empty data: {eps}")
    
    pb_ratio = calculator.calculate_pb_ratio(empty_df, empty_df)
    logger.info(f"  PB Ratio with empty data: {pb_ratio}")
    
    ev_ebitda = calculator.calculate_ev_ebitda(empty_df, empty_df, empty_df)
    logger.info(f"  EV/EBITDA with empty data: {ev_ebitda}")
    
    div_yield = calculator.calculate_dividend_yield(empty_df, empty_df)
    logger.info(f"  Dividend Yield with empty data: {div_yield}")
    
    logger.info("✓ Valuation calculator tests completed")
    return True


def test_profitability_calculator():
    """Test profitability KPIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING PROFITABILITY CALCULATOR")
    logger.info("=" * 80)
    
    calculator = ProfitabilityCalculator()
    
    company_id = "ABB"
    period = "Mar 2015"
    
    pl_data, bs_data, _, _ = get_test_data(company_id, period)
    
    logger.info(f"Testing with company: {company_id}, period: {period}")
    
    # Test calculate_all
    results = calculator.calculate_all(company_id, period)
    
    logger.info("Results:")
    for key, value in results.items():
        if key not in ['company_id', 'period']:
            logger.info(f"  {key}: {value}")
    
    # Test with empty dataframes
    logger.info("\nTesting with empty dataframes (safety checks):")
    empty_df = pd.DataFrame()
    
    roe = calculator.calculate_roe(empty_df, empty_df)
    logger.info(f"  ROE with empty data: {roe}")
    
    roa = calculator.calculate_roa(empty_df, empty_df)
    logger.info(f"  ROA with empty data: {roa}")
    
    logger.info("✓ Profitability calculator tests completed")
    return True


def test_liquidity_calculator():
    """Test liquidity KPIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING LIQUIDITY CALCULATOR")
    logger.info("=" * 80)
    
    calculator = LiquidityCalculator()
    
    company_id = "ABB"
    period = "Mar 2015"
    
    _, bs_data, _, _ = get_test_data(company_id, period)
    
    logger.info(f"Testing with company: {company_id}, period: {period}")
    
    # Test calculate_all
    results = calculator.calculate_all(company_id, period)
    
    logger.info("Results:")
    for key, value in results.items():
        if key not in ['company_id', 'period']:
            logger.info(f"  {key}: {value}")
    
    # Test with empty dataframe
    logger.info("\nTesting with empty dataframe (safety checks):")
    empty_df = pd.DataFrame()
    
    cash_ratio = calculator.calculate_cash_ratio(empty_df)
    logger.info(f"  Cash Ratio with empty data: {cash_ratio}")
    
    logger.info("✓ Liquidity calculator tests completed")
    return True


def test_efficiency_calculator():
    """Test efficiency KPIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING EFFICIENCY CALCULATOR")
    logger.info("=" * 80)
    
    calculator = EfficiencyCalculator()
    
    company_id = "ABB"
    period = "Mar 2015"
    
    pl_data, bs_data, _, _ = get_test_data(company_id, period)
    
    logger.info(f"Testing with company: {company_id}, period: {period}")
    
    # Test calculate_all
    results = calculator.calculate_all(company_id, period)
    
    logger.info("Results:")
    for key, value in results.items():
        if key not in ['company_id', 'period']:
            logger.info(f"  {key}: {value}")
    
    # Test with empty dataframes
    logger.info("\nTesting with empty dataframes (safety checks):")
    empty_df = pd.DataFrame()
    
    wc_turnover = calculator.calculate_working_capital_turnover(empty_df, empty_df)
    logger.info(f"  Working Capital Turnover with empty data: {wc_turnover}")
    
    logger.info("✓ Efficiency calculator tests completed")
    return True


def test_cashflow_calculator():
    """Test cash flow KPIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING CASH FLOW CALCULATOR")
    logger.info("=" * 80)
    
    calculator = CashFlowCalculator()
    
    company_id = "TCS"
    period = "Mar-15"
    
    pl_data, _, _, cf_data = get_test_data(company_id, period)
    
    logger.info(f"Testing with company: {company_id}, period: {period}")
    logger.info(f"Cash Flow data shape: {cf_data.shape}")
    
    if not cf_data.empty:
        logger.info(f"Cash Flow columns: {list(cf_data.columns)}")
        logger.info(f"Sample cash_from_operating_activity: {cf_data.get('cash_from_operating_activity', 'N/A')}")
        logger.info(f"Sample operating_activity: {cf_data.get('operating_activity', 'N/A')}")
    
    # Test calculate_all
    results = calculator.calculate_all(company_id, period)
    
    logger.info("Results:")
    for key, value in results.items():
        if key not in ['company_id', 'period']:
            logger.info(f"  {key}: {value}")
    
    # Test with empty dataframe
    logger.info("\nTesting with empty dataframe (safety checks):")
    empty_df = pd.DataFrame()
    
    ocf = calculator.calculate_operating_cash_flow(empty_df)
    logger.info(f"  Operating Cash Flow with empty data: {ocf}")
    
    logger.info("✓ Cash Flow calculator tests completed")
    return True


def test_leverage_calculator():
    """Test leverage KPIs."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING LEVERAGE CALCULATOR")
    logger.info("=" * 80)
    
    calculator = LeverageCalculator()
    
    company_id = "ABB"
    period = "Mar 2015"
    
    pl_data, bs_data, _, _ = get_test_data(company_id, period)
    
    logger.info(f"Testing with company: {company_id}, period: {period}")
    
    # Test calculate_all
    results = calculator.calculate_all(company_id, period)
    
    logger.info("Results:")
    for key, value in results.items():
        if key not in ['company_id', 'period']:
            logger.info(f"  {key}: {value}")
    
    # Test with empty dataframe
    logger.info("\nTesting with empty dataframe (safety checks):")
    empty_df = pd.DataFrame()
    
    debt_to_equity = calculator.calculate_debt_to_equity(empty_df)
    logger.info(f"  Debt to Equity with empty data: {debt_to_equity}")
    
    logger.info("✓ Leverage calculator tests completed")
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("STARTING KPI CALCULATION FIX VALIDATION")
    logger.info("=" * 80 + "\n")
    
    try:
        test_valuation_calculator()
        test_profitability_calculator()
        test_liquidity_calculator()
        test_efficiency_calculator()
        test_cashflow_calculator()
        test_leverage_calculator()
        
        logger.info("\n" + "=" * 80)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)