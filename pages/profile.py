"""
Compatibility wrapper for pages.profile
N100 Financial Intelligence Platform

This module provides backward compatibility for imports expecting
pages.profile by re-exporting from pages.02_profile
"""

import sys
from pathlib import Path
import importlib.util

# Import 02_profile module dynamically to handle numeric prefix
_pages_dir = Path(__file__).parent
_spec = importlib.util.spec_from_file_location(
    "02_profile",
    _pages_dir / "02_profile.py"
)
_02_profile = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _02_profile
_spec.loader.exec_module(_02_profile)

# Re-export all public functions and classes
main = _02_profile.main
get_company_list = _02_profile.get_company_list
get_company_profile = _02_profile.get_company_profile
get_company_kpis = _02_profile.get_company_kpis
get_revenue_data = _02_profile.get_revenue_data
get_roe_roce_data = _02_profile.get_roe_roce_data
get_pros_cons = _02_profile.get_pros_cons
render_company_search = _02_profile.render_company_search
render_company_card = _02_profile.render_company_card
render_kpi_cards = _02_profile.render_kpi_cards
render_revenue_chart = _02_profile.render_revenue_chart
render_roe_roce_chart = _02_profile.render_roe_roce_chart
render_pros_cons = _02_profile.render_pros_cons
render_not_found_message = _02_profile.render_not_found_message

__all__ = [
    'main',
    'get_company_list',
    'get_company_profile',
    'get_company_kpis',
    'get_revenue_data',
    'get_roe_roce_data',
    'get_pros_cons',
    'render_company_search',
    'render_company_card',
    'render_kpi_cards',
    'render_revenue_chart',
    'render_roe_roce_chart',
    'render_pros_cons',
    'render_not_found_message',
]