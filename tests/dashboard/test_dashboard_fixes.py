import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import importlib

# Dynamic import for numeric-prefixed page modules
trends_mod = importlib.import_module("src.dashboard.pages.05_trends")
sectors_mod = importlib.import_module("src.dashboard.pages.06_sectors")
capital_mod = importlib.import_module("src.dashboard.pages.07_capital")

prepare_trend_data = trends_mod.prepare_trend_data
calculate_yoy = trends_mod.calculate_yoy

get_available_sectors = sectors_mod.get_available_sectors
calculate_sector_medians = sectors_mod.calculate_sector_medians

build_treemap = capital_mod.build_treemap
build_pattern_statistics_chart = capital_mod.build_pattern_statistics_chart
calculate_pattern_statistics = capital_mod.calculate_pattern_statistics
calculate_all_pattern_statistics = capital_mod.calculate_all_pattern_statistics


def test_prepare_trend_data_valid():
    financial_data = {
        "profit_loss": pd.DataFrame({
            "year": ["2020", "2021", "2022"],
            "eps": [10.5, 12.0, 15.2]
        })
    }
    df = prepare_trend_data(financial_data, "EPS", "profit_loss", "eps")
    assert not df.empty
    assert len(df) == 3
    assert list(df["year"]) == [2020, 2021, 2022]
    assert list(df["value"]) == [10.5, 12.0, 15.2]


def test_prepare_trend_data_nan_and_non_finite_year():
    financial_data = {
        "ratios": pd.DataFrame({
            "year": ["2020", None, "invalid", "2023"],
            "revenue_cagr_5yr": [12.0, 15.0, 18.0, 20.0]
        })
    }
    df = prepare_trend_data(financial_data, "Revenue CAGR", "financial_ratios", "revenue_cagr_5yr")
    assert not df.empty
    assert len(df) == 2
    assert list(df["year"]) == [2020, 2023]
    assert list(df["value"]) == [12.0, 20.0]


def test_prepare_trend_data_missing_column():
    financial_data = {
        "ratios": pd.DataFrame({
            "year": [2020, 2021],
            "roe": [15.0, 16.0]
        })
    }
    df = prepare_trend_data(financial_data, "PAT CAGR", "financial_ratios", "pat_cagr_5yr")
    assert df.empty


def test_prepare_trend_data_empty_df():
    financial_data = {
        "ratios": pd.DataFrame()
    }
    df = prepare_trend_data(financial_data, "Revenue CAGR", "financial_ratios", "revenue_cagr_5yr")
    assert df.empty


def test_calculate_yoy():
    trend_df = pd.DataFrame({
        "year": [2020, 2021, 2022],
        "value": [100.0, 120.0, 150.0]
    })
    result = calculate_yoy(trend_df)
    assert "yoy_pct" in result.columns
    assert pd.isna(result["yoy_pct"].iloc[0])
    assert pytest.approx(result["yoy_pct"].iloc[1], 0.01) == 20.0
    assert pytest.approx(result["yoy_pct"].iloc[2], 0.01) == 25.0


def test_get_available_sectors_normal_and_whitespace():
    df = pd.DataFrame({
        "sector": [" IT Services ", "Banking", None, "IT Services", "  Healthcare  ", "nan"]
    })
    sectors = get_available_sectors(df)
    assert sectors == ["Banking", "Healthcare", "IT Services"]


def test_get_available_sectors_empty():
    df = pd.DataFrame()
    assert get_available_sectors(df) == []

    df_null = pd.DataFrame({"sector": [None, np.nan, "nan", "None"]})
    assert get_available_sectors(df_null) == []


def test_capital_allocation_charts_no_name_error():
    df = pd.DataFrame({
        "company_id": ["ABB", "TCS"],
        "company_name": ["Abbott India", "Tata Consultancy"],
        "sector": ["Capital Goods", "IT Services"],
        "capital_allocation_pattern": ["Reinvestor", "Shareholder Returns"],
        "market_cap": [10000.0, 50000.0],
        "roe": [20.0, 35.0],
        "revenue_cagr_5yr": [12.0, 15.0],
        "free_cash_flow": [500.0, 2000.0]
    })

    treemap_fig = build_treemap(df)
    assert isinstance(treemap_fig, go.Figure)

    stats_df = calculate_all_pattern_statistics(df)
    assert not stats_df.empty

    stats_fig = build_pattern_statistics_chart(stats_df)
    assert isinstance(stats_fig, go.Figure)
