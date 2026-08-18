"""
valuation.py

Valuation router for N100 Financial Intelligence Platform API.
Implements Module 6E — GET /api/v1/market-cap/{ticker}.
"""

import sqlite3
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Valuation"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================

class ValuationYearRecord(BaseModel):
    period: str = Field(..., description="Financial period/year (e.g. 2019, 2024)")
    pe_ratio: Optional[float] = Field(None, description="Price to Earnings ratio (P/E)")
    pb_ratio: Optional[float] = Field(None, description="Price to Book ratio (P/B)")
    ev_ebitda: Optional[float] = Field(None, description="EV to EBITDA multiple")
    dividend_yield: Optional[float] = Field(None, description="Dividend Yield %")
    market_cap: Optional[float] = Field(None, description="Market Capitalization in Crores")
    enterprise_value: Optional[float] = Field(None, description="Enterprise Value in Crores")


class CompanyValuationResponse(BaseModel):
    ticker: str = Field(..., description="Company ticker symbol")
    company_name: str = Field(..., description="Official company name")
    historical_valuation: List[ValuationYearRecord] = Field(..., description="Chronological annual valuation records (2019 to 2024)")


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/market-cap/{ticker}",
    response_model=CompanyValuationResponse,
    summary="Get Historical Valuation Multiples",
    description="Retrieve historical valuation multiples (P/E, P/B, EV/EBITDA, Dividend Yield) from 2019 to 2024 for a company.",
    responses={
        200: {"description": "Historical valuation data returned successfully"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"}
    }
)
def get_company_market_cap_valuation(ticker: str) -> CompanyValuationResponse:
    """
    Returns historical valuation multiples (2019–2024) for the requested ticker.
    """
    try:
        if not ticker or not ticker.strip():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticker symbol cannot be empty"
            )

        ticker_clean = ticker.strip().upper()
        conn = get_connection()

        # Check company existence
        cur = conn.execute("SELECT company_id, company_name FROM companies WHERE company_id = ?", (ticker_clean,))
        comp_row = cur.fetchone()
        if not comp_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company ticker '{ticker}' not found."
            )
        comp_name = comp_row["company_name"]

        # Query market_cap table for historical records
        mc_df = pd.read_sql_query(
            """
            SELECT period, market_cap, enterprise_value, pe_ratio, pb_ratio, ev_ebitda, dividend_yield
            FROM market_cap
            WHERE company_id = ?
            ORDER BY period ASC
            """,
            conn,
            params=[ticker_clean]
        )

        records: List[ValuationYearRecord] = []
        if not mc_df.empty:
            for _, row in mc_df.iterrows():
                pe_v = float(row["pe_ratio"]) if pd.notna(row["pe_ratio"]) else None
                pb_v = float(row["pb_ratio"]) if pd.notna(row["pb_ratio"]) else None
                ev_v = float(row["ev_ebitda"]) if pd.notna(row["ev_ebitda"]) else None
                div_v = float(row["dividend_yield"]) if pd.notna(row["dividend_yield"]) else None
                mcap_v = float(row["market_cap"]) if pd.notna(row["market_cap"]) else None
                ev_cap_v = float(row["enterprise_value"]) if pd.notna(row["enterprise_value"]) else None

                records.append(ValuationYearRecord(
                    period=str(row["period"]),
                    pe_ratio=pe_v,
                    pb_ratio=pb_v,
                    ev_ebitda=ev_v,
                    dividend_yield=div_v,
                    market_cap=mcap_v,
                    enterprise_value=ev_cap_v
                ))

        # Fallback if no market_cap records exist: check financial_ratios or financial_kpis for annual periods
        if not records:
            kpi_df = pd.read_sql_query(
                """
                SELECT period, pe_ratio, pb_ratio, ev_ebitda, dividend_yield
                FROM financial_kpis
                WHERE company_id = ? AND (period LIKE '%2019%' OR period LIKE '%2020%' OR period LIKE '%2021%' OR period LIKE '%2022%' OR period LIKE '%2023%' OR period LIKE '%2024%')
                ORDER BY period ASC
                """,
                conn,
                params=[ticker_clean]
            )
            for _, row in kpi_df.iterrows():
                pe_v = float(row["pe_ratio"]) if pd.notna(row["pe_ratio"]) else None
                pb_v = float(row["pb_ratio"]) if pd.notna(row["pb_ratio"]) else None
                ev_v = float(row["ev_ebitda"]) if pd.notna(row["ev_ebitda"]) else None
                div_v = float(row["dividend_yield"]) if pd.notna(row["dividend_yield"]) else None

                records.append(ValuationYearRecord(
                    period=str(row["period"]),
                    pe_ratio=pe_v,
                    pb_ratio=pb_v,
                    ev_ebitda=ev_v,
                    dividend_yield=div_v,
                    market_cap=None,
                    enterprise_value=None
                ))

        return CompanyValuationResponse(
            ticker=ticker_clean,
            company_name=comp_name,
            historical_valuation=records
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /market-cap/{ticker}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve market-cap valuation data"
        ) from exc
