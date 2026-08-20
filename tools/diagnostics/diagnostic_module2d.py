import pandas as pd
import sys
sys.path.insert(0, 'src')

from src.nlp.pros_cons_generator import (
    get_company_context,
    get_registered_rules,
    load_financial_data,
    OUTPUT_DIR,
    PROS_CONS_GENERATED_CSV_PATH,
    TYPE_PRO,
    TYPE_CON,
    CONFIDENCE_THRESHOLD,
    validate_confidence,
    format_confidence,
)
from src.nlp.pro_rules import get_pro_rule_instances
from src.nlp.con_rules import get_con_rule_instances

def main():
    # Load all companies from DB
    data = load_financial_data()
    companies_df = data.get("companies")
    if companies_df is None or companies_df.empty:
        print("ERROR: Could not load companies table")
        return
    companies_df["company_id"] = companies_df["company_id"].astype(str).str.strip().str.upper()
    all_company_ids = sorted(companies_df["company_id"].tolist())
    print(f"Total companies in DB: {len(all_company_ids)}")

    # Determine missing Pro/Con from existing CSV (or compute)
    try:
        existing_df = pd.read_csv(OUTPUT_DIR / "pros_cons_generated.csv")
        existing_pro = set(existing_df[existing_df["type"] == TYPE_PRO]["company_id"])
        existing_con = set(existing_df[existing_df["type"] == TYPE_CON]["company_id"])
        missing_pro = set(all_company_ids) - existing_pro
        missing_con = set(all_company_ids) - existing_con
        print(f"Missing Pro companies: {sorted(missing_pro)}")
        print(f"Missing Con companies: {sorted(missing_con)}")
    except Exception as e:
        print(f"Could not read existing CSV: {e}")
        missing_pro = set()
        missing_con = set()

    # We'll diagnose all companies, but focus on missing ones
    target_companies = sorted(set(all_company_ids) & (missing_pro | missing_con))
    if not target_companies:
        # If no missing, diagnose all
        target_companies = all_company_ids[:20]  # sample
        print("No missing companies found; diagnosing first 20 as sample")

    # Get rule instances
    pro_rules = get_pro_rule_instances()
    con_rules = get_con_rule_instances()
    all_rules = pro_rules + con_rules
    print(f"Loaded {len(pro_rules)} PRO rules and {len(con_rules)} CON rules")

    rows = []
    for idx, cid in enumerate(target_companies):
        if idx % 10 == 0:
            print(f"Processing {idx+1}/{len(target_companies)}: {cid}")
        context = get_company_context(cid)
        if context is None:
            print(f"WARNING: No context for {cid}")
            continue
        company_name = getattr(context, "company_name", "")
        sector = getattr(context, "sector", "")
        # Evaluate each rule
        for rule in all_rules:
            try:
                result = rule.evaluate(context)
                triggered = result.triggered
                confidence = result.confidence_pct
                reason = result.reason
                eligible = confidence > CONFIDENCE_THRESHOLD if triggered else False
                # Collect some latest metrics for debugging
                latest = getattr(context, "latest", {})
                history = getattr(context, "history", {})
                history_years = getattr(context, "history_years", [])
                # Build row
                row = {
                    "company_id": cid,
                    "company_name": company_name,
                    "sector": sector,
                    "rule_id": rule.rule_id,
                    "type": rule.rule_type,
                    "triggered": triggered,
                    "confidence_pct": confidence,
                    "eligible_after_threshold": eligible,
                    "reason": reason,
                    # Latest metrics
                    "latest_roe": latest.get("roe"),
                    "latest_roce": latest.get("roce"),
                    "latest_debt_to_equity": latest.get("debt_to_equity"),
                    "latest_interest_coverage": latest.get("interest_coverage"),
                    "latest_free_cash_flow": latest.get("free_cash_flow"),
                    "latest_revenue": latest.get("revenue"),
                    "latest_net_profit": latest.get("net_profit"),
                    "latest_opm": latest.get("opm"),
                    "latest_eps": latest.get("eps"),
                    "latest_dividend_yield": latest.get("dividend_yield"),
                    "latest_total_assets": latest.get("total_assets"),
                    "latest_borrowings": latest.get("borrowings"),
                    "latest_net_debt": latest.get("net_debt"),
                    "latest_ebitda": latest.get("ebitda"),
                    # Trailing metrics
                    "trailing_revenue_cagar": getattr(context, "trailing", {}).get("revenue_cagr"),
                    "trailing_profit_cagr": getattr(context, "trailing", {}).get("profit_cagr"),
                    "trailing_eps_cagr": getattr(context, "trailing", {}).get("eps_cagr"),
                    # History lengths
                    "history_years_count": len(history_years),
                    "history_roe_len": len(history.get("roe", [])),
                    "history_fcf_len": len(history.get("free_cash_flow", [])),
                    "history_opm_len": len(history.get("opm", [])),
                    "history_revenue_len": len(history.get("revenue", [])),
                }
                rows.append(row)
            except Exception as e:
                print(f"ERROR evaluating {cid} rule {rule.rule_id}: {e}")
                # Add a failed row
                row = {
                    "company_id": cid,
                    "company_name": company_name,
                    "sector": sector,
                    "rule_id": rule.rule_id,
                    "type": rule.rule_type,
                    "triggered": False,
                    "confidence_pct": 0.0,
                    "eligible_after_threshold": False,
                    "reason": f"Evaluation error: {e}",
                    "latest_roe": None,
                    "latest_roce": None,
                    "latest_debt_to_equity": None,
                    "latest_interest_coverage": None,
                    "latest_free_cash_flow": None,
                    "latest_revenue": None,
                    "latest_net_profit": None,
                    "latest_opm": None,
                    "latest_eps": None,
                    "latest_dividend_yield": None,
                    "latest_total_assets": None,
                    "latest_borrowings": None,
                    "latest_net_debt": None,
                    "latest_ebitda": None,
                    "trailing_revenue_cagar": None,
                    "trailing_profit_cagr": None,
                    "trailing_eps_cagr": None,
                    "history_years_count": 0,
                    "history_roe_len": 0,
                    "history_fcf_len": 0,
                    "history_opm_len": 0,
                    "history_revenue_len": 0,
                }
                rows.append(row)
    df = pd.DataFrame(rows)
    output_path = OUTPUT_DIR / "module_2d_coverage_diagnostic.csv"
    df.to_csv(output_path, index=False)
    print(f"Diagnostic saved to {output_path}")
    # Print summary for missing companies
    print("\n=== Summary for missing companies ===")
    for cid in target_companies:
        sub = df[df["company_id"] == cid]
        pro_trig = sub[(sub["type"] == TYPE_PRO) & (sub["eligible_after_threshold"] == True)]
        con_trig = sub[(sub["type"] == TYPE_CON) & (sub["eligible_after_threshold"] == True)]
        print(f"{cid}: Pro eligible triggers: {len(pro_trig)} (rule ids: {list(pro_trig['rule_id']) if len(pro_trig) > 0 else []})")
        print(f"    Con eligible triggers: {len(con_trig)} (rule ids: {list(con_trig['rule_id']) if len(con_trig) > 0 else []})")
        if len(pro_trig) == 0:
            # show best pro confidence
            best_pro = sub[sub["type"] == TYPE_PRO].sort_values("confidence_pct", ascending=False).head(1)
            if not best_pro.empty:
                print(f"    Best Pro confidence: {best_pro.iloc[0]['confidence_pct']} ({best_pro.iloc[0]['rule_id']}) - {best_pro.iloc[0]['reason']}")
        if len(con_trig) == 0:
            best_con = sub[sub["type"] == TYPE_CON].sort_values("confidence_pct", ascending=False).head(1)
            if not best_con.empty:
                print(f"    Best Con confidence: {best_con.iloc[0]['confidence_pct']} ({best_con.iloc[0]['rule_id']}) - {best_con.iloc[0]['reason']}")

if __name__ == "__main__":
    main()