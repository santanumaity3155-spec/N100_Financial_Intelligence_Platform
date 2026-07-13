"""
kpi_engine

Financial KPI calculation engine for the N100 Financial Intelligence Platform.

This module provides a modular, production-ready system for calculating
financial KPIs from SQLite database data.

Modules:
    calculator.py - Main KPI calculator orchestrator
    profitability.py - Profitability KPIs (ROE, ROCE, ROA, margins)
    liquidity.py - Liquidity KPIs (current ratio, quick ratio, cash ratio)
    leverage.py - Leverage KPIs (debt to equity, debt ratio, interest coverage)
    efficiency.py - Efficiency KPIs (asset turnover, inventory turnover)
    cashflow.py - Cash Flow KPIs (operating cash flow, free cash flow)
    valuation.py - Valuation KPIs (EPS, PE ratio, PB ratio, EV/EBITDA)
    growth.py - Growth KPIs (CAGR calculations, margin expansion)
    validator.py - KPI validation and data quality checks
    formatter.py - KPI result formatting and output utilities
"""

from src.kpi_engine.calculator import KPIEngine
from src.kpi_engine.profitability import ProfitabilityCalculator
from src.kpi_engine.liquidity import LiquidityCalculator
from src.kpi_engine.leverage import LeverageCalculator
from src.kpi_engine.efficiency import EfficiencyCalculator
from src.kpi_engine.cashflow import CashFlowCalculator
from src.kpi_engine.valuation import ValuationCalculator
from src.kpi_engine.growth import GrowthCalculator
from src.kpi_engine.validator import KPIValidator
from src.kpi_engine.formatter import KPIFormatter

__all__ = [
    "KPIEngine",
    "ProfitabilityCalculator",
    "LiquidityCalculator",
    "LeverageCalculator",
    "EfficiencyCalculator",
    "CashFlowCalculator",
    "ValuationCalculator",
    "GrowthCalculator",
    "KPIValidator",
    "KPIFormatter",
]

__version__ = "1.0.0"