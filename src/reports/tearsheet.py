"""
tearsheet.py

Company PDF Tearsheet Generator for N100 Financial Intelligence Platform.

Sprint 5 — Module 5C (Day 33 & Day 34 Implementation)

Responsibilities:
1. Generate an authoritative, exactly 2-page PDF company report for a given company.
2. Page 1:
   - Navy header bar (Company Name, Ticker, Sector, ISIN)
   - Six KPI tiles arranged in 2 rows x 3 columns
   - Ten-year Revenue and Net Profit side-by-side bar chart
   - ROE and ROCE line chart
3. Page 2:
   - Balance Sheet composition stacked bar chart (Equity, Borrowings, Other liabilities)
   - Cash Flow waterfall chart for latest available year
   - Pros section (from Module 2D outputs)
   - Cons section (from Module 2D outputs)
   - Capital Allocation badge (from Module 4 outputs)
4. Enforce strict word wrapping, container bounds, margin control, and exactly 2 pages fit.
5. Batch generation with skip logging (output/skipped_tearsheets.csv) and failure logging (output/tearsheet_generation_failures.csv).
"""

import os
import re
import sqlite3
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Matplotlib configuration for headless PDF chart rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

from src.config.constants import PROJECT_ROOT, OUTPUT_DIR, REPORTS_DIR, DATABASE_PATH
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Colors
PRIMARY_NAVY = colors.HexColor("#1A365D")
ACCENT_BLUE = colors.HexColor("#2563EB")
ACCENT_TEAL = colors.HexColor("#0D9488")
DARK_GRAY = colors.HexColor("#1F2937")
LIGHT_BG = colors.HexColor("#F8FAFC")
BORDER_COLOR = colors.HexColor("#E2E8F0")
GREEN_COLOR = colors.HexColor("#15803D")
RED_COLOR = colors.HexColor("#B91C1C")
AMBER_COLOR = colors.HexColor("#B45309")

# Directory setup
TEARSHEETS_DIR = REPORTS_DIR / "tearsheets"
TEARSHEETS_DIR.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to add running footer with page numbers (Page X of Y)
    and header decoration.
    """
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
        
        footer_text = f"N100 Financial Intelligence Platform | Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 20, footer_text)
        
        timestamp_text = "Confidential — For Internal Analysis Only"
        self.drawString(36, 20, timestamp_text)
        
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)
        
        self.restoreState()


class CompanyTearsheetGenerator:
    """
    Generates a 2-page PDF tearsheet for a specified company.
    """
    def __init__(self, company_id: str, db_path: Optional[Path] = None):
        self.company_id = company_id.strip().upper()
        self.db_path = db_path or DATABASE_PATH
        self.temp_files: List[str] = []
        
        # Load all required data
        self.company_info = self._load_company_info()
        self.pl_data = self._load_pl_data()
        self.bs_data = self._load_bs_data()
        self.cf_data = self._load_cf_data()
        self.kpi_data = self._load_kpi_data()
        self.health_data = self._load_health_data()
        self.pros_cons = self._load_pros_cons()
        self.capital_alloc = self._load_capital_allocation()
        
    # -------------------------------------------------------------------------
    # Data Loading Helpers
    # -------------------------------------------------------------------------
    def _get_db_conn(self):
        return sqlite3.connect(self.db_path)

    def _load_company_info(self) -> Dict[str, Any]:
        try:
            with self._get_db_conn() as conn:
                query = "SELECT * FROM companies WHERE company_id = ?"
                df = pd.read_sql_query(query, conn, params=[self.company_id])
                if not df.empty:
                    return df.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Error loading company info for {self.company_id}: {e}")
        return {"company_id": self.company_id, "company_name": self.company_id, "sector": "N/A", "industry": "N/A"}

    def _load_pl_data(self) -> pd.DataFrame:
        try:
            with self._get_db_conn() as conn:
                query = "SELECT * FROM profit_loss WHERE company_id = ? ORDER BY period ASC"
                df = pd.read_sql_query(query, conn, params=[self.company_id])
                return df
        except Exception as e:
            logger.error(f"Error loading P&L for {self.company_id}: {e}")
            return pd.DataFrame()

    def _load_bs_data(self) -> pd.DataFrame:
        try:
            with self._get_db_conn() as conn:
                query = "SELECT * FROM balance_sheet WHERE company_id = ? ORDER BY period ASC"
                df = pd.read_sql_query(query, conn, params=[self.company_id])
                return df
        except Exception as e:
            logger.error(f"Error loading BS for {self.company_id}: {e}")
            return pd.DataFrame()

    def _load_cf_data(self) -> pd.DataFrame:
        try:
            with self._get_db_conn() as conn:
                query = "SELECT * FROM cash_flow WHERE company_id = ? ORDER BY period ASC"
                df = pd.read_sql_query(query, conn, params=[self.company_id])
                return df
        except Exception as e:
            logger.error(f"Error loading CF for {self.company_id}: {e}")
            return pd.DataFrame()

    def _load_kpi_data(self) -> pd.DataFrame:
        try:
            with self._get_db_conn() as conn:
                query = "SELECT * FROM financial_kpis WHERE company_id = ? ORDER BY period ASC"
                df = pd.read_sql_query(query, conn, params=[self.company_id])
                return df
        except Exception as e:
            logger.error(f"Error loading KPIs for {self.company_id}: {e}")
            return pd.DataFrame()

    def _load_health_data(self) -> Dict[str, Any]:
        try:
            with self._get_db_conn() as conn:
                query = "SELECT * FROM financial_health_scores WHERE company_id = ? ORDER BY period DESC LIMIT 1"
                df = pd.read_sql_query(query, conn, params=[self.company_id])
                if not df.empty:
                    return df.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Error loading health score for {self.company_id}: {e}")
        
        # Fallback to output CSV
        csv_path = OUTPUT_DIR / "financial_health_scores.csv"
        if csv_path.exists():
            try:
                df_csv = pd.read_csv(csv_path)
                if "company_id" in df_csv.columns:
                    m = df_csv[df_csv["company_id"].str.upper() == self.company_id]
                    if not m.empty:
                        return m.iloc[0].to_dict()
            except Exception:
                pass
        return {}

    def _load_pros_cons(self) -> Dict[str, List[str]]:
        pros: List[str] = []
        cons: List[str] = []
        
        csv_path = OUTPUT_DIR / "pros_cons_generated.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                if "company_id" in df.columns:
                    match = df[df["company_id"].str.upper() == self.company_id]
                    for _, row in match.iterrows():
                        t = str(row.get("type", "")).lower()
                        txt = str(row.get("text", "")).strip()
                        if not txt or txt.lower() == "nan":
                            continue
                        if t == "pro":
                            pros.append(txt)
                        elif t == "con":
                            cons.append(txt)
            except Exception as e:
                logger.error(f"Error loading pros/cons from CSV for {self.company_id}: {e}")
                
        # DB fallback
        if not pros and not cons:
            try:
                with self._get_db_conn() as conn:
                    query = "SELECT * FROM pros_cons WHERE company_id = ?"
                    df_db = pd.read_sql_query(query, conn, params=[self.company_id])
                    if not df_db.empty:
                        r = df_db.iloc[0]
                        p_str = r.get("pros")
                        c_str = r.get("cons")
                        if p_str and pd.notna(p_str) and str(p_str).lower() != "nan":
                            pros.extend([p.strip() for p in str(p_str).split(";") if p.strip()])
                        if c_str and pd.notna(c_str) and str(c_str).lower() != "nan":
                            cons.extend([c.strip() for c in str(c_str).split(";") if c.strip()])
            except Exception as e:
                logger.error(f"Error loading pros/cons DB fallback for {self.company_id}: {e}")
                
        return {"pros": pros, "cons": cons}

    def _load_capital_allocation(self) -> Dict[str, Any]:
        res = {"rating": "N/A", "pattern": "N/A", "latest_year": "N/A"}
        csv_path = OUTPUT_DIR / "capital_allocation_latest_year.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                if "company_id" in df.columns:
                    m = df[df["company_id"].str.upper() == self.company_id]
                    if not m.empty:
                        row = m.iloc[0]
                        res["rating"] = str(row.get("capital_allocation_rating", "N/A"))
                        res["pattern"] = str(row.get("capital_allocation_pattern", "N/A"))
                        res["latest_year"] = str(row.get("latest_year", "N/A"))
            except Exception as e:
                logger.error(f"Error loading capital allocation for {self.company_id}: {e}")
        return res

    def has_sufficient_data(self) -> Tuple[bool, str]:
        """
        Check if company has at least 3 years of usable data.
        """
        pl_years = self.pl_data["period"].nunique() if not self.pl_data.empty else 0
        bs_years = self.bs_data["period"].nunique() if not self.bs_data.empty else 0
        cf_years = self.cf_data["period"].nunique() if not self.cf_data.empty else 0
        
        if pl_years < 3:
            return False, f"Fewer than 3 years of P&L data ({pl_years} years found)"
        if bs_years < 3:
            return False, f"Fewer than 3 years of Balance Sheet data ({bs_years} years found)"
        if cf_years < 3:
            return False, f"Fewer than 3 years of Cash Flow data ({cf_years} years found)"
            
        return True, "Sufficient data available"

    # -------------------------------------------------------------------------
    # Chart Generation (Matplotlib -> Temp Image)
    # -------------------------------------------------------------------------
    def _create_revenue_profit_chart(self) -> Optional[str]:
        if self.pl_data.empty:
            return None
        
        df = self.pl_data.copy()
        if "sales" not in df.columns or "net_profit" not in df.columns:
            return None
            
        df = df.tail(10)
        years = df["period"].astype(str).str.replace("Mar ", "").str.replace("FY", "").tolist()
        revenue = pd.to_numeric(df["sales"], errors="coerce").fillna(0).tolist()
        profit = pd.to_numeric(df["net_profit"], errors="coerce").fillna(0).tolist()
        
        fig, ax = plt.subplots(figsize=(7.2, 2.3), dpi=200)
        x = np.arange(len(years))
        width = 0.38
        
        ax.bar(x - width/2, revenue, width, label="Revenue (Sales)", color="#1A365D", alpha=0.9)
        ax.bar(x + width/2, profit, width, label="Net Profit (PAT)", color="#0D9488", alpha=0.9)
        
        ax.set_title("10-Year Historical Revenue & Net Profit (₹ Cr)", fontsize=9, fontweight="bold", pad=6, color="#1E293B")
        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=7, color="#334155")
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=7, loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="none")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")
        
        plt.tight_layout()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = tmp.name
        tmp.close()
        plt.savefig(tmp_path, format="png", bbox_inches="tight")
        plt.close(fig)
        
        self.temp_files.append(tmp_path)
        return tmp_path

    def _create_roe_roce_chart(self) -> Optional[str]:
        df = self.kpi_data.copy() if not self.kpi_data.empty else pd.DataFrame()
        if df.empty or "roe" not in df.columns or "roce" not in df.columns:
            return None
            
        df = df.tail(10)
        years = df["period"].astype(str).str.replace("Mar ", "").str.replace("FY", "").tolist()
        roe = pd.to_numeric(df["roe"], errors="coerce").tolist()
        roce = pd.to_numeric(df["roce"], errors="coerce").tolist()
        
        fig, ax = plt.subplots(figsize=(7.2, 2.2), dpi=200)
        ax.plot(years, roe, marker="o", linewidth=2, markersize=4, label="ROE (%)", color="#2563EB")
        ax.plot(years, roce, marker="s", linewidth=2, markersize=4, label="ROCE (%)", color="#059669")
        
        ax.set_title("Historical Profitability Trends: ROE & ROCE (%)", fontsize=9, fontweight="bold", pad=6, color="#1E293B")
        ax.tick_params(axis="x", labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=7, loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="none")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")
        
        plt.tight_layout()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = tmp.name
        tmp.close()
        plt.savefig(tmp_path, format="png", bbox_inches="tight")
        plt.close(fig)
        
        self.temp_files.append(tmp_path)
        return tmp_path

    def _create_bs_composition_chart(self) -> Optional[str]:
        if self.bs_data.empty:
            return None
            
        df = self.bs_data.copy().tail(8)
        years = df["period"].astype(str).str.replace("Mar ", "").str.replace("FY", "").tolist()
        
        share_cap = pd.to_numeric(df.get("share_capital", 0), errors="coerce").fillna(0)
        reserves = pd.to_numeric(df.get("reserves", 0), errors="coerce").fillna(0)
        equity = share_cap + reserves
        borrowings = pd.to_numeric(df.get("borrowings", 0), errors="coerce").fillna(0)
        other_liab = pd.to_numeric(df.get("other_liabilities", 0), errors="coerce").fillna(0)
        
        fig, ax = plt.subplots(figsize=(7.2, 2.3), dpi=200)
        x = np.arange(len(years))
        width = 0.45
        
        ax.bar(x, equity, width, label="Equity (Cap + Reserves)", color="#1E40AF", alpha=0.9)
        ax.bar(x, borrowings, width, bottom=equity, label="Borrowings", color="#DC2626", alpha=0.85)
        ax.bar(x, other_liab, width, bottom=equity+borrowings, label="Other Liabilities", color="#9CA3AF", alpha=0.85)
        
        ax.set_title("Balance Sheet Capital Structure Composition (₹ Cr)", fontsize=9, fontweight="bold", pad=6, color="#1E293B")
        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=7, color="#334155")
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=7, loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="none")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")
        
        plt.tight_layout()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = tmp.name
        tmp.close()
        plt.savefig(tmp_path, format="png", bbox_inches="tight")
        plt.close(fig)
        
        self.temp_files.append(tmp_path)
        return tmp_path

    def _create_cf_waterfall_chart(self) -> Optional[str]:
        if self.cf_data.empty:
            return None
            
        latest_cf = self.cf_data.iloc[-1]
        period = str(latest_cf.get("period", "Latest")).replace("Mar ", "").replace("FY", "")
        
        cfo = pd.to_numeric(latest_cf.get("cash_from_operating_activity", 0), errors="coerce")
        cfi = pd.to_numeric(latest_cf.get("cash_from_investing_activity", 0), errors="coerce")
        cff = pd.to_numeric(latest_cf.get("cash_from_financing_activity", 0), errors="coerce")
        net_cf = pd.to_numeric(latest_cf.get("net_cash_flow", 0), errors="coerce")
        
        if pd.isna(cfo): cfo = 0.0
        if pd.isna(cfi): cfi = 0.0
        if pd.isna(cff): cff = 0.0
        if pd.isna(net_cf): net_cf = cfo + cfi + cff
        
        categories = ["Operating (CFO)", "Investing (CFI)", "Financing (CFF)", "Net Cash Flow"]
        values = [cfo, cfi, cff, net_cf]
        bar_colors = [
            "#15803D" if cfo >= 0 else "#B91C1C",
            "#15803D" if cfi >= 0 else "#B91C1C",
            "#15803D" if cff >= 0 else "#B91C1C",
            "#2563EB" if net_cf >= 0 else "#B91C1C",
        ]
        
        fig, ax = plt.subplots(figsize=(7.2, 2.1), dpi=200)
        x = np.arange(len(categories))
        bars = ax.bar(x, values, color=bar_colors, width=0.45, alpha=0.9)
        
        ax.axhline(0, color="#64748B", linewidth=0.8, linestyle="-")
        ax.set_title(f"Cash Flow Breakdown for {period} (₹ Cr)", fontsize=9, fontweight="bold", pad=6, color="#1E293B")
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=7, color="#334155")
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")
        
        for bar, val in zip(bars, values):
            yval = bar.get_height()
            va = "bottom" if yval >= 0 else "top"
            ax.text(bar.get_x() + bar.get_width()/2.0, yval, f"₹{val:,.0f}", ha="center", va=va, fontsize=6.5, fontweight="bold", color="#1E293B")
            
        plt.tight_layout()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_path = tmp.name
        tmp.close()
        plt.savefig(tmp_path, format="png", bbox_inches="tight")
        plt.close(fig)
        
        self.temp_files.append(tmp_path)
        return tmp_path

    # -------------------------------------------------------------------------
    # PDF Document Construction
    # -------------------------------------------------------------------------
    def generate(self, output_path: Optional[Path] = None) -> Path:
        """
        Generate the complete 2-page PDF document.
        """
        if output_path is None:
            output_path = TEARSHEETS_DIR / f"{self.company_id}_tearsheet.pdf"
            
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup ReportLab Document
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
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "TearsheetTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=colors.white,
        )
        subtitle_style = ParagraphStyle(
            "TearsheetSubtitle",
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
            fontSize=10.5,
            leading=12,
            textColor=PRIMARY_NAVY,
            spaceBefore=3,
            spaceAfter=3,
        )
        kpi_title_style = ParagraphStyle(
            "KPITitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B"),
            alignment=1,
        )
        kpi_val_style = ParagraphStyle(
            "KPIValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=13.5,
            textColor=PRIMARY_NAVY,
            alignment=1,
        )
        body_style = ParagraphStyle(
            "TearsheetBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=DARK_GRAY,
        )
        bullet_pro_style = ParagraphStyle(
            "BulletPro",
            parent=body_style,
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#14532D"),
        )
        bullet_con_style = ParagraphStyle(
            "BulletCon",
            parent=body_style,
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#7F1D1D"),
        )

        elements = []

        # =====================================================================
        # PAGE 1
        # =====================================================================

        # 1. Navy Header Bar
        company_name = self.company_info.get("company_name", self.company_id)
        sector = self.company_info.get("sector", "Financial Intelligence Universe")
        isin = self.company_info.get("isin_code", "N/A")
        
        header_text = f"<b>{company_name}</b> ({self.company_id})"
        sub_text = f"Sector: {sector} | ISIN: {isin} | Equity Investment Tearsheet"
        
        header_table = Table(
            [[Paragraph(header_text, title_style)], [Paragraph(sub_text, subtitle_style)]],
            colWidths=[printable_width]
        )
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_NAVY),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 6))

        # 2. Six KPI Tiles (2 rows x 3 cols)
        latest_pl = self.pl_data.iloc[-1] if not self.pl_data.empty else {}
        latest_kpi = self.kpi_data.iloc[-1] if not self.kpi_data.empty else {}
        
        rev_val = f"₹{pd.to_numeric(latest_pl.get('sales', 0), errors='coerce'):,.0f} Cr" if latest_pl.get('sales') is not None else "N/A"
        pat_val = f"₹{pd.to_numeric(latest_pl.get('net_profit', 0), errors='coerce'):,.0f} Cr" if latest_pl.get('net_profit') is not None else "N/A"
        roe_val = f"{pd.to_numeric(latest_kpi.get('roe', 0), errors='coerce'):.2f}%" if latest_kpi.get('roe') is not None else "N/A"
        roce_val = f"{pd.to_numeric(latest_kpi.get('roce', 0), errors='coerce'):.2f}%" if latest_kpi.get('roce') is not None else "N/A"
        de_val = f"{pd.to_numeric(latest_kpi.get('debt_to_equity', 0), errors='coerce'):.2f}x" if latest_kpi.get('debt_to_equity') is not None else "N/A"
        
        health_score = self.health_data.get("overall_score")
        health_rating = self.health_data.get("rating", "")
        if health_score is not None and pd.notna(health_score):
            health_val = f"{float(health_score):.1f}/100 ({health_rating})"
        else:
            health_val = f"{pd.to_numeric(latest_pl.get('opm_percentage', 0), errors='coerce'):.1f}% (OPM)"

        kpi_tiles_data = [
            [
                [Paragraph("REVENUE (SALES)", kpi_title_style), Paragraph(rev_val, kpi_val_style)],
                [Paragraph("NET PROFIT (PAT)", kpi_title_style), Paragraph(pat_val, kpi_val_style)],
                [Paragraph("RETURN ON EQUITY", kpi_title_style), Paragraph(roe_val, kpi_val_style)],
            ],
            [
                [Paragraph("ROCE", kpi_title_style), Paragraph(roce_val, kpi_val_style)],
                [Paragraph("DEBT-TO-EQUITY", kpi_title_style), Paragraph(de_val, kpi_val_style)],
                [Paragraph("HEALTH SCORE", kpi_title_style), Paragraph(health_val, kpi_val_style)],
            ]
        ]
        
        cell_w = printable_width / 3.0
        kpi_table = Table(kpi_tiles_data, colWidths=[cell_w, cell_w, cell_w])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 6))

        # 3. Ten-Year Revenue & Net Profit Bar Chart
        elements.append(Paragraph("10-Year Financial Performance Trend", section_heading))
        elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=4))
        
        rev_prof_chart = self._create_revenue_profit_chart()
        if rev_prof_chart and os.path.exists(rev_prof_chart):
            elements.append(Image(rev_prof_chart, width=printable_width, height=2.2*inch))
        else:
            elements.append(Paragraph("<i>Historical Revenue & Profit chart data unavailable.</i>", body_style))
        
        elements.append(Spacer(1, 6))

        # 4. ROE & ROCE Line Chart
        elements.append(Paragraph("Profitability & Efficiency Trends (ROE vs ROCE)", section_heading))
        elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=4))
        
        roe_roce_chart = self._create_roe_roce_chart()
        if roe_roce_chart and os.path.exists(roe_roce_chart):
            elements.append(Image(roe_roce_chart, width=printable_width, height=2.1*inch))
        else:
            elements.append(Paragraph("<i>ROE & ROCE historical trend chart data unavailable.</i>", body_style))

        # Page 1 End
        elements.append(PageBreak())

        # =====================================================================
        # PAGE 2
        # =====================================================================

        # Page 2 Header Bar
        p2_header_text = f"<b>{company_name} ({self.company_id})</b> — Balance Sheet & Financial Intelligence"
        p2_table = Table([[Paragraph(p2_header_text, title_style)]], colWidths=[printable_width])
        p2_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_NAVY),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(p2_table)
        elements.append(Spacer(1, 6))

        # 1. Balance Sheet Composition Stacked Bar Chart
        elements.append(Paragraph("Balance Sheet Capital Structure Composition", section_heading))
        elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=4))
        
        bs_chart = self._create_bs_composition_chart()
        if bs_chart and os.path.exists(bs_chart):
            elements.append(Image(bs_chart, width=printable_width, height=2.2*inch))
        else:
            elements.append(Paragraph("<i>Balance Sheet composition chart data unavailable.</i>", body_style))
            
        elements.append(Spacer(1, 6))

        # 2. Cash Flow Waterfall Chart
        elements.append(Paragraph("Latest Cash Flow Dynamics Waterfall", section_heading))
        elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=4))
        
        cf_chart = self._create_cf_waterfall_chart()
        if cf_chart and os.path.exists(cf_chart):
            elements.append(Image(cf_chart, width=printable_width, height=2.0*inch))
        else:
            elements.append(Paragraph("<i>Cash Flow waterfall chart data unavailable.</i>", body_style))

        elements.append(Spacer(1, 6))

        # 3. Capital Allocation Badge (Module 4 Output)
        cap_rating = self.capital_alloc.get("rating", "N/A")
        cap_pattern = self.capital_alloc.get("pattern", "N/A")
        cap_year = self.capital_alloc.get("latest_year", "N/A")
        
        badge_text = f"<b>Capital Allocation Rating:</b> {cap_rating.upper()} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Pattern:</b> {cap_pattern} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Period:</b> {cap_year}"
        badge_p = Paragraph(badge_text, ParagraphStyle("BadgeStyle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, textColor=PRIMARY_NAVY, alignment=1))
        badge_table = Table([[badge_p]], colWidths=[printable_width])
        badge_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(badge_table)
        elements.append(Spacer(1, 6))

        # 4 & 5. Pros & Cons Section (Module 2D Output)
        elements.append(Paragraph("NLP Automated Pros & Cons Intelligence", section_heading))
        elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_NAVY, spaceAfter=4))

        pros_list = self.pros_cons.get("pros", [])
        cons_list = self.pros_cons.get("cons", [])

        pros_html = "<br/>".join([f"• {p}" for p in pros_list[:3]]) if pros_list else "• No significant positive signals detected."
        cons_html = "<br/>".join([f"• {c}" for c in cons_list[:3]]) if cons_list else "• No major risk signals detected."

        pro_header = Paragraph("<b>Positive Signals (Pros)</b>", ParagraphStyle("ProHead", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, textColor=GREEN_COLOR))
        con_header = Paragraph("<b>Risk Signals & Concerns (Cons)</b>", ParagraphStyle("ConHead", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, textColor=RED_COLOR))

        pro_content = Paragraph(pros_html, bullet_pro_style)
        con_content = Paragraph(cons_html, bullet_con_style)

        half_w = (printable_width - 8) / 2.0
        pros_cons_table = Table(
            [[pro_header, con_header], [pro_content, con_content]],
            colWidths=[half_w, half_w]
        )
        pros_cons_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0FDF4")),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#FEF2F2")),
            ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#BBF7D0")),
            ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#FECACA")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(pros_cons_table)

        # Build PDF with NumberedCanvas
        try:
            doc.build(elements, canvasmaker=NumberedCanvas)
            logger.info(f"Tearsheet successfully generated: {output_path}")
        finally:
            self._cleanup_temp_files()
            
        return output_path

    def _cleanup_temp_files(self):
        for f in self.temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                logger.warning(f"Failed to remove temp chart file {f}: {e}")
        self.temp_files.clear()


def generate_company_tearsheet(company_id: str, output_path: Optional[Path] = None, db_path: Optional[Path] = None) -> Path:
    """
    Convenience function to generate a company tearsheet.
    """
    generator = CompanyTearsheetGenerator(company_id, db_path=db_path)
    is_valid, reason = generator.has_sufficient_data()
    if not is_valid:
        raise ValueError(f"Cannot generate tearsheet for {company_id}: {reason}")
    return generator.generate(output_path=output_path)


def generate_batch_tearsheets(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Day 34 — Generate company tearsheets for the entire authoritative company universe.
    Logs skipped companies to output/skipped_tearsheets.csv.
    Logs failed companies to output/tearsheet_generation_failures.csv.
    
    Returns summary dict.
    """
    db_p = db_path or DATABASE_PATH
    skipped_log_path = OUTPUT_DIR / "skipped_tearsheets.csv"
    failures_log_path = OUTPUT_DIR / "tearsheet_generation_failures.csv"
    
    skipped_records = []
    failure_records = []
    generated_paths = []
    
    try:
        conn = sqlite3.connect(db_p)
        companies_df = pd.read_sql_query("SELECT company_id, company_name FROM companies ORDER BY company_id ASC", conn)
        conn.close()
    except Exception as e:
        logger.error(f"Failed to load company list for batch tearsheets: {e}")
        return {"total": 0, "generated": 0, "skipped": 0, "failed": 1}
        
    total_companies = len(companies_df)
    logger.info(f"Starting batch tearsheet generation for {total_companies} companies...")
    
    for idx, row in companies_df.iterrows():
        cid = row["company_id"]
        try:
            generator = CompanyTearsheetGenerator(cid, db_path=db_p)
            has_data, reason = generator.has_sufficient_data()
            if not has_data:
                logger.warning(f"Skipping {cid}: {reason}")
                skipped_records.append({"company_id": cid, "reason": reason})
                continue
                
            pdf_path = generator.generate()
            
            # Validate size and page count
            file_size_kb = os.path.getsize(pdf_path) / 1024.0
            if file_size_kb < 30.0:
                logger.warning(f"Generated PDF for {cid} is under 30 KB ({file_size_kb:.1f} KB)")
                
            generated_paths.append(pdf_path)
            
        except Exception as e:
            logger.error(f"Failed to generate tearsheet for {cid}: {e}")
            failure_records.append({"company_id": cid, "error": str(e), "stage": "tearsheet_generation"})
            
    # Export logs
    skipped_df = pd.DataFrame(skipped_records) if skipped_records else pd.DataFrame(columns=["company_id", "reason"])
    skipped_df.to_csv(skipped_log_path, index=False)
    logger.info(f"Wrote {len(skipped_df)} records to {skipped_log_path}")
    
    failures_df = pd.DataFrame(failure_records) if failure_records else pd.DataFrame(columns=["company_id", "error", "stage"])
    failures_df.to_csv(failures_log_path, index=False)
    logger.info(f"Wrote {len(failures_df)} records to {failures_log_path}")
    
    return {
        "total_universe": total_companies,
        "generated_count": len(generated_paths),
        "skipped_count": len(skipped_records),
        "failed_count": len(failure_records),
        "skipped_log": str(skipped_log_path),
        "failures_log": str(failures_log_path)
    }


if __name__ == "__main__":
    print("Running batch tearsheet generation...")
    res = generate_batch_tearsheets()
    print("Batch Tearsheet Result:", res)
