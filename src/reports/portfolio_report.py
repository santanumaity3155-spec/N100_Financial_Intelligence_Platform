"""
portfolio_report.py

Portfolio Summary PDF Report Generator for N100 Financial Intelligence Platform.

Sprint 5 — Module 5C (Day 35 Implementation)

Responsibilities:
1. Generate reports/portfolio/portfolio_summary.pdf.
2. Layout: Exactly ONE PAGE PER INCLUDED COMPANY.
3. Sorted alphabetically by ticker.
4. Each page includes:
   - Header with Ticker, Company Name, Sector
   - Top 6 KPIs (Revenue, Net Profit, ROE, ROCE, Debt-to-Equity, OPM / Health Score)
   - Historical comparison & Trend Arrows:
     - UP (↑): Metric improved in latest year (> 2%)
     - DOWN (↓): Metric declined in latest year (> 2%)
     - RIGHT (→): Metric flat within ±2%
5. Preserves metric direction conventions (higher is better for Revenue/Profit/ROE, lower is better for Debt/Equity).
"""

import os
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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
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
GREEN_COLOR = colors.HexColor("#15803D")
RED_COLOR = colors.HexColor("#B91C1C")

# Output directory
PORTFOLIO_DIR = REPORTS_DIR / "portfolio"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for page numbers (Page X of Y)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        footer_text = f"N100 Financial Intelligence Platform — Portfolio Summary | Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 20, footer_text)
        self.drawString(36, 20, "Confidential — Portfolio Analysis")
        
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)
        
        self.restoreState()


class PortfolioReportGenerator:
    """
    Generates Portfolio Summary PDF report (1 page per company).
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH

    def _get_db_conn(self):
        return sqlite3.connect(self.db_path)

    def _get_valid_companies(self) -> List[Dict[str, Any]]:
        """
        Retrieve all companies sorted alphabetically by ticker that have sufficient data.
        """
        try:
            with self._get_db_conn() as conn:
                comp_df = pd.read_sql_query("SELECT company_id, company_name, sector, industry FROM companies ORDER BY company_id ASC", conn)
                sec_df = pd.read_sql_query("SELECT company_id, sub_sector FROM sectors", conn)
                
                merged = comp_df.merge(sec_df, on="company_id", how="left")
                
                valid_companies = []
                for _, r in merged.iterrows():
                    cid = r["company_id"]
                    
                    # Year check
                    pl_c = conn.execute("SELECT COUNT(DISTINCT period) FROM profit_loss WHERE company_id = ?", (cid,)).fetchone()[0]
                    bs_c = conn.execute("SELECT COUNT(DISTINCT period) FROM balance_sheet WHERE company_id = ?", (cid,)).fetchone()[0]
                    cf_c = conn.execute("SELECT COUNT(DISTINCT period) FROM cash_flow WHERE company_id = ?", (cid,)).fetchone()[0]
                    
                    if pl_c < 3 or bs_c < 3 or cf_c < 3:
                        continue # Skip insufficient data companies
                        
                    valid_companies.append(r.to_dict())
                    
                return valid_companies
        except Exception as e:
            logger.error(f"Error retrieving valid portfolio companies: {e}")
            return []

    def _calculate_trend(self, curr_val: float, prev_val: float, inverted: bool = False) -> Tuple[str, str, str]:
        """
        Calculate trend arrow, pct change, and color.
        Returns: (arrow_symbol, change_pct_str, hex_color)
        """
        if pd.isna(curr_val) or pd.isna(prev_val) or prev_val == 0:
            return "→", "N/A", "#64748B"
            
        pct_change = ((curr_val - prev_val) / abs(prev_val)) * 100.0
        
        # Check flat within 2%
        if abs(pct_change) <= 2.0:
            return "→", f"{pct_change:+.1f}%", "#64748B"
            
        if not inverted:
            # Higher is better
            if pct_change > 2.0:
                return "↑", f"{pct_change:+.1f}%", "#15803D" # Green UP
            else:
                return "↓", f"{pct_change:+.1f}%", "#B91C1C" # Red DOWN
        else:
            # Lower is better (e.g. Debt-to-Equity)
            if pct_change < -2.0:
                return "↑", f"{pct_change:+.1f}%", "#15803D" # Green UP (improved/reduced debt)
            else:
                return "↓", f"{pct_change:+.1f}%", "#B91C1C" # Red DOWN (increased debt)

    def generate(self, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            output_path = PORTFOLIO_DIR / "portfolio_summary.pdf"
            
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        companies_list = self._get_valid_companies()
        
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
            "PortTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=colors.white,
        )
        subtitle_style = ParagraphStyle(
            "PortSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#E2E8F0"),
        )
        section_heading = ParagraphStyle(
            "PortSectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            textColor=PRIMARY_NAVY,
            spaceBefore=10,
            spaceAfter=6,
        )
        hdr_style = ParagraphStyle(
            "PortHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.white,
            alignment=1,
        )
        cell_style = ParagraphStyle(
            "PortCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=DARK_GRAY,
            alignment=1,
        )
        cell_left = ParagraphStyle(
            "PortCellLeft",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=PRIMARY_NAVY,
            alignment=0,
        )

        elements = []

        with self._get_db_conn() as conn:
            for idx, comp in enumerate(companies_list):
                cid = comp["company_id"]
                cname = comp["company_name"]
                sec = comp.get("sector") or comp.get("sub_sector") or "N100 Sector"
                
                # Header Bar
                hdr_text = f"<b>{cname}</b> ({cid})"
                sub_text = f"Sector: {sec} | Portfolio One-Page Executive Summary"
                
                hdr_tbl = Table([[Paragraph(hdr_text, title_style)], [Paragraph(sub_text, subtitle_style)]], colWidths=[printable_width])
                hdr_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_NAVY),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]))
                elements.append(hdr_tbl)
                elements.append(Spacer(1, 14))

                # Fetch last 2 years for trend comparison
                pl_df = pd.read_sql_query("SELECT period, sales, net_profit, opm_percentage FROM profit_loss WHERE company_id = ? ORDER BY period DESC LIMIT 2", conn, params=[cid])
                kpi_df = pd.read_sql_query("SELECT period, roe, roce, debt_to_equity FROM financial_kpis WHERE company_id = ? ORDER BY period DESC LIMIT 2", conn, params=[cid])
                hs_df = pd.read_sql_query("SELECT overall_score, rating FROM financial_health_scores WHERE company_id = ? ORDER BY period DESC LIMIT 1", conn, params=[cid])
                
                curr_sales = pl_df.iloc[0]["sales"] if len(pl_df) >= 1 else np.nan
                prev_sales = pl_df.iloc[1]["sales"] if len(pl_df) >= 2 else np.nan
                
                curr_pat = pl_df.iloc[0]["net_profit"] if len(pl_df) >= 1 else np.nan
                prev_pat = pl_df.iloc[1]["net_profit"] if len(pl_df) >= 2 else np.nan
                
                curr_opm = pl_df.iloc[0]["opm_percentage"] if len(pl_df) >= 1 else np.nan
                prev_opm = pl_df.iloc[1]["opm_percentage"] if len(pl_df) >= 2 else np.nan
                
                curr_roe = kpi_df.iloc[0]["roe"] if len(kpi_df) >= 1 else np.nan
                prev_roe = kpi_df.iloc[1]["roe"] if len(kpi_df) >= 2 else np.nan
                
                curr_roce = kpi_df.iloc[0]["roce"] if len(kpi_df) >= 1 else np.nan
                prev_roce = kpi_df.iloc[1]["roce"] if len(kpi_df) >= 2 else np.nan
                
                curr_de = kpi_df.iloc[0]["debt_to_equity"] if len(kpi_df) >= 1 else np.nan
                prev_de = kpi_df.iloc[1]["debt_to_equity"] if len(kpi_df) >= 2 else np.nan
                
                # Trends
                arr_rev, chg_rev, clr_rev = self._calculate_trend(curr_sales, prev_sales)
                arr_pat, chg_pat, clr_pat = self._calculate_trend(curr_pat, prev_pat)
                arr_roe, chg_roe, clr_roe = self._calculate_trend(curr_roe, prev_roe)
                arr_roce, chg_roce, clr_roce = self._calculate_trend(curr_roce, prev_roce)
                arr_de, chg_de, clr_de = self._calculate_trend(curr_de, prev_de, inverted=True)
                arr_opm, chg_opm, clr_opm = self._calculate_trend(curr_opm, prev_opm)

                elements.append(Paragraph("Top 6 Key Financial Metrics & Year-over-Year Trends", section_heading))
                elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=8))

                table_data = [
                    [
                        Paragraph("Metric", hdr_style),
                        Paragraph("Latest Year Value", hdr_style),
                        Paragraph("Prior Year Value", hdr_style),
                        Paragraph("YoY Change", hdr_style),
                        Paragraph("Trend Signal", hdr_style),
                    ]
                ]

                metrics_specs = [
                    ("Revenue (Sales)", f"₹{curr_sales:,.0f} Cr" if pd.notna(curr_sales) else "N/A", f"₹{prev_sales:,.0f} Cr" if pd.notna(prev_sales) else "N/A", chg_rev, arr_rev, clr_rev),
                    ("Net Profit (PAT)", f"₹{curr_pat:,.0f} Cr" if pd.notna(curr_pat) else "N/A", f"₹{prev_pat:,.0f} Cr" if pd.notna(prev_pat) else "N/A", chg_pat, arr_pat, clr_pat),
                    ("Return on Equity (ROE)", f"{curr_roe:.2f}%" if pd.notna(curr_roe) else "N/A", f"{prev_roe:.2f}%" if pd.notna(prev_roe) else "N/A", chg_roe, arr_roe, clr_roe),
                    ("Return on Capital Employed (ROCE)", f"{curr_roce:.2f}%" if pd.notna(curr_roce) else "N/A", f"{prev_roce:.2f}%" if pd.notna(prev_roce) else "N/A", chg_roce, arr_roce, clr_roce),
                    ("Debt-to-Equity (x)", f"{curr_de:.2f}x" if pd.notna(curr_de) else "N/A", f"{prev_de:.2f}x" if pd.notna(prev_de) else "N/A", chg_de, arr_de, clr_de),
                    ("Operating Profit Margin (OPM %)", f"{curr_opm:.2f}%" if pd.notna(curr_opm) else "N/A", f"{prev_opm:.2f}%" if pd.notna(prev_opm) else "N/A", chg_opm, arr_opm, clr_opm),
                ]

                for name, c_val, p_val, chg, arr, clr in metrics_specs:
                    arr_p = Paragraph(f"<font color='{clr}'><b>{arr} {chg}</b></font>", cell_style)
                    table_data.append([
                        Paragraph(name, cell_left),
                        Paragraph(c_val, cell_style),
                        Paragraph(p_val, cell_style),
                        Paragraph(chg, cell_style),
                        arr_p,
                    ])

                c_w = printable_width / 5.0
                kpi_table = Table(table_data, colWidths=[c_w*1.4, c_w*0.9, c_w*0.9, c_w*0.9, c_w*0.9])
                kpi_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_NAVY),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                elements.append(kpi_table)
                elements.append(Spacer(1, 14))

                # Financial Health & Ratings Banner
                score_val = hs_df.iloc[0]["overall_score"] if not hs_df.empty and pd.notna(hs_df.iloc[0]["overall_score"]) else np.nan
                rating_val = hs_df.iloc[0]["rating"] if not hs_df.empty and pd.notna(hs_df.iloc[0]["rating"]) else "N/A"
                
                score_str = f"{score_val:.1f}/100" if pd.notna(score_val) else "N/A"
                banner_text = f"<b>Composite Health Score:</b> {score_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Rating:</b> {rating_val} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Portfolio Rank:</b> #{idx+1} of {len(companies_list)}"
                banner_p = Paragraph(banner_text, ParagraphStyle("PortBanner", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9.5, textColor=PRIMARY_NAVY, alignment=1))
                
                banner_tbl = Table([[banner_p]], colWidths=[printable_width])
                banner_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]))
                elements.append(banner_tbl)

                # PageBreak between companies (except last)
                if idx < len(companies_list) - 1:
                    elements.append(PageBreak())

        doc.build(elements, canvasmaker=NumberedCanvas)
        logger.info(f"Portfolio Summary PDF successfully generated: {output_path}")
        return output_path


def generate_portfolio_summary_report(output_path: Optional[Path] = None, db_path: Optional[Path] = None) -> Path:
    generator = PortfolioReportGenerator(db_path=db_path)
    return generator.generate(output_path=output_path)


if __name__ == "__main__":
    print("Generating Portfolio Summary PDF...")
    pdf = generate_portfolio_summary_report()
    print(f"Generated Portfolio Summary PDF at: {pdf}")
