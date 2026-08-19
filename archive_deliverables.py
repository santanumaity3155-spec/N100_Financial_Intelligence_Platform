"""
archive_deliverables.py

Identifies, catalogs, and archives the 23 authoritative deliverables into output/final_deliverables/
Generates output/final_deliverables/manifest.txt.
"""

import os
import shutil
from pathlib import Path

DELIVERABLES = [
    {
        "filename": "NIFTY_SMALL_100.db",
        "source": "NIFTY_SMALL_100.db",
        "alt_source": "output/NIFTY_SMALL_100.db",
        "description": "SQLite Financial Database containing 20 normalized tables and 10,000+ financial records"
    },
    {
        "filename": "financial_health_scores.csv",
        "source": "output/financial_health_scores.csv",
        "description": "Financial Health Scoring Engine composite scores (0-100) and component grades"
    },
    {
        "filename": "peer_percentiles.csv",
        "source": "output/peer_percentiles.csv",
        "description": "Peer Percentile Ranking Engine dataset across 13 peer groups and 10 ratio metrics"
    },
    {
        "filename": "capital_allocation_latest_year.csv",
        "source": "output/capital_allocation_latest_year.csv",
        "description": "Capital Allocation Engine latest fiscal year deployment metrics"
    },
    {
        "filename": "capital_allocation_distribution.csv",
        "source": "output/capital_allocation_distribution.csv",
        "description": "Capital Allocation Distribution summary across reinvestment vs shareholder returns"
    },
    {
        "filename": "cashflow_intelligence.xlsx",
        "source": "output/cashflow_intelligence.xlsx",
        "description": "Cash Flow Intelligence Engine multi-year Excel analytics workbook"
    },
    {
        "filename": "pros_cons_generated.csv",
        "source": "output/pros_cons_generated.csv",
        "description": "NLP Pros and Cons Generator investment highlights and risk alerts"
    },
    {
        "filename": "valuation_summary.xlsx",
        "source": "output/valuation_summary.xlsx",
        "description": "Automated Valuation Model master summary Excel spreadsheet"
    },
    {
        "filename": "valuation_flags.csv",
        "source": "output/valuation_flags.csv",
        "description": "Valuation Mispricing Flags (Overvalued / Undervalued / Fair Value alerts)"
    },
    {
        "filename": "distress_alerts.csv",
        "source": "output/distress_alerts.csv",
        "description": "Early Warning Financial Distress & Solvency Risk Alerts"
    },
    {
        "filename": "outlier_report.csv",
        "source": "output/outlier_report.csv",
        "description": "Analytical Outlier Detection Report across company financial ratios"
    },
    {
        "filename": "cluster_labels.csv",
        "source": "output/cluster_labels.csv",
        "description": "Unsupervised K-Means Machine Learning Cluster Allocations"
    },
    {
        "filename": "cluster_profiles.csv",
        "source": "output/cluster_profiles.csv",
        "description": "Machine Learning Cluster Feature Centroids and Behavioral Profiles"
    },
    {
        "filename": "portfolio_stats.csv",
        "source": "output/portfolio_stats.csv",
        "description": "Portfolio Analytics Statistics and Aggregate Risk Metrics"
    },
    {
        "filename": "pattern_changes.csv",
        "source": "output/pattern_changes.csv",
        "description": "Financial Pattern Change Detection Log across multi-year statements"
    },
    {
        "filename": "pattern_change_summary.csv",
        "source": "output/pattern_change_summary.csv",
        "description": "Financial Pattern Change Summary Matrix"
    },
    {
        "filename": "parse_failures.csv",
        "source": "output/parse_failures.csv",
        "description": "Data Ingestion & Excel Statement Parser Diagnostic Log"
    },
    {
        "filename": "module4_cross_validation.csv",
        "source": "output/module4_cross_validation.csv",
        "description": "Financial Statement Cross-Validation Audit Results"
    },
    {
        "filename": "ratio_load_summary.csv",
        "source": "output/ratio_load_summary.csv",
        "description": "ETL Financial Ratio Load Diagnostic Summary"
    },
    {
        "filename": "postman_collection.json",
        "source": "output/postman_collection.json",
        "alt_source": "docs/postman_collection.json",
        "description": "FastAPI Postman API Test Suite Collection JSON"
    },
    {
        "filename": "perf_notes.md",
        "source": "output/perf_notes.md",
        "description": "Module 6G Performance Benchmarks and Concurrency Load Test Documentation"
    },
    {
        "filename": "correlation_heatmap.png",
        "source": "reports/correlation_heatmap.png",
        "description": "Multivariate Financial Ratio Pearson Correlation Matrix Heatmap Plot"
    },
    {
        "filename": "analyst_guide.pdf",
        "source": "docs/analyst_guide.pdf",
        "description": "Authoritative 14-Page Institutional Analyst & Operational Guide PDF"
    }
]

def main():
    dest_dir = Path("output/final_deliverables")
    dest_dir.mkdir(parents=True, exist_ok=True)

    manifest_lines = []
    manifest_lines.append("============================================================")
    manifest_lines.append("N100 FINANCIAL INTELLIGENCE PLATFORM — DELIVERABLES MANIFEST")
    manifest_lines.append("============================================================")
    manifest_lines.append(f"Total Authoritative Deliverables: {len(DELIVERABLES)}")
    manifest_lines.append("Archive Location: output/final_deliverables/")
    manifest_lines.append("============================================================\n")

    archived_count = 0

    for idx, item in enumerate(DELIVERABLES, start=1):
        filename = item["filename"]
        source_path = Path(item["source"])
        if not source_path.exists() and "alt_source" in item:
            source_path = Path(item["alt_source"])

        if not source_path.exists():
            print(f"ERROR: Missing deliverable #{idx}: {filename} at {source_path}")
            continue

        dest_path = dest_dir / filename
        shutil.copy2(source_path, dest_path)

        file_size = dest_path.stat().st_size
        archived_count += 1

        print(f"[{idx}/23] Archived {filename} ({file_size:,} bytes)")

        manifest_lines.append(f"Deliverable #{idx:02d}: {filename}")
        manifest_lines.append(f"  Source Path : {source_path}")
        manifest_lines.append(f"  Archive Path: output/final_deliverables/{filename}")
        manifest_lines.append(f"  File Size   : {file_size:,} bytes")
        manifest_lines.append(f"  Description : {item['description']}")
        manifest_lines.append("-" * 60)

    manifest_path = dest_dir / "manifest.txt"
    manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
    print(f"\nWrote deliverables manifest to {manifest_path}")
    print(f"Successfully archived {archived_count}/23 deliverables into output/final_deliverables/")

if __name__ == "__main__":
    main()
