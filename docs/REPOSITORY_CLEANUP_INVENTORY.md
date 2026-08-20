# Repository Cleanup Inventory

This document provides a comprehensive Phase 1 inventory of all files across the N100 Financial Intelligence Platform repository, classified according to project role, references, deliverable status, and proposed disposition.

| File Path | Category | Reason | Prod Ref | Test Ref | Required Deliverable | Proposed Destination | Proposed Action |
|---|---|---|---|---|---|---|---|
| `.pytest_cache/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `pages\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\analytics\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\api\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\api\routers\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\config\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\dashboard\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\dashboard\components\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\dashboard\pages\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\dashboard\utils\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\database\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\etl\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\health_score\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\nlp\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\reports\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\screener\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `src\validation\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\analytics\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\api\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\dashboard\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\health_score\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\integration\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\kpi\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\nlp\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\performance\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\pipeline\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\reports\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\screener\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tests\validation\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `tools\validation\__pycache__/` | CACHE | Generated cache / runtime metadata directory | No | No | No | `N/A` | **DELETE** |
| `.gitignore` | UNKNOWN | Unclassified repository file | No | No | No | `.gitignore` | **KEEP** |
| `CLEANUP_SUMMARY.md` | DOCUMENTATION | Project documentation file | No | No | No | `CLEANUP_SUMMARY.md` | **KEEP** |
| `NIFTY_SMALL_100.db` | PRODUCTION | Authoritative SQLite database file required for platform data | No | No | Yes | `NIFTY_SMALL_100.db` | **KEEP** |
| `README.md` | DOCUMENTATION | Project documentation file | No | No | No | `README.md` | **KEEP** |
| `TODO.md` | DOCUMENTATION | Project documentation file | No | No | No | `TODO.md` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_233525.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_233525.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_233525.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_233525.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_234525.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_234525.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_234525.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_234525.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235035.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235035.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235035.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235035.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235208.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235208.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235208.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235208.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235339.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235339.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235339.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235339.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235459.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235459.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260710_235459.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260710_235459.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000213.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000213.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000213.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000213.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000312.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000312.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000312.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000312.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000424.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000424.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000424.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000424.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000517.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000517.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000517.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000517.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000558.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000558.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000558.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000558.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000649.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000649.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000649.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000649.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000933.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000933.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_000933.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_000933.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001031.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001031.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001031.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001031.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001253.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001253.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001253.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001253.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001431.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001431.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001431.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001431.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001601.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001601.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001601.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001601.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001710.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001710.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001710.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001710.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001923.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001923.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_001923.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_001923.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_002223.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_002223.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_002223.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_002223.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_002316.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_002316.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_002316.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_002316.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_002433.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_002433.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_002433.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_002433.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005035.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005035.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005035.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005035.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005242.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005242.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005242.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005242.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005359.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005359.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005359.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005359.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005707.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005707.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005707.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005707.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005833.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005833.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_005833.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_005833.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_011436.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_011436.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260711_011436.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260711_011436.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_230017.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_230017.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_230017.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_230017.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_230034.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_230034.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_230034.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_230034.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_230411.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_230411.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_230411.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_230411.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_231117.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_231117.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_231117.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_231117.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_232503.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_232503.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_232503.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_232503.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_232634.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_232634.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_232634.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_232634.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233049.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233049.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233049.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233049.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233200.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233200.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233200.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233200.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233321.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233321.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233321.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233321.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233440.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233440.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233440.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233440.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233607.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233607.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233607.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233607.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233652.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233652.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_233652.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_233652.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_234016.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_234016.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_234016.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_234016.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_234113.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_234113.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_234113.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_234113.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_235029.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_235029.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_235029.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_235029.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_235215.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_235215.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260713_235215.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260713_235215.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_000515.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_000515.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_000515.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_000515.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_113148.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_113148.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_113148.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_113148.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_114222.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_114222.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_114222.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_114222.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_115507.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_115507.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_115507.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_115507.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_120427.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_120427.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_120427.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_120427.json` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_120440.html` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_120440.html` | **KEEP** |
| `archive\diagnostics\data_quality\data_quality_report_20260714_120440.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/data_quality/data_quality_report_20260714_120440.json` | **KEEP** |
| `archive\diagnostics\kpi_test\kpi_results.csv` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/kpi_test/kpi_results.csv` | **KEEP** |
| `archive\diagnostics\kpi_test\kpi_results.json` | UNKNOWN | Unclassified repository file | No | No | No | `archive/diagnostics/kpi_test/kpi_results.json` | **KEEP** |
| `data\database\NIFTY_SMALL_100.db` | PRODUCTION | Authoritative SQLite database file required for platform data | No | No | Yes | `data/database/NIFTY_SMALL_100.db` | **KEEP** |
| `data\database\financial_data.db` | PRODUCTION | Authoritative SQLite database file required for platform data | No | Yes | Yes | `data/database/financial_data.db` | **KEEP** |
| `data\database\n100.db` | PRODUCTION | Authoritative SQLite database file required for platform data | Yes | Yes | Yes | `data/database/n100.db` | **KEEP** |
| `data\database\n100.db-shm` | PRODUCTION | Authoritative SQLite database file required for platform data | Yes | Yes | Yes | `data/database/n100.db-shm` | **KEEP** |
| `data\database\n100.db-wal` | PRODUCTION | Authoritative SQLite database file required for platform data | Yes | Yes | Yes | `data/database/n100.db-wal` | **KEEP** |
| `data\load_audit.csv` | PRODUCTION | Raw or structured data input file | No | No | Yes | `data/load_audit.csv` | **KEEP** |
| `data\raw\analysis.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/analysis.xlsx` | **KEEP** |
| `data\raw\balancesheet.xlsx` | PRODUCTION | Raw or structured data input file | No | No | Yes | `data/raw/balancesheet.xlsx` | **KEEP** |
| `data\raw\cashflow.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/cashflow.xlsx` | **KEEP** |
| `data\raw\companies.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/companies.xlsx` | **KEEP** |
| `data\raw\documents.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/documents.xlsx` | **KEEP** |
| `data\raw\financial_ratios.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/financial_ratios.xlsx` | **KEEP** |
| `data\raw\market_cap.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/market_cap.xlsx` | **KEEP** |
| `data\raw\peer_groups.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/peer_groups.xlsx` | **KEEP** |
| `data\raw\profitandloss.xlsx` | PRODUCTION | Raw or structured data input file | No | No | Yes | `data/raw/profitandloss.xlsx` | **KEEP** |
| `data\raw\prosandcons.xlsx` | PRODUCTION | Raw or structured data input file | No | No | Yes | `data/raw/prosandcons.xlsx` | **KEEP** |
| `data\raw\sectors.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/sectors.xlsx` | **KEEP** |
| `data\raw\stock_prices.xlsx` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/raw/stock_prices.xlsx` | **KEEP** |
| `data\validation_failures.csv` | PRODUCTION | Raw or structured data input file | No | Yes | Yes | `data/validation_failures.csv` | **KEEP** |
| `docs\Architecture.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/Architecture.md` | **KEEP** |
| `docs\Demo_Checklist.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/Demo_Checklist.md` | **KEEP** |
| `docs\Project_Summary.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/Project_Summary.md` | **KEEP** |
| `docs\REPOSITORY_CLEANUP_INVENTORY.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/REPOSITORY_CLEANUP_INVENTORY.md` | **KEEP** |
| `docs\REPOSITORY_STRUCTURE.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/REPOSITORY_STRUCTURE.md` | **KEEP** |
| `docs\SPRINT1_REVIEW.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/SPRINT1_REVIEW.md` | **KEEP** |
| `docs\Sprint4_Retrospective.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/Sprint4_Retrospective.md` | **KEEP** |
| `docs\User_Guide.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/User_Guide.md` | **KEEP** |
| `docs\analyst_guide.pdf` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/analyst_guide.pdf` | **KEEP** |
| `docs\completion_reports\MODULE_1_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_1_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_2D_COVERAGE_DIAGNOSTIC_SUMMARY.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_2D_COVERAGE_DIAGNOSTIC_SUMMARY.md` | **KEEP** |
| `docs\completion_reports\MODULE_2_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_2_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_3_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_3_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_3_PRODUCTION_READINESS_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_3_PRODUCTION_READINESS_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_4A_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_4A_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_4B_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_4B_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_4C_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_4C_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_4D_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_4D_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_4_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_4_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_5A_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_5A_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_5B_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_5B_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_5C_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_5C_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_5_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_5_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6A_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6A_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6B_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6B_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6C_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6C_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6D_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6D_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6E_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6E_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6F_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6F_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6G_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6G_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6H_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6H_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6I_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6I_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6J_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6J_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6_PRODUCTION_READINESS_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6_PRODUCTION_READINESS_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_6_QA_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_6_QA_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_7_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_7_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_8_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_8_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\MODULE_9_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/MODULE_9_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\SPRINT5_MODULE_2A_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/SPRINT5_MODULE_2A_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\SPRINT5_MODULE_2B_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/SPRINT5_MODULE_2B_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\SPRINT5_MODULE_2C_COMPLETION_REPORT.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/SPRINT5_MODULE_2C_COMPLETION_REPORT.md` | **KEEP** |
| `docs\completion_reports\SPRINT_5_FINAL_STATUS.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/completion_reports/SPRINT_5_FINAL_STATUS.md` | **KEEP** |
| `docs\etl_validation_summary.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/etl_validation_summary.md` | **KEEP** |
| `docs\manual_data_review.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/manual_data_review.md` | **KEEP** |
| `docs\openapi.json` | DOCUMENTATION | Project documentation file | No | Yes | Yes | `docs/openapi.json` | **KEEP** |
| `docs\postman_collection.json` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/postman_collection.json` | **KEEP** |
| `docs\profit_loss_validation_review.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/profit_loss_validation_review.md` | **KEEP** |
| `docs\screenshots\README.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/screenshots/README.md` | **KEEP** |
| `docs\specifications\MODULE_6J_SPEC_STATUS.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `docs/specifications/MODULE_6J_SPEC_STATUS.md` | **KEEP** |
| `logs\application.log` | UNKNOWN | Unclassified repository file | Yes | Yes | No | `logs/application.log` | **KEEP** |
| `logs\dashboard.log` | UNKNOWN | Unclassified repository file | No | Yes | No | `logs/dashboard.log` | **KEEP** |
| `logs\health_score.log` | UNKNOWN | Unclassified repository file | No | Yes | No | `logs/health_score.log` | **KEEP** |
| `notebooks\exploratory_queries.sql` | DOCUMENTATION | Exploratory data analysis notebook / SQL | No | No | No | `notebooks/exploratory_queries.sql` | **KEEP** |
| `output\NIFTY_SMALL_100.db` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/NIFTY_SMALL_100.db` | **KEEP** |
| `output\acceptance_checklist.pdf` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/acceptance_checklist.pdf` | **KEEP** |
| `output\analysis_parsed.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/analysis_parsed.csv` | **KEEP** |
| `output\capital_allocation_distribution.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/capital_allocation_distribution.csv` | **KEEP** |
| `output\capital_allocation_latest_year.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/capital_allocation_latest_year.csv` | **KEEP** |
| `output\cashflow_intelligence.xlsx` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/cashflow_intelligence.xlsx` | **KEEP** |
| `output\cluster_labels.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/cluster_labels.csv` | **KEEP** |
| `output\cluster_profiles.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/cluster_profiles.csv` | **KEEP** |
| `output\cons_generated.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/cons_generated.csv` | **KEEP** |
| `output\distress_alerts.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/distress_alerts.csv` | **KEEP** |
| `output\final_deliverables\NIFTY_SMALL_100.db` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/NIFTY_SMALL_100.db` | **KEEP** |
| `output\final_deliverables\acceptance_checklist.pdf` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/acceptance_checklist.pdf` | **KEEP** |
| `output\final_deliverables\analysis_parsed.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/analysis_parsed.csv` | **KEEP** |
| `output\final_deliverables\analyst_guide.pdf` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/analyst_guide.pdf` | **KEEP** |
| `output\final_deliverables\api_main.py` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/api_main.py` | **KEEP** |
| `output\final_deliverables\capital_allocation.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/capital_allocation.csv` | **KEEP** |
| `output\final_deliverables\capital_allocation_distribution.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/capital_allocation_distribution.csv` | **KEEP** |
| `output\final_deliverables\capital_allocation_latest_year.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/capital_allocation_latest_year.csv` | **KEEP** |
| `output\final_deliverables\cashflow_intelligence.xlsx` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/cashflow_intelligence.xlsx` | **KEEP** |
| `output\final_deliverables\cluster_labels.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/cluster_labels.csv` | **KEEP** |
| `output\final_deliverables\cluster_profiles.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/cluster_profiles.csv` | **KEEP** |
| `output\final_deliverables\correlation_heatmap.png` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/correlation_heatmap.png` | **KEEP** |
| `output\final_deliverables\dashboard_app.py` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/dashboard_app.py` | **KEEP** |
| `output\final_deliverables\distress_alerts.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/distress_alerts.csv` | **KEEP** |
| `output\final_deliverables\exploratory_queries.sql` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/exploratory_queries.sql` | **KEEP** |
| `output\final_deliverables\financial_health_scores.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/financial_health_scores.csv` | **KEEP** |
| `output\final_deliverables\load_audit.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/load_audit.csv` | **KEEP** |
| `output\final_deliverables\manifest.txt` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/manifest.txt` | **KEEP** |
| `output\final_deliverables\module4_cross_validation.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/module4_cross_validation.csv` | **KEEP** |
| `output\final_deliverables\outlier_report.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/outlier_report.csv` | **KEEP** |
| `output\final_deliverables\parse_failures.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/parse_failures.csv` | **KEEP** |
| `output\final_deliverables\pattern_change_summary.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/pattern_change_summary.csv` | **KEEP** |
| `output\final_deliverables\pattern_changes.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/pattern_changes.csv` | **KEEP** |
| `output\final_deliverables\peer_comparison.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/peer_comparison.csv` | **KEEP** |
| `output\final_deliverables\peer_percentiles.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/peer_percentiles.csv` | **KEEP** |
| `output\final_deliverables\perf_notes.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `output/final_deliverables/perf_notes.md` | **KEEP** |
| `output\final_deliverables\portfolio_stats.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/portfolio_stats.csv` | **KEEP** |
| `output\final_deliverables\portfolio_summary.pdf` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/portfolio_summary.pdf` | **KEEP** |
| `output\final_deliverables\postman_collection.json` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/postman_collection.json` | **KEEP** |
| `output\final_deliverables\pros_cons_generated.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/pros_cons_generated.csv` | **KEEP** |
| `output\final_deliverables\pytest_report.html` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/pytest_report.html` | **KEEP** |
| `output\final_deliverables\ratio_load_summary.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/ratio_load_summary.csv` | **KEEP** |
| `output\final_deliverables\sample_sector_report.pdf` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/sample_sector_report.pdf` | **KEEP** |
| `output\final_deliverables\sample_tearsheet.pdf` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/sample_tearsheet.pdf` | **KEEP** |
| `output\final_deliverables\screener_config.py` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/screener_config.py` | **KEEP** |
| `output\final_deliverables\screener_output.xlsx` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/screener_output.xlsx` | **KEEP** |
| `output\final_deliverables\validation_failures.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/final_deliverables/validation_failures.csv` | **KEEP** |
| `output\final_deliverables\valuation_flags.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/valuation_flags.csv` | **KEEP** |
| `output\final_deliverables\valuation_summary.xlsx` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/final_deliverables/valuation_summary.xlsx` | **KEEP** |
| `output\final_validation_report.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `output/final_validation_report.md` | **KEEP** |
| `output\financial_health_scores.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/financial_health_scores.csv` | **KEEP** |
| `output\integration_test.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/integration_test.csv` | **KEEP** |
| `output\module4_cross_validation.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/module4_cross_validation.csv` | **KEEP** |
| `output\module_2d_coverage_diagnostic.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/module_2d_coverage_diagnostic.csv` | **KEEP** |
| `output\module_2d_coverage_summary.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/module_2d_coverage_summary.csv` | **KEEP** |
| `output\n100_data.db` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/n100_data.db` | **KEEP** |
| `output\outlier_report.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/outlier_report.csv` | **KEEP** |
| `output\parse_failures.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/parse_failures.csv` | **KEEP** |
| `output\pattern_change_summary.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/pattern_change_summary.csv` | **KEEP** |
| `output\pattern_changes.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/pattern_changes.csv` | **KEEP** |
| `output\peer_analysis.log` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/peer_analysis.log` | **KEEP** |
| `output\peer_percentiles.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/peer_percentiles.csv` | **KEEP** |
| `output\peer_reports\RELIANCE.md` | DOCUMENTATION | Project documentation file | No | Yes | Yes | `output/peer_reports/RELIANCE.md` | **KEEP** |
| `output\perf_notes.md` | DOCUMENTATION | Project documentation file | No | No | Yes | `output/perf_notes.md` | **KEEP** |
| `output\portfolio_stats.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/portfolio_stats.csv` | **KEEP** |
| `output\postman_collection.json` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/postman_collection.json` | **KEEP** |
| `output\pros_cons_coverage_failures.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/pros_cons_coverage_failures.csv` | **KEEP** |
| `output\pros_cons_generated.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/pros_cons_generated.csv` | **KEEP** |
| `output\pros_generated.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/pros_generated.csv` | **KEEP** |
| `output\pytest_report.html` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/pytest_report.html` | **KEEP** |
| `output\radar_chart.log` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/radar_chart.log` | **KEEP** |
| `output\radar_charts\TEST.png` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/radar_charts/TEST.png` | **KEEP** |
| `output\ratio_engine.log` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/ratio_engine.log` | **KEEP** |
| `output\ratio_load_summary.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/ratio_load_summary.csv` | **KEEP** |
| `output\skipped_tearsheets.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/skipped_tearsheets.csv` | **KEEP** |
| `output\tearsheet_generation_failures.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/tearsheet_generation_failures.csv` | **KEEP** |
| `output\test.xlsx` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | Yes | Yes | `output/test.xlsx` | **KEEP** |
| `output\valuation_flags.csv` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/valuation_flags.csv` | **KEEP** |
| `output\valuation_summary.xlsx` | GENERATED_OUTPUT | Generated artifact or deliverable output | No | No | Yes | `output/valuation_summary.xlsx` | **KEEP** |
| `pages\01_home.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/01_home.py` | **KEEP** |
| `pages\02_profile.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/02_profile.py` | **KEEP** |
| `pages\03_screener.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/03_screener.py` | **KEEP** |
| `pages\04_peers.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/04_peers.py` | **KEEP** |
| `pages\05_trends.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/05_trends.py` | **KEEP** |
| `pages\06_sectors.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/06_sectors.py` | **KEEP** |
| `pages\07_capital.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/07_capital.py` | **KEEP** |
| `pages\08_reports.py` | PRODUCTION | Root Streamlit pages directory (mirrored in src/dashboard/pages) | No | Yes | No | `pages/08_reports.py` | **KEEP** |
| `reports\correlation_heatmap.png` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | Yes | Yes | `reports/correlation_heatmap.png` | **KEEP** |
| `reports\elbow_plot.png` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | Yes | Yes | `reports/elbow_plot.png` | **KEEP** |
| `reports\portfolio\portfolio_summary.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/portfolio/portfolio_summary.pdf` | **KEEP** |
| `reports\sector\Automobile_Auto_Components_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Automobile_Auto_Components_sector_report.pdf` | **KEEP** |
| `reports\sector\Automobile__Auto_Components_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Automobile__Auto_Components_sector_report.pdf` | **KEEP** |
| `reports\sector\Capital_Goods_Engineering_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Capital_Goods_Engineering_sector_report.pdf` | **KEEP** |
| `reports\sector\Capital_Goods__Engineering_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Capital_Goods__Engineering_sector_report.pdf` | **KEEP** |
| `reports\sector\Conglomerates_Holding_Companies_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Conglomerates_Holding_Companies_sector_report.pdf` | **KEEP** |
| `reports\sector\Conglomerates__Holding_Companies_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Conglomerates__Holding_Companies_sector_report.pdf` | **KEEP** |
| `reports\sector\Construction_Materials_Real_Estate_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Construction_Materials_Real_Estate_sector_report.pdf` | **KEEP** |
| `reports\sector\Construction_Materials__Real_Estate_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Construction_Materials__Real_Estate_sector_report.pdf` | **KEEP** |
| `reports\sector\Energy_Power_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Energy_Power_sector_report.pdf` | **KEEP** |
| `reports\sector\Energy__Power_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Energy__Power_sector_report.pdf` | **KEEP** |
| `reports\sector\FMCG_Consumer_Goods_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/FMCG_Consumer_Goods_sector_report.pdf` | **KEEP** |
| `reports\sector\FMCG__Consumer_Goods_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/FMCG__Consumer_Goods_sector_report.pdf` | **KEEP** |
| `reports\sector\Financial_Services_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Financial_Services_sector_report.pdf` | **KEEP** |
| `reports\sector\Healthcare_Pharma_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Healthcare_Pharma_sector_report.pdf` | **KEEP** |
| `reports\sector\Healthcare__Pharma_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Healthcare__Pharma_sector_report.pdf` | **KEEP** |
| `reports\sector\Information_Technology_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Information_Technology_sector_report.pdf` | **KEEP** |
| `reports\sector\Metals_Mining_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Metals_Mining_sector_report.pdf` | **KEEP** |
| `reports\sector\Metals__Mining_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Metals__Mining_sector_report.pdf` | **KEEP** |
| `reports\sector\Services_Retail_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Services_Retail_sector_report.pdf` | **KEEP** |
| `reports\sector\Services__Retail_sector_report.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/sector/Services__Retail_sector_report.pdf` | **KEEP** |
| `reports\tearsheets\ABB_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ABB_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ADANIENSOL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ADANIENSOL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ADANIENT_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ADANIENT_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ADANIGREEN_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ADANIGREEN_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ADANIPORTS_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ADANIPORTS_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ADANIPOWER_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ADANIPOWER_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\AMBUJACEM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/AMBUJACEM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\APOLLOHOSP_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/APOLLOHOSP_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ASIANPAINT_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ASIANPAINT_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\AXISBANK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/AXISBANK_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BAJAJAUTO_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BAJAJAUTO_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BAJAJFINSV_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BAJAJFINSV_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BAJAJHLDNG_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BAJAJHLDNG_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BAJFINANCE_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BAJFINANCE_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BANKBARODA_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BANKBARODA_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BEL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BEL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BHARTIARTL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BHARTIARTL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BHEL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BHEL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BOSCHLTD_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BOSCHLTD_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BPCL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BPCL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\BRITANNIA_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/BRITANNIA_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\CANBK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/CANBK_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\CHOLAFIN_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/CHOLAFIN_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\CIPLA_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/CIPLA_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\COALINDIA_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/COALINDIA_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\DABUR_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/DABUR_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\DIVISLAB_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/DIVISLAB_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\DLF_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/DLF_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\DMART_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/DMART_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\DRREDDY_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/DRREDDY_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\EICHERMOT_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/EICHERMOT_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\GAIL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/GAIL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\GODREJCP_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/GODREJCP_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\GRASIM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/GRASIM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HAL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HAL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HAVELLS_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HAVELLS_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HCLTECH_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HCLTECH_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HDFCBANK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HDFCBANK_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HDFCLIFE_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HDFCLIFE_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HEROMOTOCO_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HEROMOTOCO_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HINDALCO_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HINDALCO_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\HINDUNILVR_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/HINDUNILVR_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ICICIBANK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ICICIBANK_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ICICIGI_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ICICIGI_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ICICIPRULI_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ICICIPRULI_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\INDIGO_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/INDIGO_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\INDUSINDBK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/INDUSINDBK_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\INFY_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/INFY_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\IOC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/IOC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\IRCTC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/IRCTC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\IRFC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/IRFC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ITC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ITC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\JINDALSTEL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/JINDALSTEL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\JSWENERGY_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/JSWENERGY_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\JSWSTEEL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/JSWSTEEL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\KOTAKBANK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/KOTAKBANK_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\LICI_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/LICI_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\LODHA_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/LODHA_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\LTIM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/LTIM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\LT_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/LT_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\MARUTI_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/MARUTI_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\MM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/MM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\MOTHERSON_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/MOTHERSON_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\NAUKRI_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/NAUKRI_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\NESTLEIND_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/NESTLEIND_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\NHPC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/NHPC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\NTPC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/NTPC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ONGC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ONGC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\PFC_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/PFC_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\PIDILITIND_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/PIDILITIND_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\PNB_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/PNB_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\POWERGRID_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/POWERGRID_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\RECLTD_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/RECLTD_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\RELIANCE_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/RELIANCE_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\SBILIFE_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/SBILIFE_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\SHREECEM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/SHREECEM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\SHRIRAMFIN_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/SHRIRAMFIN_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\SIEMENS_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/SIEMENS_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\SUNPHARMA_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/SUNPHARMA_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TATACONSUM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TATACONSUM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TATAMOTORS_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TATAMOTORS_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TATAPOWER_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TATAPOWER_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TATASTEEL_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TATASTEEL_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TCS_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TCS_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TECHM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TECHM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TITAN_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TITAN_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TORNTPHARM_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TORNTPHARM_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TRENT_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TRENT_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\TVSMOTOR_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/TVSMOTOR_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\ULTRACEMCO_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/ULTRACEMCO_tearsheet.pdf` | **KEEP** |
| `reports\tearsheets\UNIONBANK_tearsheet.pdf` | GENERATED_OUTPUT | Generated report artifact (PDF / HTML / PNG) | No | No | Yes | `reports/tearsheets/UNIONBANK_tearsheet.pdf` | **KEEP** |
| `requirements-dashboard.txt` | UNKNOWN | Unclassified repository file | No | No | No | `requirements-dashboard.txt` | **KEEP** |
| `run_etl.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `run_etl.py` | **KEEP** |
| `scratch\inspect_cf_periods.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_cf_periods.py` | **MOVE** |
| `scratch\inspect_details.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_details.py` | **MOVE** |
| `scratch\inspect_periods.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_periods.py` | **MOVE** |
| `scratch\inspect_schema.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_schema.py` | **MOVE** |
| `scratch\inspect_sectors.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_sectors.py` | **MOVE** |
| `scratch\inspect_tcs.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_tcs.py` | **MOVE** |
| `scratch\scan_raw.txt` | TEMPORARY | Scratch workspace file | No | No | No | `scratch/` | **KEEP** |
| `scratch\test_companies_endpoint_client.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_companies_endpoint_client.py` | **MOVE** |
| `scratch\test_kpi_periods.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_kpi_periods.py` | **MOVE** |
| `scratch\test_mcap.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_mcap.py` | **MOVE** |
| `scratch\test_queries.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_queries.py` | **MOVE** |
| `scratch\test_refined_sector.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_refined_sector.py` | **MOVE** |
| `scratch\test_sector_matching.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_sector_matching.py` | **MOVE** |
| `scratch\test_year_parser.py` | TEST | Root-level test script | No | No | No | `tests/validation/test_year_parser.py` | **MOVE** |
| `src\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/__init__.py` | **KEEP** |
| `src\alerts\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/alerts/__init__.py` | **KEEP** |
| `src\alerts\alerts.py` | PRODUCTION | Core production application source code | No | No | No | `src/alerts/alerts.py` | **KEEP** |
| `src\alerts\notification.py` | PRODUCTION | Core production application source code | No | No | No | `src/alerts/notification.py` | **KEEP** |
| `src\alerts\rules.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/alerts/rules.py` | **KEEP** |
| `src\alerts\watchlist.py` | PRODUCTION | Core production application source code | No | No | No | `src/alerts/watchlist.py` | **KEEP** |
| `src\analytics\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/__init__.py` | **KEEP** |
| `src\analytics\cagr.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/cagr.py` | **KEEP** |
| `src\analytics\capital_allocation_distribution.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/capital_allocation_distribution.py` | **KEEP** |
| `src\analytics\capital_allocation_pattern_changes.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/capital_allocation_pattern_changes.py` | **KEEP** |
| `src\analytics\cashflow.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/cashflow.py` | **KEEP** |
| `src\analytics\cashflow_intelligence.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/cashflow_intelligence.py` | **KEEP** |
| `src\analytics\cashflow_kpis.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/cashflow_kpis.py` | **KEEP** |
| `src\analytics\cluster_profiling.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/cluster_profiling.py` | **KEEP** |
| `src\analytics\clustering.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/clustering.py` | **KEEP** |
| `src\analytics\efficiency.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/efficiency.py` | **KEEP** |
| `src\analytics\growth.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/growth.py` | **KEEP** |
| `src\analytics\leverage.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/leverage.py` | **KEEP** |
| `src\analytics\liquidity.py` | PRODUCTION | Core production application source code | No | No | No | `src/analytics/liquidity.py` | **KEEP** |
| `src\analytics\peer.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/peer.py` | **KEEP** |
| `src\analytics\peer_report.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/peer_report.py` | **KEEP** |
| `src\analytics\profitability.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/profitability.py` | **KEEP** |
| `src\analytics\radar.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/radar.py` | **KEEP** |
| `src\analytics\ratio_engine.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/ratio_engine.py` | **KEEP** |
| `src\analytics\ratios.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/ratios.py` | **KEEP** |
| `src\analytics\sector.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/sector.py` | **KEEP** |
| `src\analytics\statistics.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/statistics.py` | **KEEP** |
| `src\analytics\trends.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/trends.py` | **KEEP** |
| `src\analytics\valuation.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/analytics/valuation.py` | **KEEP** |
| `src\api\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/__init__.py` | **KEEP** |
| `src\api\main.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/api/main.py` | **KEEP** |
| `src\api\routers\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/__init__.py` | **KEEP** |
| `src\api\routers\companies.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/companies.py` | **KEEP** |
| `src\api\routers\documents.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/documents.py` | **KEEP** |
| `src\api\routers\health.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/health.py` | **KEEP** |
| `src\api\routers\peers.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/peers.py` | **KEEP** |
| `src\api\routers\portfolio.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/portfolio.py` | **KEEP** |
| `src\api\routers\screener.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/screener.py` | **KEEP** |
| `src\api\routers\sectors.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/sectors.py` | **KEEP** |
| `src\api\routers\valuation.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/api/routers/valuation.py` | **KEEP** |
| `src\config\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/config/__init__.py` | **KEEP** |
| `src\config\column_mappings.py` | PRODUCTION | Core production application source code | No | No | No | `src/config/column_mappings.py` | **KEEP** |
| `src\config\constants.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/config/constants.py` | **KEEP** |
| `src\config\logging_config.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/config/logging_config.py` | **KEEP** |
| `src\config\settings.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/config/settings.py` | **KEEP** |
| `src\dashboard\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/__init__.py` | **KEEP** |
| `src\dashboard\app.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/dashboard/app.py` | **KEEP** |
| `src\dashboard\components\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/components/__init__.py` | **KEEP** |
| `src\dashboard\components\cards.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/components/cards.py` | **KEEP** |
| `src\dashboard\components\charts.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/components/charts.py` | **KEEP** |
| `src\dashboard\components\filters.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/components/filters.py` | **KEEP** |
| `src\dashboard\components\sidebar.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/components/sidebar.py` | **KEEP** |
| `src\dashboard\components\tables.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/components/tables.py` | **KEEP** |
| `src\dashboard\pages\01_home.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/01_home.py` | **KEEP** |
| `src\dashboard\pages\01_home.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/01_home.py.backup` | **KEEP** |
| `src\dashboard\pages\02_profile.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/02_profile.py` | **KEEP** |
| `src\dashboard\pages\02_profile.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/02_profile.py.backup` | **KEEP** |
| `src\dashboard\pages\03_screener.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/03_screener.py` | **KEEP** |
| `src\dashboard\pages\03_screener.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/03_screener.py.backup` | **KEEP** |
| `src\dashboard\pages\04_peers.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/04_peers.py` | **KEEP** |
| `src\dashboard\pages\04_peers.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/04_peers.py.backup` | **KEEP** |
| `src\dashboard\pages\05_trends.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/05_trends.py` | **KEEP** |
| `src\dashboard\pages\05_trends.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/05_trends.py.backup` | **KEEP** |
| `src\dashboard\pages\06_sectors.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/06_sectors.py` | **KEEP** |
| `src\dashboard\pages\06_sectors.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/06_sectors.py.backup` | **KEEP** |
| `src\dashboard\pages\07_capital.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/07_capital.py` | **KEEP** |
| `src\dashboard\pages\07_capital.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/07_capital.py.backup` | **KEEP** |
| `src\dashboard\pages\08_reports.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/08_reports.py` | **KEEP** |
| `src\dashboard\pages\08_reports.py.backup` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/08_reports.py.backup` | **KEEP** |
| `src\dashboard\pages\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/pages/__init__.py` | **KEEP** |
| `src\dashboard\utils\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/dashboard/utils/__init__.py` | **KEEP** |
| `src\dashboard\utils\db.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/dashboard/utils/db.py` | **KEEP** |
| `src\database\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/database/__init__.py` | **KEEP** |
| `src\database\connection.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/database/connection.py` | **KEEP** |
| `src\database\models.py` | PRODUCTION | Core production application source code | No | No | No | `src/database/models.py` | **KEEP** |
| `src\database\schema.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/database/schema.py` | **KEEP** |
| `src\database\seed.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/database/seed.py` | **KEEP** |
| `src\etl\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/etl/__init__.py` | **KEEP** |
| `src\etl\data_quality.py` | PRODUCTION | Core production application source code | No | No | No | `src/etl/data_quality.py` | **KEEP** |
| `src\etl\extract.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/etl/extract.py` | **KEEP** |
| `src\etl\load.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/etl/load.py` | **KEEP** |
| `src\etl\normalizer.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/etl/normalizer.py` | **KEEP** |
| `src\etl\pipeline.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/etl/pipeline.py` | **KEEP** |
| `src\etl\transform.py` | PRODUCTION | Core production application source code | Yes | No | No | `src/etl/transform.py` | **KEEP** |
| `src\etl\validator.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/etl/validator.py` | **KEEP** |
| `src\health_score\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/health_score/__init__.py` | **KEEP** |
| `src\health_score\constants.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/health_score/constants.py` | **KEEP** |
| `src\health_score\engine.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/health_score/engine.py` | **KEEP** |
| `src\health_score\explanation.py` | PRODUCTION | Core production application source code | No | No | No | `src/health_score/explanation.py` | **KEEP** |
| `src\health_score\grading.py` | PRODUCTION | Core production application source code | No | No | No | `src/health_score/grading.py` | **KEEP** |
| `src\health_score\rules.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/health_score/rules.py` | **KEEP** |
| `src\health_score\scoring.py` | PRODUCTION | Core production application source code | No | No | No | `src/health_score/scoring.py` | **KEEP** |
| `src\kpi_engine\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/__init__.py` | **KEEP** |
| `src\kpi_engine\calculator.py` | PRODUCTION | Core production application source code | No | No | No | `src/kpi_engine/calculator.py` | **KEEP** |
| `src\kpi_engine\cashflow.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/cashflow.py` | **KEEP** |
| `src\kpi_engine\efficiency.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/efficiency.py` | **KEEP** |
| `src\kpi_engine\formatter.py` | PRODUCTION | Core production application source code | No | No | No | `src/kpi_engine/formatter.py` | **KEEP** |
| `src\kpi_engine\growth.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/growth.py` | **KEEP** |
| `src\kpi_engine\leverage.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/leverage.py` | **KEEP** |
| `src\kpi_engine\liquidity.py` | PRODUCTION | Core production application source code | No | No | No | `src/kpi_engine/liquidity.py` | **KEEP** |
| `src\kpi_engine\profitability.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/profitability.py` | **KEEP** |
| `src\kpi_engine\validator.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/validator.py` | **KEEP** |
| `src\kpi_engine\valuation.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/kpi_engine/valuation.py` | **KEEP** |
| `src\module3_cashflow_intelligence.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/module3_cashflow_intelligence.py` | **KEEP** |
| `src\nlp\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/nlp/__init__.py` | **KEEP** |
| `src\nlp\con_rules.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/nlp/con_rules.py` | **KEEP** |
| `src\nlp\parser.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/nlp/parser.py` | **KEEP** |
| `src\nlp\pro_rules.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/nlp/pro_rules.py` | **KEEP** |
| `src\nlp\pros_cons_generator.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/nlp/pros_cons_generator.py` | **KEEP** |
| `src\peer_analysis\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/peer_analysis/__init__.py` | **KEEP** |
| `src\peer_analysis\benchmarking.py` | PRODUCTION | Core production application source code | No | No | No | `src/peer_analysis/benchmarking.py` | **KEEP** |
| `src\peer_analysis\comparison.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/peer_analysis/comparison.py` | **KEEP** |
| `src\peer_analysis\percentile.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/peer_analysis/percentile.py` | **KEEP** |
| `src\peer_analysis\radar.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/peer_analysis/radar.py` | **KEEP** |
| `src\reports\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/reports/__init__.py` | **KEEP** |
| `src\reports\company_report.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/reports/company_report.py` | **KEEP** |
| `src\reports\excel_export.py` | PRODUCTION | Core production application source code | No | No | No | `src/reports/excel_export.py` | **KEEP** |
| `src\reports\pdf_export.py` | PRODUCTION | Core production application source code | No | No | No | `src/reports/pdf_export.py` | **KEEP** |
| `src\reports\portfolio_report.py` | PRODUCTION | Core production application source code | No | No | No | `src/reports/portfolio_report.py` | **KEEP** |
| `src\reports\sector_report.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/reports/sector_report.py` | **KEEP** |
| `src\reports\tearsheet.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/reports/tearsheet.py` | **KEEP** |
| `src\reports\templates.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/reports/templates.py` | **KEEP** |
| `src\screener\README.md` | PRODUCTION | Core production application source code | No | No | No | `src/screener/README.md` | **KEEP** |
| `src\screener\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/__init__.py` | **KEEP** |
| `src\screener\constants.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/constants.py` | **KEEP** |
| `src\screener\engine.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/engine.py` | **KEEP** |
| `src\screener\exporter.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/exporter.py` | **KEEP** |
| `src\screener\filters.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/filters.py` | **KEEP** |
| `src\screener\presets.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/presets.py` | **KEEP** |
| `src\screener\ranking.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/ranking.py` | **KEEP** |
| `src\screener\screener.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/screener.py` | **KEEP** |
| `src\screener\templates.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/screener/templates.py` | **KEEP** |
| `src\sector_analysis\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/sector_analysis/__init__.py` | **KEEP** |
| `src\sector_analysis\comparison.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/sector_analysis/comparison.py` | **KEEP** |
| `src\sector_analysis\rankings.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/sector_analysis/rankings.py` | **KEEP** |
| `src\sector_analysis\sector_summary.py` | PRODUCTION | Core production application source code | No | No | No | `src/sector_analysis/sector_summary.py` | **KEEP** |
| `src\sector_analysis\visualization.py` | PRODUCTION | Core production application source code | No | No | No | `src/sector_analysis/visualization.py` | **KEEP** |
| `src\utils\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/utils/__init__.py` | **KEEP** |
| `src\utils\cache.py` | PRODUCTION | Core production application source code | No | No | No | `src/utils/cache.py` | **KEEP** |
| `src\utils\exceptions.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/utils/exceptions.py` | **KEEP** |
| `src\utils\file_manager.py` | PRODUCTION | Core production application source code | No | No | No | `src/utils/file_manager.py` | **KEEP** |
| `src\utils\formatter.py` | PRODUCTION | Core production application source code | No | No | No | `src/utils/formatter.py` | **KEEP** |
| `src\utils\helpers.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/utils/helpers.py` | **KEEP** |
| `src\utils\logger.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/utils/logger.py` | **KEEP** |
| `src\utils\parser.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/utils/parser.py` | **KEEP** |
| `src\validation\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/validation/__init__.py` | **KEEP** |
| `src\validation\final_validation.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/validation/final_validation.py` | **KEEP** |
| `src\validation\report_generator.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/validation/report_generator.py` | **KEEP** |
| `src\visualization\__init__.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/visualization/__init__.py` | **KEEP** |
| `src\visualization\bar.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/visualization/bar.py` | **KEEP** |
| `src\visualization\gauges.py` | PRODUCTION | Core production application source code | No | No | No | `src/visualization/gauges.py` | **KEEP** |
| `src\visualization\heatmap.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/visualization/heatmap.py` | **KEEP** |
| `src\visualization\line.py` | PRODUCTION | Core production application source code | Yes | Yes | No | `src/visualization/line.py` | **KEEP** |
| `src\visualization\radar.py` | PRODUCTION | Core production application source code | No | Yes | No | `src/visualization/radar.py` | **KEEP** |
| `src\visualization\treemap.py` | PRODUCTION | Core production application source code | No | No | No | `src/visualization/treemap.py` | **KEEP** |
| `src\visualization\waterfall.py` | PRODUCTION | Core production application source code | No | No | No | `src/visualization/waterfall.py` | **KEEP** |
| `tests\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\analytics\test_capital_allocation_engine.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_capital_allocation_engine.py` | **KEEP** |
| `tests\analytics\test_cashflow_intelligence.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_cashflow_intelligence.py` | **KEEP** |
| `tests\analytics\test_cluster_profiling.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_cluster_profiling.py` | **KEEP** |
| `tests\analytics\test_clustering.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_clustering.py` | **KEEP** |
| `tests\analytics\test_module4b_distribution.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_module4b_distribution.py` | **KEEP** |
| `tests\analytics\test_module4c_pattern_changes.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_module4c_pattern_changes.py` | **KEEP** |
| `tests\analytics\test_module4d_integration.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_module4d_integration.py` | **KEEP** |
| `tests\analytics\test_peer.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/analytics/test_peer.py` | **KEEP** |
| `tests\analytics\test_peer_report.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_peer_report.py` | **KEEP** |
| `tests\analytics\test_radar.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/analytics/test_radar.py` | **KEEP** |
| `tests\api\test_companies.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/api/test_companies.py` | **KEEP** |
| `tests\api\test_health.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/api/test_health.py` | **KEEP** |
| `tests\api\test_peers.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/api/test_peers.py` | **KEEP** |
| `tests\api\test_remaining.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/api/test_remaining.py` | **KEEP** |
| `tests\api\test_screener.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/api/test_screener.py` | **KEEP** |
| `tests\api\test_sectors.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/api/test_sectors.py` | **KEEP** |
| `tests\dashboard\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\dashboard\test_company_intelligence.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/dashboard/test_company_intelligence.py` | **KEEP** |
| `tests\dashboard\test_dashboard_foundation.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/dashboard/test_dashboard_foundation.py` | **KEEP** |
| `tests\health_score\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\health_score\test_health_score_engine.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/health_score/test_health_score_engine.py` | **KEEP** |
| `tests\health_score\test_health_score_src.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/health_score/test_health_score_src.py` | **KEEP** |
| `tests\integration\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\integration\test_dashboard_api.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/integration/test_dashboard_api.py` | **KEEP** |
| `tests\kpi\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\kpi\test_cagr.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/kpi/test_cagr.py` | **KEEP** |
| `tests\kpi\test_cashflow.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/kpi/test_cashflow.py` | **KEEP** |
| `tests\kpi\test_efficiency.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/kpi/test_efficiency.py` | **KEEP** |
| `tests\kpi\test_leverage.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/kpi/test_leverage.py` | **KEEP** |
| `tests\kpi\test_profitability.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/kpi/test_profitability.py` | **KEEP** |
| `tests\nlp\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\nlp\test_con_rules.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/nlp/test_con_rules.py` | **KEEP** |
| `tests\nlp\test_module_2d_integration.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/nlp/test_module_2d_integration.py` | **KEEP** |
| `tests\nlp\test_parser.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/nlp/test_parser.py` | **KEEP** |
| `tests\nlp\test_pro_rules.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/nlp/test_pro_rules.py` | **KEEP** |
| `tests\nlp\test_pros_cons_generator.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/nlp/test_pros_cons_generator.py` | **KEEP** |
| `tests\performance\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\performance\test_module6g_performance.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/performance/test_module6g_performance.py` | **KEEP** |
| `tests\performance\test_screener_load.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/performance/test_screener_load.py` | **KEEP** |
| `tests\pipeline\test_etl.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/pipeline/test_etl.py` | **KEEP** |
| `tests\pipeline\test_ratio_engine.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/pipeline/test_ratio_engine.py` | **KEEP** |
| `tests\reports\test_sector_report.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/reports/test_sector_report.py` | **KEEP** |
| `tests\reports\test_tearsheet.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/reports/test_tearsheet.py` | **KEEP** |
| `tests\screener\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\screener\test_screener_engine.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/screener/test_screener_engine.py` | **KEEP** |
| `tests\test_peer_page_smoke.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/test_peer_page_smoke.py` | **KEEP** |
| `tests\validation\__init__.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/__init__.py` | **MOVE** |
| `tests\validation\test_context.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/validation/test_context.py` | **KEEP** |
| `tests\validation\test_db.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/validation/test_db.py` | **KEEP** |
| `tests\validation\test_final_validation.py` | TEST | Authoritative pytest test suite file | No | Yes | No | `tests/validation/test_final_validation.py` | **KEEP** |
| `tests\validation\test_load_ratio.py` | TEST | Authoritative pytest test suite file | No | No | No | `tests/validation/test_load_ratio.py` | **KEEP** |
| `tools\diagnostics\_build.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/_build.py` | **MOVE** |
| `tools\diagnostics\_build_final.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_build_final.py` | **MOVE** |
| `tools\diagnostics\_check_cols.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_check_cols.py` | **MOVE** |
| `tools\diagnostics\_check_sectors.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_check_sectors.py` | **MOVE** |
| `tools\diagnostics\_gen.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/_gen.py` | **MOVE** |
| `tools\diagnostics\_gen_module.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_gen_module.py` | **MOVE** |
| `tools\diagnostics\_generate_diagnostic.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_generate_diagnostic.py` | **MOVE** |
| `tools\diagnostics\_generate_tests.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_generate_tests.py` | **MOVE** |
| `tools\diagnostics\_inspect_cf.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_inspect_cf.py` | **MOVE** |
| `tools\diagnostics\_inspect_db.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_inspect_db.py` | **MOVE** |
| `tools\diagnostics\_inspect_db2.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_inspect_db2.py` | **MOVE** |
| `tools\diagnostics\_inspect_db3.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_inspect_db3.py` | **MOVE** |
| `tools\diagnostics\_inspect_pl.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_inspect_pl.py` | **MOVE** |
| `tools\diagnostics\_make_pcg.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_make_pcg.py` | **MOVE** |
| `tools\diagnostics\_mk.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_mk.py` | **MOVE** |
| `tools\diagnostics\_profile.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | Yes | No | `tools/diagnostics/_profile.py` | **MOVE** |
| `tools\diagnostics\_profile2.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_profile2.py` | **MOVE** |
| `tools\diagnostics\_profile3.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_profile3.py` | **MOVE** |
| `tools\diagnostics\_quick_diag.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_quick_diag.py` | **MOVE** |
| `tools\diagnostics\_show_diagnostic.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_show_diagnostic.py` | **MOVE** |
| `tools\diagnostics\_simple_build.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_simple_build.py` | **MOVE** |
| `tools\diagnostics\_tmp_append.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_append.py` | **MOVE** |
| `tools\diagnostics\_tmp_check.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_check.py` | **MOVE** |
| `tools\diagnostics\_tmp_check_sectors.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_check_sectors.py` | **MOVE** |
| `tools\diagnostics\_tmp_context_check.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_context_check.py` | **MOVE** |
| `tools\diagnostics\_tmp_inspect.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_inspect.py` | **MOVE** |
| `tools\diagnostics\_tmp_inspect2.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_inspect2.py` | **MOVE** |
| `tools\diagnostics\_tmp_inspect3.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_tmp_inspect3.py` | **MOVE** |
| `tools\diagnostics\_write_module.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_write_module.py` | **MOVE** |
| `tools\diagnostics\_write_pcg.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_write_pcg.py` | **MOVE** |
| `tools\diagnostics\_write_pro_rules.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_write_pro_rules.py` | **MOVE** |
| `tools\diagnostics\_write_tests.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/_write_tests.py` | **MOVE** |
| `tools\diagnostics\analyze_diagnostic.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/diagnostics/analyze_diagnostic.py` | **KEEP** |
| `tools\diagnostics\check_bs.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_bs.py` | **MOVE** |
| `tools\diagnostics\check_cf.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_cf.py` | **MOVE** |
| `tools\diagnostics\check_data.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_data.py` | **MOVE** |
| `tools\diagnostics\check_latest_ratio.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_latest_ratio.py` | **MOVE** |
| `tools\diagnostics\check_pl.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_pl.py` | **MOVE** |
| `tools\diagnostics\check_pl_bs.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_pl_bs.py` | **MOVE** |
| `tools\diagnostics\check_presence.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_presence.py` | **MOVE** |
| `tools\diagnostics\check_ratios_detail.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_ratios_detail.py` | **MOVE** |
| `tools\diagnostics\check_unions_data.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/check_unions_data.py` | **MOVE** |
| `tools\diagnostics\debug_tables.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/debug_tables.py` | **MOVE** |
| `tools\diagnostics\diagnose_module_2d.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/diagnose_module_2d.py` | **MOVE** |
| `tools\diagnostics\diagnostic_module2d.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/diagnostic_module2d.py` | **MOVE** |
| `tools\diagnostics\examine_unions.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/examine_unions.py` | **MOVE** |
| `tools\diagnostics\inspect_abb.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_abb.py` | **MOVE** |
| `tools\diagnostics\inspect_cf.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_cf.py` | **MOVE** |
| `tools\diagnostics\inspect_data.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_data.py` | **MOVE** |
| `tools\diagnostics\inspect_db.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_db.py` | **MOVE** |
| `tools\diagnostics\inspect_dbs.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_dbs.py` | **MOVE** |
| `tools\diagnostics\inspect_kpis.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_kpis.py` | **MOVE** |
| `tools\diagnostics\inspect_module3.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_module3.py` | **MOVE** |
| `tools\diagnostics\inspect_periods.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/inspect_periods.py` | **MOVE** |
| `tools\diagnostics\raw_balance.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/raw_balance.py` | **MOVE** |
| `tools\diagnostics\raw_query.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/raw_query.py` | **MOVE** |
| `tools\diagnostics\raw_ratios.py` | DEBUG/DIAGNOSTIC | Diagnostic tool or temporary analysis script | No | No | No | `tools/diagnostics/raw_ratios.py` | **MOVE** |
| `tools\legacy\module3_cashflow_intelligence_clean.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_clean.py` | **KEEP** |
| `tools\legacy\module3_cashflow_intelligence_debug.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_debug.py` | **KEEP** |
| `tools\legacy\module3_cashflow_intelligence_final.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_final.py` | **KEEP** |
| `tools\legacy\module3_cashflow_intelligence_final.py.bak` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_final.py.bak` | **KEEP** |
| `tools\legacy\module3_cashflow_intelligence_fixed.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_fixed.py` | **KEEP** |
| `tools\legacy\module3_cashflow_intelligence_workaround.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_workaround.py` | **KEEP** |
| `tools\legacy\module3_cashflow_intelligence_workaround_fixed.py` | UNKNOWN | Unclassified repository file | No | No | No | `tools/legacy/module3_cashflow_intelligence_workaround_fixed.py` | **KEEP** |
| `tools\legacy\test_etl_comprehensive.py` | TEST | Root-level test script | No | Yes | No | `tests/validation/test_etl_comprehensive.py` | **MOVE** |
| `tools\maintenance\add_missing_docstrings.py` | DEBUG/DIAGNOSTIC | One-time maintenance or code fix utility | No | No | No | `tools/maintenance/add_missing_docstrings.py` | **MOVE** |
| `tools\maintenance\audit_and_fix_docstrings.py` | DEBUG/DIAGNOSTIC | One-time maintenance or code fix utility | No | No | No | `tools/maintenance/audit_and_fix_docstrings.py` | **MOVE** |
| `tools\maintenance\clean_boms.py` | DEBUG/DIAGNOSTIC | One-time maintenance or code fix utility | No | No | No | `tools/maintenance/clean_boms.py` | **MOVE** |
| `tools\maintenance\fix_only_placeholders.py` | DEBUG/DIAGNOSTIC | One-time maintenance or code fix utility | No | No | No | `tools/maintenance/fix_only_placeholders.py` | **MOVE** |
| `tools\maintenance\fix_placeholder_files.py` | DEBUG/DIAGNOSTIC | One-time maintenance or code fix utility | No | No | No | `tools/maintenance/fix_placeholder_files.py` | **MOVE** |
| `tools\utilities\archive_deliverables.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `tools/utilities/archive_deliverables.py` | **KEEP** |
| `tools\utilities\create_report.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `tools/utilities/create_report.py` | **KEEP** |
| `tools\utilities\generate_acceptance_checklist.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `tools/utilities/generate_acceptance_checklist.py` | **KEEP** |
| `tools\utilities\generate_analyst_guide.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `tools/utilities/generate_analyst_guide.py` | **KEEP** |
| `tools\utilities\generate_pytest_report.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `tools/utilities/generate_pytest_report.py` | **KEEP** |
| `tools\utilities\populate_financial_kpis.py` | PRODUCTION | ETL / Report generation entry script | No | No | No | `tools/utilities/populate_financial_kpis.py` | **KEEP** |
| `tools\validation\validate_con_rules.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_con_rules.py` | **KEEP** |
| `tools\validation\validate_module3.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module3.py` | **KEEP** |
| `tools\validation\validate_module4.py` | VALIDATION | Authoritative module or rules validation script | No | Yes | Yes | `tools/validation/validate_module4.py` | **KEEP** |
| `tools\validation\validate_module4a.py` | VALIDATION | Authoritative module or rules validation script | No | Yes | Yes | `tools/validation/validate_module4a.py` | **KEEP** |
| `tools\validation\validate_module4b.py` | VALIDATION | Authoritative module or rules validation script | No | Yes | Yes | `tools/validation/validate_module4b.py` | **KEEP** |
| `tools\validation\validate_module4c.py` | VALIDATION | Authoritative module or rules validation script | No | Yes | Yes | `tools/validation/validate_module4c.py` | **KEEP** |
| `tools\validation\validate_module5a.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module5a.py` | **KEEP** |
| `tools\validation\validate_module5b.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module5b.py` | **KEEP** |
| `tools\validation\validate_module5c.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module5c.py` | **KEEP** |
| `tools\validation\validate_module6a.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6a.py` | **KEEP** |
| `tools\validation\validate_module6b.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6b.py` | **KEEP** |
| `tools\validation\validate_module6c.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6c.py` | **KEEP** |
| `tools\validation\validate_module6d.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6d.py` | **KEEP** |
| `tools\validation\validate_module6e.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6e.py` | **KEEP** |
| `tools\validation\validate_module6f.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6f.py` | **KEEP** |
| `tools\validation\validate_module6g.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6g.py` | **KEEP** |
| `tools\validation\validate_module6h.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6h.py` | **KEEP** |
| `tools\validation\validate_module6i.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6i.py` | **KEEP** |
| `tools\validation\validate_module6j.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_module6j.py` | **KEEP** |
| `tools\validation\validate_pro_rules.py` | VALIDATION | Authoritative module or rules validation script | No | No | Yes | `tools/validation/validate_pro_rules.py` | **KEEP** |
| `tools\validation\verify_output.py` | VALIDATION | Authoritative module or rules validation script | No | No | No | `tools/validation/verify_output.py` | **KEEP** |

## Category Summary

- **CACHE**: 33 files/dirs
- **DEBUG/DIAGNOSTIC**: 76 files/dirs
- **DOCUMENTATION**: 58 files/dirs
- **GENERATED_OUTPUT**: 189 files/dirs
- **PRODUCTION**: 191 files/dirs
- **TEMPORARY**: 1 files/dirs
- **TEST**: 51 files/dirs
- **UNKNOWN**: 115 files/dirs
- **VALIDATION**: 21 files/dirs

## Proposed Action Summary

- **DELETE**: 33 files/dirs
- **KEEP**: 618 files/dirs
- **MOVE**: 84 files/dirs
