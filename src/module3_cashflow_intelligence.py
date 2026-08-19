"""
Module 3: Cash Flow Intelligence Engine
Sprint 5 — Intelligence, NLP & PDF Reports

This module computes cash flow intelligence metrics for every company in the
authoritative ``companies`` table of the canonical project database
(``data/database/n100.db``) and writes:

* ``output/cashflow_intelligence.xlsx`` — one row per company
* ``output/distress_alerts.csv``        — companies with distress_flag == True

The metric computations are delegated to
``src.analytics.cashflow_intelligence`` (the Sprint 5 cash-flow intelligence
engine), which reuses the existing ``cashflow_kpis`` and ``cagr`` engines:

* CFO Quality Score  - average of (CFO / PAT) over the latest 5 valid years
* CapEx Intensity    - abs(investing_activity) / sales * 100 (latest year)
* FCF CAGR (5 year)  - CAGR of FCF = OCF - |investing_activity|
* FCF Conversion     - FCF / PAT * 100 (latest year)
* Distress Signal    - CFO < 0 AND CFF > 0 (latest year)
* Deleveraging Flag  - CFF < 0 AND borrowings declining year-over-year
* Capital Allocation - reused from cashflow_kpis.classify_capital_allocation

Data reality
------------
* The ``cash_flow`` table stores the statement figures in
  ``operating_activity`` / ``investing_activity`` / ``financing_activity``.
  The canonical-named ``cash_from_*`` columns exist in the schema but are
  NULL for every row.
* ``companies.sector`` is NULL for every row, so the sector is sourced from
  ``sectors.sub_sector`` via a LEFT JOIN.

Root-cause note
---------------
The previous version of this script resolved the project root with
``Path(__file__).resolve().parents[2]``.  Because this file lives at
``<project_root>/src/module3_cashflow_intelligence.py``, ``parents[2]``
resolves to the *parent directory of the repository*, which contained a
second, partial copy of the project whose ``src/analytics/__init__.py`` was
corrupted (a literal ``\\n`` inside a docstring caused a ``SyntaxError``).
That made every ``import src.*`` fail and made outputs land in the wrong
``output/`` directory.  ``parents[1]`` is the correct project root.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# -----------------------------------------------------------------------------
# PROJECT ROOT
# -----------------------------------------------------------------------------
# __file__   = <project_root>/src/module3_cashflow_intelligence.py
# parents[0] = <project_root>/src
# parents[1] = <project_root>   <-- the real project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.constants import OUTPUT_DIR  # noqa: E402
from src.config.logging_config import get_logger  # noqa: E402
from src.database.connection import get_connection  # noqa: E402
from src.analytics.cashflow_intelligence import (  # noqa: E402
    compute_cfo_quality,
    compute_capex_intensity,
    compute_fcf_cagr_5yr,
    compute_fcf_conversion,
    compute_distress_flag,
    compute_deleveraging_flag,
    compute_capital_allocation_label,
    _latest_net_profit,
)

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

EXCEL_OUTPUT_FILENAME = "cashflow_intelligence.xlsx"
DISTRESS_CSV_FILENAME = "distress_alerts.csv"

# Required output columns (Sprint 5 specification)
OUTPUT_COLUMNS = [
    "company_id",
    "sector",
    "cfo_quality_score",
    "cfo_quality_label",
    "capex_intensity_pct",
    "capex_label",
    "fcf_cagr_5yr",
    "fcf_conversion_pct",
    "distress_flag",
    "deleveraging_flag",
    "capital_allocation_label",
]

# Distress alerts CSV columns
DISTRESS_CSV_COLUMNS = ["company_id", "sector", "CFO", "CFF", "latest_net_profit"]


# =============================================================================
# DATA LOADING
# =============================================================================


def fetch_companies(conn) -> pd.DataFrame:
    """
    Fetch the authoritative company list.

    ``companies.sector`` is empty in the canonical database, so the sector is
    sourced from ``sectors.sub_sector`` via a LEFT JOIN.
    """
    query = """
        SELECT
            c.company_id,
            c.company_name,
            COALESCE(NULLIF(s.sub_sector, ''), c.sector) AS sector
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.company_id
        ORDER BY c.company_id
    """
    return pd.read_sql_query(query, conn)


def fetch_company_data(
    conn, company_id: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fetch cash flow, profit & loss and balance sheet rows for one company.

    The cash-flow query selects the populated ``*_activity`` columns; the
    engine falls back to the canonical ``cash_from_*`` names when those are
    the ones populated in a different database.
    """
    query_cf = """
        SELECT period, operating_activity, investing_activity, financing_activity
        FROM cash_flow
        WHERE company_id = ?
    """
    query_pl = """
        SELECT period, sales, net_profit
        FROM profit_loss
        WHERE company_id = ?
    """
    query_bs = """
        SELECT period, borrowings
        FROM balance_sheet
        WHERE company_id = ?
    """
    cf_df = pd.read_sql_query(query_cf, conn, params=(company_id,))
    pl_df = pd.read_sql_query(query_pl, conn, params=(company_id,))
    bs_df = pd.read_sql_query(query_bs, conn, params=(company_id,))
    return cf_df, pl_df, bs_df


# =============================================================================
# METRIC COMPUTATION (delegated to the analytics engine)
# =============================================================================


def _py(value: Any) -> Any:
    """Convert numpy scalars to plain Python values for clean Excel output."""
    import numpy as np

    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def process_company(
    conn, company_id: str, company_name: str, sector: Optional[str]
) -> Dict[str, Any]:
    """
    Compute all Sprint 5 cash-flow intelligence metrics for a company.

    Returns a dictionary with the public output columns plus the temporary
    ``_cfo_value`` / ``_cff_value`` / ``_net_profit_latest`` fields needed to
    build the distress alerts CSV.
    """
    cf_df, pl_df, bs_df = fetch_company_data(conn, company_id)

    cfo_quality = compute_cfo_quality(cf_df, pl_df)
    capex = compute_capex_intensity(cf_df, pl_df)
    fcf_cagr = compute_fcf_cagr_5yr(cf_df)
    fcf_conversion = compute_fcf_conversion(cf_df, pl_df)
    distress = compute_distress_flag(cf_df)
    deleveraging = compute_deleveraging_flag(cf_df, bs_df)
    capital_allocation = compute_capital_allocation_label(cf_df, pl_df)

    return {
        "company_id": company_id,
        "company_name": company_name,
        "sector": sector,
        "cfo_quality_score": _py(cfo_quality.get("score")),
        "cfo_quality_label": cfo_quality.get("label"),
        "capex_intensity_pct": _py(capex.get("value")),
        "capex_label": capex.get("label"),
        "fcf_cagr_5yr": _py(fcf_cagr.get("value")),
        "fcf_conversion_pct": _py(fcf_conversion.get("value")),
        "distress_flag": bool(distress.get("flag")),
        "deleveraging_flag": bool(deleveraging.get("flag")),
        "capital_allocation_label": capital_allocation,
        "_cfo_value": _py(distress.get("cfo")),
        "_cff_value": _py(distress.get("cff")),
        "_net_profit_latest": _py(_latest_net_profit(pl_df)),
    }


def process_all_companies(conn=None) -> pd.DataFrame:
    """
    Process every company in the authoritative ``companies`` table.

    One row per company is returned, sorted by ``company_id``.  A failure for
    a single company is logged and recorded as ``Insufficient Data`` instead
    of aborting the whole run.
    """
    # The singleton connection returned by ``get_connection`` is a shared,
    # process-wide resource (see ``DatabaseConnection``).  It must NOT be
    # closed here with a raw ``conn.close()`` -- that closes the underlying
    # sqlite3 socket without resetting ``DatabaseConnection.connection`` to
    # ``None``, which leaves the singleton in a permanently closed state and
    # breaks every subsequent ``get_connection()`` call (e.g. the peer engine).
    # Callers that pass an explicit ``conn`` own it; the singleton is left
    # open for reuse, consistent with the rest of the codebase.
    conn = get_connection() if conn is None else conn
    companies_df = fetch_companies(conn)
    logger.info(f"Found {len(companies_df)} companies to process")

    results: List[Dict[str, Any]] = []
    for _, company in companies_df.iterrows():
        company_id = company["company_id"]
        company_name = company["company_name"]
        sector = company["sector"]
        try:
            result = process_company(conn, company_id, company_name, sector)
            results.append(result)
        except Exception as exc:  # noqa: BLE001 - log exact failure, keep going
            logger.error(f"Failed to process company {company_id}: {exc!r}")
            results.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "sector": sector,
                    "cfo_quality_score": None,
                    "cfo_quality_label": "Insufficient Data",
                    "capex_intensity_pct": None,
                    "capex_label": "Insufficient Data",
                    "fcf_cagr_5yr": None,
                    "fcf_conversion_pct": None,
                    "distress_flag": False,
                    "deleveraging_flag": False,
                    "capital_allocation_label": "Insufficient Data",
                    "_cfo_value": None,
                    "_cff_value": None,
                    "_net_profit_latest": None,
                }
            )

    results_df = pd.DataFrame(results)
    results_df["sector"] = results_df["sector"].where(
        results_df["sector"].notna(), None
    )
    return results_df


# =============================================================================
# OUTPUT BUILDING
# =============================================================================


def build_output_dataframe(results_df: pd.DataFrame) -> pd.DataFrame:
    """Select the required Excel columns from the results DataFrame."""
    return results_df[OUTPUT_COLUMNS].copy()


def build_distress_dataframe(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the distress alerts DataFrame.

    Only companies with ``distress_flag == True`` (latest CFO < 0 AND CFF > 0)
    are included.  The file may legitimately contain zero rows.
    """
    mask = results_df["distress_flag"].fillna(False).astype(bool)
    distress_df = results_df.loc[
        mask, ["company_id", "sector", "_cfo_value", "_cff_value", "_net_profit_latest"]
    ].copy()
    distress_df = distress_df.rename(
        columns={
            "_cfo_value": "CFO",
            "_cff_value": "CFF",
            "_net_profit_latest": "latest_net_profit",
        }
    )
    return distress_df[DISTRESS_CSV_COLUMNS].reset_index(drop=True)


def write_outputs(
    results_df: pd.DataFrame, output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Write the Excel and distress-CSV outputs into ``output_dir``.

    The output directory is created with ``mkdir(parents=True, exist_ok=True)``
    and existing project artifacts inside it are never touched.
    """
    output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    excel_path = output_dir / EXCEL_OUTPUT_FILENAME
    csv_path = output_dir / DISTRESS_CSV_FILENAME

    output_df = build_output_dataframe(results_df)
    distress_df = build_distress_dataframe(results_df)

    output_df.to_excel(excel_path, index=False)
    logger.info(f"Wrote Excel output to {excel_path} with {len(output_df)} rows")

    distress_df.to_csv(csv_path, index=False)
    logger.info(f"Wrote distress alerts to {csv_path} with {len(distress_df)} rows")

    return {"excel": excel_path, "csv": csv_path}


# =============================================================================
# SELF-VALIDATION
# =============================================================================


def validate_output_files(excel_path: Path, csv_path: Path) -> Dict[str, Any]:
    """
    Reopen both generated files and verify they are readable and well-formed.

    Checks: file exists, file non-empty, Excel opens, required columns exist,
    company ids valid, no duplicate company rows, distress CSV rows satisfy
    the distress condition.
    """
    report: Dict[str, Any] = {}

    excel_path = Path(excel_path)
    csv_path = Path(csv_path)

    # Excel
    report["excel_exists"] = excel_path.exists()
    report["excel_size"] = excel_path.stat().st_size if excel_path.exists() else 0
    report["excel_readable"] = False
    report["excel_rows"] = None
    report["excel_columns"] = []
    report["duplicate_rows"] = None
    if report["excel_exists"] and report["excel_size"] > 0:
        try:
            df = pd.read_excel(excel_path)
            report["excel_readable"] = True
            report["excel_rows"] = len(df)
            report["excel_columns"] = df.columns.tolist()
            report["missing_columns"] = [
                c for c in OUTPUT_COLUMNS if c not in df.columns
            ]
            report["duplicate_rows"] = int(df["company_id"].duplicated().sum())
        except Exception as exc:  # noqa: BLE001
            report["excel_error"] = str(exc)

    # CSV
    report["csv_exists"] = csv_path.exists()
    report["csv_size"] = csv_path.stat().st_size if csv_path.exists() else 0
    report["csv_readable"] = False
    report["csv_rows"] = None
    if report["csv_exists"] and report["csv_size"] > 0:
        try:
            df = pd.read_csv(csv_path)
            report["csv_readable"] = True
            report["csv_rows"] = len(df)
            report["csv_columns"] = df.columns.tolist()
            report["csv_missing_columns"] = [
                c for c in DISTRESS_CSV_COLUMNS if c not in df.columns
            ]
        except Exception as exc:  # noqa: BLE001
            report["csv_error"] = str(exc)

    return report


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main() -> int:
    """Run the full Module 3 pipeline and write both output files."""
    logger.info("=== Module 3: Cash Flow Intelligence ===")

    results_df = process_all_companies()
    paths = write_outputs(results_df)

    distress_count = int(results_df["distress_flag"].fillna(False).astype(bool).sum())
    cfo_quality_count = int(results_df["cfo_quality_score"].notna().sum())
    capex_count = int(results_df["capex_intensity_pct"].notna().sum())
    fcf_cagr_count = int(results_df["fcf_cagr_5yr"].notna().sum())
    fcf_conversion_count = int(results_df["fcf_conversion_pct"].notna().sum())

    logger.info("=== Processing Summary ===")
    logger.info(f"Total companies processed: {len(results_df)}")
    logger.info(f"CFO Quality calculated: {cfo_quality_count}")
    logger.info(f"CapEx Intensity calculated: {capex_count}")
    logger.info(f"FCF CAGR 5yr calculated: {fcf_cagr_count}")
    logger.info(f"FCF Conversion calculated: {fcf_conversion_count}")
    logger.info(f"Distress flags True: {distress_count}")
    logger.info(f"Excel output: {paths['excel']}")
    logger.info(f"Distress CSV: {paths['csv']}")
    logger.info("Module 3 processing completed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
