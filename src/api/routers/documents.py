"""
documents.py

Documents router for N100 Financial Intelligence Platform API.
Implements Module 6E — GET /api/v1/companies/{ticker}/documents.
"""

import re
import sqlite3
from urllib.parse import urlparse
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Documents"])


# =============================================================================
# PYDANTIC RESPONSE MODELS
# =============================================================================


class DocumentItem(BaseModel):
    """DocumentItem class representation."""

    id: Optional[int] = Field(None, description="Primary key ID")
    company_id: str = Field(..., description="Company ticker symbol")
    year: Optional[str] = Field(None, description="Financial report year")
    annual_report: Optional[str] = Field(None, description="Annual report document URL")
    document_url: Optional[str] = Field(None, description="Alias for annual report URL")
    is_url_valid: bool = Field(
        ..., description="Boolean flag indicating whether document URL is valid"
    )


class CompanyDocumentsResponse(BaseModel):
    """CompanyDocumentsResponse class representation."""

    ticker: str = Field(..., description="Requested company ticker symbol")
    company_name: str = Field(..., description="Official company name")
    document_count: int = Field(..., description="Total annual report documents found")
    documents: List[DocumentItem] = Field(
        ..., description="List of annual report document entries"
    )


# =============================================================================
# URL VALIDATION HELPER
# =============================================================================


def validate_annual_report_url(url: Optional[str]) -> bool:
    """
    Validate annual report URL structure.
    Checks scheme, host domain, syntax, and path extension.
    """
    if not url or not isinstance(url, str):
        return False

    cleaned_url = url.strip()
    if not cleaned_url:
        return False

    try:
        parsed = urlparse(cleaned_url)
        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.netloc:
            return False

        # Domain whitelist or standard regulatory domains
        valid_domains = ("bseindia.com", "nseindia.com", "mkt.in", "sec.gov")
        domain_match = any(domain in parsed.netloc.lower() for domain in valid_domains)

        # Basic path check for pdf or document path
        path_lower = parsed.path.lower()
        has_doc_extension = (
            path_lower.endswith(".pdf")
            or "corpfiling" in path_lower
            or "annualreport" in path_lower
            or "his_ann_rpt" in path_lower
            or "attachhis" in path_lower
        )

        return domain_match or has_doc_extension

    except Exception:
        return False


# =============================================================================
# ENDPOINT
# =============================================================================


@router.get(
    "/companies/{ticker}/documents",
    response_model=CompanyDocumentsResponse,
    summary="Get Company Annual Reports & Documents",
    description="Retrieve annual report links and link validity status for requested company.",
    responses={
        200: {"description": "Document list returned successfully"},
        404: {"description": "Company ticker not found"},
        500: {"description": "Internal server error"},
    },
)
def get_company_documents(ticker: str) -> CompanyDocumentsResponse:
    """
    Returns annual report links and url validity status for the specified company.
    """
    try:
        if not ticker or not ticker.strip():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticker symbol cannot be empty",
            )

        ticker_clean = ticker.strip().upper()
        conn = get_connection()

        # Check company existence
        cur = conn.execute(
            "SELECT company_id, company_name FROM companies WHERE company_id = ?",
            (ticker_clean,),
        )
        comp_row = cur.fetchone()
        if not comp_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company ticker '{ticker}' not found.",
            )
        comp_name = comp_row["company_name"]

        # Query documents table
        doc_cur = conn.execute(
            """
            SELECT id, company_id, year, annual_report, document_url, document_type
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (ticker_clean,),
        )
        rows = doc_cur.fetchall()

        doc_items: List[DocumentItem] = []
        for r in rows:
            doc_id = r["id"]
            yr = r["year"]
            rep_url = r["annual_report"] or r["document_url"]
            is_valid = validate_annual_report_url(rep_url)

            doc_items.append(
                DocumentItem(
                    id=doc_id,
                    company_id=ticker_clean,
                    year=str(yr) if yr is not None else None,
                    annual_report=rep_url,
                    document_url=rep_url,
                    is_url_valid=is_valid,
                )
            )

        return CompanyDocumentsResponse(
            ticker=ticker_clean,
            company_name=comp_name,
            document_count=len(doc_items),
            documents=doc_items,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error in GET /companies/{ticker}/documents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company documents",
        ) from exc
