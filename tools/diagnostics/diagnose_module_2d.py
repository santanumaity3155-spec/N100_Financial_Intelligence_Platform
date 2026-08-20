#!/usr/bin/env python3
"""
Module 2D Coverage Diagnostic Script
Analyzes 14 failing companies to understand why coverage requirement is not met.
Does NOT modify rules, does NOT lower threshold, does NOT fabricate signals.
"""

import sys
import os
import logging
from collections import defaultdict
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_connection
from src.nlp.pros_cons_generator import (
    get_company_context,
    TYPE_PRO,
    TYPE_CON,
)
from src.nlp.pro_rules import get_pro_rule_instances
from src.nlp.con_rules import get_con_rule_instances
from src.config.constants import PROJECT_ROOT

# The 14 failing companies
FAILING_COMPANIES = [
    'UNIONBANK',
    'BAJAJFINSV',
    'BOSCHLTD',
    'COALINDIA',
    'DIVISLAB',
    'DMART',
    'HDFCLIFE',
    'ICICIGI',
    'ICICIPRULI',
    'INDIGO',
    'IRCTC',
    'ITC',
    'MARUTI',
    'PNB',
]

def extract_rule_details(rule, rule_type, ctx):
    """
    Extract detailed information about a rule evaluation.
    Returns dict with rule metadata and evaluation results.
    """
    result = {
        'rule_id': rule.rule_id,
        'rule_type': rule_type,
        'description': rule.description,
        'triggered': False,
        'confidence_pct': 0.0,
        'final_output_eligible': False,  # confidence > 60
        'reason': 'Not evaluated',
        'metric_values': {},
        'missing_metrics': [],
        'available_years': [],
        'historical_years': 0,
    }
    
    try:
        # Evaluate the rule
        rule_result = rule.evaluate(ctx)
        
        result['triggered'] = rule_result.triggered
        result['confidence_pct'] = rule_result.confidence_pct
        result['final_output_eligible'] = rule_result.confidence_pct > 60.0
        result['reason'] = rule_result.reason
        
        # Extract metric values from context
        result['metric_values'] = {
            'latest_year': ctx.latest_year,
            'roe': ctx.latest.get('roe', np.nan),
            'debt_to_equity': ctx.latest.get('debt_to_equity', np.nan),
            'net_profit_margin': ctx.latest.get('npm', np.nan),
            'operating_profit_margin': ctx.latest.get('opm', np.nan),
            'revenue_cagr': ctx.trailing.get('revenue_cagr', np.nan),
            'eps_cagr': ctx.trailing.get('eps_cagr', np.nan),
            'interest_coverage': ctx.latest.get('interest_coverage', np.nan),
            'free_cash_flow': ctx.latest.get('free_cash_flow', np.nan),
            'current_ratio': ctx.latest.get('current_ratio', np.nan),
        }
        
        result['available_years'] = list(ctx.history_years)
        result['historical_years'] = len(ctx.history_years)
            
        # Identify missing metrics by checking which are NaN
        for metric, value in result['metric_values'].items():
            if pd.isna(value):
                result['missing_metrics'].append(metric)
                
    except Exception as e:
        result['reason'] = f"ERROR: {str(e)}"
        result['error'] = True
    
    return result

def diagnose_company(company_id, conn):
    """
    Diagnose a single company: evaluate all 24 rules and capture details.
    """
    logger.info(f"Diagnosing company: {company_id}")
    
    # Build context
    ctx = get_company_context(company_id, conn)
    if ctx is None or ctx.latest_year is None:
        logger.warning(f"  Could not build context for {company_id}")
        return None
    
    # Collect company metadata
    company_info = {
        'company_id': company_id,
        'latest_year': ctx.latest_year,
        'sector': ctx.sector if ctx.sector else 'Unknown',
        'available_years': list(ctx.history_years) if ctx.history_years else [],
        'historical_years': len(ctx.history_years) if ctx.history_years else 0,
    }
    
    # Evaluate all rules
    rules_data = []
    
    # PRO rules
    pro_rules = get_pro_rule_instances()
    for rule in pro_rules:
        details = extract_rule_details(rule, TYPE_PRO, ctx)
        details.update({'company_id': company_id})
        rules_data.append(details)
    
    # CON rules
    con_rules = get_con_rule_instances()
    for rule in con_rules:
        details = extract_rule_details(rule, TYPE_CON, ctx)
        details.update({'company_id': company_id})
        rules_data.append(details)
    
    return {
        'company_info': company_info,
        'rules': rules_data,
    }

def main():
    """Main diagnostic routine."""
    logger.info("=" * 80)
    logger.info("MODULE 2D COVERAGE DIAGNOSTIC - FAILING COMPANIES ANALYSIS")
    logger.info("=" * 80)
    
    conn = get_connection()
    
    # Load company metadata for reference
    companies_df = pd.read_sql_query(
        "SELECT company_id, company_name, sector FROM companies",
        conn
    )
    company_names = dict(zip(companies_df['company_id'], companies_df['company_name']))
    
    # Diagnose all failing companies
    all_diagnostic_data = []
    company_summaries = []
    
    for company_id in FAILING_COMPANIES:
        logger.info(f"\n--- Diagnosing {company_id} ---")
        
        diagnosis = diagnose_company(company_id, conn)
        if diagnosis is None:
            continue
        
        info = diagnosis['company_info']
        rules = diagnosis['rules']
        
        # Add company name
        info['company_name'] = company_names.get(company_id, 'Unknown')
        
        # Summarize coverage
        pro_triggered = sum(1 for r in rules if r['rule_type'] == TYPE_PRO and r['triggered'])
        con_triggered = sum(1 for r in rules if r['rule_type'] == TYPE_CON and r['triggered'])
        pro_eligible = sum(1 for r in rules if r['rule_type'] == TYPE_PRO and r['final_output_eligible'])
        con_eligible = sum(1 for r in rules if r['rule_type'] == TYPE_CON and r['final_output_eligible'])
        
        summary = {
            'company_id': company_id,
            'company_name': info['company_name'],
            'sector': info['sector'],
            'latest_year': info['latest_year'],
            'historical_years': info['historical_years'],
            'pro_triggered': pro_triggered,
            'con_triggered': con_triggered,
            'pro_eligible': pro_eligible,
            'con_eligible': con_eligible,
            'coverage_status': 'PASS' if (pro_eligible > 0 and con_eligible > 0) else 'FAIL',
            'fail_reason': (
                'No Pro signals >60' if (pro_eligible == 0 and con_eligible > 0) else
                'No Con signals >60' if (pro_eligible > 0 and con_eligible == 0) else
                'Neither Pro nor Con signals >60' if (pro_eligible == 0 and con_eligible == 0) else
                'Both have signals'
            )
        }
        company_summaries.append(summary)
        
        # Add all rule details
        for rule in rules:
            rule['company_name'] = info['company_name']
            rule['sector'] = info['sector']
            rule['latest_year'] = info['latest_year']
            rule['historical_years'] = info['historical_years']
            all_diagnostic_data.append(rule)
        
        # Print summary for this company
        logger.info(f"  {company_id} ({info['company_name']}) - {info['sector']}")
        logger.info(f"    Latest Year: {info['latest_year']}")
        logger.info(f"    Historical Years: {info['historical_years']} years")
        logger.info(f"    Pro Rules Triggered/Eligible: {pro_triggered}/{pro_eligible}")
        logger.info(f"    Con Rules Triggered/Eligible: {con_triggered}/{con_eligible}")
        logger.info(f"    Coverage Status: {summary['coverage_status']} - {summary['fail_reason']}")
        
        # Show details for Con rules specifically (since most failures are Con-related)
        con_rules = [r for r in rules if r['rule_type'] == TYPE_CON]
        logger.info(f"\n    CON RULES DETAIL ({len(con_rules)} total):")
        for rule in con_rules:
            status = "✓ ELIGIBLE" if rule['final_output_eligible'] else "✗ NOT ELIGIBLE"
            logger.info(
                f"      {rule['rule_id']}: {status} (conf={rule['confidence_pct']:.2f}%, "
                f"triggered={rule['triggered']}) - {rule['reason']}"
            )
            if rule['missing_metrics']:
                logger.info(f"        Missing: {', '.join(rule['missing_metrics'])}")
    
    # Write diagnostic CSV
    output_csv = os.path.join(PROJECT_ROOT, 'output', 'module_2d_coverage_diagnostic.csv')
    df_diagnostic = pd.DataFrame(all_diagnostic_data)
    
    # Select and reorder columns for clarity
    columns_to_keep = [
        'company_id', 'company_name', 'sector', 'latest_year', 'historical_years',
        'rule_type', 'rule_id', 'description',
        'triggered', 'confidence_pct', 'final_output_eligible',
        'reason', 'missing_metrics', 'available_years',
    ]
    
    df_diagnostic = df_diagnostic[[c for c in columns_to_keep if c in df_diagnostic.columns]]
    df_diagnostic.to_csv(output_csv, index=False)
    logger.info(f"\nDiagnostic CSV written to: {output_csv}")
    
    # Write summary CSV
    summary_csv = os.path.join(PROJECT_ROOT, 'output', 'module_2d_coverage_summary.csv')
    df_summary = pd.DataFrame(company_summaries)
    df_summary.to_csv(summary_csv, index=False)
    logger.info(f"Summary CSV written to: {summary_csv}")
    
    # Print terminal summary
    logger.info("\n" + "=" * 80)
    logger.info("COVERAGE SUMMARY FOR 14 FAILING COMPANIES")
    logger.info("=" * 80)
    for s in company_summaries:
        logger.info(
            f"{s['company_id']:12} | {s['company_name']:40} | "
            f"Pro: {s['pro_eligible']}/{s['pro_triggered']} | "
            f"Con: {s['con_eligible']}/{s['con_triggered']} | "
            f"{s['coverage_status']:4} ({s['fail_reason']})"
        )
    
    # Overall statistics
    passes = sum(1 for s in company_summaries if s['coverage_status'] == 'PASS')
    logger.info("\n" + "-" * 80)
    logger.info(f"Diagnosis Complete: {passes}/{len(FAILING_COMPANIES)} companies now have both Pro & Con >60%")
    logger.info("-" * 80)
    
    conn.close()

if __name__ == '__main__':
    main()
