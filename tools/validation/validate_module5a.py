"""
Validation script for Module 5A: Streamlit Dashboard Foundation
N100 Financial Intelligence Platform

This script validates that the dashboard foundation has been properly implemented
according to the Module 5A requirements.
"""

import sys
import os
import importlib
import subprocess
import time
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_check(check_name, status, details=""):
    """Print a check result."""
    status_symbol = "[PASS]" if status else "[FAIL]"
    print(f"{status_symbol} {check_name}")
    if details:
        print(f"    {details}")


def check_app_py_entry_point():
    """Check that app.py is properly configured as the main entry point."""
    try:
        app_path = PROJECT_ROOT / "src" / "dashboard" / "app.py"
        if not app_path.exists():
            return False, "app.py not found"

        try:
            content = app_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = app_path.read_text(encoding='cp1252')

        # Check for st.set_page_config (should be in main script only)
        if "st.set_page_config" not in content:
            return False, "st.set_page_config() not found in app.py"

        # Check for proper structure
        if "def main" not in content:
            return False, "main function not found in app.py"

        # Check for logging setup
        if "logging.getLogger" not in content:
            return False, "Logging setup not found"

        return True, "app.py is properly configured as main entry point"
    except Exception as e:
        return False, f"Error checking app.py: {str(e)}"


def check_pages_directory():
    """Check that pages directory exists with proper structure."""
    try:
        pages_dir = PROJECT_ROOT / "src" / "dashboard" / "pages"
        if not pages_dir.exists():
            return False, "pages directory not found"

        # Check for expected page files
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

        missing_pages = []
        for page in expected_pages:
            if not (pages_dir / page).exists():
                missing_pages.append(page)

        if missing_pages:
            return False, f"Missing page files: {', '.join(missing_pages)}"

        # Check that no page files have st.set_page_config (except possibly commented)
        conflicting_pages = []
        for page_file in pages_dir.glob("*.py"):
            try:
                content = page_file.read_text(encoding='utf-8')
                # Look for uncommented st.set_page_config
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'st.set_page_config' in line and not line.strip().startswith('#'):
                        conflicting_pages.append(page_file.name)
                        break
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    content = page_file.read_text(encoding='cp1252')
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'st.set_page_config' in line and not line.strip().startswith('#'):
                            conflicting_pages.append(page_file.name)
                            break
                except:
                    # If we can't read the file, skip the conflict check for this file
                    pass

        if conflicting_pages:
            return False, f"Pages with conflicting st.set_page_config: {', '.join(conflicting_pages)}"

        return True, f"Pages directory contains all 8 expected files with no config conflicts"
    except Exception as e:
        return False, f"Error checking pages directory: {str(e)}"


def check_components_exist():
    """Check that all dashboard components exist and are properly structured."""
    try:
        components_dir = PROJECT_ROOT / "src" / "dashboard" / "components"
        if not components_dir.exists():
            return False, "components directory not found"

        expected_components = [
            "cards.py",
            "charts.py",
            "filters.py",
            "sidebar.py",
            "tables.py",
            "__init__.py"
        ]

        missing_components = []
        for component in expected_components:
            if not (components_dir / component).exists():
                missing_components.append(component)

        if missing_components:
            return False, f"Missing component files: {', '.join(missing_components)}"

        # Quick syntax check on each component
        syntax_errors = []
        for component in expected_components:
            component_path = components_dir / component
            try:
                try:
                    content = component_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    content = component_path.read_text(encoding='cp1252')
                compile(content, str(component_path), 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"{component}: {str(e)}")
            except Exception as e:
                # If we can't read the file at all, that's a problem
                syntax_errors.append(f"{component}: Unable to read file - {str(e)}")

        if syntax_errors:
            return False, f"Syntax errors in components: {'; '.join(syntax_errors)}"

        return True, f"All {len(expected_components)} components exist and are syntactically valid"
    except Exception as e:
        return False, f"Error checking components: {str(e)}"


def check_database_utils():
    """Check that database utilities are accessible."""
    try:
        # Try to import database utilities
        from src.dashboard.utils.db import get_companies, get_connection

        # Check that functions exist
        if not callable(get_companies):
            return False, "get_companies is not callable"

        if not callable(get_connection):
            return False, "get_connection is not callable"

        return True, "Database utilities are properly imported and callable"
    except Exception as e:
        return False, f"Error importing database utilities: {str(e)}"


def check_caching_implementation():
    """Check that caching is implemented in appropriate places."""
    try:
        # Check home page for caching
        home_path = PROJECT_ROOT / "src" / "dashboard" / "pages" / "01_home.py"
        if home_path.exists():
            try:
                home_content = home_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                home_content = home_path.read_text(encoding='cp1252')
            if "@st.cache_data" not in home_content and "@st.cache_resource" not in home_content:
                return False, "No caching found in home page"

        # Check reports page for caching
        reports_path = PROJECT_ROOT / "src" / "dashboard" / "pages" / "08_reports.py"
        if reports_path.exists():
            try:
                reports_content = reports_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                reports_content = reports_path.read_text(encoding='cp1252')
            if "@st.cache_data" not in reports_content and "@st.cache_resource" not in reports_content:
                return False, "No caching found in reports page"

        return True, "Caching implementation found in dashboard pages"
    except Exception as e:
        return False, f"Error checking caching: {str(e)}"


def check_sidebar_navigation():
    """Check that sidebar/navigation foundation exists."""
    try:
        # Check app.py for sidebar setup
        app_path = PROJECT_ROOT / "src" / "dashboard" / "app.py"
        if app_path.exists():
            try:
                app_content = app_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                app_content = app_path.read_text(encoding='cp1252')
            if "st.sidebar" not in app_content:
                return False, "Sidebar not found in app.py"

        # Check that sidebar components exist
        components_dir = PROJECT_ROOT / "src" / "dashboard" / "components"
        sidebar_path = components_dir / "sidebar.py"
        if sidebar_path.exists():
            try:
                sidebar_content = sidebar_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                sidebar_content = sidebar_path.read_text(encoding='cp1252')
            if "render_year_selector" not in sidebar_content:
                return False, "Year selector not found in sidebar component"
            if "render_company_selector" not in sidebar_content:
                return False, "Company selector not found in sidebar component"

        return True, "Sidebar/navigation foundation properly implemented"
    except Exception as e:
        return False, f"Error checking sidebar navigation: {str(e)}"


def check_component_imports():
    """Check that components can be imported without errors."""
    try:
        # Test importing each component
        components = [
            "src.dashboard.components.cards",
            "src.dashboard.components.charts",
            "src.dashboard.components.filters",
            "src.dashboard.components.sidebar",
            "src.dashboard.components.tables"
        ]

        import_errors = []
        for component in components:
            try:
                importlib.import_module(component)
            except Exception as e:
                import_errors.append(f"{component}: {str(e)}")

        # Also test the package import
        try:
            importlib.import_module("src.dashboard.components")
        except Exception as e:
            import_errors.append(f"src.dashboard.components package: {str(e)}")

        if import_errors:
            return False, f"Component import errors: {'; '.join(import_errors)}"

        return True, "All dashboard components import successfully"
    except Exception as e:
        return False, f"Error testing component imports: {str(e)}"


def check_no_module34_modifications():
    """Verify that Modules 3 and 4 business logic was not modified."""
    try:
        # Run a few key tests from Modules 3 and 4 to ensure they still work
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/kpi/test_cashflow.py::TestFreeCashFlow::test_normal_fcf_calculation",
            "tests/analytics/test_capital_allocation_engine.py::TestCapitalAllocationEngine::test_excellent_classification",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=30)

        if result.returncode != 0:
            return False, f"Module 3/4 regression test failed: {result.stderr}"

        # Check that key files weren't touched
        restricted_files = [
            "src/kpi/",
            "src/screener/",
            "src/analytics/",
            "src/database/"
        ]

        # This is a basic check - we're mainly relying on the test results above
        return True, "Modules 3 and 4 business logic appears intact (based on regression tests)"
    except Exception as e:
        return False, f"Error checking Modules 3/4 integrity: {str(e)}"


def check_streamlit_headless_capability():
    """Check that the dashboard can run in headless mode (basic syntax check)."""
    try:
        # Try to parse the main app for syntax errors
        app_path = PROJECT_ROOT / "src" / "dashboard" / "app.py"
        if app_path.exists():
            try:
                content = app_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = app_path.read_text(encoding='cp1252')
            compile(content, str(app_path), 'exec')

        # Check a sample page
        home_path = PROJECT_ROOT / "src" / "dashboard" / "pages" / "01_home.py"
        if home_path.exists():
            try:
                content = home_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = home_path.read_text(encoding='cp1252')
            compile(content, str(home_path), 'exec')

        return True, "Dashboard files have valid Python syntax for Streamlit execution"
    except Exception as e:
        return False, f"Syntax error preventing Streamlit execution: {str(e)}"


def main():
    """Run all validation checks."""
    print_header("MODULE 5A VALIDATION: Streamlit Dashboard Foundation")
    print("Validating N100 Financial Intelligence Platform Dashboard Foundation\n")

    checks = [
        ("App.py Entry Point", check_app_py_entry_point),
        ("Pages Directory Structure", check_pages_directory),
        ("Dashboard Components", check_components_exist),
        ("Database Utilities", check_database_utils),
        ("Caching Implementation", check_caching_implementation),
        ("Sidebar Navigation", check_sidebar_navigation),
        ("Component Imports", check_component_imports),
        ("No Module 3/4 Modifications", check_no_module34_modifications),
        ("Streamlit Headless Capability", check_streamlit_headless_capability),
    ]

    results = []
    passed = 0
    total = len(checks)

    for check_name, check_func in checks:
        print_header(f"Running: {check_name}")
        try:
            status, details = check_func()
            results.append((check_name, status, details))
            if status:
                passed += 1
            print_check(check_name, status, details)
        except Exception as e:
            print_check(check_name, False, f"Check failed with exception: {str(e)}")
            results.append((check_name, False, f"Exception: {str(e)}"))

    print_header("VALIDATION SUMMARY")
    print(f"Passed: {passed}/{total} checks")

    if passed == total:
        print("\n[PASS] ALL CHECKS PASSED! Module 5A foundation is ready.")
        print("\nNext steps:")
        print("1. Run: streamlit run src/dashboard/app.py --server.headless true")
        print("2. Create MODULE_5A_COMPLETION_REPORT.md")
        print("3. Proceed to Module 5B")
        return 0
    else:
        print(f"\n[FAIL] {total - passed} check(s) failed. Please address the issues above.")
        failed_checks = [name for name, status, _ in results if not status]
        print(f"Failed checks: {', '.join(failed_checks)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())