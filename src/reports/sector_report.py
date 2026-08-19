"""
sector_report.py

Sector PDF Report Generator for N100 Financial Intelligence Platform.

Sprint 5 — Module 5C (Day 34 Implementation)

Responsibilities:
1. Generate sector PDF reports for each sector (11 broad sectors covering the company universe).
2. Each Sector Report PDF includes:
   - Sector Summary / Overview Header Page
   - Sector Median KPIs across key financial metrics
   - Detailed Company Table listing all companies in the sector
   - Eight key financial metrics per company (Revenue, PAT, OPM %, ROE %, ROCE %, Debt-to-Equity, Interest Coverage, Health Score)
3. Strict layout control: full word wrapping, responsive table column widths, no blank pages, readable typography.
4. Output directory: reports/sector/
"""

import os
import re
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas

from src.config.constants import PROJECT_ROOT, OUTPUT_DIR, REPORTS_DIR, DATABASE_PATH
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Colors
PRIMARY_NAVY = colors.HexColor("#1A365D")
ACCENT_BLUE = colors.HexColor("#2563EB")
DARK_GRAY = colors.HexColor("#1F2937")
LIGHT_BG = colors.HexColor("#F8FAFC")
BORDER_COLOR = colors.HexColor("#E2E8F0")

# Output directory
SECTOR_REPORTS_DIR = REPORTS_DIR / "sector"
SECTOR_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 11 Broad Sectors Mapping Dictionary
SUB_SECTOR_TO_BROAD_SECTOR = {
    "Private Banks": "Financial Services",
    "Public Sector Banks": "Financial Services",
    "Life Insurance": "Financial Services",
    "General Insurance": "Financial Services",
    "Consumer Finance": "Financial Services",
    "Speciality Finance": "Financial Services",
    "Diversified Financials": "Financial Services",
    "IT Services": "Information Technology",
    "Internet & Platforms": "Information Technology",
    "Pharmaceuticals": "Healthcare & Pharma",
    "Healthcare": "Healthcare & Pharma",
    "Specialty Chemicals": "Healthcare & Pharma",
    "Automobiles": "Automobile & Auto Components",
    "Two Wheelers": "Automobile & Auto Components",
    "Auto Ancillaries": "Automobile & Auto Components",
    "Power & Utilities": "Energy & Power",
    "Renewable Energy": "Energy & Power",
    "Power Transmission": "Energy & Power",
    "Gas Distribution": "Energy & Power",
    "Oil & Gas Refining": "Energy & Power",
    "Oil & Gas Exploration": "Energy & Power",
    "Steel": "Metals & Mining",
    "Metals & Mining": "Metals & Mining",
    "Mining & Metals": "Metals & Mining",
    "Personal Products": "FMCG & Consumer Goods",
    "Food Products": "FMCG & Consumer Goods",
    "Food & Beverages": "FMCG & Consumer Goods",
    "Diversified FMCG": "FMCG & Consumer Goods",
    "FMCG": "FMCG & Consumer Goods",
    "Paints & Coatings": "FMCG & Consumer Goods",
    "Gems & Jewellery": "FMCG & Consumer Goods",
    "Capital Goods": "Capital Goods & Engineering",
    "Defence Electronics": "Capital Goods & Engineering",
    "Defence & Aerospace": "Capital Goods & Engineering",
    "Consumer Electricals": "Capital Goods & Engineering",
    "Diversified Industrials": "Capital Goods & Engineering",
    "Engineering & Construction": "Capital Goods & Engineering",
    "Cement": "Construction Materials & Real Estate",
    "Real Estate": "Construction Materials & Real Estate",
    "Infrastructure": "Construction Materials & Real Estate",
    "Retail": "Services & Retail",
    "Airlines": "Services & Retail",
    "Travel & Tourism": "Services & Retail",
    "Telecommunications": "Services & Retail",
    "Conglomerates": "Conglomerates & Holding Companies",
    "Holding Companies": "Conglomerates & Holding Companies",
}


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for footer page numbering."""

    def __init__(self, *args, **kwargs):
        """Initialize class instance attributes."""
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        """Showpage functionality."""
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Save functionality."""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        """Draw page number functionality."""
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        footer_text = f"N100 Financial Intelligence Platform — Sector Report | Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 20, footer_text)
        self.drawString(36, 20, "Confidential — Sector Intelligence")

        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)

        self.restoreState()


class SectorReportGenerator:
    """
    Generates a Sector PDF Report for a specific sector.
    """

    def __init__(self, sector_name: str, db_path: Optional[Path] = None):
        """Initialize class instance attributes."""
        self.sector_name = sector_name.strip()
        self.db_path = db_path or DATABASE_PATH
        self.company_data = self._load_sector_companies()

    def _get_db_conn(self):
        return sqlite3.connect(self.db_path)

    def _load_sector_companies(self) -> pd.DataFrame:
        """
        Load all companies belonging to the target sector along with their 8 key metrics.
        """
        try:
            with self._get_db_conn() as conn:
                comp_df = pd.read_sql_query(
                    "SELECT company_id, company_name, sector, industry FROM companies",
                    conn,
                )
                sec_df = pd.read_sql_query(
                    "SELECT company_id, sub_sector FROM sectors", conn
                )

                merged = comp_df.merge(sec_df, on="company_id", how="left")
                merged["broad_sector"] = (
                    merged["sub_sector"]
                    .map(SUB_SECTOR_TO_BROAD_SECTOR)
                    .fillna("Capital Goods & Engineering")
                )

                # Filter to sector
                sector_comps = merged[
                    merged["broad_sector"].str.upper() == self.sector_name.upper()
                ].copy()
                if sector_comps.empty:
                    # Fallback to sub_sector or raw sector matching
                    sector_comps = merged[
                        merged["sub_sector"].str.upper() == self.sector_name.upper()
                    ].copy()

                if sector_comps.empty:
                    logger.warning(f"No companies found for sector {self.sector_name}")
                    return pd.DataFrame()

                # Fetch 8 metrics for each company in sector
                records = []
                for _, row in sector_comps.iterrows():
                    cid = row["company_id"]
                    cname = row["company_name"]
                    sub_sec = row.get("sub_sector", "N/A")

                    # Latest P&L
                    pl = pd.read_sql_query(
                        "SELECT sales, net_profit, opm_percentage FROM profit_loss WHERE company_id = ? ORDER BY period DESC LIMIT 1",
                        conn,
                        params=[cid],
                    )
                    sales = (
                        pl.iloc[0]["sales"]
                        if not pl.empty and pd.notna(pl.iloc[0]["sales"])
                        else np.nan
                    )
                    pat = (
                        pl.iloc[0]["net_profit"]
                        if not pl.empty and pd.notna(pl.iloc[0]["net_profit"])
                        else np.nan
                    )
                    opm = (
                        pl.iloc[0]["opm_percentage"]
                        if not pl.empty and pd.notna(pl.iloc[0]["opm_percentage"])
                        else np.nan
                    )

                    # Latest KPIs
                    kpi = pd.read_sql_query(
                        "SELECT roe, roce, debt_to_equity, interest_coverage FROM financial_kpis WHERE company_id = ? ORDER BY period DESC LIMIT 1",
                        conn,
                        params=[cid],
                    )
                    roe = (
                        kpi.iloc[0]["roe"]
                        if not kpi.empty and pd.notna(kpi.iloc[0]["roe"])
                        else np.nan
                    )
                    roce = (
                        kpi.iloc[0]["roce"]
                        if not kpi.empty and pd.notna(kpi.iloc[0]["roce"])
                        else np.nan
                    )
                    de = (
                        kpi.iloc[0]["debt_to_equity"]
                        if not kpi.empty and pd.notna(kpi.iloc[0]["debt_to_equity"])
                        else np.nan
                    )
                    ic = (
                        kpi.iloc[0]["interest_coverage"]
                        if not kpi.empty and pd.notna(kpi.iloc[0]["interest_coverage"])
                        else np.nan
                    )

                    # Health score
                    hs = pd.read_sql_query(
                        "SELECT overall_score, rating FROM financial_health_scores WHERE company_id = ? ORDER BY period DESC LIMIT 1",
                        conn,
                        params=[cid],
                    )
                    score = (
                        hs.iloc[0]["overall_score"]
                        if not hs.empty and pd.notna(hs.iloc[0]["overall_score"])
                        else np.nan
                    )
                    rating = (
                        hs.iloc[0]["rating"]
                        if not hs.empty and pd.notna(hs.iloc[0]["rating"])
                        else "N/A"
                    )

                    records.append(
                        {
                            "company_id": cid,
                            "company_name": cname,
                            "sub_sector": sub_sec,
                            "revenue": sales,
                            "net_profit": pat,
                            "opm": opm,
                            "roe": roe,
                            "roce": roce,
                            "debt_to_equity": de,
                            "interest_coverage": ic,
                            "health_score": score,
                            "health_rating": rating,
                        }
                    )

                return pd.DataFrame(records)

        except Exception as e:
            logger.error(f"Error loading sector companies for {self.sector_name}: {e}")
            return pd.DataFrame()

    def generate(self, output_path: Optional[Path] = None) -> Path:
        """
        Generate Sector PDF report.
        """
        if output_path is None:
            clean_name = re.sub(r"[^\w\s-]", "", self.sector_name)
            clean_name = re.sub(r"\s+", "_", clean_name.strip())
            output_path = SECTOR_REPORTS_DIR / f"{clean_name}_sector_report.pdf"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=40,
        )

        printable_width = A4[0] - 72
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "SectorTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=colors.white,
        )
        subtitle_style = ParagraphStyle(
            "SectorSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#E2E8F0"),
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=PRIMARY_NAVY,
            spaceBefore=6,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "SectorBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=DARK_GRAY,
        )
        table_hdr_style = ParagraphStyle(
            "TableHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.white,
            alignment=1,
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=DARK_GRAY,
            alignment=1,
        )
        table_cell_left = ParagraphStyle(
            "TableCellLeft",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=DARK_GRAY,
            alignment=0,
        )

        elements = []

        # 1. Header Banner
        company_cnt = len(self.company_data)
        header_text = f"<b>Sector Intelligence Report: {self.sector_name}</b>"
        sub_text = (
            f"Total Companies: {company_cnt} | N100 Financial Intelligence Universe"
        )

        header_table = Table(
            [
                [Paragraph(header_text, title_style)],
                [Paragraph(sub_text, subtitle_style)],
            ],
            colWidths=[printable_width],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_NAVY),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 8))

        if self.company_data.empty:
            elements.append(
                Paragraph(
                    "<i>No company data available for this sector.</i>", body_style
                )
            )
            doc.build(elements, canvasmaker=NumberedCanvas)
            return output_path

        # 2. Sector Overview & Median KPIs
        elements.append(
            Paragraph("Sector Overview & Median Benchmarks", section_heading)
        )
        elements.append(
            HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=6)
        )

        df = self.company_data
        med_rev = df["revenue"].median()
        med_pat = df["net_profit"].median()
        med_opm = df["opm"].median()
        med_roe = df["roe"].median()
        med_roce = df["roce"].median()
        med_de = df["debt_to_equity"].median()
        med_ic = df["interest_coverage"].median()
        med_score = df["health_score"].median()

        median_tiles_data = [
            [
                Paragraph("<b>Median Revenue</b>", table_cell_style),
                Paragraph("<b>Median Net Profit</b>", table_cell_style),
                Paragraph("<b>Median OPM %</b>", table_cell_style),
                Paragraph("<b>Median ROE %</b>", table_cell_style),
            ],
            [
                Paragraph(
                    f"₹{med_rev:,.0f} Cr" if pd.notna(med_rev) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"₹{med_pat:,.0f} Cr" if pd.notna(med_pat) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"{med_opm:.2f}%" if pd.notna(med_opm) else "N/A", table_cell_style
                ),
                Paragraph(
                    f"{med_roe:.2f}%" if pd.notna(med_roe) else "N/A", table_cell_style
                ),
            ],
            [
                Paragraph("<b>Median ROCE %</b>", table_cell_style),
                Paragraph("<b>Median D/E (x)</b>", table_cell_style),
                Paragraph("<b>Median Int. Coverage</b>", table_cell_style),
                Paragraph("<b>Median Health Score</b>", table_cell_style),
            ],
            [
                Paragraph(
                    f"{med_roce:.2f}%" if pd.notna(med_roce) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"{med_de:.2f}x" if pd.notna(med_de) else "N/A", table_cell_style
                ),
                Paragraph(
                    f"{med_ic:.2f}x" if pd.notna(med_ic) else "N/A", table_cell_style
                ),
                Paragraph(
                    f"{med_score:.1f}/100" if pd.notna(med_score) else "N/A",
                    table_cell_style,
                ),
            ],
        ]

        c_w = printable_width / 4.0
        med_table = Table(median_tiles_data, colWidths=[c_w, c_w, c_w, c_w])
        med_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
                    ("BACKGROUND", (0, 2), (-1, 2), LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(med_table)
        elements.append(Spacer(1, 10))

        # 3. Eight Metrics Per Company Table
        elements.append(
            Paragraph(
                "Company Financial Performance Matrix (Eight Key Metrics)",
                section_heading,
            )
        )
        elements.append(
            HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=6)
        )

        # Headers: Company, Revenue, PAT, OPM%, ROE%, ROCE%, D/E, Health Score
        table_data = [
            [
                Paragraph("Company / Ticker", table_hdr_style),
                Paragraph("Revenue<br/>(₹ Cr)", table_hdr_style),
                Paragraph("Net Profit<br/>(₹ Cr)", table_hdr_style),
                Paragraph("OPM<br/>(%)", table_hdr_style),
                Paragraph("ROE<br/>(%)", table_hdr_style),
                Paragraph("ROCE<br/>(%)", table_hdr_style),
                Paragraph("Debt/Eq<br/>(x)", table_hdr_style),
                Paragraph("Int Cover<br/>(x)", table_hdr_style),
                Paragraph("Health<br/>Score", table_hdr_style),
            ]
        ]

        for _, r in df.sort_values(by="company_id").iterrows():
            cid_str = f"<b>{r['company_id']}</b><br/>{str(r['company_name'])[:22]}"
            rev_str = f"{r['revenue']:,.0f}" if pd.notna(r["revenue"]) else "N/A"
            pat_str = f"{r['net_profit']:,.0f}" if pd.notna(r["net_profit"]) else "N/A"
            opm_str = f"{r['opm']:.1f}%" if pd.notna(r["opm"]) else "N/A"
            roe_str = f"{r['roe']:.1f}%" if pd.notna(r["roe"]) else "N/A"
            roce_str = f"{r['roce']:.1f}%" if pd.notna(r["roce"]) else "N/A"
            de_str = (
                f"{r['debt_to_equity']:.2f}" if pd.notna(r["debt_to_equity"]) else "N/A"
            )
            ic_str = (
                f"{r['interest_coverage']:.1f}"
                if pd.notna(r["interest_coverage"])
                else "N/A"
            )
            hs_str = (
                f"{r['health_score']:.1f}" if pd.notna(r["health_score"]) else "N/A"
            )

            table_data.append(
                [
                    Paragraph(cid_str, table_cell_left),
                    Paragraph(rev_str, table_cell_style),
                    Paragraph(pat_str, table_cell_style),
                    Paragraph(opm_str, table_cell_style),
                    Paragraph(roe_str, table_cell_style),
                    Paragraph(roce_str, table_cell_style),
                    Paragraph(de_str, table_cell_style),
                    Paragraph(ic_str, table_cell_style),
                    Paragraph(hs_str, table_cell_style),
                ]
            )

        col_widths = [105, 52, 52, 45, 45, 45, 45, 45, 49]
        comp_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        comp_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_NAVY),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        elements.append(comp_table)

        doc.build(elements, canvasmaker=NumberedCanvas)
        logger.info(f"Sector Report successfully generated: {output_path}")
        return output_path


def generate_sector_report(
    sector_name: str, output_path: Optional[Path] = None, db_path: Optional[Path] = None
) -> Path:
    """Generate sector report functionality."""
    generator = SectorReportGenerator(sector_name, db_path=db_path)
    return generator.generate(output_path=output_path)


def generate_all_sector_reports(db_path: Optional[Path] = None) -> List[Path]:
    """
    Generate Sector Reports for all 11 broad sectors.
    """
    sectors_11 = [
        "Financial Services",
        "Energy & Power",
        "Capital Goods & Engineering",
        "Automobile & Auto Components",
        "FMCG & Consumer Goods",
        "Healthcare & Pharma",
        "Information Technology",
        "Services & Retail",
        "Construction Materials & Real Estate",
        "Metals & Mining",
        "Conglomerates & Holding Companies",
    ]

    generated = []
    for sec in sectors_11:
        try:
            pdf = generate_sector_report(sec, db_path=db_path)
            generated.append(pdf)
        except Exception as e:
            logger.error(f"Failed to generate sector report for {sec}: {e}")

    return generated


if __name__ == "__main__":
    test_sec = "Financial Services"
    print(f"Generating test sector report for {test_sec}...")
    pdf = generate_sector_report(test_sec)
    print(f"Generated Sector Report at: {pdf}")
