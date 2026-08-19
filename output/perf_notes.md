# Module 6G Performance Notes

## Test Environment

- **Python version**: 3.14.0
- **OS**: Windows-11-10.0.26200-SP0 (win32)
- **CPU**: 12 Logical Cores
- **RAM**: 15.64 GB
- **SQLite version**: 3.50.4
- **FastAPI version**: 0.116.1
- **Streamlit version**: 1.60.0

## Screener Load Test

- **Requests**: 10
- **Concurrency**: 10
- **Total time**: 0.203 seconds
- **Successful**: 10
- **Failed**: 0
- **Target**: <= 10 seconds
- **Status**: PASS

## Company Profile Performance

| Ticker | Duration | Target | Status |
|--------|----------|--------|--------|
| ABB | 0.346 sec | < 3 seconds | PASS |
| ADANIENSOL | 0.189 sec | < 3 seconds | PASS |
| ADANIENT | 0.203 sec | < 3 seconds | PASS |
| ADANIGREEN | 0.165 sec | < 3 seconds | PASS |
| ADANIPORTS | 0.191 sec | < 3 seconds | PASS |

- **Target**: < 3 seconds each
- **Overall Status**: PASS

## End-to-End Test

- **FastAPI**: PASS
- **Streamlit**: PASS
- **Port 8000**: PASS (Available / Non-conflicting)
- **Port 8501**: PASS (Available / Non-conflicting)
- **Dashboard/API integration**: PASS

## Database Optimization

### Existing indexes:
- `idx_companies_sector` on `companies(sector)`
- `idx_companies_industry` on `companies(industry)`
- `idx_profit_loss_company` on `profit_loss(company_id)`
- `idx_profit_loss_period` on `profit_loss(period)`
- `idx_balance_sheet_company` on `balance_sheet(company_id)`
- `idx_balance_sheet_period` on `balance_sheet(period)`
- `idx_cash_flow_company` on `cash_flow(company_id)`
- `idx_cash_flow_period` on `cash_flow(period)`
- `idx_financial_ratios_company` on `financial_ratios(company_id)`
- `idx_financial_ratios_period` on `financial_ratios(period)`
- `idx_financial_kpis_company` on `financial_kpis(company_id)`
- `idx_financial_kpis_period` on `financial_kpis(period)`
- `idx_financial_kpis_company_period` on `financial_kpis(company_id, period)`
- `idx_market_cap_company` on `market_cap(company_id)`
- `idx_market_cap_period` on `market_cap(period)`
- `idx_peer_groups_company` on `peer_groups(company_id)`
- `idx_peer_groups_name` on `peer_groups(peer_group_name)`
- `idx_peer_percentiles_company` on `peer_percentiles(company_id)`

### New indexes added:
- `idx_sectors_company` on `sectors(company_id)`
- `idx_financial_ratios_company_period` on `financial_ratios(company_id, period DESC)`
- `idx_cash_flow_company_period` on `cash_flow(company_id, period DESC)`
- `idx_market_cap_company_period` on `market_cap(company_id, period DESC)`
- `idx_profit_loss_company_period` on `profit_loss(company_id, period DESC)`
- `idx_balance_sheet_company_period` on `balance_sheet(company_id, period DESC)`

### Before/after measurements:
- **Screener Query Execution Time**:
  - Before: 2.353 ms per query
  - After: 2.296 ms per query
  - Improvement: 2.42% reduction in latency & eliminated temporary B-Tree sorting passes in SQLite query plan.

## Bottlenecks

1. **SQLite Singleton Thread Contention**: Global connection object was shared across threads without thread-local isolation, causing `sqlite3.InterfaceError` under concurrent load.
2. **Missing `sectors` table index**: Queries joining `sectors` performed full table scans.
3. **Temp B-Tree Sorting**: Ordering by `period DESC` without compound `(company_id, period DESC)` indexes required temporary B-Tree sorts.

## Fixes Applied

1. Refactored `DatabaseConnection` in `src/database/connection.py` to use `threading.local()` for thread-safe SQLite connection management.
2. Created index `idx_sectors_company` on `sectors(company_id)`.
3. Created compound `(company_id, period DESC)` indexes on financial metrics tables to eliminate temporary B-Tree sorting.
4. Corrected dict key access for `sqlite3.Row` objects in `screener.py`.

## Remaining Issues

- None. All 10 concurrent requests finish in < 0.25 seconds (target <= 10.0s), and all 5 company profile loads finish in < 0.35 seconds (target < 3.0s each).
