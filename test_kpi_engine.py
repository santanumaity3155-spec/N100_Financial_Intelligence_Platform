"""
Test script for the KPI Engine

This script tests the KPI calculation engine with the actual database.
"""

import logging
from src.kpi_engine.calculator import KPIEngine

# Logging is already configured in logging_config.py

def test_kpi_engine():
    """Test the KPI engine with sample data."""
    
    print("=" * 80)
    print("TESTING KPI ENGINE")
    print("=" * 80)
    
    # Initialize KPI Engine
    engine = KPIEngine()
    
    # Get available companies
    companies = engine.get_available_companies()
    print(f"\n✓ Found {len(companies)} companies in database")
    
    if not companies:
        print("✗ No companies found in database. Please run ETL pipeline first.")
        return False
    
    # Test with first 3 companies
    test_companies = companies[:3]
    print(f"✓ Testing with first {len(test_companies)} companies: {test_companies}")
    
    # Get available periods for first company
    periods = engine.get_available_periods(test_companies[0])
    print(f"✓ Found {len(periods)} periods for {test_companies[0]}: {periods}")
    
    if not periods:
        print("✗ No periods found. Please run ETL pipeline first.")
        return False
    
    # Test 1: Calculate KPIs for single company, single period
    print("\n" + "=" * 80)
    print("TEST 1: Single Company, Single Period")
    print("=" * 80)
    
    test_company = test_companies[0]
    test_period = periods[0]
    
    print(f"\nCalculating KPIs for {test_company}, period {test_period}...")
    kpi_results = engine.calculate_all_kpis(test_company, test_period)
    
    if kpi_results:
        print(f"✓ Successfully calculated {len([v for v in kpi_results.values() if v is not None])} KPIs")
        
        # Display results
        engine.formatter.print_kpi_results(kpi_results)
        
        # Validate results
        validation = engine.validate_kpi_results([kpi_results])
        print(f"\n✓ Validation: {validation['valid_kpis']}/{validation['total_kpis']} KPIs valid")
        
        if validation['failed_kpis'] > 0:
            print(f"⚠ Warning: {validation['failed_kpis']} KPIs failed validation")
            for error in validation['company_validations'][0]['errors']:
                print(f"  - {error}")
    else:
        print("✗ Failed to calculate KPIs")
        return False
    
    # Test 2: Calculate KPIs for multiple companies
    print("\n" + "=" * 80)
    print("TEST 2: Multiple Companies, Single Period")
    print("=" * 80)
    
    print(f"\nCalculating KPIs for {len(test_companies)} companies...")
    batch_results = engine.calculate_kpis_for_all_companies(test_companies, test_period)
    
    if batch_results:
        print(f"✓ Successfully calculated KPIs for {len(batch_results)} companies")
        
        # Validate batch
        batch_validation = engine.validate_kpi_results(batch_results)
        print(f"✓ Batch validation: {batch_validation['valid_kpis']}/{batch_validation['total_kpis']} KPIs valid")
        
        # Get statistics
        stats = engine.get_kpi_statistics(batch_results)
        print(f"\n✓ KPI Statistics:")
        for kpi_name, kpi_stats in stats.get('kpi_statistics', {}).items():
            print(f"  {kpi_name}: mean={kpi_stats['mean']}, min={kpi_stats['min']}, max={kpi_stats['max']}")
    else:
        print("✗ Failed to calculate batch KPIs")
        return False
    
    # Test 3: Calculate growth KPIs
    if len(periods) >= 2:
        print("\n" + "=" * 80)
        print("TEST 3: Growth KPIs (Multiple Periods)")
        print("=" * 80)
        
        test_periods = periods[:3]  # Use first 3 periods
        print(f"\nCalculating growth KPIs for {test_company} across {len(test_periods)} periods...")
        
        growth_results = engine.calculate_growth_kpis(test_company, test_periods)
        
        if growth_results:
            print(f"✓ Successfully calculated {len([v for v in growth_results.values() if v is not None])} growth KPIs")
            engine.formatter.print_kpi_results(growth_results)
        else:
            print("⚠ No growth KPIs calculated (may need more periods)")
    else:
        print("\n⚠ Skipping growth KPIs test (need at least 2 periods)")
    
    # Test 4: Save results
    print("\n" + "=" * 80)
    print("TEST 4: Save KPI Results")
    print("=" * 80)
    
    import os
    output_dir = "reports/kpi_test"
    
    print(f"\nSaving KPI results to {output_dir}...")
    save_results = engine.save_kpi_results(batch_results, output_dir)
    
    if save_results.get('json') or save_results.get('csv'):
        print(f"✓ Successfully saved KPI results")
        print(f"  - JSON: {'✓' if save_results.get('json') else '✗'}")
        print(f"  - CSV: {'✓' if save_results.get('csv') else '✗'}")
    else:
        print("✗ Failed to save KPI results")
    
    # Test 5: Get KPI descriptions and formulas
    print("\n" + "=" * 80)
    print("TEST 5: KPI Metadata")
    print("=" * 80)
    
    descriptions = engine.get_kpi_descriptions()
    formulas = engine.get_kpi_formulas()
    
    print(f"\n✓ Found {len(descriptions)} KPI descriptions")
    print(f"✓ Found {len(formulas)} KPI formulas")
    
    print("\nSample KPI Descriptions:")
    for i, (kpi_name, desc) in enumerate(list(descriptions.items())[:5]):
        print(f"  {i+1}. {kpi_name}: {desc}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_kpi_engine()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)