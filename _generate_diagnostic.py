"""
Generate module_2d_coverage_diagnostic.csv

For each of the 14 companies missing Pro or Con, evaluate all 24 rules
and report:
- Rule trigger status
- Confidence percentage
- Whether it qualifies after the 60% threshold
- Why it doesn't qualify
- Required metric values
- Missing metrics
- Available historical years
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.config.constants import OUTPUT_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.nlp.pros_cons_generator import (
    get_company_context,
    load_financial_data,
    CompanyContext,
    safe_float,
    CONFIDENCE_THRESHOLD,
)
from src.nlp.pro_rules import get_pro_rule_instances
from src.nlp.con_rules import get_con_rule_instances

logger = get_logger(__name__)

# The 14 companies that are missing Pro or Con signals
MISSING_PRO = ["UNIONBANK"]
MISSING_CON = [
    "BAJAJFINSV", "BOSCHLTD", "COALINDIA", "DIVISLAB", "DMART",
    "HDFCLIFE", "ICICIGI", "ICICIPRULI", "INDIGO", "IRCTC", "ITC",
    "MARUTI", "PNB"
]
TARGET_COMPANIES = sorted(set(MISSING_PRO + MISSING_CON))

# Output file path
DIAGNOSTIC_OUTPUT = OUTPUT_DIR / "module_2d_coverage_diagnostic.csv"


def extract_metrics_from_context(context: CompanyContext) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Extract all available and missing metrics from context."""
    all_metric_names = set()
    
    # Collect all possible metric names from latest
    if context.latest:
        all_metric_names.update(context.latest.keys())
    
    # Collect from history
    if context.history:
        all_metric_names.update(context.history.keys())
    
    # Collect from trailing
    if context.trailing:
        all_metric_names.update(context.trailing.keys())
    
    available_metrics = {}
    missing_metrics = []
    
    for metric in sorted(all_metric_names):
        value = None
        
        # Try to get latest value first
        if context.latest and metric in context.latest:
            value = context.latest[metric]
        elif context.trailing and metric in context.trailing:
            value = context.trailing[metric]
        elif context.history and metric in context.history:
            hist = context.history[metric]
            if hist:
                # Get last valid value from history
                for v in reversed(hist):
                    if v is not None and not (isinstance(v, float) and np.isnan(v)):
                        value = v
                        break
        
        if value is not None and not (isinstance(value, float) and np.isnan(value)):
            available_metrics[metric] = value
        else:
            missing_metrics.append(metric)
    
    return available_metrics, missing_metrics


def collect_rule_diagnostics(
    company_id: str,
    context: CompanyContext,
) -> List[Dict[str, Any]]:
    """Evaluate all 24 rules and collect diagnostic data."""
    results = []
    
    all_rules = []
    all_rules.extend([(rule, "pro") for rule in get_pro_rule_instances()])
    all_rules.extend([(rule, "con") for rule in get_con_rule_instances()])
    
    for rule, rule_type in all_rules:
        try:
            rule_result = rule.evaluate(context, conn=None)
            
            triggered = rule_result.triggered
            confidence = safe_float(rule_result.confidence_pct) or 0.0
            eligible_after_threshold = confidence > CONFIDENCE_THRESHOLD
            
            # Extract available metrics that were used in evaluation
            available_metrics, missing_metrics = extract_metrics_from_context(context)
            
            results.append({
                "company_id": company_id,
                "company_name": context.company_name,
                "sector": context.sector,
                "rule_id": rule_result.rule_id,
                "type": rule_result.rule_type,
                "triggered": triggered,
                "confidence_pct": confidence,
                "eligible_after_threshold": eligible_after_threshold,
                "reason": rule_result.reason,
                "required_metric_values": json.dumps(available_metrics) if available_metrics else "{}",
                "missing_metrics": "|".join(missing_metrics) if missing_metrics else "",
                "available_historical_years": len(context.history_years),
            })
        except Exception as exc:
            logger.error(f"Error evaluating rule {rule.rule_id} for {company_id}: {exc}")
    
    return results


def summarize_company_diagnostics(
    company_id: str,
    context: CompanyContext,
    diagnostics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Summarize why a company is missing Pro/Con signals."""
    df_diag = pd.DataFrame(diagnostics)
    
    # Filter to this company
    df_co = df_diag[df_diag["company_id"] == company_id]
    
    # Separate Pro and Con
    df_pro = df_co[df_co["type"] == "pro"]
    df_con = df_co[df_co["type"] == "con"]
    
    # Count triggered rules that pass the threshold
    pro_passing = len(df_pro[(df_pro["triggered"]) & (df_pro["eligible_after_threshold"])])
    con_passing = len(df_con[(df_con["triggered"]) & (df_con["eligible_after_threshold"])])
    
    # Count rules that triggered but failed threshold
    pro_below_threshold = len(df_pro[(df_pro["triggered"]) & (~df_pro["eligible_after_threshold"])])
    con_below_threshold = len(df_con[(df_con["triggered"]) & (~df_con["eligible_after_threshold"])])
    
    # Collect reasons why Pro failed
    pro_failure_reasons = []
    for _, row in df_pro.iterrows():
        if not row["eligible_after_threshold"]:
            reason = row["reason"]
            if row["triggered"]:
                reason = f"[CONFIDENCE {row['confidence_pct']:.1f}%] {reason}"
            pro_failure_reasons.append({
                "rule": row["rule_id"],
                "triggered": row["triggered"],
                "confidence": row["confidence_pct"],
                "reason": reason[:150]  # Truncate for readability
            })
    
    # Collect reasons why Con failed
    con_failure_reasons = []
    for _, row in df_con.iterrows():
        if not row["eligible_after_threshold"]:
            reason = row["reason"]
            if row["triggered"]:
                reason = f"[CONFIDENCE {row['confidence_pct']:.1f}%] {reason}"
            con_failure_reasons.append({
                "rule": row["rule_id"],
                "triggered": row["triggered"],
                "confidence": row["confidence_pct"],
                "reason": reason[:150]
            })
    
    # Determine root cause
    issue_type = ""
    issue_details = []
    
    # Check for missing data
    available_metrics, missing_metrics = extract_metrics_from_context(context)
    critical_missing = [m for m in missing_metrics if m in [
        "roe", "roce", "debt_to_equity", "interest_coverage", "free_cash_flow",
        "revenue", "net_profit", "operating_profit", "eps"
    ]]
    
    if critical_missing:
        issue_type = "missing data"
        issue_details.append(f"Critical metrics missing: {', '.join(critical_missing)}")
    
    # Check for insufficient history
    if context.history_years and len(context.history_years) < 3:
        issue_type = "insufficient historical data" if not issue_type else issue_type
        issue_details.append(f"Only {len(context.history_years)} years of history (need >= 3)")
    
    # Check for all triggered below threshold
    if pro_below_threshold > 0 and pro_passing == 0:
        if not issue_type:
            issue_type = "confidence below 60"
        issue_details.append(f"{pro_below_threshold} Pro rule(s) triggered but below 60% confidence")
    
    if con_below_threshold > 0 and con_passing == 0:
        if not issue_type:
            issue_type = "confidence below 60"
        issue_details.append(f"{con_below_threshold} Con rule(s) triggered but below 60% confidence")
    
    # Check for genuinely no qualifying signal
    if pro_passing == 0 and pro_below_threshold == 0:
        if not issue_type:
            issue_type = "genuinely no qualifying Pro signal"
        issue_details.append("No Pro rules triggered for any reason")
    
    if con_passing == 0 and con_below_threshold == 0:
        if not issue_type:
            issue_type = "genuinely no qualifying Con signal"
        issue_details.append("No Con rules triggered for any reason")
    
    return {
        "company_id": company_id,
        "company_name": context.company_name,
        "sector": context.sector,
        "pro_passing": pro_passing,
        "con_passing": con_passing,
        "pro_below_threshold": pro_below_threshold,
        "con_below_threshold": con_below_threshold,
        "pro_failure_reasons": pro_failure_reasons[:3],  # Top 3
        "con_failure_reasons": con_failure_reasons[:3],  # Top 3
        "available_metrics_count": len(available_metrics),
        "missing_metrics_count": len(missing_metrics),
        "critical_missing": critical_missing,
        "history_years": context.history_years,
        "issue_type": issue_type or "unknown",
        "issue_details": "; ".join(issue_details) if issue_details else "Unable to determine root cause"
    }


def main() -> None:
    """Generate the diagnostic report."""
    logger.info("=" * 80)
    logger.info("Generating Module 2D Coverage Diagnostic")
    logger.info("=" * 80)
    
    start = time.time()
    conn = get_connection()
    data = load_financial_data(conn)
    
    # Collect all diagnostics
    all_diagnostics = []
    summaries = []
    
    for company_id in TARGET_COMPANIES:
        logger.info(f"Processing {company_id}...")
        
        try:
            context = get_company_context(company_id, conn=conn, data=data)
            
            # Evaluate all 24 rules
            diagnostics = collect_rule_diagnostics(company_id, context)
            all_diagnostics.extend(diagnostics)
            
            # Summarize findings
            summary = summarize_company_diagnostics(company_id, context, diagnostics)
            summaries.append(summary)
            
        except Exception as exc:
            logger.error(f"Failed to process {company_id}: {exc}")
    
    # Write the detailed diagnostic CSV
    if all_diagnostics:
        df_diagnostic = pd.DataFrame(all_diagnostics)
        
        # Reorder columns for readability
        cols = [
            "company_id", "company_name", "sector",
            "rule_id", "type",
            "triggered", "confidence_pct", "eligible_after_threshold",
            "reason",
            "required_metric_values", "missing_metrics",
            "available_historical_years"
        ]
        df_diagnostic = df_diagnostic[[c for c in cols if c in df_diagnostic.columns]]
        
        output_path = DIAGNOSTIC_OUTPUT
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_diagnostic.to_csv(output_path, index=False)
        logger.info(f"Diagnostic CSV written to {output_path}")
        logger.info(f"Total rows: {len(df_diagnostic)}")
    
    # Write summary report
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY BY COMPANY")
    logger.info("=" * 80)
    
    for summary in summaries:
        logger.info(f"\n{summary['company_id']} ({summary['sector']})")
        logger.info(f"  Issue Type: {summary['issue_type']}")
        logger.info(f"  Pro Signals: {summary['pro_passing']} passing, {summary['pro_below_threshold']} below threshold")
        logger.info(f"  Con Signals: {summary['con_passing']} passing, {summary['con_below_threshold']} below threshold")
        logger.info(f"  Available Metrics: {summary['available_metrics_count']}")
        logger.info(f"  Missing Metrics: {summary['missing_metrics_count']}")
        if summary['critical_missing']:
            logger.info(f"  Critical Missing: {', '.join(summary['critical_missing'])}")
        logger.info(f"  History Years: {len(summary['history_years'])} ({summary['history_years']})")
        logger.info(f"  Details: {summary['issue_details']}")
    
    elapsed = time.time() - start
    logger.info(f"\nDiagnostic generation completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
