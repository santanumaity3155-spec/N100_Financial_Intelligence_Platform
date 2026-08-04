# Sprint 4 Module 3 - Production Readiness Fixes

## Plan Steps

- [ ] 1. Add `_safe_percentile()` helper function to `pages/04_peers.py`
  - Safely converts a value to a float in [0,1]
  - NaN/None → returns `0.0` (safe replacement)
  - Valid numeric in [0,1] → returns as-is
  - Non-numeric / out-of-range → returns `None` (skip metric, log warning)

- [ ] 2. Refactor `build_radar_chart()` in `pages/04_peers.py`
  - Split empty dataframe check and missing `company_id` column check into separate checks with distinct log messages
  - Add execution time tracking
  - Build radar data from valid metrics only (skip invalid/missing metrics)
  - Log missing metrics, invalid percentiles, NaN replacements
  - Keep one-company peer group support (peer average = company value)

- [ ] 3. Update `main()` in `pages/04_peers.py`
  - Change warning message to "No peer comparison data available."

- [ ] 4. Run smoke tests to verify `build_radar_chart(pd.DataFrame(), ...)` returns empty Figure without exception
- [ ] 5. Verify all 9 smoke test scenarios pass
- [ ] 6. Verify peer page still functions correctly
