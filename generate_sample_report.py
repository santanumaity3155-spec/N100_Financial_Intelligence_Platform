#!/usr/bin/env python3
"""
Generate a sample peer comparison report for testing Module 9.
"""

from src.analytics.peer_report import run_peer_report_engine

if __name__ == "__main__":
    print("=" * 80)
    print("GENERATING SAMPLE PEER COMPARISON REPORT")
    print("=" * 80)
    
    # Generate report for RELIANCE
    results = run_peer_report_engine(company_ids=["RELIANCE"])
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total Companies: {results['total_companies']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Execution Time: {results['execution_time']:.2f}s")
    
    if results['successful'] > 0:
        print("\n✅ SUCCESS: Sample report generated!")
        if results['results']:
            report_path = results['results'][0].get('report_path')
            if report_path:
                print(f"📄 Report location: {report_path}")
    else:
        print("\n❌ FAILED: No reports generated")
        if results.get('errors'):
            print("Errors:")
            for error in results['errors'][:5]:
                print(f"  - {error}")
    
    print("=" * 80)