"""
pro_rules.py

Sprint 5 - Module 2B: 12 Pro Rules (PRO_01 - PRO_12) for the Auto Pros/Cons
Generator.

Every rule is a :class:`FinancialRule` subclass that receives the normalized
per-company :class:`CompanyContext` produced by the Module 2A foundation and
returns a :class:`RuleResult`. Rules only consume the prepared context -- they
never re-load the database, never fabricate values, never coerce missing data to
zero, and never crash on malformed inputs.

Confidence values are deterministic, always within ``[0, 100]``, and reflect
signal strength (streak length, margin above threshold, CAGR magnitude, etc.).

Specification conflict (PRO_11)
-------------------------------
The sprint specification states the operating-leverage condition as
``Revenue CAGR > PAT CAGR``, but the supplied explanatory text reads
"Revenue growing slower than profits shows improving operating leverage and
scale benefits", which describes the opposite inequality. Per the Module 2B
instructions we implement the *explicit condition* (``Revenue CAGR > PAT
CAGR``), keep the *exact supplied text*, and document the contradiction (also
flagged inside the rule's reason field). The business rule is not "fixed"
without explicit approval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.nlp.pros_cons_generator import (
    FinancialRule,
    RuleResult,
    TYPE_PRO,
    calculate_cagr,
    get_latest_value,
    get_metric_history,
    is_declining,
    is_improving,
    safe_float,
)

# =============================================================================
# COMMON THRESHOLDS
# =============================================================================

PRO_01_ROE_MIN: float = 20.0  # ROE > 20% for >= 3 consecutive years
PRO_01_REQUIRED_YEARS: int = 3

PRO_02_REQUIRED_YEARS: int = 5  # FCF > 0 for >= 5 consecutive years

PRO_04_REV_CAGR_MIN: float = 15.0  # Revenue CAGR 5yr > 15%
PRO_05_OPM_MIN: float = 25.0  # Latest OPM > 25%
PRO_06_PAT_CAGR_MIN: float = 20.0  # PAT CAGR 5yr > 20%
PRO_07_ICR_MIN: float = 10.0  # ICR > 10 (or debt-free)
PRO_08_YIELD_MIN: float = 2.0  # Dividend yield > 2%
PRO_09_EPS_CAGR_MIN: float = 15.0  # EPS CAGR 5yr > 15%
PRO_10_IMPROVING_VALUES: int = 4  # 3 consecutive YoY improvements
PRO_12_TREND_PERIODS: int = 3  # project trend convention window

# Very-small floating-point tolerance used to treat a D/E value as zero.
DE_ZERO_EPSILON: float = 1e-9

# Confidence scale used by strong, near-binary balance-sheet signals.
CONF_DEBT_FREE: float = 90.0

# ---------------------------------------------------------------------------
# Local helpers (deterministic confidence + defensive result builders)
# ---------------------------------------------------------------------------


def _clamp_conf(value: Any) -> float:
    """Round a confidence score and clamp it into ``[0, 100]``."""
    val = safe_float(value)
    if val is None:
        return 0.0
    return round(min(max(val, 0.0), 100.0), 2)


def _company_id(context: Any) -> str:
    """Safely read ``company_id`` from a context-like object."""
    return str(getattr(context, "company_id", "") or "UNKNOWN")


def _latest_of(context: Any) -> Dict[str, Any]:
    """Return the ``latest`` metric dict (or an empty dict when absent)."""
    data = getattr(context, "latest", None)
    return data if isinstance(data, dict) else {}


def _trailing_of(context: Any) -> Dict[str, Any]:
    """Return the ``trailing`` metric dict (or an empty dict when absent)."""
    data = getattr(context, "trailing", None)
    return data if isinstance(data, dict) else {}


def _untriggered(rule: FinancialRule, context: Any, reason: str) -> RuleResult:
    """Build a standard ``triggered=False`` result safe for missing companies."""
    return RuleResult(
        company_id=_company_id(context),
        rule_id=rule.rule_id,
        rule_type=rule.rule_type,
        triggered=False,
        text="",
        confidence_pct=0.0,
        reason=reason,
    )


def _longest_consecutive_run(
    context: Any, metric: str, predicate: Any
) -> Tuple[int, List[float]]:
    """Return ``(run_length, run_values)`` for the longest year-consecutive run.

    Uses the raw (year-aligned) history so a missing or non-finite year does not
    silently pass: a year whose value is missing/NaN breaks the streak, mirroring
    the requirement that missing years are never counted as passing. Successive
    valid years must also be consecutive calendar years.
    """
    years = list(getattr(context, "history_years", None) or [])
    raw = getattr(context, "history", None) or {}
    values = raw.get(metric, [])
    n = min(len(years), len(values))
    best_len = 0
    best_run: List[float] = []
    current: List[float] = []
    prev_year: Optional[int] = None
    for i in range(n):
        year = years[i]
        number = safe_float(values[i])
        ok = number is not None and bool(predicate(number))
        adjacent = prev_year is None or (year - prev_year == 1)
        if ok and adjacent:
            current.append(float(number))
            prev_year = year
        else:
            current = [float(number)] if ok else []
            prev_year = year if ok else None
        if len(current) > best_len:
            best_len = len(current)
            best_run = list(current)
    return best_len, best_run


def _cagr_for_history(series: Sequence[Any], min_points: int) -> Optional[float]:
    """Compute a fallback CAGR (percent) from a historical value series."""
    if len(series) < min_points:
        return None
    years = max(1, len(series) - 1)
    return calculate_cagr(series[0], series[-1], years)


# =============================================================================
# PRO_01 - Sustained High ROE
# =============================================================================


class PRO_01(FinancialRule):
    """ROE > 20%% for at least 3 consecutive valid financial years."""

    rule_id = "PRO_01"
    rule_type = TYPE_PRO
    name = "Sustained High ROE"
    description = "ROE > 20%% for at least 3 consecutive years"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        roe_series = get_metric_history(context, "roe")
        if len(roe_series) < PRO_01_REQUIRED_YEARS:
            return _untriggered(
                self,
                context,
                f"Insufficient ROE history ({len(roe_series)} valid years, "
                f"need >= {PRO_01_REQUIRED_YEARS})",
            )
        run_len, run_values = _longest_consecutive_run(
            context, "roe", lambda v: v > PRO_01_ROE_MIN
        )
        if run_len < PRO_01_REQUIRED_YEARS:
            return _untriggered(
                self,
                context,
                f"ROE > 20% for only {run_len} consecutive year(s) "
                f"(need >= {PRO_01_REQUIRED_YEARS})",
            )
        avg_roe = sum(run_values) / len(run_values)
        margin = avg_roe - PRO_01_ROE_MIN
        conf = 60.0 + min((run_len - 3) * 4.0, 20.0) + min(margin * 2.0, 15.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Consistently high return on equity above 20% demonstrates "
                "exceptional capital efficiency"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=(
                f"ROE > 20% for {run_len} consecutive years; " f"avg ROE={avg_roe:.1f}%"
            ),
        )


# =============================================================================
# PRO_02 - Sustained Positive FCF
# =============================================================================


class PRO_02(FinancialRule):
    """FCF > 0 for at least 5 consecutive valid financial years."""

    rule_id = "PRO_02"
    rule_type = TYPE_PRO
    name = "Sustained Positive FCF"
    description = "FCF > 0 for at least 5 consecutive years"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        fcf_series = get_metric_history(context, "free_cash_flow")
        if not fcf_series:
            return _untriggered(self, context, "No FCF history available")
        run_len, run_values = _longest_consecutive_run(
            context, "free_cash_flow", lambda v: v > 0
        )
        if run_len < PRO_02_REQUIRED_YEARS:
            return _untriggered(
                self,
                context,
                f"Positive FCF for only {run_len} consecutive year(s) "
                f"(need >= {PRO_02_REQUIRED_YEARS})",
            )
        conf = 60.0 + min((run_len - 5) * 4.0, 20.0)
        avg_fcf = sum(run_values) / len(run_values)
        latest_revenue = safe_float(_latest_of(context).get("revenue"))
        if latest_revenue is not None and latest_revenue > 0:
            margin = (avg_fcf / latest_revenue) * 100.0
            conf += min(margin * 1.5, 15.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Strong free cash flow generation over 5 years signals "
                "healthy business fundamentals"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=(
                f"Positive FCF for {run_len} consecutive years; "
                f"avg FCF={avg_fcf:,.0f}"
            ),
        )


# =============================================================================
# PRO_03 - Debt Free
# =============================================================================


class PRO_03(FinancialRule):
    """Latest-year D/E equals zero (incl. 0.0 / very small floats)."""

    rule_id = "PRO_03"
    rule_type = TYPE_PRO
    name = "Debt Free"
    description = "Latest D/E = 0 (missing D/E is not treated as debt-free)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        latest_dict = _latest_of(context)
        de = latest_dict.get("debt_to_equity")
        if de is None:
            return _untriggered(
                self, context, "Latest D/E unavailable (not treated as debt-free)"
            )
        is_debt_free = (
            de == 0
            or de == 0.0
            or (isinstance(de, (int, float)) and abs(float(de)) < DE_ZERO_EPSILON)
        )
        if not is_debt_free:
            return _untriggered(
                self,
                context,
                f"D/E = {float(de):.4f} (not debt-free)",
            )
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Debt-free balance sheet provides financial flexibility and "
                "eliminates interest burden"
            ),
            confidence_pct=CONF_DEBT_FREE,
            reason=f"D/E = {float(de):.6f} (debt-free)",
        )


# =============================================================================
# PRO_04 - Strong Revenue Growth
# =============================================================================


class PRO_04(FinancialRule):
    """Revenue CAGR (5yr) above 15%%."""

    rule_id = "PRO_04"
    rule_type = TYPE_PRO
    name = "Strong Revenue Growth"
    description = "Revenue CAGR 5yr > 15%%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        rev_cagr = safe_float(_trailing_of(context).get("revenue_cagr"))
        if rev_cagr is None:
            rev_cagr = safe_float(_latest_of(context).get("revenue_cagr"))
        if rev_cagr is None:
            rev_cagr = _cagr_for_history(
                get_metric_history(context, "revenue"), min_points=5
            )
        if rev_cagr is None:
            return _untriggered(self, context, "Revenue CAGR 5yr unavailable")
        if rev_cagr <= PRO_04_REV_CAGR_MIN:
            return _untriggered(
                self,
                context,
                f"Revenue CAGR 5yr = {rev_cagr:.1f}% (<= 15%)",
            )
        conf = 60.0 + min((rev_cagr - PRO_04_REV_CAGR_MIN) * 1.5, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Revenue growing at above 15% CAGR over 5 years reflects "
                "strong business momentum"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=f"Revenue CAGR 5yr = {rev_cagr:.1f}%",
        )


# =============================================================================
# PRO_05 - Strong Operating Margin
# =============================================================================


class PRO_05(FinancialRule):
    """Latest-year OPM above 25%% (OPM, not NPM/ROE/ROCE)."""

    rule_id = "PRO_05"
    rule_type = TYPE_PRO
    name = "Strong Operating Margin"
    description = "Latest OPM > 25%%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        latest_dict = _latest_of(context)
        opm = safe_float(latest_dict.get("opm"))
        if opm is None:
            rev = safe_float(latest_dict.get("revenue"))
            op_profit = safe_float(latest_dict.get("operating_profit"))
            if rev is not None and rev > 0 and op_profit is not None:
                opm = (op_profit / rev) * 100.0
        if opm is None:
            return _untriggered(self, context, "OPM unavailable")
        if opm <= PRO_05_OPM_MIN:
            return _untriggered(
                self,
                context,
                f"OPM = {opm:.1f}% (<= 25%)",
            )
        conf = 60.0 + min((opm - PRO_05_OPM_MIN) * 1.2, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Operating profit margin above 25% indicates strong pricing "
                "power and cost discipline"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=f"OPM = {opm:.1f}%",
        )


# =============================================================================
# PRO_06 - Strong PAT Growth
# =============================================================================


class PRO_06(FinancialRule):
    """Net-profit (PAT) CAGR 5yr above 20%%."""

    rule_id = "PRO_06"
    rule_type = TYPE_PRO
    name = "Strong PAT Growth"
    description = "PAT CAGR 5yr > 20%%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        pat_cagr = safe_float(_trailing_of(context).get("profit_cagr"))
        if pat_cagr is None:
            pat_cagr = safe_float(_latest_of(context).get("profit_cagr"))
        if pat_cagr is None:
            pat_cagr = _cagr_for_history(
                get_metric_history(context, "net_profit"), min_points=5
            )
        if pat_cagr is None:
            return _untriggered(self, context, "PAT CAGR 5yr unavailable")
        if pat_cagr <= PRO_06_PAT_CAGR_MIN:
            return _untriggered(
                self,
                context,
                f"PAT CAGR 5yr = {pat_cagr:.1f}% (<= 20%)",
            )
        conf = 60.0 + min((pat_cagr - PRO_06_PAT_CAGR_MIN) * 1.5, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Net profit compounding at above 20% over 5 years creates "
                "significant shareholder value"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=f"PAT CAGR 5yr = {pat_cagr:.1f}%",
        )


# =============================================================================
# PRO_07 - Strong Interest Coverage / Debt Free
# =============================================================================


class PRO_07(FinancialRule):
    """ICR > 10 OR debt-free. Missing ICR / D/E is never treated as a pass."""

    rule_id = "PRO_07"
    rule_type = TYPE_PRO
    name = "Strong Interest Coverage / Debt Free"
    description = "ICR > 10 OR Debt Free (missing values never pass)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        latest_dict = _latest_of(context)

        de = latest_dict.get("debt_to_equity")
        is_debt_free = False
        if de is not None:
            is_debt_free = (
                de == 0
                or de == 0.0
                or (isinstance(de, (int, float)) and abs(float(de)) < DE_ZERO_EPSILON)
            )
        if is_debt_free:
            return RuleResult(
                company_id=context.company_id,
                rule_id=self.rule_id,
                rule_type=self.rule_type,
                triggered=True,
                text=(
                    "Very high interest coverage ratio reflects negligible "
                    "financial stress from debt servicing"
                ),
                confidence_pct=CONF_DEBT_FREE,
                reason="Debt-free (D/E = 0)",
            )

        icr = safe_float(latest_dict.get("interest_coverage"))
        if icr is None:
            return _untriggered(
                self,
                context,
                "ICR unavailable and company is not debt-free",
            )
        if icr <= PRO_07_ICR_MIN:
            return _untriggered(
                self,
                context,
                f"ICR = {icr:.1f} (<= 10) and not debt-free",
            )
        conf = 60.0 + min((icr - PRO_07_ICR_MIN) * 1.2, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Very high interest coverage ratio reflects negligible "
                "financial stress from debt servicing"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=f"ICR = {icr:.1f} (> 10)",
        )


# =============================================================================
# PRO_08 - Dividend Quality
# =============================================================================


class PRO_08(FinancialRule):
    """Dividend yield > 2%% AND positive free cash flow (both required)."""

    rule_id = "PRO_08"
    rule_type = TYPE_PRO
    name = "Dividend Quality"
    description = "Dividend Yield > 2% AND FCF positive"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        latest_dict = _latest_of(context)
        div_yield = safe_float(_trailing_of(context).get("dividend_yield"))
        if div_yield is None:
            div_yield = safe_float(latest_dict.get("dividend_yield"))

        if div_yield is None:
            return _untriggered(self, context, "Dividend yield unavailable")

        fcf = safe_float(latest_dict.get("free_cash_flow"))
        if fcf is None:
            fcf_series = get_metric_history(context, "free_cash_flow")
            fcf = get_latest_value(fcf_series) if fcf_series else None

        cond_yield = div_yield > PRO_08_YIELD_MIN
        cond_fcf = fcf is not None and fcf > 0
        if not (cond_yield and cond_fcf):
            reasons: List[str] = []
            if not cond_yield:
                reasons.append(f"dividend yield = {div_yield:.1f}% (<= 2%)")
            if not cond_fcf:
                reasons.append(
                    "FCF not positive" if fcf is not None else "FCF unavailable"
                )
            return _untriggered(self, context, "; ".join(reasons))
        conf = 65.0 + min((div_yield - PRO_08_YIELD_MIN) * 5.0, 30.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Consistent dividend yield above 2% backed by positive free "
                "cash flow"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=f"Dividend yield = {div_yield:.1f}%, FCF positive",
        )


# =============================================================================
# PRO_09 - Strong EPS Growth
# =============================================================================


class PRO_09(FinancialRule):
    """EPS CAGR (5yr) above 15%%."""

    rule_id = "PRO_09"
    rule_type = TYPE_PRO
    name = "Strong EPS Growth"
    description = "EPS CAGR 5yr > 15%%"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        eps_cagr = safe_float(_trailing_of(context).get("eps_cagr"))
        if eps_cagr is None:
            eps_cagr = safe_float(_latest_of(context).get("eps_cagr"))
        if eps_cagr is None:
            eps_cagr = _cagr_for_history(
                get_metric_history(context, "eps"), min_points=5
            )
        if eps_cagr is None:
            return _untriggered(self, context, "EPS CAGR 5yr unavailable")
        if eps_cagr <= PRO_09_EPS_CAGR_MIN:
            return _untriggered(
                self,
                context,
                f"EPS CAGR 5yr = {eps_cagr:.1f}% (<= 15%)",
            )
        conf = 60.0 + min((eps_cagr - PRO_09_EPS_CAGR_MIN) * 1.5, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Earnings per share growing above 15% CAGR indicates strong "
                "earnings quality and compounding"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=f"EPS CAGR 5yr = {eps_cagr:.1f}%",
        )


# =============================================================================
# PRO_10 - Improving ROE
# =============================================================================


class PRO_10(FinancialRule):
    """ROE improving for 3 consecutive years (3 YoY improvements)."""

    rule_id = "PRO_10"
    rule_type = TYPE_PRO
    name = "Improving ROE"
    description = "ROE improving for 3 consecutive YoY steps (4 values)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        roe_series = get_metric_history(context, "roe")
        if len(roe_series) < PRO_10_IMPROVING_VALUES:
            return _untriggered(
                self,
                context,
                f"Insufficient ROE history ({len(roe_series)} valid years, "
                f"need >= {PRO_10_IMPROVING_VALUES} for 3 YoY steps)",
            )
        improving = is_improving(roe_series, periods=PRO_10_IMPROVING_VALUES)
        if not improving:
            return _untriggered(
                self,
                context,
                "ROE not improving for 3 consecutive years",
            )
        start_roe = roe_series[-PRO_10_IMPROVING_VALUES]
        end_roe = roe_series[-1]
        total_improvement = end_roe - start_roe
        conf = 60.0 + min(total_improvement * 2.0, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Return on equity improving for 3 consecutive years shows "
                "strengthening business quality"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=(
                f"ROE improved from {start_roe:.1f}% to {end_roe:.1f}% "
                f"over 3 consecutive YoY steps"
            ),
        )


# =============================================================================
# PRO_11 - Operating Leverage
#
# SPECIFICATION CONFLICT (documented, not silently "fixed"):
#   - Condition (explicit): Revenue CAGR > PAT CAGR
#   - Supplied text:        "Revenue growing slower than profits shows
#                            improving operating leverage and scale benefits"
# These are mathematically contradictory. We implement the explicit condition
# and keep the exact supplied text. The contradiction is flagged here and in
# the rule's reason field.
# =============================================================================


class PRO_11(FinancialRule):
    """Operating leverage: Revenue CAGR > PAT CAGR (see module docstring)."""

    rule_id = "PRO_11"
    rule_type = TYPE_PRO
    name = "Operating Leverage"
    description = "Revenue CAGR > PAT CAGR (text contradicts the condition)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        rev_cagr = safe_float(_trailing_of(context).get("revenue_cagr"))
        if rev_cagr is None:
            rev_cagr = safe_float(_latest_of(context).get("revenue_cagr"))
        pat_cagr = safe_float(_trailing_of(context).get("profit_cagr"))
        if pat_cagr is None:
            pat_cagr = safe_float(_latest_of(context).get("profit_cagr"))
        if rev_cagr is None or pat_cagr is None:
            missing = [
                m
                for m, v in (("Revenue CAGR", rev_cagr), ("PAT CAGR", pat_cagr))
                if v is None
            ]
            return _untriggered(self, context, f"{', '.join(missing)} unavailable")
        if rev_cagr <= pat_cagr:
            return _untriggered(
                self,
                context,
                f"Revenue CAGR ({rev_cagr:.1f}%) <= PAT CAGR ({pat_cagr:.1f}%)",
            )
        gap = rev_cagr - pat_cagr
        conf = 60.0 + min(gap * 3.0, 35.0)
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Revenue growing slower than profits shows improving "
                "operating leverage and scale benefits"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=(
                f"Revenue CAGR ({rev_cagr:.1f}%) > PAT CAGR ({pat_cagr:.1f}%). "
                "SPEC CONTRADICTION: 'Revenue growing slower than profits' "
                "(text) conflicts with condition Revenue CAGR > PAT CAGR."
            ),
        )


# =============================================================================
# PRO_12 - Asset Growth + Declining Debt
# =============================================================================


class PRO_12(FinancialRule):
    """Balance-sheet assets growing while borrowings decline (trend window)."""

    rule_id = "PRO_12"
    rule_type = TYPE_PRO
    name = "Asset Growth + Declining Debt"
    description = "Assets increasing while borrowings decline (>= 3 years)"

    def evaluate(self, context: Any, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate functionality."""
        if context is None:
            return _untriggered(self, None, "No company context")
        assets_series = get_metric_history(context, "total_assets")
        borrowings_series = get_metric_history(context, "borrowings")
        if (
            len(assets_series) < PRO_12_TREND_PERIODS
            or len(borrowings_series) < PRO_12_TREND_PERIODS
        ):
            return _untriggered(
                self,
                context,
                f"Insufficient history (assets={len(assets_series)}, "
                f"borrowings={len(borrowings_series)}, need >= "
                f"{PRO_12_TREND_PERIODS} each)",
            )
        assets_increasing = is_improving(assets_series, periods=PRO_12_TREND_PERIODS)
        borrowings_declining = is_declining(
            borrowings_series, periods=PRO_12_TREND_PERIODS
        )
        if not (assets_increasing and borrowings_declining):
            reasons: List[str] = []
            if not assets_increasing:
                reasons.append("total_assets not increasing")
            if not borrowings_declining:
                reasons.append("borrowings not declining")
            return _untriggered(self, context, "; ".join(reasons))

        a0 = assets_series[-PRO_12_TREND_PERIODS]
        a1 = assets_series[-1]
        b0 = borrowings_series[-PRO_12_TREND_PERIODS]
        b1 = borrowings_series[-1]
        assets_change = ((a1 - a0) / a0) * 100.0 if a0 else 0.0
        borrowings_change = ((b1 - b0) / b0) * 100.0 if b0 else -100.0
        conf = (
            60.0
            + min(max(assets_change, 0.0) * 0.8, 20.0)
            + min(max(-borrowings_change, 0.0) * 0.8, 15.0)
        )
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            text=(
                "Growing asset base funded by internal accruals reflects "
                "self-sustaining growth"
            ),
            confidence_pct=_clamp_conf(conf),
            reason=(
                f"Assets growing ({assets_change:+.1f}%) and borrowings "
                f"declining ({borrowings_change:+.1f}%)"
            ),
        )


# =============================================================================
# PRO RULE REGISTRY (Module 2B)
# =============================================================================

PRO_RULES_LIST: List[Any] = [
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


def get_pro_rule_instances() -> List[FinancialRule]:
    """Return one instantiated rule for each of the 12 Pro rules."""
    return [cls() for cls in PRO_RULES_LIST]


# ---------------------------------------------------------------------------
# Idempotent registration into the shared pros_cons_generator registry.
#
# The foundation module already attempts this registration at import time, but
# that hook can be skipped when `pro_rules` is imported FIRST (circular-import
# guard). Registering here guarantees the shared PRO_RULES registry is populated
# regardless of import order. register_pro_rule() ignores duplicates.
# ---------------------------------------------------------------------------
def _register_into_shared_registry() -> None:
    from src.nlp.pros_cons_generator import register_pro_rule  # noqa: PLC0415

    for _rule in get_pro_rule_instances():
        register_pro_rule(_rule)


_register_into_shared_registry()
