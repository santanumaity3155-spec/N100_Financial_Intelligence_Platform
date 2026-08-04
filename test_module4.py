"""
Module 4 Test Suite - N100 Financial Intelligence Platform
Sprint 4 - Module 4 Implementation Validation

This script tests all four dashboard pages:
- 05_trends.py (Trend Analysis)
- 06_sectors.py (Sector Analysis)
- 07_capital.py (Capital Allocation)
- 08_reports.py (Annual Reports)
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Test results
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "errors": [],
}


def test_import(module_name: str, import_path: str) -> bool:
    """
    Test if a module can be imported successfully.
    
    Parameters
    ----------
    module_name : str
        Name of the module for logging.
    import_path : str
        Import path to test.
    
    Returns
    -------
    bool
        True if import successful, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        __import__(import_path)
        logger.info(f"PASS: {module_name} import successful")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: {module_name} import failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"{module_name}: {str(e)}")
        return False


def test_page_compilation(page_path: str) -> bool:
    """
    Test if a page file compiles without syntax errors.
    
    Parameters
    ----------
    page_path : str
        Path to the page file.
    
    Returns
    -------
    bool
        True if compilation successful, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, page_path, 'exec')
        logger.info(f"PASS: {page_path} compiles successfully")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: {page_path} compilation failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"{page_path}: {str(e)}")
        return False


def test_database_helpers() -> bool:
    """
    Test if required database helper functions exist.
    
    Returns
    -------
    bool
        True if all helpers exist, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        import src.dashboard.utils.db as db_module
        
        required_functions = [
            "get_companies",
            "get_ratios",
            "get_pl",
            "get_cf",
            "get_bs",
            "get_all_screener_data",
            "_read_df",
        ]
        
        missing = []
        for func_name in required_functions:
            if not hasattr(db_module, func_name) or not callable(getattr(db_module, func_name)):
                missing.append(func_name)
        
        if missing:
            raise ImportError(f"Missing functions: {missing}")
        
        logger.info("PASS: All database helper functions available")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: Database helpers test failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"Database helpers: {str(e)}")
        return False


def test_analytics_engines() -> bool:
    """
    Test if analytics engines are available.
    
    Returns
    -------
    bool
        True if analytics engines available, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        # Test peer analysis engine
        from src.analytics.peer import calculate_percentile_rank
        
        # Test cashflow KPIs
        from src.analytics.cashflow_kpis import classify_capital_allocation
        
        logger.info("PASS: Analytics engines available")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: Analytics engines test failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"Analytics engines: {str(e)}")
        return False


def test_visualization_libraries() -> bool:
    """
    Test if visualization libraries are available.
    
    Returns
    -------
    bool
        True if libraries available, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd
        import numpy as np
        import streamlit as st
        
        logger.info("PASS: Visualization libraries available")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: Visualization libraries test failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"Visualization libraries: {str(e)}")
        return False


def test_page_structure(page_path: str, page_name: str) -> bool:
    """
    Test if a page has the required structure.
    
    Parameters
    ----------
    page_path : str
        Path to the page file.
    page_name : str
        Name of the page for logging.
    
    Returns
    -------
    bool
        True if structure is correct, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            "st.set_page_config",
            "st.title",
            "def main()",
            "if __name__",
        ]
        
        missing = []
        for element in required_elements:
            if element not in content:
                missing.append(element)
        
        if missing:
            raise ValueError(f"Missing required elements: {missing}")
        
        logger.info(f"PASS: {page_name} has correct structure")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: {page_name} structure test failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"{page_name}: {str(e)}")
        return False


def test_error_handling(page_path: str, page_name: str) -> bool:
    """
    Test if a page has proper error handling.
    
    Parameters
    ----------
    page_path : str
        Path to the page file.
    page_name : str
        Name of the page for logging.
    
    Returns
    -------
    bool
        True if error handling is present, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for error handling patterns
        error_patterns = [
            "try:",
            "except",
            "logger.error",
            "st.error",
            "st.warning",
        ]
        
        missing = []
        for pattern in error_patterns:
            if pattern not in content:
                missing.append(pattern)
        
        if missing:
            raise ValueError(f"Missing error handling: {missing}")
        
        logger.info(f"PASS: {page_name} has proper error handling")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: {page_name} error handling test failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"{page_name}: {str(e)}")
        return False


def test_caching(page_path: str, page_name: str) -> bool:
    """
    Test if a page uses caching properly.
    
    Parameters
    ----------
    page_path : str
        Path to the page file.
    page_name : str
        Name of the page for logging.
    
    Returns
    -------
    bool
        True if caching is used, False otherwise.
    """
    test_results["total_tests"] += 1
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for caching decorator
        if "@st.cache_data" not in content:
            raise ValueError("Missing @st.cache_data decorator")
        
        logger.info(f"PASS: {page_name} uses caching")
        test_results["passed_tests"] += 1
        return True
    except Exception as e:
        logger.error(f"FAIL: {page_name} caching test failed: {str(e)}")
        test_results["failed_tests"] += 1
        test_results["errors"].append(f"{page_name}: {str(e)}")
        return False


def run_all_tests() -> dict:
    """
    Run all tests and return results.
    
    Returns
    -------
    dict
        Test results dictionary.
    """
    logger.info("=" * 80)
    logger.info("STARTING MODULE 4 TEST SUITE")
    logger.info("=" * 80)
    
    # Test 1: Import tests
    logger.info("\n[1] Testing imports...")
    test_import("pages/05_trends", "pages.05_trends")
    test_import("pages/06_sectors", "pages.06_sectors")
    test_import("pages/07_capital", "pages.07_capital")
    test_import("pages/08_reports", "pages.08_reports")
    
    # Test 2: Database helpers
    logger.info("\n[2] Testing database helpers...")
    test_database_helpers()
    
    # Test 3: Analytics engines
    logger.info("\n[3] Testing analytics engines...")
    test_analytics_engines()
    
    # Test 4: Visualization libraries
    logger.info("\n[4] Testing visualization libraries...")
    test_visualization_libraries()
    
    # Test 5: Page compilation
    logger.info("\n[5] Testing page compilation...")
    test_page_compilation("pages/05_trends.py")
    test_page_compilation("pages/06_sectors.py")
    test_page_compilation("pages/07_capital.py")
    test_page_compilation("pages/08_reports.py")
    
    # Test 6: Page structure
    logger.info("\n[6] Testing page structure...")
    test_page_structure("pages/05_trends.py", "Trend Analysis")
    test_page_structure("pages/06_sectors.py", "Sector Analysis")
    test_page_structure("pages/07_capital.py", "Capital Allocation")
    test_page_structure("pages/08_reports.py", "Annual Reports")
    
    # Test 7: Error handling
    logger.info("\n[7] Testing error handling...")
    test_error_handling("pages/05_trends.py", "Trend Analysis")
    test_error_handling("pages/06_sectors.py", "Sector Analysis")
    test_error_handling("pages/07_capital.py", "Capital Allocation")
    test_error_handling("pages/08_reports.py", "Annual Reports")
    
    # Test 8: Caching
    logger.info("\n[8] Testing caching implementation...")
    test_caching("pages/05_trends.py", "Trend Analysis")
    test_caching("pages/06_sectors.py", "Sector Analysis")
    test_caching("pages/07_capital.py", "Capital Allocation")
    test_caching("pages/08_reports.py", "Annual Reports")
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed_tests']}")
    logger.info(f"Failed: {test_results['failed_tests']}")
    logger.info(f"Success Rate: {(test_results['passed_tests'] / test_results['total_tests'] * 100):.1f}%")
    
    if test_results["errors"]:
        logger.info("\nErrors:")
        for error in test_results["errors"]:
            logger.error(f"  - {error}")
    
    logger.info("=" * 80)
    
    return test_results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with appropriate code
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        logger.info("SUCCESS: All tests passed!")
        sys.exit(0)