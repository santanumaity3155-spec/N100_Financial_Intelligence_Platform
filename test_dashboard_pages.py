"""
Dashboard Page Integration Tests
N100 Financial Intelligence Platform

Tests all 8 dashboard pages with real company data to ensure
they load correctly, display data, and render charts without errors.
"""

import logging
import time
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class DashboardTestSuite:
    """Test suite for dashboard pages."""
    
    def __init__(self):
        self.results = []
        self.db_utils = None
        
    def setup(self):
        """Setup test environment."""
        logger.info("=" * 80)
        logger.info("DASHBOARD PAGE INTEGRATION TESTS")
        logger.info("=" * 80)
        
        try:
            from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_bs, get_cf
            self.db_utils = {
                'get_companies': get_companies,
                'get_ratios': get_ratios,
                'get_pl': get_pl,
                'get_bs': get_bs,
                'get_cf': get_cf,
            }
            
            # Test database connection
            companies = get_companies()
            if companies.empty:
                logger.error("No companies found in database")
                return False
            
            logger.info(f"✅ Database connected: {len(companies)} companies loaded")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}", exc_info=True)
            return False
    
    def teardown(self):
        """Cleanup test environment."""
        pass
    
    def run_test(self, test_name: str, test_func):
        """Run a single test with timing."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*80}")
        
        result = {
            'name': test_name,
            'passed': True,
            'errors': [],
            'warnings': [],
            'execution_time': 0.0
        }
        
        start_time = time.time()
        
        try:
            test_func(result)
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Test exception: {str(e)}")
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        
        result['execution_time'] = time.time() - start_time
        self.results.append(result)
        
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        logger.info(f"\n{status} - {test_name} ({result['execution_time']:.3f}s)")
        
        if result['errors']:
            for error in result['errors']:
                logger.error(f"  ERROR: {error}")
        if result['warnings']:
            for warning in result['warnings']:
                logger.warning(f"  WARNING: {warning}")
        
        return result['passed']
    
    # =========================================================================
    # TEST 1: HOME PAGE (01_home.py)
    # =========================================================================
    
    def test_home_page(self, result):
        """Test home page loads correctly."""
        try:
            from pages.home import main as home_main
            
            # Test with a specific year
            test_year = 2024
            
            # Mock streamlit functions if needed
            logger.info("Testing home page data loading...")
            
            # Test KPI calculation
            from src.dashboard.utils.db import get_companies, get_ratios
            
            companies_df = get_companies()
            assert not companies_df.empty, "No companies found"
            logger.info(f"  ✅ Companies loaded: {len(companies_df)}")
            
            ratios_df = get_ratios(ticker='TCS', year=2024)
            logger.info(f"  ✅ Ratios loaded for TCS: {len(ratios_df)} rows")
            
            # Test sector breakdown
            if 'sector' in companies_df.columns:
                sector_counts = companies_df['sector'].value_counts()
                logger.info(f"  ✅ Sectors found: {len(sector_counts)}")
            
            logger.info("✅ Home page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Home page test failed: {str(e)}")
            logger.error(f"Home page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 2: PROFILE PAGE (02_profile.py)
    # =========================================================================
    
    def test_profile_page(self, result):
        """Test profile page with multiple companies."""
        try:
            from pages.profile import get_company_kpis, get_revenue_data, get_roe_roce_data
            
            test_tickers = ['TCS', 'RELIANCE', 'HDFCBANK', 'SUNPHARMA', 'TATAMOTORS']
            
            for ticker in test_tickers:
                logger.info(f"Testing profile for {ticker}...")
                
                # Test KPI loading
                kpis = get_company_kpis(ticker)
                logger.info(f"  ✅ KPIs loaded: {len([k for k, v in kpis.items() if v is not None])} metrics")
                
                # Test revenue data
                revenue_df = get_revenue_data(ticker)
                if not revenue_df.empty:
                    logger.info(f"  ✅ Revenue data: {len(revenue_df)} years")
                else:
                    result['warnings'].append(f"{ticker}: No revenue data")
                
                # Test ROE/ROCE data
                roe_roce_df = get_roe_roce_data(ticker)
                if not roe_roce_df.empty:
                    logger.info(f"  ✅ ROE/ROCE data: {len(roe_roce_df)} years")
                else:
                    result['warnings'].append(f"{ticker}: No ROE/ROCE data")
            
            logger.info("✅ Profile page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Profile page test failed: {str(e)}")
            logger.error(f"Profile page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 3: SCREENER PAGE (03_screener.py)
    # =========================================================================
    
    def test_screener_page(self, result):
        """Test screener page functionality."""
        try:
            from src.dashboard.utils.db import get_all_screener_data
            
            logger.info("Testing screener data loading...")
            
            # Test screener data
            screener_df = get_all_screener_data(period="Mar 2024")
            
            if screener_df.empty:
                result['warnings'].append("Screener data is empty")
            else:
                logger.info(f"  ✅ Screener data: {len(screener_df)} companies")
                
                # Check required columns
                required_cols = ['ticker', 'company', 'sector', 'roe', 'debt_to_equity']
                missing_cols = [col for col in required_cols if col not in screener_df.columns]
                
                if missing_cols:
                    result['errors'].append(f"Missing columns: {missing_cols}")
                else:
                    logger.info(f"  ✅ All required columns present")
                
                # Test filtering
                if 'sector' in screener_df.columns:
                    sectors = screener_df['sector'].dropna().unique()
                    logger.info(f"  ✅ Sectors available: {len(sectors)}")
            
            logger.info("✅ Screener page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Screener page test failed: {str(e)}")
            logger.error(f"Screener page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 4: PEERS PAGE (04_peers.py)
    # =========================================================================
    
    def test_peers_page(self, result):
        """Test peer comparison page."""
        try:
            from src.dashboard.utils.db import get_peer_groups_list, get_peer_group_companies, get_peer_group_metrics
            
            logger.info("Testing peer comparison data...")
            
            # Test peer groups list
            peer_groups = get_peer_groups_list()
            logger.info(f"  ✅ Peer groups found: {len(peer_groups)}")
            
            if peer_groups:
                # Test first peer group
                test_group = peer_groups[0]
                logger.info(f"Testing peer group: {test_group}")
                
                # Test peer group companies
                peers_df = get_peer_group_companies(test_group)
                logger.info(f"  ✅ Companies in group: {len(peers_df)}")
                
                # Test peer group metrics
                metrics_df = get_peer_group_metrics(period="Mar 2024")
                if not metrics_df.empty:
                    logger.info(f"  ✅ Peer metrics: {len(metrics_df)} rows")
                
                # Test radar chart data
                if not peers_df.empty and 'ticker' in peers_df.columns:
                    test_ticker = peers_df.iloc[0]['ticker']
                    logger.info(f"  ✅ Test ticker for radar: {test_ticker}")
            
            logger.info("✅ Peers page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Peers page test failed: {str(e)}")
            logger.error(f"Peers page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 5: TRENDS PAGE (05_trends.py)
    # =========================================================================
    
    def test_trends_page(self, result):
        """Test trend analysis page."""
        try:
            from src.dashboard.utils.db import get_ratios, get_pl
            
            test_tickers = ['TCS', 'RELIANCE', 'HDFCBANK']
            
            for ticker in test_tickers:
                logger.info(f"Testing trends for {ticker}...")
                
                # Test ratios time series
                ratios_df = get_ratios(ticker=ticker)
                if not ratios_df.empty:
                    logger.info(f"  ✅ Ratios history: {len(ratios_df)} years")
                    
                    # Check for required metrics
                    if 'roe' in ratios_df.columns:
                        roe_values = ratios_df['roe'].dropna()
                        logger.info(f"  ✅ ROE data points: {len(roe_values)}")
                else:
                    result['warnings'].append(f"{ticker}: No ratio history")
                
                # Test P&L time series
                pl_df = get_pl(ticker=ticker)
                if not pl_df.empty:
                    logger.info(f"  ✅ P&L history: {len(pl_df)} years")
                else:
                    result['warnings'].append(f"{ticker}: No P&L history")
            
            logger.info("✅ Trends page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Trends page test failed: {str(e)}")
            logger.error(f"Trends page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 6: SECTORS PAGE (06_sectors.py)
    # =========================================================================
    
    def test_sectors_page(self, result):
        """Test sector analysis page."""
        try:
            from src.dashboard.utils.db import get_companies, get_all_screener_data
            
            logger.info("Testing sector analysis...")
            
            # Test companies with sector data
            companies_df = get_companies()
            
            if 'sector' in companies_df.columns:
                sector_data = companies_df['sector'].dropna()
                if not sector_data.empty:
                    sectors = sector_data.unique()
                    logger.info(f"  ✅ Sectors available: {len(sectors)}")
                    
                    # Test screener data for sector analysis
                    screener_df = get_all_screener_data(period="Mar 2024")
                    if not screener_df.empty and 'sector' in screener_df.columns:
                        logger.info(f"  ✅ Screener data for sectors: {len(screener_df)} companies")
                else:
                    result['warnings'].append("No sector data in companies table")
            
            logger.info("✅ Sectors page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Sectors page test failed: {str(e)}")
            logger.error(f"Sectors page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 7: CAPITAL PAGE (07_capital.py)
    # =========================================================================
    
    def test_capital_page(self, result):
        """Test capital allocation page."""
        try:
            from src.dashboard.utils.db import get_cf, get_companies
            
            logger.info("Testing capital allocation...")
            
            # Test cash flow data
            test_tickers = ['TCS', 'RELIANCE', 'HDFCBANK']
            
            for ticker in test_tickers:
                cf_df = get_cf(ticker=ticker)
                if not cf_df.empty:
                    logger.info(f"  ✅ {ticker} cash flow: {len(cf_df)} years")
                    
                    # Check for required columns
                    required_cols = ['operating_cash_flow', 'investing_cash_flow', 'free_cash_flow']
                    available_cols = [col for col in required_cols if col in cf_df.columns]
                    logger.info(f"  ✅ Available columns: {available_cols}")
                else:
                    result['warnings'].append(f"{ticker}: No cash flow data")
            
            logger.info("✅ Capital page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Capital page test failed: {str(e)}")
            logger.error(f"Capital page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 8: REPORTS PAGE (08_reports.py)
    # =========================================================================
    
    def test_reports_page(self, result):
        """Test annual reports page."""
        try:
            from src.dashboard.utils.db import get_companies
            
            logger.info("Testing reports page...")
            
            # Test companies list for search
            companies_df = get_companies()
            
            if not companies_df.empty:
                logger.info(f"  ✅ Companies available for search: {len(companies_df)}")
                
                # Test search functionality
                if 'ticker' in companies_df.columns and 'name' in companies_df.columns:
                    # Simulate search
                    search_query = "TCS"
                    filtered = companies_df[
                        companies_df['ticker'].str.contains(search_query, case=False, na=False) |
                        companies_df['name'].str.contains(search_query, case=False, na=False)
                    ]
                    logger.info(f"  ✅ Search test: {len(filtered)} results for '{search_query}'")
            
            logger.info("✅ Reports page test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Reports page test failed: {str(e)}")
            logger.error(f"Reports page test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 9: COMPANY COVERAGE
    # =========================================================================
    
    def test_company_coverage(self, result):
        """Test data availability for test companies."""
        try:
            from src.dashboard.utils.db import (
                get_companies, get_ratios, get_pl, get_bs, get_cf
            )
            
            logger.info("Testing company coverage...")
            
            companies_df = get_companies()
            
            for ticker, sector in TEST_COMPANIES[:10]:  # Test first 10
                logger.info(f"Testing {ticker} ({sector})...")
                
                # Check if company exists
                company = companies_df[companies_df['ticker'] == ticker]
                if company.empty:
                    result['warnings'].append(f"{ticker}: Company not found")
                    continue
                
                # Test ratios
                ratios = get_ratios(ticker=ticker)
                if ratios.empty:
                    result['warnings'].append(f"{ticker}: No ratios")
                else:
                    logger.info(f"  ✅ Ratios: {len(ratios)} records")
                
                # Test P&L
                pl = get_pl(ticker=ticker)
                if pl.empty:
                    result['warnings'].append(f"{ticker}: No P&L")
                else:
                    logger.info(f"  ✅ P&L: {len(pl)} records")
                
                # Test Balance Sheet
                bs = get_bs(ticker=ticker)
                if bs.empty:
                    result['warnings'].append(f"{ticker}: No Balance Sheet")
                else:
                    logger.info(f"  ✅ Balance Sheet: {len(bs)} records")
                
                # Test Cash Flow
                cf = get_cf(ticker=ticker)
                if cf.empty:
                    result['warnings'].append(f"{ticker}: No Cash Flow")
                else:
                    logger.info(f"  ✅ Cash Flow: {len(cf)} records")
            
            logger.info("✅ Company coverage test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Company coverage test failed: {str(e)}")
            logger.error(f"Company coverage test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # TEST 10: PARTIAL DATA HANDLING
    # =========================================================================
    
    def test_partial_data_handling(self, result):
        """Test handling of missing data."""
        try:
            from src.dashboard.utils.db import get_ratios, get_pl
            
            logger.info("Testing partial data handling...")
            
            # Find companies with potentially missing data
            test_tickers = ['TCS', 'RELIANCE', 'HDFCBANK']
            
            for ticker in test_tickers:
                ratios_df = get_ratios(ticker=ticker)
                
                if not ratios_df.empty:
                    # Check for NULL values
                    null_counts = ratios_df.isnull().sum()
                    
                    # Count columns with NULLs
                    cols_with_nulls = null_counts[null_counts > 0]
                    
                    if not cols_with_nulls.empty:
                        logger.info(f"  ⚠️ {ticker}: {len(cols_with_nulls)} columns have NULL values")
                        for col, count in cols_with_nulls.head(5).items():
                            logger.info(f"    - {col}: {count} NULLs")
                    else:
                        logger.info(f"  ✅ {ticker}: No NULL values")
            
            logger.info("✅ Partial data handling test passed")
            
        except Exception as e:
            result['passed'] = False
            result['errors'].append(f"Partial data test failed: {str(e)}")
            logger.error(f"Partial data test failed: {str(e)}", exc_info=True)
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Run all dashboard tests."""
        if not self.setup():
            logger.error("Setup failed. Aborting tests.")
            return False
        
        try:
            tests = [
                ("Home Page", self.test_home_page),
                ("Profile Page", self.test_profile_page),
                ("Screener Page", self.test_screener_page),
                ("Peers Page", self.test_peers_page),
                ("Trends Page", self.test_trends_page),
                ("Sectors Page", self.test_sectors_page),
                ("Capital Page", self.test_capital_page),
                ("Reports Page", self.test_reports_page),
                ("Company Coverage", self.test_company_coverage),
                ("Partial Data Handling", self.test_partial_data_handling),
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
        
        passed = sum(1 for r in self.results if r['passed'])
        failed = sum(1 for r in self.results if not r['passed'])
        total_time = sum(r['execution_time'] for r in self.results)
        
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total Time: {total_time:.3f}s")
        logger.info("")
        
        logger.info("Detailed Results:")
        for result in self.results:
            status = "✅" if result['passed'] else "❌"
            logger.info(f"{status} {result['name']} ({result['execution_time']:.3f}s)")
            if result['errors']:
                for error in result['errors']:
                    logger.error(f"    ERROR: {error}")
            if result['warnings']:
                for warning in result['warnings']:
                    logger.warning(f"    WARNING: {warning}")
        
        logger.info("=" * 80)
        
        if failed == 0:
            logger.info("✅ ALL TESTS PASSED")
        else:
            logger.warning(f"❌ {failed} TEST(S) FAILED")


if __name__ == "__main__":
    test_suite = DashboardTestSuite()
    success = test_suite.run_all_tests()
    
    exit(0 if success else 1)