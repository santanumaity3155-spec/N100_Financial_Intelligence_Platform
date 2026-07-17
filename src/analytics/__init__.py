"""
analytics module

Financial Ratio Engine for the N100 Financial Intelligence Platform.

This module provides functions to calculate profitability, leverage, and efficiency
ratios for all company-year records.
"""

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
)

from src.analytics.cagr import (
    calculate_cagr,
    calculate_revenue_cagr,
    calculate_pat_cagr,
    calculate_eps_cagr,
    calculate_all_cagr,
)

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_fcf_margin,
    calculate_cash_conversion,
    calculate_capex_intensity,
    calculate_cash_reinvestment_ratio,
    calculate_cash_return_on_assets,
    calculate_operating_cashflow_growth,
    classify_capital_allocation,
    calculate_all_cashflow_kpis,
    generate_capital_allocation_csv,
)

from src.analytics.ratio_engine import (
    ValidationError,
    validate_company_period,
    validate_financial_data_availability,
    insert_financial_ratios,
    check_duplicate_period,
    merge_kpi_data,
    process_company,
    RatioEnginePipeline,
    run_ratio_engine_pipeline,
    get_pipeline_statistics,
    validate_database_integrity,
)

__all__ = [
    # Ratio functions
    "calculate_net_profit_margin",
    "calculate_operating_profit_margin",
    "calculate_roe",
    "calculate_roce",
    "calculate_roa",
    "calculate_debt_to_equity",
    "calculate_interest_coverage",
    "calculate_net_debt",
    "calculate_asset_turnover",
    # CAGR functions
    "calculate_cagr",
    "calculate_revenue_cagr",
    "calculate_pat_cagr",
    "calculate_eps_cagr",
    "calculate_all_cagr",
    # Cash Flow KPI functions
    "calculate_free_cash_flow",
    "calculate_fcf_margin",
    "calculate_cash_conversion",
    "calculate_capex_intensity",
    "calculate_cash_reinvestment_ratio",
    "calculate_cash_return_on_assets",
    "calculate_operating_cashflow_growth",
    "classify_capital_allocation",
    "calculate_all_cashflow_kpis",
    "generate_capital_allocation_csv",
    # Ratio Engine Pipeline functions
    "ValidationError",
    "validate_company_period",
    "validate_financial_data_availability",
    "insert_financial_ratios",
    "check_duplicate_period",
    "merge_kpi_data",
    "process_company",
    "RatioEnginePipeline",
    "run_ratio_engine_pipeline",
    "get_pipeline_statistics",
    "validate_database_integrity",
]
