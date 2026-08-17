#!/usr/bin/env python3
"""Quick diagnostic for the 14 failing companies."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_connection
from src.nlp.pros_cons_generator import (
    get_company_context,
    evaluate_rules_for_company,
    TYPE_PRO,
    TYPE_CON,
)

FAILING_COMPANIES = [
    'UNIONBANK', 'BAJAJFINSV', 'BOSCHLTD', 'COALINDIA', 'DIVISLAB', 'DMART',
    'HDFCLIFE', 'ICICIGI', 'ICICIPRULI', 'INDIGO', 'IRCTC', 'ITC', 'MARUTI', 'PNB'
]

conn = get_connection()

for cid in FAILING_COMPANIES:
    ctx = get_company_context(cid, conn=conn)
    results = evaluate_rules_for_company(ctx, conn=conn)
    
    pro_eligible = [r for r in results if r.rule_type == TYPE_PRO and r.confidence_pct > 60]
    con_eligible = [r for r in results if r.rule_type == TYPE_CON and r.confidence_pct > 60]
    
    print(f"\n{'='*60}")
    print(f"{cid} | {ctx.company_name} | {ctx.sector}")
    print(f"  latest_year={ctx.latest_year}, history_years={len(ctx.history_years)}")
    print(f"  latest={ctx.latest}")
    print(f"  Pro eligible ({len(pro_eligible)}):")
    for r in pro_eligible:
        print(f"    {r.rule_id}: conf={r.confidence_pct:.2f} | {r.reason}")
    print(f"  Con eligible ({len(con_eligible)}):")
    for r in con_eligible:
        print(f"    {r.rule_id}: conf={r.confidence_pct:.2f} | {r.reason}")
    if not pro_eligible and not con_eligible:
        print(f"  *** NO ELIGIBLE SIGNALS ***")

conn.close()
