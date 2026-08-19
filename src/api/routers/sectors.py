"""
sectors.py

Sectors router for N100 Financial Intelligence Platform API.
Implements Module 6E — GET /api/v1/sectors and GET /api/v1/sectors/{sector}/companies.
"""

import sqlite3
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Sectors"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================


class SectorSummaryItem(BaseModel):
    """SectorSummaryItem class representation."""

    sector: str = Field(..., description="Name of the industry sector")
    company_count: int = Field(..., description="Number of companies in this sector")
    median_roe: Optional[float] = Field(
        None, description="Median Return on Equity % across sector"
    )
    median_pe: Optional[float] = Field(
        None, description="Median Price to Earnings ratio across sector"
    )
    median_de: Optional[float] = Field(
        None, description="Median Debt to Equity ratio across sector"
    )


class SectorCompanyItem(BaseModel):
    """SectorCompanyItem class representation."""

    company_id: str = Field(..., description="Unique company ticker symbol")
    company_name: str = Field(..., description="Official company name")
    sector: str = Field(..., description="Sector classification")
    roe: Optional[float] = Field(None, description="Latest Return on Equity %")
    roce: Optional[float] = Field(
        None, description="Latest Return on Capital Employed %"
    )
    debt_to_equity: Optional[float] = Field(
        None, description="Latest Debt to Equity ratio"
    )
    pe_ratio: Optional[float] = Field(
        None, description="Latest Price to Earnings ratio"
    )
    net_profit_margin: Optional[float] = Field(
        None, description="Latest Net Profit Margin %"
    )
    latest_kpis: Optional[Dict[str, Any]] = Field(
        None, description="Consolidated latest financial KPIs"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_sector_data_df() -> pd.DataFrame:
    """
    Consolidate companies, sector classifications, financial_ratios, and market_cap.
    """
    conn = get_connection()
    comp = pd.read_sql_query(
        """
        SELECT c.company_id, c.company_name,
               COALESCE(s.sub_sector, s.broad_sector, c.sector, 'Other') AS sector
        FROM companies c
        LEFT JOIN (
            SELECT company_id, sub_sector, broad_sector 
            FROM sectors 
            GROUP BY company_id
        ) s ON c.company_id = s.company_id
        """,
        conn,
    )
    fr = pd.read_sql_query(
        """
        SELECT company_id, roe, debt_to_equity
        FROM financial_ratios
        ORDER BY period DESC
        """,
        conn,
    ).drop_duplicates(subset=["company_id"], keep="first")

    kpi = pd.read_sql_query(
        """
        SELECT company_id, roce, net_profit_margin
        FROM financial_kpis
        ORDER BY period DESC
        """,
        conn,
    ).drop_duplicates(subset=["company_id"], keep="first")

    mc = pd.read_sql_query(
        """
        SELECT company_id, pe_ratio
        FROM market_cap
        WHERE pe_ratio IS NOT NULL
        ORDER BY period DESC
        """,
        conn,
    ).drop_duplicates(subset=["company_id"], keep="first")

    df = (
        comp.merge(fr, on="company_id", how="left")
        .merge(kpi, on="company_id", how="left")
        .merge(mc, on="company_id", how="left")
    )
    return df


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/sectors",
    response_model=List[SectorSummaryItem],
    summary="Get Sector Summaries",
    description="Retrieve sector aggregated statistics including company count, median ROE, median P/E, and median D/E.",
    responses={
        200: {"description": "Sector summary list returned successfully"},
        500: {"description": "Internal server error"},
    },
)
def get_sectors() -> List[SectorSummaryItem]:
    """
    Returns aggregated financial stats for all authoritative sectors.
    """
    try:
        df = get_sector_data_df()
        if df.empty:
            return []

        sectors_list: List[SectorSummaryItem] = []
        for sec_name, group in df.groupby("sector"):
            roe_series = group["roe"].dropna()
            pe_series = group["pe_ratio"].dropna()
            de_series = group["debt_to_equity"].dropna()

            med_roe = float(roe_series.median()) if not roe_series.empty else None
            med_pe = float(pe_series.median()) if not pe_series.empty else None
            med_de = float(de_series.median()) if not de_series.empty else None

            # Ensure valid floats (handling nan)
            if med_roe is not None and (np.isnan(med_roe) or np.isinf(med_roe)):
                med_roe = None
            if med_pe is not None and (np.isnan(med_pe) or np.isinf(med_pe)):
                med_pe = None
            if med_de is not None and (np.isnan(med_de) or np.isinf(med_de)):
                med_de = None

            sectors_list.append(
                SectorSummaryItem(
                    sector=str(sec_name),
                    company_count=int(len(group)),
                    median_roe=med_roe,
                    median_pe=med_pe,
                    median_de=med_de,
                )
            )

        # Sort by sector name ascending
        sectors_list.sort(key=lambda s: s.sector.lower())
        return sectors_list

    except Exception as exc:
        logger.exception("Error in GET /sectors")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sector summary",
        ) from exc


@router.get(
    "/sectors/{sector}/companies",
    response_model=List[SectorCompanyItem],
    summary="Get Companies by Sector",
    description="Retrieve list of companies and latest financial KPIs belonging to a specific sector.",
    responses={
        200: {"description": "List of companies in sector returned successfully"},
        404: {"description": "Sector not found"},
        500: {"description": "Internal server error"},
    },
)
def get_sector_companies(sector: str) -> List[SectorCompanyItem]:
    """
    Returns all companies belonging to the specified sector name.
    """
    try:
        if not sector or not sector.strip():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sector name cannot be empty",
            )

        df = get_sector_data_df()
        sec_clean = sector.strip().lower()

        # Find matching sector using exact or flexible matching
        matching_mask = df["sector"].str.lower() == sec_clean
        if not matching_mask.any():
            # Try partial/contains match if exact match yields 0
            matching_mask = (
                df["sector"].str.lower().str.contains(sec_clean, regex=False)
            )

        matched_df = df[matching_mask]
        if matched_df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sector '{sector}' not found in database.",
            )

        results: List[SectorCompanyItem] = []
        for _, row in matched_df.iterrows():
            roe_val = float(row["roe"]) if pd.notna(row["roe"]) else None
            roce_val = float(row["roce"]) if pd.notna(row["roce"]) else None
            de_val = (
                float(row["debt_to_equity"])
                if pd.notna(row["debt_to_equity"])
                else None
            )
            pe_val = float(row["pe_ratio"]) if pd.notna(row["pe_ratio"]) else None
            npm_val = (
                float(row["net_profit_margin"])
                if pd.notna(row["net_profit_margin"])
                else None
            )

            latest_kpis_dict = {
                "roe": roe_val,
                "roce": roce_val,
                "debt_to_equity": de_val,
                "pe_ratio": pe_val,
                "net_profit_margin": npm_val,
            }

            results.append(
                SectorCompanyItem(
                    company_id=row["company_id"],
                    company_name=row["company_name"],
                    sector=row["sector"],
                    roe=roe_val,
                    roce=roce_val,
                    debt_to_equity=de_val,
                    pe_ratio=pe_val,
                    net_profit_margin=npm_val,
                    latest_kpis=latest_kpis_dict,
                )
            )

        return results

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /sectors/{sector}/companies")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sector companies",
        ) from exc
