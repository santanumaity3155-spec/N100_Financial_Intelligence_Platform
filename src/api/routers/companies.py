"""
companies.py

Companies router for N100 Financial Intelligence Platform API.
Implements Module 6D — API Endpoints: Company Data.
"""

import re
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config.constants import REPORTS_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(prefix="/companies", tags=["Companies"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================


class CompanyListItem(BaseModel):
    """CompanyListItem class representation."""

    company_id: str = Field(..., description="Unique company ticker identifier")
    company_name: str = Field(..., description="Official company name")
    broad_sector: Optional[str] = Field(
        None, description="Broad industry sector classification"
    )
    sub_sector: Optional[str] = Field(
        None, description="Specific sub-sector classification"
    )
    market_cap_category: Optional[str] = Field(
        None, description="Market cap category (e.g. Large Cap)"
    )
    roe_pct: Optional[float] = Field(None, description="Return on Equity percentage")
    roce_pct: Optional[float] = Field(
        None, description="Return on Capital Employed percentage"
    )


class CompanyProfile(BaseModel):
    """CompanyProfile class representation."""

    company_id: str = Field(..., description="Company ticker symbol")
    company_name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Sector description")
    industry: Optional[str] = Field(None, description="Industry description")
    broad_sector: Optional[str] = Field(None, description="Broad sector classification")
    sub_sector: Optional[str] = Field(None, description="Sub-sector classification")
    market_cap_category: Optional[str] = Field(None, description="Market cap category")
    listed_date: Optional[str] = Field(None, description="Listing date")
    isin_code: Optional[str] = Field(None, description="ISIN security identifier")
    company_logo: Optional[str] = Field(None, description="URL to company logo image")
    chart_link: Optional[str] = Field(None, description="Interactive chart URL")
    about_company: Optional[str] = Field(
        None, description="Business overview and description"
    )
    website: Optional[str] = Field(None, description="Official company website URL")
    nse_profile: Optional[str] = Field(None, description="NSE stock profile page URL")
    bse_profile: Optional[str] = Field(None, description="BSE stock profile page URL")
    face_value: Optional[float] = Field(None, description="Face value per share")
    book_value: Optional[float] = Field(None, description="Book value per share")
    roce_percentage: Optional[float] = Field(None, description="ROCE percentage")
    roe_percentage: Optional[float] = Field(None, description="ROE percentage")
    latest_kpis: Optional[Dict[str, Any]] = Field(
        None, description="Latest calculated KPIs and financial metrics"
    )


class ProfitLossRecord(BaseModel):
    """ProfitLossRecord class representation."""

    id: Optional[int] = Field(None, description="Record primary key ID")
    company_id: str = Field(..., description="Company ticker")
    period: str = Field(..., description="Financial period (e.g. Mar 2024)")
    sales: Optional[float] = Field(None, description="Total sales / revenue")
    expenses: Optional[float] = Field(None, description="Total operating expenses")
    operating_profit: Optional[float] = Field(
        None, description="Operating profit (EBITDA)"
    )
    opm_percentage: Optional[float] = Field(
        None, description="Operating profit margin %"
    )
    other_income: Optional[float] = Field(
        None, description="Other non-operating income"
    )
    interest: Optional[float] = Field(None, description="Interest expense")
    depreciation: Optional[float] = Field(
        None, description="Depreciation and amortization"
    )
    profit_before_tax: Optional[float] = Field(
        None, description="Profit before tax (PBT)"
    )
    tax_percentage: Optional[float] = Field(None, description="Effective tax rate %")
    net_profit: Optional[float] = Field(None, description="Net profit after tax (PAT)")
    eps: Optional[float] = Field(None, description="Earnings per share")
    dividend_payout: Optional[float] = Field(
        None, description="Dividend payout ratio %"
    )


class BalanceSheetRecord(BaseModel):
    """BalanceSheetRecord class representation."""

    id: Optional[int] = Field(None, description="Record primary key ID")
    company_id: str = Field(..., description="Company ticker")
    period: str = Field(..., description="Financial period")
    share_capital: Optional[float] = Field(None, description="Share capital")
    reserves: Optional[float] = Field(None, description="Reserves and surplus")
    borrowings: Optional[float] = Field(None, description="Total borrowings / debt")
    other_liabilities: Optional[float] = Field(None, description="Other liabilities")
    total_liabilities: Optional[float] = Field(None, description="Total liabilities")
    fixed_assets: Optional[float] = Field(None, description="Fixed assets")
    cwip: Optional[float] = Field(None, description="Capital work in progress")
    investments: Optional[float] = Field(None, description="Investments")
    other_assets: Optional[float] = Field(None, description="Other assets")
    total_assets: Optional[float] = Field(None, description="Total assets")
    equity_capital: Optional[float] = Field(None, description="Equity capital")


class CashFlowRecord(BaseModel):
    """CashFlowRecord class representation."""

    id: Optional[int] = Field(None, description="Record primary key ID")
    company_id: str = Field(..., description="Company ticker")
    period: str = Field(..., description="Financial period")
    cash_from_operating_activity: Optional[float] = Field(
        None, description="Operating cash flow"
    )
    cash_from_investing_activity: Optional[float] = Field(
        None, description="Investing cash flow"
    )
    cash_from_financing_activity: Optional[float] = Field(
        None, description="Financing cash flow"
    )
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow")
    net_cash_flow: Optional[float] = Field(None, description="Net change in cash")
    operating_activity: Optional[float] = Field(
        None, description="Operating activity cash flow"
    )
    investing_activity: Optional[float] = Field(
        None, description="Investing activity cash flow"
    )
    financing_activity: Optional[float] = Field(
        None, description="Financing activity cash flow"
    )


class RatioRecord(BaseModel):
    """RatioRecord class representation."""

    company_id: str = Field(..., description="Company ticker")
    period: str = Field(..., description="Financial period")
    roe: Optional[float] = Field(None, description="Return on Equity %")
    roce: Optional[float] = Field(None, description="Return on Capital Employed %")
    roa: Optional[float] = Field(None, description="Return on Assets %")
    net_profit_margin: Optional[float] = Field(None, description="Net profit margin %")
    operating_margin: Optional[float] = Field(
        None, description="Operating profit margin %"
    )
    ebit_margin: Optional[float] = Field(None, description="EBIT margin %")
    gross_margin: Optional[float] = Field(None, description="Gross profit margin %")
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    quick_ratio: Optional[float] = Field(None, description="Quick ratio")
    cash_ratio: Optional[float] = Field(None, description="Cash ratio")
    debt_to_equity: Optional[float] = Field(None, description="Debt to Equity ratio")
    debt_ratio: Optional[float] = Field(None, description="Debt ratio")
    interest_coverage: Optional[float] = Field(
        None, description="Interest coverage ratio"
    )
    financial_leverage: Optional[float] = Field(None, description="Financial leverage")
    asset_turnover: Optional[float] = Field(None, description="Asset turnover ratio")
    inventory_turnover: Optional[float] = Field(
        None, description="Inventory turnover ratio"
    )
    receivable_turnover: Optional[float] = Field(
        None, description="Receivables turnover ratio"
    )
    operating_cash_flow: Optional[float] = Field(
        None, description="Operating cash flow"
    )
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow")
    eps: Optional[float] = Field(None, description="Earnings per share")
    pe_ratio: Optional[float] = Field(None, description="Price to Earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price to Book ratio")
    ev_ebitda: Optional[float] = Field(None, description="EV to EBITDA ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield %")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def normalize_ticker(ticker: str) -> str:
    """Normalize ticker string by stripping whitespace and converting to uppercase."""
    if not ticker:
        return ""
    return ticker.strip().upper()


def validate_company_exists(ticker: str) -> bool:
    """Check if normalized ticker exists in the companies table."""
    norm_ticker = normalize_ticker(ticker)
    if not norm_ticker:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM companies WHERE UPPER(TRIM(company_id)) = ?", (norm_ticker,)
    )
    row = cursor.fetchone()
    return row is not None


def parse_year_string(year_str: Optional[str]) -> Optional[int]:
    """
    Validate and parse year parameter (format YYYY or YYYY-MM).
    Raises HTTPException 400 if invalid format.
    Returns integer year (e.g. 2024).
    """
    if not year_str:
        return None

    clean_str = year_str.strip()

    # Format YYYY-MM
    match_ym = re.match(r"^(\d{4})-(0[1-9]|1[0-2])$", clean_str)
    if match_ym:
        return int(match_ym.group(1))

    # Format YYYY
    match_y = re.match(r"^\d{4}$", clean_str)
    if match_y:
        return int(match_y.group(0))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid year format '{year_str}'. Expected format YYYY or YYYY-MM (e.g., 2024 or 2024-03).",
    )


def extract_year_from_db_period(period_str: Optional[str]) -> int:
    """
    Extract integer year from database period string.
    Supports formats like 'Mar 2024', 'Dec 2012', '2024', 'Mar-24', 'Mar-2013'.
    """
    if not period_str:
        return 0

    p_str = str(period_str).strip()

    # Check 4-digit year
    m4 = re.search(r"\b(19\d\d|20\d\d)\b", p_str)
    if m4:
        return int(m4.group(1))

    # Check 2-digit year (e.g., Mar-24 -> 2024, Mar-13 -> 2013)
    m2 = re.search(r"-(1\d|2\d)\b", p_str)
    if m2:
        return 2000 + int(m2.group(1))

    return 0


def validate_year_range(from_year: Optional[str], to_year: Optional[str]):
    """
    Validate from_year and to_year syntax and ensure from_year <= to_year.
    Returns (from_year_int, to_year_int).
    """
    fy_int = parse_year_string(from_year)
    ty_int = parse_year_string(to_year)

    if fy_int is not None and ty_int is not None and fy_int > ty_int:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid year range: from_year ({from_year}) cannot be greater than to_year ({to_year}).",
        )

    return fy_int, ty_int


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "",
    response_model=List[CompanyListItem],
    summary="Get List of Companies",
    description="Retrieve list of all authoritative companies with optional sector, market cap, and search filters.",
    responses={
        200: {"description": "List of companies returned successfully"},
        500: {"description": "Internal server error"},
    },
)
def get_companies(
    sector: Optional[str] = Query(
        None, description="Filter by broad or sub sector (case-insensitive)"
    ),
    market_cap_category: Optional[str] = Query(
        None, description="Filter by market cap category (e.g. Large Cap)"
    ),
    search: Optional[str] = Query(
        None, description="Partial search by company name or ticker"
    ),
) -> List[CompanyListItem]:
    """
    Returns list of all companies from the database.
    Supports sector, market_cap_category, and partial search parameters.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                c.company_id,
                c.company_name,
                COALESCE(s.broad_sector, c.sector) AS broad_sector,
                COALESCE(s.sub_sector, c.industry) AS sub_sector,
                s.market_cap_category,
                c.roe_percentage AS roe_pct,
                c.roce_percentage AS roce_pct
            FROM companies c
            LEFT JOIN sectors s ON c.company_id = s.company_id
            WHERE 1=1
        """
        params: List[Any] = []

        if sector and sector.strip():
            sec_clean = sector.strip()
            sec_lower = sec_clean.lower()
            if sec_lower == "it":
                query += """ AND (
                    LOWER(s.sub_sector) = 'it' OR 
                    LOWER(s.sub_sector) LIKE 'it %' OR 
                    LOWER(s.sub_sector) LIKE '% it%' OR 
                    LOWER(s.sub_sector) LIKE '%information technology%' OR
                    LOWER(c.sector) = 'it' OR
                    LOWER(c.industry) = 'it'
                )"""
            else:
                query += """ AND (
                    LOWER(s.broad_sector) = LOWER(?) OR 
                    LOWER(s.sub_sector) = LOWER(?) OR 
                    LOWER(c.sector) = LOWER(?) OR
                    LOWER(c.industry) = LOWER(?) OR
                    LOWER(s.sub_sector) LIKE LOWER(?)
                )"""
                sec_pattern = f"%{sec_clean}%"
                params.extend([sec_clean, sec_clean, sec_clean, sec_clean, sec_pattern])

        if market_cap_category and market_cap_category.strip():
            mcap_clean = market_cap_category.strip()
            query += " AND LOWER(s.market_cap_category) = LOWER(?)"
            params.append(mcap_clean)

        if search and search.strip():
            search_clean = f"%{search.strip()}%"
            query += " AND (LOWER(c.company_name) LIKE LOWER(?) OR LOWER(c.company_id) LIKE LOWER(?))"
            params.extend([search_clean, search_clean])

        query += " ORDER BY c.company_id ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result: List[CompanyListItem] = []
        for r in rows:
            result.append(
                CompanyListItem(
                    company_id=r["company_id"],
                    company_name=r["company_name"],
                    broad_sector=r["broad_sector"],
                    sub_sector=r["sub_sector"],
                    market_cap_category=r["market_cap_category"],
                    roe_pct=r["roe_pct"],
                    roce_pct=r["roce_pct"],
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in GET /companies")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company list",
        ) from exc


@router.get(
    "/{ticker}",
    response_model=CompanyProfile,
    summary="Get Company Profile",
    description="Retrieve complete profile and latest calculated KPIs for a company by ticker symbol.",
    responses={
        200: {"description": "Company profile returned successfully"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"},
    },
)
def get_company_profile(ticker: str) -> CompanyProfile:
    """
    Returns complete company profile for given ticker symbol.
    """
    norm_ticker = normalize_ticker(ticker)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                c.company_id,
                c.company_name,
                c.sector,
                c.industry,
                s.broad_sector,
                s.sub_sector,
                s.market_cap_category,
                c.listed_date,
                c.isin_code,
                c.company_logo,
                c.chart_link,
                c.about_company,
                c.website,
                c.nse_profile,
                c.bse_profile,
                c.face_value,
                c.book_value,
                c.roce_percentage,
                c.roe_percentage
            FROM companies c
            LEFT JOIN sectors s ON c.company_id = s.company_id
            WHERE UPPER(TRIM(c.company_id)) = ?
        """,
            (norm_ticker,),
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ticker '{ticker}' not found",
            )

        # Fetch latest calculated KPIs for company
        cursor.execute(
            """
            SELECT *
            FROM financial_kpis
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY id DESC
            LIMIT 10
        """,
            (norm_ticker,),
        )
        kpi_rows = cursor.fetchall()

        latest_kpis: Dict[str, Any] = {}
        for kr in kpi_rows:
            kd = dict(kr)
            non_null_count = sum(1 for v in kd.values() if v is not None)
            if non_null_count > 3:
                latest_kpis = {
                    k: v
                    for k, v in kd.items()
                    if k not in ("id", "company_id", "calculated_at")
                }
                break
        if not latest_kpis and kpi_rows:
            latest_kpis = {
                k: v
                for k, v in dict(kpi_rows[0]).items()
                if k not in ("id", "company_id", "calculated_at")
            }

        return CompanyProfile(
            company_id=row["company_id"],
            company_name=row["company_name"],
            sector=row["sector"],
            industry=row["industry"],
            broad_sector=row["broad_sector"] or row["sector"],
            sub_sector=row["sub_sector"] or row["industry"],
            market_cap_category=row["market_cap_category"],
            listed_date=row["listed_date"],
            isin_code=row["isin_code"],
            company_logo=row["company_logo"],
            chart_link=row["chart_link"],
            about_company=row["about_company"],
            website=row["website"],
            nse_profile=row["nse_profile"],
            bse_profile=row["bse_profile"],
            face_value=row["face_value"],
            book_value=row["book_value"],
            roce_percentage=row["roce_percentage"],
            roe_percentage=row["roe_percentage"],
            latest_kpis=latest_kpis,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company profile",
        ) from exc


@router.get(
    "/{ticker}/pl",
    response_model=List[ProfitLossRecord],
    summary="Get P&L History",
    description="Retrieve Profit & Loss historical statements for a company with optional year filtering.",
    responses={
        200: {"description": "P&L history array returned successfully"},
        400: {"description": "Invalid year format or range"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"},
    },
)
def get_profit_loss_history(
    ticker: str,
    from_year: Optional[str] = Query(
        None, description="Start year filter (YYYY or YYYY-MM)"
    ),
    to_year: Optional[str] = Query(
        None, description="End year filter (YYYY or YYYY-MM)"
    ),
) -> List[ProfitLossRecord]:
    """
    Returns historical P&L statements for company.
    """
    norm_ticker = normalize_ticker(ticker)
    if not validate_company_exists(norm_ticker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker}' not found",
        )

    fy_int, ty_int = validate_year_range(from_year, to_year)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM profit_loss
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY id ASC
        """,
            (norm_ticker,),
        )

        rows = cursor.fetchall()

        records: List[ProfitLossRecord] = []
        for r in rows:
            r_year = extract_year_from_db_period(r["period"])
            if fy_int is not None and r_year < fy_int and r_year != 0:
                continue
            if ty_int is not None and r_year > ty_int and r_year != 0:
                continue

            records.append(
                ProfitLossRecord(
                    id=r["id"],
                    company_id=r["company_id"],
                    period=r["period"],
                    sales=r["sales"],
                    expenses=r["expenses"],
                    operating_profit=r["operating_profit"],
                    opm_percentage=r["opm_percentage"],
                    other_income=r["other_income"],
                    interest=r["interest"],
                    depreciation=r["depreciation"],
                    profit_before_tax=r["profit_before_tax"],
                    tax_percentage=r["tax_percentage"],
                    net_profit=r["net_profit"],
                    eps=r["eps"],
                    dividend_payout=r["dividend_payout"],
                )
            )

        records.sort(key=lambda item: extract_year_from_db_period(item.period))
        return records

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}/pl")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve P&L history",
        ) from exc


@router.get(
    "/{ticker}/bs",
    response_model=List[BalanceSheetRecord],
    summary="Get Balance Sheet History",
    description="Retrieve Balance Sheet historical statements for a company with optional year filtering.",
    responses={
        200: {"description": "Balance Sheet history array returned successfully"},
        400: {"description": "Invalid year format or range"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"},
    },
)
def get_balance_sheet_history(
    ticker: str,
    from_year: Optional[str] = Query(
        None, description="Start year filter (YYYY or YYYY-MM)"
    ),
    to_year: Optional[str] = Query(
        None, description="End year filter (YYYY or YYYY-MM)"
    ),
) -> List[BalanceSheetRecord]:
    """
    Returns historical Balance Sheet statements for company.
    """
    norm_ticker = normalize_ticker(ticker)
    if not validate_company_exists(norm_ticker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker}' not found",
        )

    fy_int, ty_int = validate_year_range(from_year, to_year)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM balance_sheet
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY id ASC
        """,
            (norm_ticker,),
        )

        rows = cursor.fetchall()

        records: List[BalanceSheetRecord] = []
        for r in rows:
            r_year = extract_year_from_db_period(r["period"])
            if fy_int is not None and r_year < fy_int and r_year != 0:
                continue
            if ty_int is not None and r_year > ty_int and r_year != 0:
                continue

            records.append(
                BalanceSheetRecord(
                    id=r["id"],
                    company_id=r["company_id"],
                    period=r["period"],
                    share_capital=r["share_capital"],
                    reserves=r["reserves"],
                    borrowings=r["borrowings"],
                    other_liabilities=r["other_liabilities"],
                    total_liabilities=r["total_liabilities"],
                    fixed_assets=r["fixed_assets"],
                    cwip=r["cwip"],
                    investments=r["investments"],
                    other_assets=r["other_assets"],
                    total_assets=r["total_assets"],
                    equity_capital=r["equity_capital"],
                )
            )

        records.sort(key=lambda item: extract_year_from_db_period(item.period))
        return records

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}/bs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Balance Sheet history",
        ) from exc


@router.get(
    "/{ticker}/cashflow",
    response_model=List[CashFlowRecord],
    summary="Get Cash Flow History",
    description="Retrieve Cash Flow historical statements for a company with optional year filtering.",
    responses={
        200: {"description": "Cash Flow history array returned successfully"},
        400: {"description": "Invalid year format or range"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"},
    },
)
def get_cash_flow_history(
    ticker: str,
    from_year: Optional[str] = Query(
        None, description="Start year filter (YYYY or YYYY-MM)"
    ),
    to_year: Optional[str] = Query(
        None, description="End year filter (YYYY or YYYY-MM)"
    ),
) -> List[CashFlowRecord]:
    """
    Returns historical Cash Flow statements for company.
    """
    norm_ticker = normalize_ticker(ticker)
    if not validate_company_exists(norm_ticker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker}' not found",
        )

    fy_int, ty_int = validate_year_range(from_year, to_year)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM cash_flow
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY id ASC
        """,
            (norm_ticker,),
        )

        rows = cursor.fetchall()

        records: List[CashFlowRecord] = []
        for r in rows:
            r_year = extract_year_from_db_period(r["period"])
            if fy_int is not None and r_year < fy_int and r_year != 0:
                continue
            if ty_int is not None and r_year > ty_int and r_year != 0:
                continue

            records.append(
                CashFlowRecord(
                    id=r["id"],
                    company_id=r["company_id"],
                    period=r["period"],
                    cash_from_operating_activity=r["cash_from_operating_activity"],
                    cash_from_investing_activity=r["cash_from_investing_activity"],
                    cash_from_financing_activity=r["cash_from_financing_activity"],
                    free_cash_flow=r["free_cash_flow"],
                    net_cash_flow=r["net_cash_flow"],
                    operating_activity=r["operating_activity"],
                    investing_activity=r["investing_activity"],
                    financing_activity=r["financing_activity"],
                )
            )

        records.sort(key=lambda item: extract_year_from_db_period(item.period))
        return records

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}/cashflow")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Cash Flow history",
        ) from exc


@router.get(
    "/{ticker}/ratios",
    response_model=List[RatioRecord],
    summary="Get Financial Ratios and KPIs",
    description="Retrieve all computed financial ratios and KPIs per year for a company.",
    responses={
        200: {"description": "Ratios and KPIs array returned successfully"},
        400: {"description": "Invalid year format"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"},
    },
)
def get_company_ratios(
    ticker: str,
    year: Optional[str] = Query(
        None, description="Optional year filter (YYYY or YYYY-MM)"
    ),
) -> List[RatioRecord]:
    """
    Returns historical financial ratios and KPIs for company.
    If year is supplied, returns only matching year records.
    """
    norm_ticker = normalize_ticker(ticker)
    if not validate_company_exists(norm_ticker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker}' not found",
        )

    filter_year_int = parse_year_string(year)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                k.company_id,
                k.period,
                k.roe,
                k.roce,
                k.roa,
                k.net_profit_margin,
                k.operating_margin,
                k.ebit_margin,
                k.gross_margin,
                k.current_ratio,
                k.quick_ratio,
                k.cash_ratio,
                k.debt_to_equity,
                k.debt_ratio,
                k.interest_coverage,
                k.financial_leverage,
                k.asset_turnover,
                k.inventory_turnover,
                k.receivable_turnover,
                k.operating_cash_flow,
                k.free_cash_flow,
                k.eps,
                k.pe_ratio,
                k.pb_ratio,
                k.ev_ebitda,
                k.dividend_yield
            FROM financial_kpis k
            WHERE UPPER(TRIM(k.company_id)) = ?
            ORDER BY k.id ASC
        """,
            (norm_ticker,),
        )

        rows = cursor.fetchall()

        records: List[RatioRecord] = []
        for r in rows:
            r_year = extract_year_from_db_period(r["period"])
            if filter_year_int is not None and r_year != filter_year_int:
                continue

            records.append(
                RatioRecord(
                    company_id=r["company_id"],
                    period=r["period"],
                    roe=r["roe"],
                    roce=r["roce"],
                    roa=r["roa"],
                    net_profit_margin=r["net_profit_margin"],
                    operating_margin=r["operating_margin"],
                    ebit_margin=r["ebit_margin"],
                    gross_margin=r["gross_margin"],
                    current_ratio=r["current_ratio"],
                    quick_ratio=r["quick_ratio"],
                    cash_ratio=r["cash_ratio"],
                    debt_to_equity=r["debt_to_equity"],
                    debt_ratio=r["debt_ratio"],
                    interest_coverage=r["interest_coverage"],
                    financial_leverage=r["financial_leverage"],
                    asset_turnover=r["asset_turnover"],
                    inventory_turnover=r["inventory_turnover"],
                    receivable_turnover=r["receivable_turnover"],
                    operating_cash_flow=r["operating_cash_flow"],
                    free_cash_flow=r["free_cash_flow"],
                    eps=r["eps"],
                    pe_ratio=r["pe_ratio"],
                    pb_ratio=r["pb_ratio"],
                    ev_ebitda=r["ev_ebitda"],
                    dividend_yield=r["dividend_yield"],
                )
            )

        records.sort(key=lambda item: extract_year_from_db_period(item.period))
        return records

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}/ratios")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve financial ratios",
        ) from exc


@router.get(
    "/{ticker}/tearsheet",
    summary="Get Company Tearsheet PDF",
    description="Download pre-generated PDF tearsheet report for a company.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF tearsheet file returned successfully",
        },
        400: {"description": "Invalid ticker parameter"},
        404: {"description": "Company ticker or tearsheet PDF not found"},
        500: {"description": "Internal server error"},
    },
)
def get_company_tearsheet(ticker: str):
    """
    Returns pre-generated company tearsheet PDF.
    Enforces path traversal safety and validates ticker against DB.
    """
    norm_ticker = normalize_ticker(ticker)

    # Path traversal validation
    if not norm_ticker or re.search(r"[/\\]|\.\.", ticker):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ticker format",
        )

    if not validate_company_exists(norm_ticker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker}' not found",
        )

    tearsheet_dir = (REPORTS_DIR / "tearsheets").resolve()
    pdf_path = (tearsheet_dir / f"{norm_ticker}_tearsheet.pdf").resolve()

    # Strictly enforce path containment
    if not pdf_path.is_relative_to(tearsheet_dir):
        logger.warning(f"Path traversal attempt blocked for ticker: {ticker}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path"
        )

    if not pdf_path.exists() or not pdf_path.is_file():
        logger.warning(f"Tearsheet PDF missing for ticker: {norm_ticker} at {pdf_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tearsheet PDF for ticker '{ticker}' not found on server",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{norm_ticker}_tearsheet.pdf",
    )
