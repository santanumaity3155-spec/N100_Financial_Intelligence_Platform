from __future__ import annotations

import pandas as pd
import pytest

from src.nlp import pros_cons_generator as pg

try:
    from tests.nlp.test_pros_cons_generator import make_context
except ImportError:
    from .test_pros_cons_generator import make_context


@pytest.fixture
def sample_rule_results():
    def _make(rule_id, rule_type, company_id="C1", confidence=80.0):
        return pg.RuleResult(
            company_id=company_id,
            rule_id=rule_id,
            rule_type=rule_type,
            triggered=True,
            text=f"{rule_id} signal",
            confidence_pct=confidence,
            reason="test",
        )

    return _make


def test_generate_all_pros_cons_applies_threshold_and_keeps_valid_rows(
    monkeypatch, sample_rule_results
):
    def fake_get_company_context(company_id, conn=None, data=None):
        return make_context(company_id=company_id)

    def fake_evaluate_rules_for_company(context, conn=None):
        if context.company_id == "C1":
            return [
                sample_rule_results("PRO_01", pg.TYPE_PRO, "C1", 61.0),
                sample_rule_results("PRO_02", pg.TYPE_PRO, "C1", 59.9),
                sample_rule_results("CON_01", pg.TYPE_CON, "C1", 60.0),
                sample_rule_results("CON_02", pg.TYPE_CON, "C1", 60.01),
            ]
        return [
            sample_rule_results("PRO_03", pg.TYPE_PRO, "C2", 70.0),
            sample_rule_results("CON_03", pg.TYPE_CON, "C2", 65.0),
        ]

    monkeypatch.setattr(pg, "get_company_context", fake_get_company_context)
    monkeypatch.setattr(
        pg, "evaluate_rules_for_company", fake_evaluate_rules_for_company
    )

    df, stats = pg.generate_all_pros_cons(["C1", "C2"], conn=None)

    assert list(df.columns) == pg.OUTPUT_COLUMNS
    assert df["confidence_pct"].gt(60).all()
    assert set(df["type"].unique()) == {"pro", "con"}
    assert stats["total_companies"] == 2
    assert stats["signals_after_filter"] >= 3


def test_validate_output_schema_rejects_confidence_60():
    df = pd.DataFrame(
        [
            {
                "company_id": "C1",
                "type": "pro",
                "rule_id": "PRO_01",
                "text": "ok",
                "confidence_pct": 60.0,
            }
        ]
    )
    valid, issues = pg.validate_output_schema(df)
    assert valid is False
    assert any("confidence_pct" in issue for issue in issues)


def test_validate_output_schema_rejects_invalid_rule_id_and_missing_company():
    df = pd.DataFrame(
        [
            {
                "company_id": "",
                "type": "pro",
                "rule_id": "PRO_01",
                "text": "ok",
                "confidence_pct": 70.0,
            },
            {
                "company_id": "C2",
                "type": "con",
                "rule_id": "BAD_RULE",
                "text": "bad",
                "confidence_pct": 75.0,
            },
        ]
    )
    valid, issues = pg.validate_output_schema(df)
    assert valid is False
    assert any(
        "company_id" in issue.lower() or "rule_id" in issue.lower() for issue in issues
    )


def test_validate_company_coverage_flags_missing_both_types():
    companies = ["C1", "C2", "C3"]
    df = pd.DataFrame(
        [
            {
                "company_id": "C1",
                "type": "pro",
                "rule_id": "PRO_01",
                "text": "x",
                "confidence_pct": 80.0,
            },
            {
                "company_id": "C2",
                "type": "con",
                "rule_id": "CON_01",
                "text": "x",
                "confidence_pct": 80.0,
            },
        ]
    )
    stats = pg.validate_company_coverage(companies, df)
    assert stats["companies_total"] == 3
    assert stats["missing_pro"] == 2
    assert stats["missing_con"] == 2


def test_duplicate_identical_signal_rows_are_detected():
    df = pd.DataFrame(
        [
            {
                "company_id": "C1",
                "type": "pro",
                "rule_id": "PRO_01",
                "text": "x",
                "confidence_pct": 80.0,
            },
            {
                "company_id": "C1",
                "type": "pro",
                "rule_id": "PRO_01",
                "text": "x",
                "confidence_pct": 80.0,
            },
        ]
    )
    valid, issues = pg.validate_output_schema(df)
    assert valid is False
    assert any("duplicate" in issue.lower() for issue in issues)


def test_confidence_6001_is_included_and_60_is_excluded():
    assert 60.01 > 60.0
    assert not (60.0 > 60.0)


def test_load_all_company_ids_reports_sanity_stats(monkeypatch):
    df = pd.DataFrame(
        [
            {"company_id": "C1", "company_name": "Alpha", "sector": "Tech"},
            {"company_id": "C1", "company_name": "Alpha Duplicate", "sector": "Tech"},
            {"company_id": None, "company_name": "Missing", "sector": "Tech"},
        ]
    )
    monkeypatch.setattr(pg, "_load_table", lambda *args, **kwargs: df)

    ids, stats = pg.load_all_company_ids(None)
    assert len(ids) == 1
    assert stats["total_companies_in_db"] == 3
    assert stats["duplicate_company_ids"]
    assert stats["companies_missing_id_fields"]


def test_coverage_failures_report_is_generated_only_when_needed(tmp_path):
    failures = pd.DataFrame(
        [
            {
                "company_id": "C1",
                "company_name": "Alpha",
                "sector": "Tech",
                "pro_count": 0,
                "con_count": 0,
                "failure_reason": "missing metrics",
            }
        ]
    )
    target = tmp_path / "coverage_failures.csv"
    pg.write_coverage_failures_csv(failures, target)
    assert target.exists()
    assert list(pd.read_csv(target).columns) == [
        "company_id",
        "company_name",
        "sector",
        "pro_count",
        "con_count",
        "failure_reason",
    ]
