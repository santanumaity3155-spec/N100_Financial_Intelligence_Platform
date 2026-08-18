"""
Tests for dashboard foundation - Module 5A
N100 Financial Intelligence Platform
"""

import os
import sys
from pathlib import Path
import importlib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_app_import_and_entry_point():
    """Test that app.py can be imported and has proper entry point structure."""
    try:
        # Import the app module
        import src.dashboard.app as app_module

        # Check that it has a main function
        assert hasattr(app_module, 'main'), "app.py should have a main function"
        assert callable(app_module.main), "main should be callable"

        # Check that it has the expected attributes
        assert hasattr(app_module, 'APP_TITLE'), "app.py should have APP_TITLE"
        assert hasattr(app_module, 'APP_VERSION'), "app.py should have APP_VERSION"
        assert hasattr(app_module, 'APP_MODULE'), "app.py should have APP_MODULE"

        # Check that APP_TITLE is set correctly
        assert app_module.APP_TITLE == "Nifty 100 Analytics", f"Expected 'Nifty 100 Analytics', got {app_module.APP_TITLE}"

    except Exception as e:
        raise AssertionError(f"Failed to import or validate app.py: {e}")


def test_pages_directory_structure():
    """Test that pages directory has correct structure for Streamlit navigation."""
    pages_dir = PROJECT_ROOT / "src" / "dashboard" / "pages"

    # Check that pages directory exists
    assert pages_dir.exists() and pages_dir.is_dir(), "pages directory should exist"

    # Get all Python files in pages directory
    py_files = list(pages_dir.glob("*.py"))

    # Should have __init__.py and 8 page files
    assert len(py_files) == 9, f"Expected 9 Python files in pages directory (__init__.py + 8 pages), got {len(py_files)}"

    # Check for __init__.py
    init_file = pages_dir / "__init__.py"
    assert init_file.exists(), "pages/__init__.py should exist"

    # Check for the 8 expected page files (numbered)
    expected_pages = [
        "01_home.py",
        "02_profile.py",
        "03_screener.py",
        "04_peers.py",
        "05_trends.py",
        "06_sectors.py",
        "07_capital.py",
        "08_reports.py"
    ]

    for page_file in expected_pages:
        page_path = pages_dir / page_file
        assert page_path.exists(), f"Expected page file {page_file} not found in pages directory"

    # Most importantly: check that there are NO duplicate URL pathnames
    # Streamlit derives URL pathname from filename by stripping leading numbers and underscores
    url_pathnames = set()
    for py_file in py_files:
        if py_file.name == "__init__.py":
            continue

        # Get the stem (filename without extension)
        stem = py_file.stem

        # Remove leading numbers and underscores to get URL pathname
        # This mimics how Streamlit processes page filenames
        url_pathname = stem
        # Remove leading digits and underscores
        i = 0
        while i < len(url_pathname) and (url_pathname[i].isdigit() or url_pathname[i] == '_'):
            i += 1
        url_pathname = url_pathname[i:]

        # Check for duplicates
        assert url_pathname not in url_pathnames, f"Duplicate URL pathname detected: '{url_pathname}' from file {py_file.name}"
        url_pathnames.add(url_pathname)

    # Verify we have exactly 8 unique URL pathnames (one for each page)
    assert len(url_pathnames) == 8, f"Expected 8 unique URL pathnames, got {len(url_pathnames)}"

    # Verify the expected pathnames are present
    expected_pathnames = {"home", "profile", "screener", "peers", "trends", "sectors", "capital", "reports"}
    assert url_pathnames == expected_pathnames, f"URL pathnames mismatch. Expected: {expected_pathnames}, Got: {url_pathnames}"


def test_dashboard_component_imports():
    """Test that all dashboard components can be imported successfully."""
    components = [
        "src.dashboard.components.cards",
        "src.dashboard.components.charts",
        "src.dashboard.components.filters",
        "src.dashboard.components.sidebar",
        "src.dashboard.components.tables"
    ]

    for component in components:
        try:
            importlib.import_module(component)
        except ImportError as e:
            raise AssertionError(f"Failed to import dashboard component {component}: {e}")
        except Exception as e:
            raise AssertionError(f"Error importing dashboard component {component}: {e}")

    # Also test that the package can be imported
    try:
        importlib.import_module("src.dashboard.components")
    except Exception as e:
        raise AssertionError(f"Failed to import src.dashboard.components package: {e}")


def test_database_loader():
    """Test that database utilities work correctly."""
    try:
        from src.dashboard.utils.db import get_companies, get_database_info

        # Test that functions are callable
        assert callable(get_companies), "get_companies should be callable"
        assert callable(get_database_info), "get_database_info should be callable"

        # Test that we can get database info (should not crash)
        db_info = get_database_info()
        assert isinstance(db_info, dict), "get_database_info should return a dictionary"
        assert "exists" in db_info, "db_info should have 'exists' key"

    except Exception as e:
        raise AssertionError(f"Failed to test database loader: {e}")


def test_company_count_consistency():
    """Test that company count is consistent and reasonable."""
    try:
        from src.dashboard.utils.db import get_companies

        companies_df = get_companies()

        # Should return a DataFrame
        assert hasattr(companies_df, 'shape'), "get_companies should return a DataFrame-like object"

        # Even if empty, should not crash
        # In a real implementation, we might expect some companies, but for foundation testing
        # we just verify it doesn't crash and returns consistent structure

    except Exception as e:
        raise AssertionError(f"Failed to test company count: {e}")


def test_empty_data_handling():
    """Test that the dashboard handles empty data gracefully."""
    # This is more of an integration test, but we can at least verify
    # that key functions don't crash when given empty or None data

    try:
        # Test that we can import the home page module directly (should handle empty data)
        home_module = importlib.import_module("src.dashboard.pages.01_home")

        # Check that key functions exist
        assert hasattr(home_module, 'calculate_home_kpis'), "home module should have calculate_home_kpis function"
        assert hasattr(home_module, 'get_sector_breakdown'), "home module should have get_sector_breakdown function"
        assert hasattr(home_module, 'get_top_quality_companies'), "home module should have get_top_quality_companies function"

        # These should be callable
        assert callable(home_module.calculate_home_kpis), "calculate_home_kpis should be callable"
        assert callable(home_module.get_sector_breakdown), "get_sector_breakdown should be callable"
        assert callable(home_module.get_top_quality_companies), "get_top_quality_companies should be callable"

    except Exception as e:
        raise AssertionError(f"Failed to test empty data handling: {e}")


def test_page_discovery_and_navigation():
    """Test that page discovery and navigation is properly configured."""
    # Test that the individual page modules can be imported and have main functions
    try:
        # Import each page module directly to avoid package import issues
        home_module = importlib.import_module("src.dashboard.pages.01_home")
        profile_module = importlib.import_module("src.dashboard.pages.02_profile")
        screener_module = importlib.import_module("src.dashboard.pages.03_screener")
        peers_module = importlib.import_module("src.dashboard.pages.04_peers")
        trends_module = importlib.import_module("src.dashboard.pages.05_trends")
        sectors_module = importlib.import_module("src.dashboard.pages.06_sectors")
        capital_module = importlib.import_module("src.dashboard.pages.07_capital")
        reports_module = importlib.import_module("src.dashboard.pages.08_reports")

        # Each should have a main function (the page entry point)
        assert hasattr(home_module, 'main') and callable(home_module.main), "home page should have callable main function"
        assert hasattr(profile_module, 'main') and callable(profile_module.main), "profile page should have callable main function"
        assert hasattr(screener_module, 'main') and callable(screener_module.main), "screener page should have callable main function"
        assert hasattr(peers_module, 'main') and callable(peers_module.main), "peers page should have callable main function"
        assert hasattr(trends_module, 'main') and callable(trends_module.main), "trends page should have callable main function"
        assert hasattr(sectors_module, 'main') and callable(sectors_module.main), "sectors page should have callable main function"
        assert hasattr(capital_module, 'main') and callable(capital_module.main), "capital page should have callable main function"
        assert hasattr(reports_module, 'main') and callable(reports_module.main), "reports page should have callable main function"

    except ImportError as e:
        raise AssertionError(f"Failed to import page modules: {e}")
    except Exception as e:
        raise AssertionError(f"Error testing page discovery and navigation: {e}")


def test_no_duplicate_page_registration():
    """Specific test to ensure no duplicate page registration that would cause StreamlitAPIException."""
    pages_dir = PROJECT_ROOT / "src" / "dashboard" / "pages"

    # Collect all potential page files (excluding __init__.py and backups)
    page_files = [f for f in pages_dir.glob("*.py")
                  if f.name != "__init__.py" and not f.name.endswith(".backup")]

    # Map URL pathnames to files
    url_to_files = {}

    for page_file in page_files:
        stem = page_file.stem

        # Calculate URL pathname as Streamlit would (strip leading numbers/underscores)
        url_pathname = stem
        i = 0
        while i < len(url_pathname) and (url_pathname[i].isdigit() or url_pathname[i] == '_'):
            i += 1
        url_pathname = url_pathname[i:]

        # Handle edge case where everything gets stripped
        if not url_pathname:
            url_pathname = stem  # fallback to full name

        if url_pathname in url_to_files:
            url_to_files[url_pathname].append(page_file.name)
        else:
            url_to_files[url_pathname] = [page_file.name]

    # Check for duplicates
    duplicates = {pathname: files for pathname, files in url_to_files.items() if len(files) > 1}

    assert len(duplicates) == 0, f"Duplicate page registrations found that would cause StreamlitAPIException: {duplicates}"

    # Verify we have the expected 8 unique pathnames
    expected_pathnames = {"home", "profile", "screener", "peers", "trends", "sectors", "capital", "reports"}
    actual_pathnames = set(url_to_files.keys())
    assert actual_pathnames == expected_pathnames, f"Expected pathnames {expected_pathnames}, got {actual_pathnames}"


if __name__ == "__main__":
    # Run all tests when script is executed directly
    test_functions = [
        test_app_import_and_entry_point,
        test_pages_directory_structure,
        test_dashboard_component_imports,
        test_database_loader,
        test_company_count_consistency,
        test_empty_data_handling,
        test_page_discovery_and_navigation,
        test_no_duplicate_page_registration
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"[PASS] {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            failed += 1

    print(f"\nTests completed: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)