"""
peers.py

Peers router for N100 Financial Intelligence Platform API.
Implements Module 6E — GET /api/v1/peers/{group_name} and GET /api/v1/companies/{ticker}/peers/compare.
"""

import sqlite3
import pandas as pd
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Peers"])


# =============================================================================
# CONSTANTS - 10 PEER METRICS & 8 RADAR AXES
# =============================================================================

REQUIRED_PEER_METRICS = [
    "roe",
    "roce",
    "net_profit_margin",
    "debt_to_equity",
    "free_cash_flow",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]

RADAR_AXES = [
    "roe",
    "roce",
    "net_profit_margin",
    "debt_to_equity",
    "free_cash_flow",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "composite_quality_score",
]


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================

class PeerPercentileMetricItem(BaseModel):
    metric: str = Field(..., description="Financial metric name")
    metric_value: Optional[float] = Field(None, description="Actual metric value")
    percentile_rank: float = Field(..., description="Percentile rank within peer group (0.0 to 1.0)")


class PeerCompanyPercentileItem(BaseModel):
    company_id: str = Field(..., description="Company ticker symbol")
    company_name: str = Field(..., description="Company name")
    percentiles: Dict[str, float] = Field(..., description="Dictionary mapping metric to percentile rank")
    metric_details: List[PeerPercentileMetricItem] = Field(..., description="Detailed metric list with values and percentiles")


class PeerGroupResponse(BaseModel):
    peer_group_name: str = Field(..., description="Peer group identifier")
    company_count: int = Field(..., description="Total companies in peer group")
    companies: List[PeerCompanyPercentileItem] = Field(..., description="List of companies with 10 metric percentiles")


class RadarCompareResponse(BaseModel):
    ticker: str = Field(..., description="Requested company ticker")
    company_name: str = Field(..., description="Requested company name")
    peer_group_name: Optional[str] = Field(None, description="Assigned peer group")
    benchmark_ticker: Optional[str] = Field(None, description="Benchmark company ticker for this peer group")
    metrics: List[str] = Field(..., description="List of 8 radar axis metrics")
    company_values: Dict[str, Optional[float]] = Field(..., description="8 metric values for requested company")
    peer_average: Dict[str, Optional[float]] = Field(..., description="8 metric average values across peer group")
    benchmark_values: Dict[str, Optional[float]] = Field(..., description="8 metric values for benchmark company")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/peers/{group_name}",
    response_model=PeerGroupResponse,
    summary="Get Peer Group Companies and Percentiles",
    description="Retrieve percentile rankings for all 10 core peer metrics across companies in a peer group.",
    responses={
        200: {"description": "Peer group percentile data returned successfully"},
        404: {"description": "Peer group not found"},
        500: {"description": "Internal server error"}
    }
)
def get_peer_group_details(group_name: str) -> PeerGroupResponse:
    """
    Returns percentile ranks for all 10 peer metrics for each company in the requested peer group.
    """
    try:
        if not group_name or not group_name.strip():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Peer group name cannot be empty"
            )

        group_clean = group_name.strip()
        conn = get_connection()

        # Check if group exists in peer_percentiles or peer_groups
        group_cur = conn.execute(
            """
            SELECT DISTINCT peer_group_name FROM peer_percentiles 
            WHERE LOWER(peer_group_name) = LOWER(?)
            UNION
            SELECT DISTINCT peer_group_name FROM peer_groups 
            WHERE LOWER(peer_group_name) = LOWER(?)
            """,
            (group_clean, group_clean)
        )
        row = group_cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Peer group '{group_name}' not found."
            )
        canonical_group_name = row[0]

        # Query peer_percentiles data
        df = pd.read_sql_query(
            """
            SELECT pp.company_id, c.company_name, pp.metric, pp.metric_value, pp.percentile_rank
            FROM peer_percentiles pp
            LEFT JOIN companies c ON pp.company_id = c.company_id
            WHERE LOWER(pp.peer_group_name) = LOWER(?)
            """,
            conn,
            params=[canonical_group_name]
        )

        if df.empty:
            # Fallback to query peer_groups companies
            pg_df = pd.read_sql_query(
                """
                SELECT pg.company_id, c.company_name
                FROM peer_groups pg
                LEFT JOIN companies c ON pg.company_id = c.company_id
                WHERE LOWER(pg.peer_group_name) = LOWER(?)
                """,
                conn,
                params=[canonical_group_name]
            )
            if pg_df.empty:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Peer group '{group_name}' contains no companies."
                )

        company_items: List[PeerCompanyPercentileItem] = []
        for c_id, group_df in df.groupby("company_id"):
            c_name = group_df["company_name"].iloc[0] or c_id
            perc_dict = {}
            metric_list = []

            # Populate metrics for company
            for m in REQUIRED_PEER_METRICS:
                m_rows = group_df[group_df["metric"] == m]
                if not m_rows.empty:
                    m_val = float(m_rows["metric_value"].iloc[0]) if pd.notna(m_rows["metric_value"].iloc[0]) else None
                    p_rank = float(m_rows["percentile_rank"].iloc[0]) if pd.notna(m_rows["percentile_rank"].iloc[0]) else 0.5
                else:
                    m_val = None
                    p_rank = 0.5

                perc_dict[m] = p_rank
                metric_list.append(PeerPercentileMetricItem(
                    metric=m,
                    metric_value=m_val,
                    percentile_rank=p_rank
                ))

            company_items.append(PeerCompanyPercentileItem(
                company_id=c_id,
                company_name=c_name,
                percentiles=perc_dict,
                metric_details=metric_list
            ))

        return PeerGroupResponse(
            peer_group_name=canonical_group_name,
            company_count=len(company_items),
            companies=company_items
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /peers/{group_name}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve peer group data"
        ) from exc


@router.get(
    "/companies/{ticker}/peers/compare",
    response_model=RadarCompareResponse,
    summary="Get Peer Radar Comparison Data",
    description="Retrieve 8 radar axis metrics for requested company, peer group average, and benchmark company.",
    responses={
        200: {"description": "Radar comparison data returned successfully"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"}
    }
)
def get_company_peer_compare(ticker: str) -> RadarCompareResponse:
    """
    Returns 8-axis radar comparison metrics for company vs peer average vs benchmark company.
    """
    try:
        if not ticker or not ticker.strip():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticker symbol cannot be empty"
            )

        ticker_clean = ticker.strip().upper()
        conn = get_connection()

        # Validate company exists
        comp_cur = conn.execute("SELECT company_id, company_name FROM companies WHERE company_id = ?", (ticker_clean,))
        comp_row = comp_cur.fetchone()
        if not comp_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company ticker '{ticker}' not found."
            )
        req_c_name = comp_row["company_name"]

        # Find peer group for company
        pg_cur = conn.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (ticker_clean,))
        pg_row = pg_cur.fetchone()
        
        peer_group_name = pg_row["peer_group_name"] if pg_row else None

        if not peer_group_name:
            # Fallback lookup in sectors
            sec_cur = conn.execute(
                "SELECT COALESCE(sub_sector, broad_sector) FROM sectors WHERE company_id = ?",
                (ticker_clean,)
            )
            sec_row = sec_cur.fetchone()
            peer_group_name = sec_row[0] if sec_row else "Other"

        # Find benchmark company for this peer group
        bench_cur = conn.execute(
            "SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1",
            (peer_group_name,)
        )
        bench_row = bench_cur.fetchone()
        bench_ticker = bench_row["company_id"] if bench_row else None

        # Build metric dictionary helper for a company
        def get_8_metrics_for_company(cid: str) -> Dict[str, Optional[float]]:
            cur = conn.execute(
                """
                SELECT 
                    fr.roe,
                    kpi.roce,
                    kpi.net_profit_margin,
                    fr.debt_to_equity,
                    cf.free_cash_flow,
                    kpi.revenue_cagr,
                    kpi.profit_cagr,
                    fhs.overall_score
                FROM companies c
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
                    SELECT company_id, roce, net_profit_margin, revenue_cagr, profit_cagr,
                           ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY period DESC) as rn
                    FROM financial_kpis
                ) kpi ON c.company_id = kpi.company_id AND kpi.rn = 1
                LEFT JOIN (
                    SELECT company_id, overall_score,
                           ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY period DESC) as rn
                    FROM financial_health_scores
                ) fhs ON c.company_id = fhs.company_id AND fhs.rn = 1
                WHERE c.company_id = ?
                """,
                (cid,)
            )
            r = cur.fetchone()
            if not r:
                return {axis: None for axis in RADAR_AXES}
            
            return {
                "roe": float(r[0]) if r[0] is not None else None,
                "roce": float(r[1]) if r[1] is not None else None,
                "net_profit_margin": float(r[2]) if r[2] is not None else None,
                "debt_to_equity": float(r[3]) if r[3] is not None else None,
                "free_cash_flow": float(r[4]) if r[4] is not None else None,
                "revenue_cagr_5yr": float(r[5]) if r[5] is not None else None,
                "pat_cagr_5yr": float(r[6]) if r[6] is not None else None,
                "composite_quality_score": float(r[7]) if r[7] is not None else None,
            }

        # 1. Company values
        c_values = get_8_metrics_for_company(ticker_clean)

        # 2. Benchmark values
        if bench_ticker:
            b_values = get_8_metrics_for_company(bench_ticker)
        else:
            b_values = dict(c_values)
            bench_ticker = ticker_clean

        # 3. Peer group average
        peer_cids_cur = conn.execute(
            "SELECT DISTINCT company_id FROM peer_groups WHERE peer_group_name = ?",
            (peer_group_name,)
        )
        peer_cids = [r[0] for r in peer_cids_cur.fetchall()]
        if not peer_cids:
            peer_cids = [ticker_clean]

        all_peer_metrics = [get_8_metrics_for_company(cid) for cid in peer_cids]
        peer_avg_dict = {}
        for axis in RADAR_AXES:
            vals = [m[axis] for m in all_peer_metrics if m[axis] is not None]
            peer_avg_dict[axis] = float(sum(vals) / len(vals)) if vals else None

        return RadarCompareResponse(
            ticker=ticker_clean,
            company_name=req_c_name,
            peer_group_name=peer_group_name,
            benchmark_ticker=bench_ticker,
            metrics=RADAR_AXES,
            company_values=c_values,
            peer_average=peer_avg_dict,
            benchmark_values=b_values
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}/peers/compare")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve radar comparison data"
        ) from exc
