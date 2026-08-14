"""
con_rules.py

Sprint 5 - Module 2C: 12 Con Rules (CON_01 - CON_12) for the Auto Pros/Cons
Generator.

Each rule is a FinancialRule subclass that evaluates a company's financial
health based on its CompanyContext, returning a RuleResult. These rules
identify potential financial weaknesses or risks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.nlp.pros_cons_generator import (
    FinancialRule,
    RuleResult,
    TYPE_CON,
    get_metric_history,
    is_declining,
    is_improving,
    safe_divide,
    safe_float,
    check_consecutive_condition,
)

# =============================================================================
# HELPERS
# =============================================================================

def _clamp_conf(value: Any) -> float:
    """Round a confidence score and clamp it into [0, 100]."""
    val = safe_float(value)
    if val is None:
        return 0.0
    return round(min(max(val, 0.0), 100.0), 2)

def _untriggered(rule: FinancialRule, context: Any, reason: str) -> RuleResult:
    """Build a standard triggered=False result."""
    return RuleResult(
        company_id=getattr(context, "company_id", "UNKNOWN"),
        rule_id=rule.rule_id,
        rule_type=rule.rule_type,
        triggered=False,
        text="",
        confidence_pct=0.0,
        reason=reason,
    )

def _latest_of(context: Any) -> Dict[str, Any]:
    """Return the `latest` metric dict (or an empty dict when absent)."""
    data = getattr(context, "latest", None)
    return data if isinstance(data, dict) else {}

def _trailing_of(context: Any) -> Dict[str, Any]:
    """Return the `trailing` metric dict (or an empty dict when absent)."""
    data = getattr(context, "trailing", None)
    return data if isinstance(data, dict) else {}

# =============================================================================
# CON RULES (CON_01 - CON_12)
# =============================================================================

class CON_01(FinancialRule):
    """CON_01: D/E > 2.0 AND NOT Financials."""
    rule_id = "CON_01"
    rule_type = TYPE_CON
    name = "High Debt-to-Equity"
    description = "D/E > 2.0 for non-financial companies"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        if getattr(context, "is_financial", True):
            return _untriggered(self, context, "Company is in a financial sector.")
        
        de = safe_float(_latest_of(context).get("debt_to_equity"))
        if de is None:
            return _untriggered(self, context, "Latest D/E is unavailable.")
        
        if de > 2.0:
            conf = 60.0 + min((de - 2.0) * 10.0, 35.0)
            de_str = f"{de:.2f}"
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text=f"Debt-to-equity ratio of {de_str} is elevated for a non-financial company and warrants monitoring",
                confidence_pct=_clamp_conf(conf),
                reason=f"D/E = {de_str} (> 2.0)",
            )
        return _untriggered(self, context, f"D/E = {de:.2f} (<= 2.0)")

class CON_02(FinancialRule):
    """CON_02: FCF negative for 3 consecutive years."""
    rule_id = "CON_02"
    rule_type = TYPE_CON
    name = "Sustained Negative FCF"
    description = "FCF < 0 for at least 3 consecutive years"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        history = list(getattr(context, "history", {}).get("free_cash_flow", []))
        if len(history) < 3:
            return _untriggered(self, context, f"Insufficient FCF history ({len(history)} years).")

        if check_consecutive_condition(history, lambda v: v < 0, required=3):
            conf = 65.0
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                confidence_pct=_clamp_conf(conf),
                reason="FCF < 0 for 3+ consecutive years.",
            )
        return _untriggered(self, context, "No 3-year consecutive negative FCF streak.")

class CON_03(FinancialRule):
    """CON_03: OPM declining for 3 consecutive years."""
    rule_id = "CON_03"
    rule_type = TYPE_CON
    name = "Declining OPM"
    description = "OPM declining for 3 consecutive YoY steps (4 values)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        history = list(getattr(context, "history", {}).get("opm", []))
        if len(history) < 4:
            return _untriggered(self, context, f"Insufficient OPM history ({len(history)} years).")

        if is_declining(history, periods=4):
            conf = 70.0
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                confidence_pct=_clamp_conf(conf),
                reason="OPM declining for 3 consecutive years.",
            )
        return _untriggered(self, context, "No 3-year consecutive OPM decline.")

class CON_04(FinancialRule):
    """CON_04: Latest-year Net Profit < 0."""
    rule_id = "CON_04"
    rule_type = TYPE_CON
    name = "Net Loss"
    description = "Latest-year Net Profit < 0"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        net_profit = safe_float(_latest_of(context).get("net_profit"))
        if net_profit is None:
            return _untriggered(self, context, "Latest net profit unavailable.")
        
        if net_profit < 0:
            conf = 75.0
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Company reported a net loss in the most recent financial year",
                confidence_pct=_clamp_conf(conf),
                reason=f"Latest Net Profit = {net_profit:,.0f} (< 0)",
            )
        return _untriggered(self, context, f"Latest Net Profit = {net_profit:,.0f} (>= 0)")

class CON_05(FinancialRule):
    """CON_05: Revenue declining for 2+ consecutive years."""
    rule_id = "CON_05"
    rule_type = TYPE_CON
    name = "Revenue Decline"
    description = "Revenue declining for 2+ consecutive years (3 values)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        history = get_metric_history(context, "revenue")
        if len(history) < 3:
            return _untriggered(self, context, f"Insufficient revenue history ({len(history)} years).")

        if is_declining(history, periods=3):
            conf = 68.0
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                confidence_pct=_clamp_conf(conf),
                reason="Revenue declining for 2+ consecutive years.",
            )
        return _untriggered(self, context, "No 2-year consecutive revenue decline.")

class CON_06(FinancialRule):
    """CON_06: ICR < 1.5."""
    rule_id = "CON_06"
    rule_type = TYPE_CON
    name = "Low Interest Coverage"
    description = "Latest ICR < 1.5"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        icr = safe_float(_latest_of(context).get("interest_coverage"))
        if icr is None:
            return _untriggered(self, context, "Latest ICR unavailable.")
        
        if icr < 1.5:
            conf = 60.0 + min((1.5 - icr) * 20.0, 35.0)
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                confidence_pct=_clamp_conf(conf),
                reason=f"ICR = {icr:.2f} (< 1.5)",
            )
        return _untriggered(self, context, f"ICR = {icr:.2f} (>= 1.5)")

class CON_07(FinancialRule):
    """CON_07: Dividend payout > 100%."""
    rule_id = "CON_07"
    rule_type = TYPE_CON
    name = "Excessive Dividend Payout"
    description = "Latest dividend payout > 100%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        payout = safe_float(_latest_of(context).get("dividend_payout"))
        if payout is None:
            return _untriggered(self, context, "Latest dividend payout unavailable.")
        
        if payout > 100.0:
            conf = 60.0 + min((payout - 100.0) * 0.5, 35.0)
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                confidence_pct=_clamp_conf(conf),
                reason=f"Dividend Payout = {payout:.1f}% (> 100%)",
            )
        return _untriggered(self, context, f"Dividend Payout = {payout:.1f}% (<= 100%)")

class CON_08(FinancialRule):
    """CON_08: D/E rising for 3 consecutive years."""
    rule_id = "CON_08"
    rule_type = TYPE_CON
    name = "Rising D/E"
    description = "D/E rising for 3 consecutive YoY steps (4 values)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        history = get_metric_history(context, "debt_to_equity")
        if len(history) < 4:
            return _untriggered(self, context, f"Insufficient D/E history ({len(history)} years).")

        if is_improving(history, periods=4): # is_improving means strictly increasing
            conf = 72.0
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                confidence_pct=_clamp_conf(conf),
                reason="D/E rising for 3 consecutive years.",
            )
        return _untriggered(self, context, "No 3-year consecutive D/E rise.")

class CON_09(FinancialRule):
    """CON_09: EPS declining for 3 consecutive years."""
    rule_id = "CON_09"
    rule_type = TYPE_CON
    name = "Declining EPS"
    description = "EPS declining for 3 consecutive YoY steps (4 values)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        history = get_metric_history(context, "eps")
        if len(history) < 4:
            return _untriggered(self, context, f"Insufficient EPS history ({len(history)} years).")

        if is_declining(history, periods=4):
            conf = 70.0
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                confidence_pct=_clamp_conf(conf),
                reason="EPS declining for 3 consecutive years.",
            )
        return _untriggered(self, context, "No 3-year consecutive EPS decline.")

class CON_10(FinancialRule):
    """CON_10: ROCE < 10%."""
    rule_id = "CON_10"
    rule_type = TYPE_CON
    name = "Low ROCE"
    description = "Latest ROCE < 10%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        roce = safe_float(_latest_of(context).get("roce"))
        if roce is None:
            return _untriggered(self, context, "Latest ROCE unavailable.")
        
        if roce < 10.0:
            conf = 60.0 + min((10.0 - roce) * 2.0, 35.0)
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                confidence_pct=_clamp_conf(conf),
                reason=f"ROCE = {roce:.1f}% (< 10%)",
            )
        return _untriggered(self, context, f"ROCE = {roce:.1f}% (>= 10%)")

class CON_11(FinancialRule):
    """CON_11: Net Debt > 3 x EBITDA."""
    rule_id = "CON_11"
    rule_type = TYPE_CON
    name = "High Net Debt / EBITDA"
    description = "Net Debt > 3 x EBITDA"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        latest = _latest_of(context)
        net_debt = safe_float(latest.get("net_debt"))
        ebitda = safe_float(latest.get("ebitda"))

        if net_debt is None or ebitda is None:
            return _untriggered(self, context, "Net Debt or EBITDA unavailable.")
        
        if ebitda <= 0:
            return _untriggered(self, context, f"EBITDA is not positive ({ebitda:,.0f}).")

        ratio = safe_divide(net_debt, ebitda)
        if ratio is None:
             return _untriggered(self, context, "Could not calculate Net Debt / EBITDA ratio.")

        if ratio > 3.0:
            conf = 60.0 + min((ratio - 3.0) * 5.0, 35.0)
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                confidence_pct=_clamp_conf(conf),
                reason=f"Net Debt/EBITDA = {ratio:.2f}x (> 3x)",
            )
        return _untriggered(self, context, f"Net Debt/EBITDA = {ratio:.2f}x (<= 3x)")

class CON_12(FinancialRule):
    """CON_12: Revenue CAGR < 5% over 5 years."""
    rule_id = "CON_12"
    rule_type = TYPE_CON
    name = "Low Revenue Growth"
    description = "Revenue CAGR 5yr < 5%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        cagr = safe_float(_trailing_of(context).get("revenue_cagr"))
        if cagr is None:
            return _untriggered(self, context, "5-year Revenue CAGR unavailable.")
        
        if cagr < 5.0:
            conf = 60.0 + min((5.0 - cagr) * 3.0, 35.0)
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text="Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                confidence_pct=_clamp_conf(conf),
                reason=f"Revenue CAGR 5yr = {cagr:.1f}% (< 5%)",
            )
        return _untriggered(self, context, f"Revenue CAGR 5yr = {cagr:.1f}% (>= 5%)")


CON_RULES_LIST: List[Any] = [
    CON_01, CON_02, CON_03, CON_04, CON_05, CON_06,
    CON_07, CON_08, CON_09, CON_10, CON_11, CON_12,
]

def get_con_rule_instances() -> List[FinancialRule]:
    """Return one instantiated rule for each of the 12 Con rules."""
    return [cls() for cls in CON_RULES_LIST]

def _register_into_shared_registry() -> None:
    from src.nlp.pros_cons_generator import register_con_rule

    for _rule in get_con_rule_instances():
        register_con_rule(_rule)

_register_into_shared_registry()