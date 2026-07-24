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

from src.analytics.peer import (
    # Core functions
    load_peer_groups,
    assign_peer_groups,
    calculate_percentile_rank,
    calculate_metric_percentiles,
    calculate_all_percentiles,
    save_peer_percentiles,
    export_percentiles,
    get_peer_summary,
    validate_peer_data,
    # Classes
    PeerPercentileEngine,
    PeerAnalysisError,
    PeerGroupNotFoundError,
    MetricNotFoundError,
    ValidationError as PeerValidationError,
    # Main entry point
    run_peer_percentile_engine,
    # Utility functions
    get_peer_percentile_statistics,
    validate_database_integrity as validate_peer_database_integrity,
    # Constants
    SUPPORTED_METRICS,
    SUPPORTED_PEER_GROUPS,
    INVERTED_METRICS,
)

from src.analytics.radar import (
    # Core functions
    load_percentile_data,
    load_company_data,
    calculate_peer_benchmark,
    prepare_radar_data,
    validate_chart_inputs,
    generate_radar_chart,
    save_chart,
    generate_all_charts,
    # Utility functions
    get_radar_chart_statistics,
    validate_radar_chart_output,
    # Classes
    RadarChartEngine,
    RadarChartError,
    CompanyNotFoundError,
    PeerGroupNotFoundError as RadarPeerGroupNotFoundError,
    MetricValidationError,
    ChartGenerationError,
    # Main entry point
    run_radar_chart_engine,
    # Constants
    RADAR_CHARTS_DIR,
    METRIC_DISPLAY_NAMES,
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
    # Peer Percentile Engine functions (Module 7)
    "load_peer_groups",
    "assign_peer_groups",
    "calculate_percentile_rank",
    "calculate_metric_percentiles",
    "calculate_all_percentiles",
    "save_peer_percentiles",
    "export_percentiles",
    "get_peer_summary",
    "validate_peer_data",
    "PeerPercentileEngine",
    "PeerAnalysisError",
    "PeerGroupNotFoundError",
    "MetricNotFoundError",
    "PeerValidationError",
    "run_peer_percentile_engine",
    "get_peer_percentile_statistics",
    "validate_peer_database_integrity",
    "SUPPORTED_METRICS",
    "SUPPORTED_PEER_GROUPS",
    "INVERTED_METRICS",
    # Radar Chart Engine functions (Module 8)
    "load_percentile_data",
    "load_company_data",
    "calculate_peer_benchmark",
    "prepare_radar_data",
    "validate_chart_inputs",
    "generate_radar_chart",
    "save_chart",
    "generate_all_charts",
    "get_radar_chart_statistics",
    "validate_radar_chart_output",
    "RadarChartEngine",
    "RadarChartError",
    "CompanyNotFoundError",
    "RadarPeerGroupNotFoundError",
    "MetricValidationError",
    "ChartGenerationError",
    "run_radar_chart_engine",
    "RADAR_CHARTS_DIR",
    "METRIC_DISPLAY_NAMES",
]
