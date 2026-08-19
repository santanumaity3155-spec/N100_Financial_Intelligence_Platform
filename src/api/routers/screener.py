"""
screener.py

Screener router for N100 Financial Intelligence Platform API.
Implements Module 6E — GET /api/v1/screener.
"""

import math
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Screener"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================

class ScreenerCompanyItem(BaseModel):
    company_id: str = Field(..., description="Unique company ticker symbol")
    company_name: str = Field(..., description="Official company name")
    sector: Optional[str] = Field(None, description="Industry sector classification")
    rank: int = Field(..., description="Screener ranking position")
    ranking: Optional[int] = Field(None, description="Alias for screener ranking position")
    roe: Optional[float] = Field(None, description="Return on Equity %")
    debt_to_equity: Optional[float] = Field(None, description="Debt to Equity ratio")
    de: Optional[float] = Field(None, description="Alias for Debt to Equity ratio")
    free_cash_flow: Optional[float] = Field(None, description="Free Cash Flow in Crores/Millions")
    fcf: Optional[float] = Field(None, description="Alias for Free Cash Flow")
    revenue_cagr_5yr: Optional[float] = Field(None, description="5-Year Revenue CAGR %")
    pat_cagr_5yr: Optional[float] = Field(None, description="5-Year Net Profit CAGR %")
    pe_ratio: Optional[float] = Field(None, description="Price to Earnings ratio")
    pe: Optional[float] = Field(None, description="Alias for Price to Earnings ratio")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_float_param(val: Any, param_name: str) -> Optional[float]:
    """
    Validate numeric parameters. Returns float or None.
    Raises HTTPException(400) if value is invalid string/non-numeric.
    """
    if val is None:
        return None
    if hasattr(val, "default"):
        if val.default is None or str(val.default).startswith("PydanticUndefined"):
            return None
        val = val.default
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parameter '{param_name}': must be a finite number."
            )
        return float(val)
    try:
        f_val = float(str(val).strip())
        if math.isnan(f_val) or math.isinf(f_val):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parameter '{param_name}': must be a finite number."
            )
        return f_val
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter '{param_name}': expected numeric value."
        ) from exc


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/screener",
    response_model=List[ScreenerCompanyItem],
    summary="Screen Companies by Financial KPIs",
    description="Filter Nifty 100 companies based on ROE, D/E, Free Cash Flow, Sector, CAGR, and P/E ratio.",
    responses={
        200: {"description": "Filtered and ranked company list returned successfully"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"}
    }
)
def get_screener_results(
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity % (ROE >= threshold)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt to Equity ratio (D/E <= threshold)"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (FCF >= threshold)"),
    sector: Optional[str] = Query(None, description="Exact or partial sector filter"),
    min_rev_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-Year Revenue CAGR %"),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-Year PAT CAGR %"),
    max_pe: Optional[float] = Query(None, description="Maximum Price to Earnings ratio (P/E <= threshold)")
) -> List[ScreenerCompanyItem]:
    """
    Returns ranked stock screening results based on specified KPI filters.
    """
    try:
        # Explicit validation for non-numeric/invalid values
        v_min_roe = validate_float_param(min_roe, "min_roe")
        v_max_de = validate_float_param(max_de, "max_de")
        v_min_fcf = validate_float_param(min_fcf, "min_fcf")
        v_min_rev_cagr_5yr = validate_float_param(min_rev_cagr_5yr, "min_rev_cagr_5yr")
        v_min_pat_cagr_5yr = validate_float_param(min_pat_cagr_5yr, "min_pat_cagr_5yr")
        v_max_pe = validate_float_param(max_pe, "max_pe")

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                c.company_id,
                c.company_name,
                COALESCE(s.sub_sector, s.broad_sector, c.sector, 'Other') AS sector_name,
                fr.roe,
                fr.debt_to_equity,
                cf.free_cash_flow,
                kpi.revenue_cagr AS rev_cagr_5yr,
                kpi.profit_cagr AS pat_cagr_5yr,
                mc.pe_ratio
            FROM companies c
            LEFT JOIN (
                SELECT company_id, sub_sector, broad_sector 
                FROM sectors 
                GROUP BY company_id
            ) s ON c.company_id = s.company_id
            LEFT JOIN (
                SELECT company_id, roe, debt_to_equity,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY period DESC) as rn
                FROM financial_ratios
            ) fr ON c.company_id = fr.company_id AND fr.rn = 1
            LEFT JOIN (
                SELECT company_id, free_cash_flow,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY period DESC) as rn
                FROM cash_flow
                WHERE free_cash_flow IS NOT NULL
            ) cf ON c.company_id = cf.company_id AND cf.rn = 1
            LEFT JOIN (
                SELECT company_id, revenue_cagr, profit_cagr,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY period DESC) as rn
                FROM financial_kpis
                WHERE revenue_cagr IS NOT NULL OR profit_cagr IS NOT NULL
            ) kpi ON c.company_id = kpi.company_id AND kpi.rn = 1
            LEFT JOIN (
                SELECT company_id, pe_ratio,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY period DESC) as rn
                FROM market_cap
                WHERE pe_ratio IS NOT NULL
            ) mc ON c.company_id = mc.company_id AND mc.rn = 1
            WHERE 1=1
        """
        params: List[Any] = []

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # In-memory filtering for precise financial logic handling (NULL safety)
        filtered_results = []
        for r in rows:
            c_id = r["company_id"]
            c_name = r["company_name"]
            c_sec = r["sector_name"]
            roe_val = r["roe"]
            de_val = r["debt_to_equity"]
            fcf_val = r["free_cash_flow"]
            rev_cagr_val = r["rev_cagr_5yr"]
            pat_cagr_val = r["pat_cagr_5yr"]
            pe_val = r["pe_ratio"]

            # Fallbacks from peer_percentiles if primary metrics are missing
            if fcf_val is None or roe_val is None or de_val is None or rev_cagr_val is None or pat_cagr_val is None:
                pp_cur = conn.execute(
                    "SELECT metric, metric_value FROM peer_percentiles WHERE company_id = ?",
                    (c_id,)
                )
                pp_dict = {row["metric"]: row["metric_value"] for row in pp_cur.fetchall()}
                if fcf_val is None:
                    fcf_val = pp_dict.get("free_cash_flow")
                if roe_val is None:
                    roe_val = pp_dict.get("roe")
                if de_val is None:
                    de_val = pp_dict.get("debt_to_equity")
                if rev_cagr_val is None:
                    rev_cagr_val = pp_dict.get("revenue_cagr_5yr")
                if pat_cagr_val is None:
                    pat_cagr_val = pp_dict.get("pat_cagr_5yr")

            # Apply filters safely
            if v_min_roe is not None:
                if roe_val is None or roe_val < v_min_roe:
                    continue

            if v_max_de is not None:
                if de_val is None or de_val > v_max_de:
                    continue

            if v_min_fcf is not None:
                if fcf_val is None or fcf_val < v_min_fcf:
                    continue

            if isinstance(sector, str) and sector.strip():
                sec_clean = sector.strip().lower()
                if sec_clean not in c_sec.lower() and c_sec.lower() not in sec_clean:
                    continue

            if v_min_rev_cagr_5yr is not None:
                if rev_cagr_val is None or rev_cagr_val < v_min_rev_cagr_5yr:
                    continue

            if v_min_pat_cagr_5yr is not None:
                if pat_cagr_val is None or pat_cagr_val < v_min_pat_cagr_5yr:
                    continue

            if v_max_pe is not None:
                if pe_val is None or pe_val > v_max_pe:
                    continue

            filtered_results.append({
                "company_id": c_id,
                "company_name": c_name,
                "sector": c_sec,
                "roe": roe_val,
                "debt_to_equity": de_val,
                "free_cash_flow": fcf_val,
                "revenue_cagr_5yr": rev_cagr_val,
                "pat_cagr_5yr": pat_cagr_val,
                "pe_ratio": pe_val,
            })

        # Sort by ROE descending (handling None values)
        filtered_results.sort(
            key=lambda item: (item["roe"] is not None, item["roe"] if item["roe"] is not None else -999999),
            reverse=True
        )

        results: List[ScreenerCompanyItem] = []
        for index, item in enumerate(filtered_results, start=1):
            results.append(ScreenerCompanyItem(
                company_id=item["company_id"],
                company_name=item["company_name"],
                sector=item["sector"],
                rank=index,
                ranking=index,
                roe=item["roe"],
                debt_to_equity=item["debt_to_equity"],
                de=item["debt_to_equity"],
                free_cash_flow=item["free_cash_flow"],
                fcf=item["free_cash_flow"],
                revenue_cagr_5yr=item["revenue_cagr_5yr"],
                pat_cagr_5yr=item["pat_cagr_5yr"],
                pe_ratio=item["pe_ratio"],
                pe=item["pe_ratio"],
            ))

        return results

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error executing screener query")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute screener query"
        ) from exc
