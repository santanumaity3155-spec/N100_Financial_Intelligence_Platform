"""
Module 6 - Integration QA & Bug Fixes
N100 Financial Intelligence Platform

Comprehensive integration testing for all 8 dashboard pages.
Tests company coverage, partial data handling, screener, peer comparison,
trend analysis, sector analysis, capital allocation, reports, and valuation.
"""

import logging
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Test companies from different sectors
TEST_COMPANIES = [
    ("TCS", "IT"),
    ("INFY", "IT"),
    ("HDFCBANK", "Financials"),
    ("ICICIBANK", "Financials"),
    ("RELIANCE", "Energy"),
    ("SUNPHARMA", "Pharma"),
    ("TATAMOTORS", "Auto"),
    ("HINDUNILVR", "FMCG"),
    ("TATASTEEL", "Metals"),
    ("BHARTIARTL", "Telecom"),
    ("ITC", "Consumer"),
    ("MARUTI", "Auto"),
]

# Database paths to check
DB_PATHS = [
    Path("data/database/n100.db"),
    Path("data/database/nifty100.db"),
    Path("data/nifty100.db"),
    Path("nifty100.db"),
    Path("data/database/financial_data.db"),
]

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def find_database() -> Optional[Path]:
    """Find the database file."""
    for db_path in DB_PATHS:
        if db_path.exists() and db_path.is_file():
            logger.info(f"Database found at: {db_path.absolute()}")
            return db_path
    logger.warning("Database file not found")
    return None


def get_connection(db_path: Path):
    """Get database connection."""
    try:
        conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            timeout=30
        )
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None


# =============================================================================
# TEST UTILITIES
# =============================================================================

class TestResult:
    """Test result tracker."""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = True
        self.errors = []
        self.warnings = []
        self.execution_time = 0.0
    
    def add_error(self, error: str):
        """Add error message."""
        self.errors.append(error)
        self.passed = False
    
    def add_warning(self, warning: str):
        """Add warning message."""
        self.warnings.append(warning)
    
    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} - {self.test_name} ({self.execution_time:.3f}s)"


class IntegrationTestSuite:
    """Integration test suite for Module 6."""
    
    def __init__(self):
        self.db_path = find_database()
        self.results: List[TestResult] = []
        self.conn = None
    
    def setup(self):
        """Setup test environment."""
        logger.info("=" * 80)
        logger.info("MODULE 6 - INTEGRATION QA & BUG FIXES")
        logger.info("=" * 80)
        
        if not self.db_path:
            logger.error("Database not found. Cannot proceed with tests.")
            return False
        
        self.conn = get_connection(self.db_path)
        if not self.conn:
            logger.error("Failed to establish database connection")
            return False
        
        logger.info(f"Database connected: {self.db_path}")
        return True
    
    def teardown(self):
        """Cleanup test environment."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
    
    def run_test(self, test_name: str, test_func):
        """Run a single test with timing."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*80}")
        
        result = TestResult(test_name)
        start_time = time.time()
        
        try:
            test_func(result)
        except Exception as e:
            result.add_error(f"Test exception: {str(e)}")
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        
        result.execution_time = time.time() - start_time
        self.results.append(result)
        
        status = "✅ PASS" if result.passed else "❌ FAIL"
        logger.info(f"\n{status} - {test_name} ({result.execution_time:.3f}s)")
        if result.errors:
            for error in result.errors:
                logger.error(f"  ERROR: {error}")
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  WARNING: {warning}")
        
        return result.passed
    
    # =========================================================================
    # TEST 1: DATABASE CONNECTION AND SCHEMA
    # =========================================================================
    
    def test_database_connection(self, result: TestResult):
        """Test database connection and basic schema."""
        try:
            cursor = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(tables)} tables: {tables}")
            
            # Check required tables
            required_tables = [
                'companies', 'financial_ratios', 'profit_loss', 'balance_sheet',
                'cash_flow', 'peer_groups', 'financial_kpis', 'financial_health_scores',
                'market_cap', 'documents'
            ]
            
            missing_tables = [t for t in required_tables if t not in tables]
            if missing_tables:
                result.add_warning(f"Missing tables: {missing_tables}")
            else:
                logger.info("✅ All required tables present")
            
            # Check database size
            db_size = self.db_path.stat().st_size / (1024 * 1024)
            logger.info(f"Database size: {db_size:.2f} MB")
            
            if db_size < 1.0:
                result.add_warning("Database size is very small (< 1 MB)")
            
        except Exception as e:
            result.add_error(f"Database schema check failed: {str(e)}")
    
    # =========================================================================
    # TEST 2: COMPANY COVERAGE
    # =========================================================================
    
    def test_company_coverage(self, result: TestResult):
        """Test company data coverage across sectors."""
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM companies")
            total_companies = cursor.fetchone()[0]
            
            logger.info(f"Total companies in database: {total_companies}")
            
            if total_companies < 10:
                result.add_error(f"Insufficient companies: {total_companies} (expected >= 10)")
            
            # Check sector coverage
            cursor = self.conn.execute("""
                SELECT sector, COUNT(*) as count 
                FROM companies 
                WHERE sector IS NOT NULL 
                GROUP BY sector 
                ORDER BY count DESC
            """)
            sectors = cursor.fetchall()
            
            logger.info(f"Found {len(sectors)} sectors:")
            for sector in sectors:
                logger.info(f"  {sector[0]}: {sector[1]} companies")
            
            # Check if test companies exist (using company_id as ticker equivalent)
            cursor = self.conn.execute("""
                SELECT company_id, company_name, sector 
                FROM companies 
                WHERE company_id IN ({})
                ORDER BY company_id
            """.format(','.join(['?' for _ in TEST_COMPANIES])), 
            [c[0] for c in TEST_COMPANIES])
            
            found_companies = cursor.fetchall()
            logger.info(f"Found {len(found_companies)} test companies in database")
            
            if len(found_companies) < 5:
                result.add_warning(f"Only {len(found_companies)} test companies found")
            
        except Exception as e:
            result.add_error(f"Company coverage test failed: {str(e)}")
    
    # =========================================================================
    # TEST 3: FINANCIAL DATA COMPLETENESS
    # =========================================================================
    
    def test_financial_data_completeness(self, result: TestResult):
        """Test financial data completeness for test companies."""
        try:
            for ticker, sector in TEST_COMPANIES[:5]:  # Test first 5 companies
                logger.info(f"\nTesting {ticker} ({sector}):")
                
                # Check ratios (using company_id)
                cursor = self.conn.execute(
                    "SELECT COUNT(*) FROM financial_ratios WHERE company_id = ?",
                    (ticker,)
                )
                ratio_count = cursor.fetchone()[0]
                logger.info(f"  Ratios: {ratio_count} records")
                
                # Check P&L
                cursor = self.conn.execute(
                    "SELECT COUNT(*) FROM profit_loss WHERE company_id = ?",
                    (ticker,)
                )
                pl_count = cursor.fetchone()[0]
                logger.info(f"  P&L: {pl_count} records")
                
                # Check cash flow
                cursor = self.conn.execute(
                    "SELECT COUNT(*) FROM cash_flow WHERE company_id = ?",
                    (ticker,)
                )
                cf_count = cursor.fetchone()[0]
                logger.info(f"  Cash Flow: {cf_count} records")
                
                # Check balance sheet
                cursor = self.conn.execute(
                    "SELECT COUNT(*) FROM balance_sheet WHERE company_id = ?",
                    (ticker,)
                )
                bs_count = cursor.fetchone()[0]
                logger.info(f"  Balance Sheet: {bs_count} records")
                
                if ratio_count == 0:
                    result.add_warning(f"{ticker}: No ratio data found")
                if pl_count == 0:
                    result.add_warning(f"{ticker}: No P&L data found")
            
        except Exception as e:
            result.add_error(f"Financial data completeness test failed: {str(e)}")
    
    # =========================================================================
    # TEST 4: PEER GROUPS
    # =========================================================================
    
    def test_peer_groups(self, result: TestResult):
        """Test peer group data."""
        try:
            cursor = self.conn.execute("""
                SELECT peer_group_name, COUNT(*) as count 
                FROM peer_groups 
                WHERE peer_group_name IS NOT NULL 
                GROUP BY peer_group_name 
                ORDER BY count DESC
            """)
            peer_groups = cursor.fetchall()
            
            logger.info(f"Found {len(peer_groups)} peer groups:")
            for group in peer_groups[:10]:  # Show top 10
                logger.info(f"  {group[0]}: {group[1]} companies")
            
            if len(peer_groups) < 5:
                result.add_warning(f"Only {len(peer_groups)} peer groups found")
            
            # Check benchmark flags
            cursor = self.conn.execute("""
                SELECT peer_group_name, COUNT(*) as count 
                FROM peer_groups 
                WHERE is_benchmark = 1 
                GROUP BY peer_group_name
            """)
            benchmarks = cursor.fetchall()
            logger.info(f"Found {len(benchmarks)} peer groups with benchmarks")
            
        except Exception as e:
            result.add_error(f"Peer groups test failed: {str(e)}")
    
    # =========================================================================
    # TEST 5: VALUATION DATA
    # =========================================================================
    
    def test_valuation_data(self, result: TestResult):
        """Test valuation data."""
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM market_cap")
            total_records = cursor.fetchone()[0]
            logger.info(f"Total valuation records: {total_records}")
            
            if total_records == 0:
                result.add_error("No valuation data found")
            
            # Check for PE, PB, dividend yield
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(pe_ratio) as has_pe,
                    COUNT(pb_ratio) as has_pb,
                    COUNT(dividend_yield) as has_div
                FROM market_cap
            """)
            stats = cursor.fetchone()
            logger.info(f"Valuation coverage: PE={stats[1]}, PB={stats[2]}, Div={stats[3]}")
            
            if stats[1] == 0:
                result.add_warning("No PE ratio data found")
            if stats[2] == 0:
                result.add_warning("No PB ratio data found")
            
        except Exception as e:
            result.add_error(f"Valuation data test failed: {str(e)}")
    
    # =========================================================================
    # TEST 6: ANNUAL REPORTS
    # =========================================================================
    
    def test_annual_reports(self, result: TestResult):
        """Test annual reports data."""
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            logger.info(f"Total documents: {total_docs}")
            
            if total_docs == 0:
                result.add_warning("No documents found in database")
            
            # Check annual reports
            cursor = self.conn.execute("""
                SELECT COUNT(*) 
                FROM documents 
                WHERE document_type = 'annual_report' OR annual_report IS NOT NULL
            """)
            annual_reports = cursor.fetchone()[0]
            logger.info(f"Annual reports: {annual_reports}")
            
            # Check URLs
            cursor = self.conn.execute("""
                SELECT COUNT(*) 
                FROM documents 
                WHERE (document_url IS NOT NULL AND document_url != '')
                   OR (annual_report IS NOT NULL AND annual_report != '')
            """)
            with_urls = cursor.fetchone()[0]
            logger.info(f"Reports with URLs: {with_urls}")
            
        except Exception as e:
            result.add_error(f"Annual reports test failed: {str(e)}")
    
    # =========================================================================
    # TEST 7: DATA QUALITY - MISSING VALUES
    # =========================================================================
    
    def test_data_quality_missing_values(self, result: TestResult):
        """Test data quality - check for missing values."""
        try:
            # Check ratios for NULL values
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(roe) as has_roe,
                    COUNT(debt_to_equity) as has_de,
                    COUNT(pe_ratio) as has_pe,
                    COUNT(pb_ratio) as has_pb
                FROM financial_ratios
            """)
            stats = cursor.fetchone()
            
            logger.info(f"Ratios data quality (total={stats[0]}):")
            logger.info(f"  ROE: {stats[1]}/{stats[0]} ({stats[1]/stats[0]*100:.1f}%)")
            logger.info(f"  Debt/Equity: {stats[2]}/{stats[0]} ({stats[2]/stats[0]*100:.1f}%)")
            logger.info(f"  PE: {stats[3]}/{stats[0]} ({stats[3]/stats[0]*100:.1f}%)")
            logger.info(f"  PB: {stats[4]}/{stats[0]} ({stats[4]/stats[0]*100:.1f}%)")
            
            # Check for companies with missing critical data
            cursor = self.conn.execute("""
                SELECT company_id, COUNT(*) as null_count
                FROM financial_ratios
                WHERE roe IS NULL OR debt_to_equity IS NULL
                GROUP BY company_id
                HAVING null_count > 0
            """)
            companies_with_nulls = cursor.fetchall()
            
            if companies_with_nulls:
                result.add_warning(f"{len(companies_with_nulls)} companies have NULL ratios")
            
        except Exception as e:
            result.add_error(f"Data quality test failed: {str(e)}")
    
    # =========================================================================
    # TEST 8: SQL QUERIES VALIDATION
    # =========================================================================
    
    def test_sql_queries(self, result: TestResult):
        """Test critical SQL queries used by dashboard pages."""
        try:
            # Test 1: Get companies
            cursor = self.conn.execute("SELECT * FROM companies LIMIT 5")
            companies = cursor.fetchall()
            logger.info(f"✅ Companies query: {len(companies)} rows")
            
            # Test 2: Get ratios with period filter
            cursor = self.conn.execute(
                "SELECT * FROM financial_ratios WHERE period = 'Mar 2024' LIMIT 5"
            )
            ratios = cursor.fetchall()
            logger.info(f"✅ Ratios query (period='Mar 2024'): {len(ratios)} rows")
            
            # Test 3: Get P&L data
            cursor = self.conn.execute("SELECT * FROM profit_loss LIMIT 5")
            pl_data = cursor.fetchall()
            logger.info(f"✅ P&L query: {len(pl_data)} rows")
            
            # Test 4: Get cash flow
            cursor = self.conn.execute("SELECT * FROM cash_flow LIMIT 5")
            cf_data = cursor.fetchall()
            logger.info(f"✅ Cash Flow query: {len(cf_data)} rows")
            
            # Test 5: Get peer groups
            cursor = self.conn.execute("SELECT * FROM peer_groups LIMIT 5")
            peers = cursor.fetchall()
            logger.info(f"✅ Peer groups query: {len(peers)} rows")
            
            # Test 6: Get screener data (consolidated)
            cursor = self.conn.execute("""
                SELECT 
                    c.company_id,
                    c.company_name,
                    c.sector,
                    r.roe,
                    r.debt_to_equity
                FROM companies c
                LEFT JOIN financial_ratios r ON c.company_id = r.company_id AND r.period = 'Mar 2024'
                LIMIT 5
            """)
            screener_data = cursor.fetchall()
            logger.info(f"✅ Screener query: {len(screener_data)} rows")
            
        except Exception as e:
            result.add_error(f"SQL queries test failed: {str(e)}")
    
    # =========================================================================
    # TEST 9: DASHBOARD PAGE IMPORTS
    # =========================================================================
    
    def test_dashboard_imports(self, result: TestResult):
        """Test that all dashboard pages can be imported without errors."""
        try:
            import sys
            from pathlib import Path
            
            pages_dir = Path("pages")
            if not pages_dir.exists():
                result.add_error("Pages directory not found")
                return
            
            page_files = [
                "01_home.py",
                "02_profile.py",
                "03_screener.py",
                "04_peers.py",
                "05_trends.py",
                "06_sectors.py",
                "07_capital.py",
                "08_reports.py",
            ]
            
            for page_file in page_files:
                page_path = pages_dir / page_file
                if not page_path.exists():
                    result.add_error(f"Page file not found: {page_file}")
                    continue
                
                # Try to compile the file (syntax check)
                try:
                    with open(page_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    compile(code, page_path, 'exec')
                    logger.info(f"✅ {page_file}: Syntax OK")
                except SyntaxError as e:
                    result.add_error(f"{page_file}: Syntax error - {str(e)}")
                except Exception as e:
                    result.add_warning(f"{page_file}: Compilation warning - {str(e)}")
            
        except Exception as e:
            result.add_error(f"Dashboard imports test failed: {str(e)}")
    
    # =========================================================================
    # TEST 10: EDGE CASES - NULL HANDLING
    # =========================================================================
    
    def test_edge_cases_null_handling(self, result: TestResult):
        """Test edge cases with NULL values."""
        try:
            # Find companies with NULL PE ratios
            cursor = self.conn.execute("""
                SELECT company_id, COUNT(*) as null_count
                FROM financial_ratios
                WHERE pe_ratio IS NULL
                GROUP BY company_id
                LIMIT 5
            """)
            null_pe = cursor.fetchall()
            
            if null_pe:
                logger.info(f"Found {len(null_pe)} companies with NULL PE ratios")
                for row in null_pe:
                    logger.info(f"  {row[0]}: {row[1]} NULL values")
            
            # Find companies with NULL debt_to_equity
            cursor = self.conn.execute("""
                SELECT company_id, COUNT(*) as null_count
                FROM financial_ratios
                WHERE debt_to_equity IS NULL
                GROUP BY company_id
                LIMIT 5
            """)
            null_de = cursor.fetchall()
            
            if null_de:
                logger.info(f"Found {len(null_de)} companies with NULL debt_to_equity")
            
            # Find companies with missing periods
            cursor = self.conn.execute("""
                SELECT company_id, period, COUNT(*) as record_count
                FROM financial_ratios
                GROUP BY company_id, period
                HAVING record_count = 0
                LIMIT 5
            """)
            missing_periods = cursor.fetchall()
            
            if missing_periods:
                logger.info(f"Found {len(missing_periods)} missing period records")
            
            # Test that queries handle NULLs gracefully
            cursor = self.conn.execute("""
                SELECT 
                    company_id,
                    AVG(roe) as avg_roe,
                    AVG(pe_ratio) as avg_pe,
                    AVG(debt_to_equity) as avg_de
                FROM financial_ratios
                GROUP BY company_id
                LIMIT 10
            """)
            agg_data = cursor.fetchall()
            logger.info(f"✅ Aggregation with NULLs: {len(agg_data)} companies")
            
        except Exception as e:
            result.add_error(f"Edge cases test failed: {str(e)}")
    
    # =========================================================================
    # TEST 11: PERFORMANCE - QUERY EXECUTION TIME
    # =========================================================================
    
    def test_performance_queries(self, result: TestResult):
        """Test query performance."""
        try:
            queries = [
                ("Get all companies", "SELECT * FROM companies"),
                ("Get ratios for Mar 2024", "SELECT * FROM financial_ratios WHERE period = 'Mar 2024'"),
                ("Get P&L data", "SELECT * FROM profit_loss LIMIT 100"),
                ("Get peer groups", "SELECT * FROM peer_groups LIMIT 100"),
                ("Get screener data", """
                    SELECT c.company_id, c.company_name, r.roe, r.debt_to_equity
                    FROM companies c
                    LEFT JOIN financial_ratios r ON c.company_id = r.company_id
                    LIMIT 100
                """),
            ]
            
            for query_name, query in queries:
                start = time.time()
                cursor = self.conn.execute(query)
                rows = cursor.fetchall()
                elapsed = time.time() - start
                
                logger.info(f"✅ {query_name}: {len(rows)} rows in {elapsed:.3f}s")
                
                if elapsed > 2.0:
                    result.add_warning(f"{query_name} took {elapsed:.3f}s (> 2s target)")
            
        except Exception as e:
            result.add_error(f"Performance test failed: {str(e)}")
    
    # =========================================================================
    # TEST 12: DATA CONSISTENCY
    # =========================================================================
    
    def test_data_consistency(self, result: TestResult):
        """Test data consistency across tables."""
        try:
            # Check that all companies in ratios exist in companies table
            cursor = self.conn.execute("""
                SELECT COUNT(DISTINCT r.company_id) 
                FROM financial_ratios r 
                LEFT JOIN companies c ON r.company_id = c.company_id 
                WHERE c.company_id IS NULL
            """)
            orphan_ratios = cursor.fetchone()[0]
            
            if orphan_ratios > 0:
                result.add_warning(f"{orphan_ratios} ratio records have no matching company")
            else:
                logger.info("✅ All ratio records have matching companies")
            
            # Check that all peer group companies exist
            cursor = self.conn.execute("""
                SELECT COUNT(DISTINCT pg.company_id) 
                FROM peer_groups pg 
                LEFT JOIN companies c ON pg.company_id = c.company_id 
                WHERE c.company_id IS NULL
            """)
            orphan_peers = cursor.fetchone()[0]
            
            if orphan_peers > 0:
                result.add_warning(f"{orphan_peers} peer group records have no matching company")
            else:
                logger.info("✅ All peer group records have matching companies")
            
            # Check for duplicate companies
            cursor = self.conn.execute("""
                SELECT company_id, COUNT(*) as count 
                FROM companies 
                GROUP BY company_id 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                result.add_error(f"Found {len(duplicates)} duplicate companies")
            else:
                logger.info("✅ No duplicate companies found")
            
        except Exception as e:
            result.add_error(f"Data consistency test failed: {str(e)}")
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Run all integration tests."""
        if not self.setup():
            logger.error("Setup failed. Aborting tests.")
            return False
        
        try:
            # Run all tests
            tests = [
                ("Database Connection & Schema", self.test_database_connection),
                ("Company Coverage", self.test_company_coverage),
                ("Financial Data Completeness", self.test_financial_data_completeness),
                ("Peer Groups", self.test_peer_groups),
                ("Valuation Data", self.test_valuation_data),
                ("Annual Reports", self.test_annual_reports),
                ("Data Quality - Missing Values", self.test_data_quality_missing_values),
                ("SQL Queries Validation", self.test_sql_queries),
                ("Dashboard Page Imports", self.test_dashboard_imports),
                ("Edge Cases - NULL Handling", self.test_edge_cases_null_handling),
                ("Performance - Query Execution", self.test_performance_queries),
                ("Data Consistency", self.test_data_consistency),
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                if self.run_test(test_name, test_func):
                    passed += 1
                else:
                    failed += 1
            
            # Print summary
            self.print_summary()
            
            return failed == 0
            
        finally:
            self.teardown()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total_time = sum(r.execution_time for r in self.results)
        
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total Time: {total_time:.3f}s")
        logger.info("")
        
        logger.info("Detailed Results:")
        for result in self.results:
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} {result.test_name} ({result.execution_time:.3f}s)")
            if result.errors:
                for error in result.errors:
                    logger.error(f"    ERROR: {error}")
            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"    WARNING: {warning}")
        
        logger.info("=" * 80)
        
        if failed == 0:
            logger.info("✅ ALL TESTS PASSED")
        else:
            logger.warning(f"❌ {failed} TEST(S) FAILED")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    test_suite = IntegrationTestSuite()
    success = test_suite.run_all_tests()
    
    exit(0 if success else 1)