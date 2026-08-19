"""
Tests for Company Intelligence Dashboard - Module 5B
N100 Financial Intelligence Platform
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import importlib
from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_raw_statement,
    get_company_financial_health,
    get_company_pros_cons_signals,
    get_company_capital_allocation_detail,
    get_company_valuation_detail,
    get_company_peer_percentiles,
)
from src.analytics.cashflow_intelligence import (
    compute_cfo_quality,
    compute_capex_intensity,
    compute_fcf_cagr_5yr,
    compute_fcf_conversion,
    compute_distress_flag,
    compute_deleveraging_flag,
    compute_capital_allocation_label,
)


def test_01_company_list_loading():
    """Test 1: Verify company list loading from authoritative companies table."""
    profile_module = importlib.import_module("src.dashboard.pages.02_profile")
    comps = profile_module.load_company_master_list()
    assert isinstance(comps, pd.DataFrame)
    assert not comps.empty, "Company master list should not be empty"
    assert "ticker" in comps.columns
    assert "name" in comps.columns
    assert "sector" in comps.columns


def test_02_company_selection():
    """Test 2: Verify full intelligence loading for a valid selected company (e.g. INFY)."""
    profile_module = importlib.import_module("src.dashboard.pages.02_profile")
    intel = profile_module.load_company_full_intelligence("INFY")
    assert isinstance(intel, dict)
    assert intel["ticker"] == "INFY"
    assert intel["profile"] is not None
    assert intel["profile"]["ticker"] == "INFY"


def test_03_invalid_company_handling():
    """Test 3: Verify graceful handling of invalid company ticker."""
    profile_module = importlib.import_module("src.dashboard.pages.02_profile")
    intel = profile_module.load_company_full_intelligence("INVALID_TICKER_999")
    assert isinstance(intel, dict)
    assert intel["ticker"] == "INVALID_TICKER_999"
    assert intel["profile"] is None
    assert intel["ratios_df"].empty


def test_04_kpi_retrieval():
    """Test 4: Verify financial KPI retrieval for a company."""
    ratios_df = get_ratios("INFY")
    pl_df = get_pl("INFY")
    assert (
        not ratios_df.empty or not pl_df.empty
    ), "KPI statements should return data for INFY"
    if not ratios_df.empty:
        assert "roe" in ratios_df.columns
        assert "debt_equity" in ratios_df.columns
    if not pl_df.empty:
        assert "sales" in pl_df.columns
        assert "net_profit" in pl_df.columns


def test_05_health_score_retrieval():
    """Test 5: Verify financial health score retrieval."""
    health = get_company_financial_health("INFY")
    assert health is not None, "Health score should exist for INFY"
    assert "overall_score" in health
    assert "rating" in health
    assert health["overall_score"] > 0


def test_06_cash_flow_data_retrieval():
    """Test 6: Verify Module 3 cash flow intelligence function integration."""
    raw_cf = get_raw_statement("INFY", "cash_flow")
    raw_pl = get_raw_statement("INFY", "profit_loss")
    raw_bs = get_raw_statement("INFY", "balance_sheet")

    assert not raw_cf.empty
    assert not raw_pl.empty

    cfo_q = compute_cfo_quality(raw_cf, raw_pl)
    capex_i = compute_capex_intensity(raw_cf, raw_pl)
    distress = compute_distress_flag(raw_cf)
    deleveraging = compute_deleveraging_flag(raw_cf, raw_bs)

    assert "score" in cfo_q
    assert "value" in capex_i
    assert "flag" in distress
    assert "flag" in deleveraging


def test_07_pros_retrieval():
    """Test 7: Verify pros retrieval from Module 2D output."""
    signals = get_company_pros_cons_signals("INFY")
    assert "pros" in signals
    assert isinstance(signals["pros"], list)
    if signals["pros"]:
        first_pro = signals["pros"][0]
        assert "text" in first_pro
        assert "rule_id" in first_pro


def test_08_cons_retrieval():
    """Test 8: Verify cons retrieval from Module 2D output."""
    signals = get_company_pros_cons_signals("INFY")
    assert "cons" in signals
    assert isinstance(signals["cons"], list)


def test_09_capital_allocation_retrieval():
    """Test 9: Verify capital allocation detail retrieval from Module 4 output."""
    detail = get_company_capital_allocation_detail("INFY")
    assert isinstance(detail, dict)
    assert "rating" in detail
    assert "pattern" in detail


def test_10_valuation_retrieval():
    """Test 10: Verify valuation metric and flag retrieval."""
    val = get_company_valuation_detail("INFY")
    assert isinstance(val, dict)
    assert "pe" in val
    assert "valuation_flag" in val


def test_11_peer_data_retrieval():
    """Test 11: Verify peer percentile and peer group data retrieval."""
    pp_df = get_company_peer_percentiles("INFY")
    assert isinstance(pp_df, pd.DataFrame)
    if not pp_df.empty:
        assert "metric" in pp_df.columns
        assert "percentile_rank" in pp_df.columns


def test_12_historical_trend_retrieval():
    """Test 12: Verify multi-year historical trend retrieval for P&L, BS, CF."""
    pl_df = get_pl("TCS")
    bs_df = get_bs("TCS")
    cf_df = get_cf("TCS")
    assert len(pl_df) > 1, "P&L should return multi-year history"
    assert len(bs_df) > 1, "Balance sheet should return multi-year history"
    assert len(cf_df) > 1, "Cash flow should return multi-year history"


def test_13_missing_data_handling():
    """Test 13: Verify graceful handling when financial metrics or data are missing (no exceptions)."""
    profile_module = importlib.import_module("src.dashboard.pages.02_profile")
    # Empty inputs to section renderers must not crash or raise exceptions
    profile_module.render_section_1_header(None, "UNKNOWN")
    profile_module.render_section_2_health(None)
    profile_module.render_section_3_kpis(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    profile_module.render_section_4_profitability(
        pd.DataFrame(), pd.DataFrame(), "UNKNOWN"
    )
    profile_module.render_section_5_cashflow_intelligence({})
    profile_module.render_section_6_pros_cons({"pros": [], "cons": []})
    profile_module.render_section_7_capital_allocation({})
    profile_module.render_section_8_valuation({})
    profile_module.render_section_9_peer_position(pd.DataFrame(), "UNKNOWN")
    profile_module.render_section_10_historical_trend(
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    )


def test_14_database_failure_handling():
    """Test 14: Verify defensive handling when database returns empty records or errors."""
    health = get_company_financial_health("")
    assert health is None
    signals = get_company_pros_cons_signals("")
    assert signals == {"pros": [], "cons": []}
    val = get_company_valuation_detail("")
    assert isinstance(val, dict)


def test_15_duplicate_company_handling():
    """Test 15: Verify duplicate company records are deduplicated in company selector list."""
    profile_module = importlib.import_module("src.dashboard.pages.02_profile")
    comps = profile_module.load_company_master_list()
    if not comps.empty:
        duplicates = comps.duplicated(subset=["ticker"]).sum()
        assert duplicates == 0, "Company master list should deduplicate ticker symbols"
