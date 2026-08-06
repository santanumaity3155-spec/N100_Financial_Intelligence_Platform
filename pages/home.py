"""
Compatibility wrapper for pages.home
N100 Financial Intelligence Platform

This module provides backward compatibility for imports expecting
pages.home by re-exporting from pages.01_home
"""

import sys
from pathlib import Path
import importlib.util

# Import 01_home module dynamically to handle numeric prefix
_pages_dir = Path(__file__).parent
_spec = importlib.util.spec_from_file_location(
    "01_home",
    _pages_dir / "01_home.py"
)
_01_home = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _01_home
_spec.loader.exec_module(_01_home)

# Re-export all public functions and classes
main = _01_home.main
render_year_filter = _01_home.render_year_filter
calculate_home_kpis = _01_home.calculate_home_kpis
get_sector_breakdown = _01_home.get_sector_breakdown
get_top_quality_companies = _01_home.get_top_quality_companies
render_kpi_cards = _01_home.render_kpi_cards
render_sector_breakdown = _01_home.render_sector_breakdown
render_top_quality_companies = _01_home.render_top_quality_companies
render_quick_stats = _01_home.render_quick_stats

__all__ = [
    'main',
    'render_year_filter',
    'calculate_home_kpis',
    'get_sector_breakdown',
    'get_top_quality_companies',
    'render_kpi_cards',
    'render_sector_breakdown',
    'render_top_quality_companies',
    'render_quick_stats',
]
