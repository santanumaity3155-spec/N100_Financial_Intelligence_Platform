"""
pro_rules.py

Sprint 5 - Module 2B: 12 Pro Rules (PRO_01 - PRO_12) for the Auto Pros/Cons Generator.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from src.nlp.pros_cons_generator import (
    TYPE_CON,
    TYPE_PRO,
    FinancialRule,
    RuleResult,
    calculate_cagr,
    get_latest_value,
    get_metric_history,
    is_declining,
    is_improving,
)


class PRO_01(FinancialRule):
    """Consistently high return on equity above 20% demonstrates exceptional capital efficiency."""

    rule_id = "PRO_01"
    rule_type = TYPE_PRO
    name = "Sustained High ROE"
    description = "ROE > 20% for at least 3 consecutive years"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        roe_series = get_metric_history(context, "roe")
        if len(roe_series) < 3:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"Insufficient ROE history ({len(roe_series)} valid years, need >=3)",
            )

        run = 0
        max_run = 0
        for value in reversed(roe_series):
            if value is not None and value > 20.0:
                run += 1
                max_run = max(max_run, run)
            else:
                break

        if max_run < 3:
            return RuleResult(
class PRO_02(FinancialRule):
    """Strong free cash flow generation over 5 years signals healthy business fundamentals."""

    rule_id = "PRO_02"
    rule_type = TYPE_PRO
    name = "Sustained Positive FCF"
    description = "FCF > 0 for at least 5 consecutive years"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        fcf_series = get_metric_history(context, "free_cash_flow")
        if not fcf_series:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="No FCF history available",
            )

        run = 0
        max_run = 0
        for value in reversed(fcf_series):
            if value is not None and value > 0:
                run += 1
                max_run = max(max_run, run)
            else:
                break

        if max_run < 5:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"Positive FCF for only {max_run} consecutive year(s) (need >=5)",
            )

        confidence = 60.0 + (min(max_run - 5, 6) * 4.0)
        latest_revenue = context.latest.get("revenue")
        if latest_revenue and latest_revenue > 0:
            avg_fcf = sum(fcf_series[-max_run:]) / max_run
            fcf_margin = (avg_fcf / latest_revenue) * 100.0
            confidence += min(fcf_margin * 2.0, 35.0)
        confidence = min(max(confidence, 60.0), 95.0)

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Strong free cash flow generation over 5 years signals healthy business fundamentals",
            confidence_pct=round(confidence, 2),
            reason=f"Positive FCF for {max_run} consecutive years",
        )


class PRO_03(FinancialRule):
    """Debt-free balance sheet provides financial flexibility and eliminates interest burden."""

    rule_id = "PRO_03"
    rule_type = TYPE_PRO
    name = "Debt Free"
    description = "Latest D/E = 0"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        de = context.latest.get("debt_to_equity")
        if de is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
class PRO_04(FinancialRule):
    """Revenue growing at above 15% CAGR over 5 years reflects strong business momentum."""

    rule_id = "PRO_04"
    rule_type = TYPE_PRO
    name = "Strong Revenue Growth"
    description = "Revenue CAGR 5yr > 15%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        rev_cagr = context.trailing.get("revenue_cagr")
        if rev_cagr is None:
            rev_cagr = context.latest.get("revenue_cagr")
        if rev_cagr is None:
            rev_series = get_metric_history(context, "revenue")
            if len(rev_series) >= 5:
                rev_cagr = calculate_cagr(rev_series[0], rev_series[-1], len(rev_series) - 1)
        if rev_cagr is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="Revenue CAGR 5yr unavailable",
            )

        if rev_cagr <= 15.0:
            triggered = False
            confidence = 0.0
            reason = f"Revenue CAGR 5yr = {rev_cagr:.1f}% (<=15%)"
        else:
            triggered = True
            confidence = 60.0 + (rev_cagr - 15.0) * 1.5
            confidence = min(max(confidence, 60.0), 95.0)
            reason = f"Revenue CAGR 5yr = {rev_cagr:.1f}%"

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=triggered,
            text="Revenue growing at above 15% CAGR over 5 years reflects strong business momentum" if triggered else "",
            confidence_pct=round(confidence, 2),
            reason=reason,
        )


class PRO_05(FinancialRule):
    """Operating profit margin above 25% indicates strong pricing power and cost discipline."""

    rule_id = "PRO_05"
    rule_type = TYPE_PRO
    name = "Strong Operating Margin"
    description = "Latest OPM > 25%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        opm = context.latest.get("opm")
        if opm is None:
            rev = context.latest.get("revenue")
            op_profit = context.latest.get("operating_profit")
            if rev and op_profit and rev > 0:
                opm = (op_profit / rev) * 100.0
        if opm is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="OPM unavailable",
            )

        if opm <= 25.0:
            triggered = False
            confidence = 0.0
            reason = f"OPM = {opm:.1f}% (<=25%)"
        else:
            triggered = True
            confidence = 60.0 + (opm - 25.0) * 1.2
            confidence = min(max(confidence, 60.0), 95.0)
            reason = f"OPM = {opm:.1f}%"

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=triggered,
            text="Operating profit margin above 25% indicates strong pricing power and cost discipline" if triggered else "",
            confidence_pct=round(confidence, 2),
            reason=reason,
        )


class PRO_06(FinancialRule):
    """Net profit compounding at above 20% over 5 years creates significant shareholder value."""

    rule_id = "PRO_06"
    rule_type = TYPE_PRO
    name = "Strong PAT Growth"
    description = "PAT CAGR 5yr > 20%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        pat_cagr = context.trailing.get("profit_cagr")
        if pat_cagr is None:
            pat_cagr = context.latest.get("profit_cagr")
        if pat_cagr is None:
            pat_series = get_metric_history(context, "net_profit")
            if len(pat_series) >= 5:
                pat_cagr = calculate_cagr(pat_series[0], pat_series[-1], len(pat_series) - 1)
        if pat_cagr is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="PAT CAGR 5yr unavailable",
class PRO_07(FinancialRule):
    """Very high interest coverage ratio reflects negligible financial stress from debt servicing."""

    rule_id = "PRO_07"
    rule_type = TYPE_PRO
    name = "Strong Interest Coverage / Debt Free"
    description = "ICR > 10 OR Debt Free"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        de = context.latest.get("debt_to_equity")
        is_debt_free = False
        if de is not None:
            is_debt_free = de == 0.0 or (isinstance(de, (int, float)) and abs(de) < 1e-9)

        if is_debt_free:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                confidence_pct=95.0,
                reason="Debt-free (D/E = 0)",
            )

        icr = context.latest.get("interest_coverage")
        if icr is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="ICR unavailable and not debt-free",
            )

        if icr <= 10.0:
            triggered = False
            confidence = 0.0
            reason = f"ICR = {icr:.1f} (<=10)"
        else:
            triggered = True
            confidence = 60.0 + min((icr - 10.0) * 2.0, 35.0)
            confidence = min(max(confidence, 60.0), 95.0)
            reason = f"ICR = {icr:.1f}"

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=triggered,
            text="Very high interest coverage ratio reflects negligible financial stress from debt servicing" if triggered else "",
            confidence_pct=round(confidence, 2),
            reason=reason,
        )
class PRO_08(FinancialRule):
    """Consistent dividend yield above 2% backed by positive free cash flow."""

    rule_id = "PRO_08"
    rule_type = TYPE_PRO
    name = "Dividend Quality"
    description = "Dividend Yield > 2% AND FCF positive"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        div_yield = context.latest.get("dividend_yield")
        if div_yield is None:
            div_yield = context.trailing.get("dividend_yield")
        if div_yield is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="Dividend yield unavailable",
            )

        fcf = context.latest.get("free_cash_flow")
        if fcf is None:
            fcf_series = get_metric_history(context, "free_cash_flow")
            fcf = get_latest_value(fcf_series) if fcf_series else None

        cond_yield = div_yield is not None and div_yield > 2.0
        cond_fcf = fcf is not None and fcf > 0

        if not (cond_yield and cond_fcf):
            reasons = []
            if not cond_yield:
                reasons.append(f"dividend yield = {div_yield:.1f}% (<=2%)" if div_yield is not None else "dividend yield unavailable")
            if not cond_fcf:
                reasons.append("FCF not positive" if fcf is not None else "FCF unavailable")
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="; ".join(reasons),
            )

        confidence = 65.0 + min((div_yield - 2.0) * 5.0, 35.0)
        confidence = min(max(confidence, 65.0), 95.0)

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Consistent dividend yield above 2% backed by positive free cash flow",
            confidence_pct=round(confidence, 2),
            reason=f"Dividend yield = {div_yield:.1f}%, FCF positive",
        )


class PRO_09(FinancialRule):
    """Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding."""

    rule_id = "PRO_09"
    rule_type = TYPE_PRO
    name = "Strong EPS Growth"
    description = "EPS CAGR 5yr > 15%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        eps_cagr = context.trailing.get("eps_cagr")
        if eps_cagr is None:
            eps_cagr = context.latest.get("eps_cagr")
        if eps_cagr is None:
            eps_series = get_metric_history(context, "eps")
            if len(eps_series) >= 5:
                eps_cagr = calculate_cagr(eps_series[0], eps_series[-1], len(eps_series) - 1)
        if eps_cagr is None:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="EPS CAGR 5yr unavailable",
            )

        if eps_cagr <= 15.0:
            triggered = False
            confidence = 0.0
            reason = f"EPS CAGR 5yr = {eps_cagr:.1f}% (<=15%)"
        else:
            triggered = True
            confidence = 60.0 + (eps_cagr - 15.0) * 1.5
            confidence = min(max(confidence, 60.0), 95.0)
            reason = f"EPS CAGR 5yr = {eps_cagr:.1f}%"

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=triggered,
            text="Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding" if triggered else "",
            confidence_pct=round(confidence, 2),
            reason=reason,
        )


class PRO_10(FinancialRule):
    """Return on equity improving for 3 consecutive years shows strengthening business quality."""

    rule_id = "PRO_10"
    rule_type = TYPE_PRO
    name = "Improving ROE"
    description = "ROE improving for 3 consecutive years"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        roe_series = get_metric_history(context, "roe")
        if len(roe_series) < 4:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"Insufficient ROE history ({len(roe_series)} valid years, need >=4 for 3 YoY steps)",
            )

        improving = is_improving(roe_series, periods=4)
        if not improving:
            return RuleResult(
class PRO_11(FinancialRule):
    """Revenue growing slower than profits shows improving operating leverage and scale benefits.

    NOTE: The sprint specification condition is `Revenue CAGR > PAT CAGR`, but the
    supplied explanatory text describes the opposite scenario ('Revenue growing slower
    than profits'). These are contradictory. We implement the explicit condition
    (Revenue CAGR > PAT CAGR) as specified and document this contradiction.
    """

    rule_id = "PRO_11"
    rule_type = TYPE_PRO
    name = "Operating Leverage"
    description = "Revenue CAGR > PAT CAGR (spec contradicts text)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        rev_cagr = context.trailing.get("revenue_cagr")
        if rev_cagr is None:
            rev_cagr = context.latest.get("revenue_cagr")
        pat_cagr = context.trailing.get("profit_cagr")
        if pat_cagr is None:
            pat_cagr = context.latest.get("profit_cagr")

        if rev_cagr is None or pat_cagr is None:
            missing = []
            if rev_cagr is None:
                missing.append("Revenue CAGR")
            if pat_cagr is None:
                missing.append("PAT CAGR")
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"{', '.join(missing)} unavailable",
            )

        if rev_cagr <= pat_cagr:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"Revenue CAGR ({rev_cagr:.1f}%) <= PAT CAGR ({pat_cagr:.1f}%)",
            )

        gap = rev_cagr - pat_cagr
        confidence = 60.0 + min(gap * 3.0, 35.0)
        confidence = min(max(confidence, 60.0), 95.0)

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Revenue growing slower than profits shows improving operating leverage and scale benefits",
            confidence_pct=round(confidence, 2),
            reason=(
                f"Revenue CAGR ({rev_cagr:.1f}%) > PAT CAGR ({pat_cagr:.1f}%). "
                "SPEC CONTRADICTION: text describes 'revenue growing slower than profits' "
                "but condition checks Revenue CAGR > PAT CAGR."
            ),
        )


class PRO_12(FinancialRule):
    """Growing asset base funded by internal accruals reflects self-sustaining growth."""

    rule_id = "PRO_12"
    rule_type = TYPE_PRO
    name = "Asset Growth + Declining Debt"
    description = "Assets growing while borrowings decline"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        assets_series = get_metric_history(context, "total_assets")
        borrowings_series = get_metric_history(context, "borrowings")

        if len(assets_series) < 2 or len(borrowings_series) < 2:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"Insufficient history (assets={len(assets_series)}, borrowings={len(borrowings_series)}, need >=2 each)",
            )

        assets_increasing = is_improving(assets_series, periods=min(3, len(assets_series)))
        borrowings_declining = is_declining(borrowings_series, periods=min(3, len(borrowings_series)))

        if not (assets_increasing and borrowings_declining):
            reasons = []
            if not assets_increasing:
                reasons.append("total_assets not increasing")
            if not borrowings_declining:
                reasons.append("borrowings not declining")
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="; ".join(reasons),
            )

        assets_change = ((assets_series[-1] - assets_series[0]) / assets_series[0]) * 100.0 if assets_series[0] else 0
        borrowings_change = ((borrowings_series[-1] - borrowings_series[0]) / borrowings_series[0]) * 100.0 if borrowings_series[0] else 0
        confidence = 60.0 + min(abs(assets_change) * 1.5, 20.0) + min(abs(borrowings_change) * 1.5, 15.0)
        confidence = min(max(confidence, 60.0), 95.0)

# ---------------------------------------------------------------------------
# PRO RULE REGISTRY (Module 2B)
# ---------------------------------------------------------------------------

PRO_RULES_LIST = [
    PRO_01,
    PRO_02,
    PRO_03,
    PRO_04,
    PRO_05,
    PRO_06,
    PRO_07,
    PRO_08,
    PRO_09,
    PRO_10,
    PRO_11,
    PRO_12,
]


def get_pro_rule_instances() -> list:
    """Return instantiated Pro rules."""
    return [cls() for cls in PRO_RULES_LIST]

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Growing asset base funded by internal accruals reflects self-sustaining growth",
            confidence_pct=round(confidence, 2),
            reason=f"Assets growing ({assets_change:+.1f}%) and borrowings declining ({borrowings_change:+.1f}%)",
        )

                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason="ROE not improving for 3 consecutive years",
            )

        start_roe = roe_series[-4]
        end_roe = roe_series[-1]
        total_improvement = end_roe - start_roe
        confidence = 60.0 + min(total_improvement * 2.5, 35.0)
        confidence = min(max(confidence, 60.0), 95.0)

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Return on equity improving for 3 consecutive years shows strengthening business quality",
            confidence_pct=round(confidence, 2),
            reason=f"ROE improved from {start_roe:.1f}% to {end_roe:.1f}% over 3 consecutive years",
        )

            )

        if pat_cagr <= 20.0:
            triggered = False
            confidence = 0.0
            reason = f"PAT CAGR 5yr = {pat_cagr:.1f}% (<=20%)"
        else:
            triggered = True
            confidence = 60.0 + (pat_cagr - 20.0) * 1.5
            confidence = min(max(confidence, 60.0), 95.0)
            reason = f"PAT CAGR 5yr = {pat_cagr:.1f}%"

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=triggered,
            text="Net profit compounding at above 20% over 5 years creates significant shareholder value" if triggered else "",
            confidence_pct=round(confidence, 2),
            reason=reason,
        )

                reason="Latest D/E unavailable",
            )

        is_debt_free = de == 0.0 or (isinstance(de, (int, float)) and abs(de) < 1e-9)

        if not is_debt_free:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"D/E = {de:.4f} (not debt-free)",
            )

        confidence = 95.0
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Debt-free balance sheet provides financial flexibility and eliminates interest burden",
            confidence_pct=confidence,
            reason=f"D/E = {de:.4f} (debt-free)",
        )

                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=False,
                text="",
                confidence_pct=0.0,
                reason=f"ROE > 20% for only {max_run} consecutive year(s) (need >=3)",
            )

        recent = [v for v in roe_series if v is not None and v > 20.0][-max_run:]
        avg_roe = sum(recent) / len(recent)
        above_threshold = avg_roe - 20.0
        confidence = 60.0 + (min(max_run - 3, 5) * 5.0) + min(above_threshold * 2.0, 35.0)
        confidence = min(max(confidence, 60.0), 95.0)

        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text="Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
            confidence_pct=round(confidence, 2),
            reason=f"ROE > 20% for {max_run} consecutive years; avg ROE={avg_roe:.1f}%",
        )
