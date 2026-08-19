"""
portfolio.py

Portfolio router for N100 Financial Intelligence Platform API.
Implements Module 6E — GET /api/v1/portfolio/stats.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config.constants import OUTPUT_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Portfolio"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================


class KPIPercentileStatItem(BaseModel):
    """KPIPercentileStatItem class representation."""

    kpi: str = Field(..., description="Financial KPI identifier")
    count: Optional[int] = Field(None, description="Number of valid company samples")
    P10: float = Field(..., description="10th Percentile value")
    P25: float = Field(..., description="25th Percentile value")
    P50: float = Field(..., description="50th Percentile (Median) value")
    P75: float = Field(..., description="75th Percentile value")
    P90: float = Field(..., description="90th Percentile value")
    Mean: Optional[float] = Field(None, description="Mean average value")
    Std: Optional[float] = Field(None, description="Standard deviation")


class PortfolioStatsResponse(BaseModel):
    """PortfolioStatsResponse class representation."""

    total_kpis: int = Field(..., description="Total core KPIs analyzed")
    stats: List[KPIPercentileStatItem] = Field(
        ..., description="Percentile statistics list for core KPIs"
    )


# =============================================================================
# ENDPOINT
# =============================================================================


@router.get(
    "/portfolio/stats",
    response_model=PortfolioStatsResponse,
    summary="Get Portfolio KPI Percentile Statistics",
    description="Retrieve statistical percentiles (P10, P25, P50, P75, P90, Mean, Std) for core financial KPIs across the company universe.",
    responses={
        200: {"description": "Portfolio statistics returned successfully"},
        500: {"description": "Internal server error"},
    },
)
def get_portfolio_stats() -> PortfolioStatsResponse:
    """
    Returns percentile statistics table for core KPIs across the Nifty 100 universe.
    """
    try:
        csv_path = OUTPUT_DIR / "portfolio_stats.csv"

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            stat_items: List[KPIPercentileStatItem] = []

            for _, row in df.iterrows():
                kpi_name = str(row["kpi"]).strip()
                count_val = (
                    int(row["count"])
                    if "count" in row and pd.notna(row["count"])
                    else None
                )
                p10_v = float(row["P10"]) if pd.notna(row["P10"]) else 0.0
                p25_v = float(row["P25"]) if pd.notna(row["P25"]) else 0.0
                p50_v = float(row["P50"]) if pd.notna(row["P50"]) else 0.0
                p75_v = float(row["P75"]) if pd.notna(row["P75"]) else 0.0
                p90_v = float(row["P90"]) if pd.notna(row["P90"]) else 0.0
                mean_v = (
                    float(row["Mean"])
                    if "Mean" in row and pd.notna(row["Mean"])
                    else None
                )
                std_v = (
                    float(row["Std"]) if "Std" in row and pd.notna(row["Std"]) else None
                )

                stat_items.append(
                    KPIPercentileStatItem(
                        kpi=kpi_name,
                        count=count_val,
                        P10=p10_v,
                        P25=p25_v,
                        P50=p50_v,
                        P75=p75_v,
                        P90=p90_v,
                        Mean=mean_v,
                        Std=std_v,
                    )
                )

            return PortfolioStatsResponse(total_kpis=len(stat_items), stats=stat_items)

        # Fallback to compute statistics dynamically from financial_ratios if CSV is absent
        conn = get_connection()
        fr_df = pd.read_sql_query(
            """
            SELECT roe, roce, roa, net_profit_margin, debt_to_equity, interest_coverage
            FROM financial_ratios
            WHERE period = (SELECT MAX(period) FROM financial_ratios)
            """,
            conn,
        )

        stat_items: List[KPIPercentileStatItem] = []
        for col in fr_df.columns:
            series = fr_df[col].dropna()
            if series.empty:
                continue

            q = series.quantile([0.10, 0.25, 0.50, 0.75, 0.90]).to_dict()
            stat_items.append(
                KPIPercentileStatItem(
                    kpi=col,
                    count=int(len(series)),
                    P10=float(q.get(0.10, 0.0)),
                    P25=float(q.get(0.25, 0.0)),
                    P50=float(q.get(0.50, 0.0)),
                    P75=float(q.get(0.75, 0.0)),
                    P90=float(q.get(0.90, 0.0)),
                    Mean=float(series.mean()),
                    Std=float(series.std()) if len(series) > 1 else 0.0,
                )
            )

        return PortfolioStatsResponse(total_kpis=len(stat_items), stats=stat_items)

    except Exception as exc:
        logger.exception("Error in GET /portfolio/stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio statistics",
        ) from exc
