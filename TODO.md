# Sprint 4 – Module 3 Implementation TODO

## Steps

- [x] 0. Analyze task & gather repo understanding
- [x] 1. Inspect database schema & data availability
- [x] 2. Present & approve implementation plan

- [ ] 3. Add minimal read-only DB helper functions to `src/dashboard/utils/db.py`
      - `get_peer_groups_list()`
      - `get_peer_group_companies(group_name)`
      - `get_peer_group_metrics()`
      - `get_all_screener_data()`
      - `get_latest_financial_data()` (shared latest-period loader)

- [ ] 4. Implement `pages/03_screener.py`
      - Screener title/subtitle
      - 10 dynamic sidebar sliders
      - 6 preset buttons (populate sliders + run filter)
      - Sortable result table (15 columns)
      - Live result count
      - CSV export (visible rows, UTF-8)
      - Empty state + error handling
      - Logging

- [ ] 5. Implement `pages/04_peers.py`
      - Peer group dropdown (11 groups)
      - Company selector with search/autocomplete
      - Plotly Scatterpolar radar chart (8 metrics)
      - Peer KPI table with highlights (selected/benchmark/best/worst)
      - Percentile computation (live, reusing Peer Engine)
      - Error handling + logging

- [ ] 6. Run headless smoke-test validation
      - Import checks
      - DB helper tests
      - Screener filter pipeline test
      - Radar data prep test
      - No SQL/runtime/cache errors

- [ ] 7. Produce Module 3 completion report

## Constraints
- Do NOT modify Modules 1–2 pages
- Do NOT modify Sprint 3 engine logic
- Do NOT change DB schema
- Do NOT duplicate filtering/peer/radar logic

