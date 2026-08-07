"""
parser.py

NLP Analysis Text Parser for the N100 Financial Intelligence Platform.

Sprint 5 – Module 1

Extracts structured CAGR and ROE values from textual fields in analysis.xlsx
using regular expressions. Produces two CSV outputs:

1. output/analysis_parsed.csv   — successfully parsed rows with validation
2. output/parse_failures.csv    — rows where parsing failed

Cross-checks parsed CAGR values against existing Ratio Engine outputs
(financial_kpis table) and flags rows where |parsed - calculated| > 5%.
"""

import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config.constants import RAW_DATA_DIR, OUTPUT_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.etl.extract import DataExtractor

# =============================================================================
# LOGGER
# =============================================================================

logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Columns to target from analysis.xlsx
TARGET_COLUMNS: List[str] = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]

# Dataset name used by DataExtractor
ANALYSIS_DATASET_NAME: str = "analysis"

# Paths
PARSED_CSV_PATH: Path = OUTPUT_DIR / "analysis_parsed.csv"
FAILURES_CSV_PATH: Path = OUTPUT_DIR / "parse_failures.csv"

# Manual review threshold (percentage points)
MANUAL_REVIEW_THRESHOLD: float = 5.0

# Official Sprint regex pattern for "<N> Years: <value>%"
# Group 1: number of years (integer)
# Group 2: value (signed float, e.g. 21 or -2 or 17.6)
PERIOD_REGEX: re.Pattern = re.compile(
    r"(\d+)\s*Years?:?\s*([+-]?\d+(?:\.\d+)?)%",
    re.IGNORECASE,
)

# Metric type labels for the output CSV
METRIC_SALES_GROWTH: str = "compounded_sales_growth"
METRIC_PROFIT_GROWTH: str = "compounded_profit_growth"
METRIC_STOCK_CAGR: str = "stock_price_cagr"
METRIC_ROE: str = "roe"

# Mapping from parsed metric_type to the reference column in the financial_kpis
# or financial_ratios table used for validation.
# stock_price_cagr has no existing Ratio Engine reference → no validation.
REFERENCE_MAPPING: Dict[str, Optional[str]] = {
    METRIC_SALES_GROWTH: "revenue_cagr",
    METRIC_PROFIT_GROWTH: "profit_cagr",
    METRIC_STOCK_CAGR: None,  # No existing reference; no manual recalc
    METRIC_ROE: "roe",
}

# Reference table names
TABLE_FINANCIAL_KPIS: str = "financial_kpis"
TABLE_FINANCIAL_RATIOS: str = "financial_ratios"

# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ParseResult:
    """Represents the result of parsing a single metric text value."""

    company_id: str
    metric_type: str
    period_years: Optional[int]
    value_pct: Optional[float]
    source_text: str
    parsed_success: bool
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a flat dictionary for DataFrame construction."""
        return asdict(self)


# =============================================================================
# DATA LOADING
# =============================================================================


def load_analysis_data() -> pd.DataFrame:
    """
    Load analysis.xlsx and return only the target columns.

    Uses the existing DataExtractor to read the file with auto-detected
    header row and column mapping.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['company_id'] + TARGET_COLUMNS.
        Returns an empty DataFrame if the file is missing or target columns
        are absent.

    Raises
    ------
    FileNotFoundError
        If analysis.xlsx does not exist.
    """
    start = time.time()
    logger.info("Loading analysis.xlsx data...")

    try:
        extractor = DataExtractor()
        df = extractor.extract_single_dataset(ANALYSIS_DATASET_NAME)
    except FileNotFoundError:
        logger.error("analysis.xlsx not found in %s", RAW_DATA_DIR)
        raise
    except Exception as exc:
        logger.error("Failed to load analysis.xlsx: %s", exc)
        raise

    # Normalize column names (lowercase, strip)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Ensure company_id is present
    if "company_id" not in df.columns:
        logger.error("analysis.xlsx missing 'company_id' column. Found: %s", list(df.columns))
        raise ValueError("analysis.xlsx missing required 'company_id' column")

    # Keep only target columns that actually exist
    available = [c for c in TARGET_COLUMNS if c in df.columns]
    missing = [c for c in TARGET_COLUMNS if c not in df.columns]
    if missing:
        logger.warning("Target columns missing from analysis.xlsx: %s", missing)

    if not available:
        logger.error("No target columns found in analysis.xlsx. Available: %s", list(df.columns))
        raise ValueError("No target columns found in analysis.xlsx")

    result = df[["company_id"] + available].copy()
    logger.info(
        "Loaded %d rows, %d target columns (%s) in %.3fs",
        len(result),
        len(available),
        available,
        time.time() - start,
    )
    return result


# =============================================================================
# PARSING
# =============================================================================


def parse_metric(text: Any, metric_type: str) -> ParseResult:
    """
    Parse a single text value using the Sprint regex.

    Handles:
    - ``"10 Years: 21%"``       → period=10, value=21.0
    - ``"5 Year : 17.6%"``      → period=5,  value=17.6
    - ``"3 Years: -1%"``        → period=3,  value=-1.0
    - ``"TTM: 43%"``            → failure (no numeric period)
    - ``"Last Year: 12%"``      → failure (no numeric period)
    - ``"1 Year: -2%"``         → period=1,  value=-2.0
    - ``None`` / ``NaN``        → failure
    - Garbage strings           → failure

    Parameters
    ----------
    text : Any
        Raw cell value from the DataFrame.
    metric_type : str
        One of TARGET_COLUMNS.

    Returns
    -------
    ParseResult
        Parsed result with success/failure indicators.
    """
    # Normalise text
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return ParseResult(
            company_id="",
            metric_type=metric_type,
            period_years=None,
            value_pct=None,
            source_text=str(text),
            parsed_success=False,
            failure_reason="Empty or NaN value",
        )

    raw = str(text).strip()
    if not raw or raw in ("nan", "None", ""):
        return ParseResult(
            company_id="",
            metric_type=metric_type,
            period_years=None,
            value_pct=None,
            source_text=raw,
            parsed_success=False,
            failure_reason="Empty or NaN value",
        )

    # Apply the Sprint regex
    match = PERIOD_REGEX.search(raw)
    if match:
        try:
            period = int(match.group(1))
            value = float(match.group(2))
            return ParseResult(
                company_id="",
                metric_type=metric_type,
                period_years=period,
                value_pct=value,
                source_text=raw,
                parsed_success=True,
                failure_reason=None,
            )
        except (ValueError, TypeError) as exc:
            return ParseResult(
                company_id="",
                metric_type=metric_type,
                period_years=None,
                value_pct=None,
                source_text=raw,
                parsed_success=False,
                failure_reason=f"Regex match but parsing failed: {exc}",
            )

    # No regex match — failure
    # Determine a descriptive reason
    upper = raw.upper()
    if "TTM" in upper:
        reason = "TTM period (no numeric years) — cannot map to a period_years value"
    elif "LAST YEAR" in upper or "LASTYEAR" in upper:
        reason = "Last Year period (no numeric years) — cannot map to a period_years value"
    elif "1 YEAR" in upper or "1YEAR" in upper:
        reason = "1 Year period (regex expects 'Years') — cannot parse"
    else:
        reason = f"Unrecognised format: '{raw}'"

    return ParseResult(
        company_id="",
        metric_type=metric_type,
        period_years=None,
        value_pct=None,
        source_text=raw,
        parsed_success=False,
        failure_reason=reason,
    )


def parse_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Vectorised parse of all target columns in the analysis DataFrame.

    The DataFrame is melted from wide to long format so each row corresponds
    to a single (company_id, metric_type) pair. Each text cell is then parsed
    via ``parse_metric``.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``company_id`` and at least one of TARGET_COLUMNS.

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (parsed_df, failures_df) where:
        - parsed_df  contains only rows with ``parsed_success=True``
        - failures_df contains only rows with ``parsed_success=False``
    """
    start = time.time()
    logger.info("Parsing %d rows × %d metric columns...", len(df), len(TARGET_COLUMNS))

    # Identify the metric columns actually present
    metric_cols = [c for c in TARGET_COLUMNS if c in df.columns]

    # Melt: wide → long
    id_vars = ["company_id"]
    melted = df.melt(
        id_vars=id_vars,
        value_vars=metric_cols,
        var_name="metric_type",
        value_name="source_text",
    )

    # Drop rows where source_text is entirely empty
    melted = melted.dropna(subset=["source_text"]).reset_index(drop=True)

    if melted.empty:
        logger.warning("No data rows after melting — all metric columns are empty")
        empty_df = pd.DataFrame(columns=[
            "company_id", "metric_type", "period_years", "value_pct",
            "source_text", "parsed_success", "failure_reason",
        ])
        return empty_df, empty_df.copy()

    # Apply parse_metric to each row
    # Using a list comprehension for clarity; vectorised application
    parsed: List[ParseResult] = []
    for _, row in melted.iterrows():
        result = parse_metric(row["source_text"], row["metric_type"])
        result.company_id = row["company_id"]
        parsed.append(result)

    # Build DataFrames
    all_df = pd.DataFrame([r.to_dict() for r in parsed])

    # Split into successes and failures
    parsed_df = all_df[all_df["parsed_success"] == True].copy()
    failures_df = all_df[all_df["parsed_success"] == False].copy()

    # Type conversions
    for col in ["period_years", "value_pct"]:
        if col in parsed_df.columns:
            parsed_df[col] = pd.to_numeric(parsed_df[col], errors="coerce")
    if "period_years" in parsed_df.columns:
        parsed_df["period_years"] = parsed_df["period_years"].astype("Int64")  # nullable int

    # Sort: company_id, metric_type, period_years
    parsed_df = parsed_df.sort_values(
        ["company_id", "metric_type", "period_years"],
        ascending=[True, True, True],
    ).reset_index(drop=True)

    failures_df = failures_df.sort_values(
        ["company_id", "metric_type"],
        ascending=[True, True],
    ).reset_index(drop=True)

    elapsed = time.time() - start
    logger.info(
        "Parsing complete: %d rows parsed, %d rows failed in %.3fs",
        len(parsed_df),
        len(failures_df),
        elapsed,
    )
    return parsed_df, failures_df


# =============================================================================
# VALIDATION
# =============================================================================


def _fetch_reference_values() -> Dict[str, Dict[str, float]]:
    """
    Fetch reference CAGR/ROE values from the database.

    Returns
    -------
    Dict[str, Dict[str, float]]
        Nested dict: {company_id: {metric_reference_key: value}}
        e.g. {"HDFCBANK": {"revenue_cagr": 20.29, "profit_cagr": 21.6, "roe": 14.34}}
    """
    refs: Dict[str, Dict[str, float]] = {}

    try:
        conn = get_connection()

        # --- financial_kpis: revenue_cagr, profit_cagr (TTM rows) ---
        kpi_query = """
            SELECT company_id, revenue_cagr, profit_cagr
            FROM financial_kpis
            WHERE period = 'TTM'
              AND revenue_cagr IS NOT NULL
        """
        kpi_df = pd.read_sql_query(kpi_query, conn)
        for _, row in kpi_df.iterrows():
            cid = str(row["company_id"]).strip().upper()
            if cid not in refs:
                refs[cid] = {}
            if pd.notna(row.get("revenue_cagr")):
                refs[cid]["revenue_cagr"] = float(row["revenue_cagr"])
            if pd.notna(row.get("profit_cagr")):
                refs[cid]["profit_cagr"] = float(row["profit_cagr"])

        # --- financial_ratios: roe (latest period per company) ---
        ratios_query = """
            SELECT company_id, period, roe
            FROM financial_ratios
            WHERE roe IS NOT NULL
            ORDER BY company_id, period DESC
        """
        ratios_df = pd.read_sql_query(ratios_query, conn)
        # Keep only the latest period per company
        latest = ratios_df.groupby("company_id").first().reset_index()
        for _, row in latest.iterrows():
            cid = str(row["company_id"]).strip().upper()
            if cid not in refs:
                refs[cid] = {}
            if pd.notna(row.get("roe")):
                refs[cid]["roe"] = float(row["roe"])

        conn.close()
    except Exception as exc:
        logger.warning("Failed to fetch reference values: %s", exc)
        return refs

    logger.info("Fetched reference values for %d companies", len(refs))
    return refs


def _get_reference_key(metric_type: str) -> Optional[str]:
    """
    Map a parsed metric type to its reference key in the database.

    Parameters
    ----------
    metric_type : str
        One of TARGET_COLUMNS.

    Returns
    -------
    Optional[str]
        Reference column name, or None if no reference exists.
    """
    return REFERENCE_MAPPING.get(metric_type)


def validate_against_ratio_engine(
    parsed_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cross-check parsed values against existing Ratio Engine outputs.

    For each successfully parsed row, fetch the corresponding reference value
    from the database and compute ``difference_pct`` and ``manual_review``.

    Rules:
    - If no reference value exists: ``difference_pct = None``,
      ``manual_review = False``.
    - If ``abs(difference_pct) > MANUAL_REVIEW_THRESHOLD``:
      ``manual_review = True``.
    - If reference exists and diff <= threshold: ``manual_review = False``.

    Parameters
    ----------
    parsed_df : pd.DataFrame
        DataFrame of successfully parsed rows (must contain columns
        ``company_id``, ``metric_type``, ``value_pct``).

    Returns
    -------
    pd.DataFrame
        Input DataFrame with additional columns ``manual_review`` (bool)
        and ``difference_pct`` (float or None).
    """
    if parsed_df.empty:
        logger.warning("No parsed rows to validate")
        return parsed_df.copy()

    start = time.time()
    logger.info("Validating %d parsed rows against Ratio Engine...", len(parsed_df))

    # Fetch reference values
    refs = _fetch_reference_values()

    result = parsed_df.copy()
    result["manual_review"] = False
    result["difference_pct"] = None

    for idx, row in result.iterrows():
        cid = str(row["company_id"]).strip().upper()
        metric_type = row["metric_type"]
        ref_key = _get_reference_key(metric_type)
        parsed_value = row["value_pct"]

        if ref_key is None:
            # No reference exists (e.g. stock_price_cagr) — skip validation
            continue

        # Look up reference
        company_refs = refs.get(cid, {})
        ref_value = company_refs.get(ref_key)

        if ref_value is None or pd.isna(parsed_value):
            # No reference available or parsed value is NaN
            continue

        try:
            diff = parsed_value - ref_value
            result.at[idx, "difference_pct"] = round(diff, 2)

            if abs(diff) > MANUAL_REVIEW_THRESHOLD:
                result.at[idx, "manual_review"] = True
                logger.debug(
                    "Manual review flagged: %s | %s | parsed=%.2f ref=%.2f diff=%.2f",
                    cid,
                    metric_type,
                    parsed_value,
                    ref_value,
                    diff,
                )
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Validation error for %s / %s: %s", cid, metric_type, exc
            )

    flagged = result["manual_review"].sum()
    logger.info(
        "Validation complete: %d rows flagged for manual review in %.3fs",
        flagged,
        time.time() - start,
    )
    return result


# =============================================================================
# CSV OUTPUT
# =============================================================================


def save_analysis_csv(parsed_df: pd.DataFrame, path: Path = PARSED_CSV_PATH) -> None:
    """
    Save the parsed analysis DataFrame to CSV.

    Columns: ``company_id, metric_type, period_years, value_pct,
    source_text, parsed_success, manual_review, difference_pct``

    Parameters
    ----------
    parsed_df : pd.DataFrame
        DataFrame with parsed and validated rows.
    path : Path, optional
        Output path (default ``output/analysis_parsed.csv``).
    """
    if parsed_df.empty:
        logger.warning("No parsed rows to save — creating empty CSV with headers")
        empty_df = pd.DataFrame(columns=[
            "company_id", "metric_type", "period_years", "value_pct",
            "source_text", "parsed_success", "manual_review", "difference_pct",
        ])
        empty_df.to_csv(path, index=False)
        logger.info("Empty analysis CSV saved to %s", path)
        return

    out = parsed_df.copy()

    # Ensure columns exist
    for col in ["manual_review", "difference_pct"]:
        if col not in out.columns:
            out[col] = None if col == "difference_pct" else False

    # Select and order columns
    cols = [
        "company_id", "metric_type", "period_years", "value_pct",
        "source_text", "parsed_success", "manual_review", "difference_pct",
    ]
    out = out[[c for c in cols if c in out.columns]]

    # Sort: company_id, metric_type, period_years
    sort_cols = [c for c in ["company_id", "metric_type", "period_years"] if c in out.columns]
    out = out.sort_values(sort_cols).reset_index(drop=True)

    out.to_csv(path, index=False)
    logger.info("Analysis CSV saved to %s (%d rows)", path, len(out))


def save_failures_csv(
    failures_df: pd.DataFrame, path: Path = FAILURES_CSV_PATH
) -> None:
    """
    Save the parse failures DataFrame to CSV.

    Columns: ``company_id, metric_type, source_text, failure_reason``

    Parameters
    ----------
    failures_df : pd.DataFrame
        DataFrame with rows where parsing failed.
    path : Path, optional
        Output path (default ``output/parse_failures.csv``).
    """
    if failures_df.empty:
        logger.warning("No failures to save — creating empty CSV with headers")
        empty_df = pd.DataFrame(columns=[
            "company_id", "metric_type", "source_text", "failure_reason",
        ])
        empty_df.to_csv(path, index=False)
        logger.info("Empty failures CSV saved to %s", path)
        return

    cols = ["company_id", "metric_type", "source_text", "failure_reason"]
    out = failures_df[[c for c in cols if c in failures_df.columns]].copy()
    out = out.sort_values(["company_id", "metric_type"]).reset_index(drop=True)

    out.to_csv(path, index=False)
    logger.info("Failures CSV saved to %s (%d rows)", path, len(out))


# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================


def main() -> Dict[str, Any]:
    """
    Execute the full NLP Analysis Text Parser pipeline.

    Steps
    -----
    1. Load analysis.xlsx
    2. Parse all metric columns with regex
    3. Validate parsed values against the Ratio Engine
    4. Save analysis_parsed.csv
    5. Save parse_failures.csv
    6. Log summary statistics

    Returns
    -------
    Dict[str, Any]
        Summary statistics including timing, row counts, and validation results.
    """
    overall_start = time.time()
    logger.info("=" * 80)
    logger.info("NLP Analysis Text Parser — Sprint 5 Module 1")
    logger.info("=" * 80)

    summary: Dict[str, Any] = {
        "status": "success",
        "total_rows_loaded": 0,
        "total_rows_parsed": 0,
        "total_rows_failed": 0,
        "rows_flagged_manual_review": 0,
        "execution_time_seconds": 0.0,
        "errors": [],
        "warnings": [],
    }

    try:
        # ---------------------------------------------------------------
        # Step 1: Load data
        # ---------------------------------------------------------------
        df = load_analysis_data()
        summary["total_rows_loaded"] = len(df)
        logger.info("Step 1/5 — Data loaded: %d rows", len(df))

        # ---------------------------------------------------------------
        # Step 2: Parse
        # ---------------------------------------------------------------
        parsed_df, failures_df = parse_dataframe(df)
        summary["total_rows_parsed"] = len(parsed_df)
        summary["total_rows_failed"] = len(failures_df)
        logger.info("Step 2/5 — Parsing complete: %d parsed, %d failed", len(parsed_df), len(failures_df))

        # ---------------------------------------------------------------
        # Step 3: Validate
        # ---------------------------------------------------------------
        validated_df = validate_against_ratio_engine(parsed_df)
        summary["rows_flagged_manual_review"] = int(validated_df["manual_review"].sum()) if not validated_df.empty else 0
        logger.info("Step 3/5 — Validation complete: %d flagged for manual review", summary["rows_flagged_manual_review"])

        # ---------------------------------------------------------------
        # Step 4: Save CSVs
        # ---------------------------------------------------------------
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        save_analysis_csv(validated_df)
        save_failures_csv(failures_df)
        logger.info("Step 4/5 — CSVs exported")

        # ---------------------------------------------------------------
        # Step 5: Log summary
        # ---------------------------------------------------------------
        elapsed = time.time() - overall_start
        summary["execution_time_seconds"] = round(elapsed, 3)

        if failures_df.empty:
            logger.info("No parsing failures — all rows parsed successfully")
        else:
            warning_msg = f"{len(failures_df)} rows failed to parse"
            logger.warning(warning_msg)
            summary["warnings"].append(warning_msg)

        logger.info("Step 5/5 — Pipeline complete in %.3fs", elapsed)
        logger.info("=" * 80)
        logger.info("SUMMARY")
        logger.info("  Rows loaded:     %d", summary["total_rows_loaded"])
        logger.info("  Rows parsed:     %d", summary["total_rows_parsed"])
        logger.info("  Rows failed:     %d", summary["total_rows_failed"])
        logger.info("  Manual review:   %d", summary["rows_flagged_manual_review"])
        logger.info("  Execution time:  %.3fs", elapsed)
        logger.info("=" * 80)

    except FileNotFoundError as exc:
        summary["status"] = "failed"
        summary["errors"].append(str(exc))
        logger.error("Fatal error: %s", exc)
    except ValueError as exc:
        summary["status"] = "failed"
        summary["errors"].append(str(exc))
        logger.error("Fatal error: %s", exc)
    except Exception as exc:
        summary["status"] = "failed"
        summary["errors"].append(str(exc))
        logger.exception("Unexpected error during pipeline execution")
    finally:
        if summary["execution_time_seconds"] == 0.0:
            summary["execution_time_seconds"] = round(time.time() - overall_start, 3)

    return summary


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    result = main()
    print(f"\nPipeline completed with status: {result['status']}")
    print(f"Execution time: {result['execution_time_seconds']:.3f}s")
