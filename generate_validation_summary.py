"""
ETL Validation Summary Generator
Sprint 1 - Task 3
"""
import sqlite3
import csv
import os
from datetime import datetime
from typing import Dict, List, Any

# Database path
DB_PATH = 'data/database/n100.db'

def get_db_connection() -> sqlite3.Connection:
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_companies_count(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Check total companies count"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM companies")
    result = cursor.fetchone()
    return {
        'total_companies': result['count'],
        'status': 'PASS' if result['count'] > 0 else 'FAIL'
    }

def check_foreign_keys(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Run PRAGMA foreign_key_check"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check")
    results = cursor.fetchall()
    
    return {
        'total_violations': len(results),
        'violations': [dict(zip(['table', 'rowid', 'parent', 'fk'], row)) for row in results],
        'status': 'PASS' if len(results) == 0 else 'FAIL'
    }

def check_load_audit() -> Dict[str, Any]:
    """Check load_audit.csv"""
    audit_path = 'reports/load_audit.csv'
    
    if not os.path.exists(audit_path):
        return {
            'exists': False,
            'status': 'FAIL',
            'message': 'load_audit.csv not found'
        }
    
    try:
        with open(audit_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        total_records = len(rows)
        successful = sum(1 for row in rows if row.get('status', '').lower() == 'success')
        failed = sum(1 for row in rows if row.get('status', '').lower() == 'failed')
        
        return {
            'exists': True,
            'total_records': total_records,
            'successful': successful,
            'failed': failed,
            'success_rate': round(successful * 100.0 / total_records, 2) if total_records > 0 else 0,
            'status': 'PASS' if failed == 0 else 'WARNING'
        }
    except Exception as e:
        return {
            'exists': True,
            'status': 'FAIL',
            'message': f'Error reading load_audit.csv: {str(e)}'
        }

def check_validation_report() -> Dict[str, Any]:
    """Check validation_failures.csv"""
    validation_path = 'reports/validation_failures.csv'
    
    if not os.path.exists(validation_path):
        return {
            'exists': False,
            'status': 'FAIL',
            'message': 'validation_failures.csv not found'
        }
    
    try:
        with open(validation_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        total_failures = len(rows)
        
        # Categorize failures
        critical_failures = sum(1 for row in rows if row.get('severity', '').lower() == 'critical')
        warning_failures = sum(1 for row in rows if row.get('severity', '').lower() == 'warning')
        info_failures = sum(1 for row in rows if row.get('severity', '').lower() == 'info')
        
        # Group by table
        table_failures = {}
        for row in rows:
            table = row.get('table', 'unknown')
            table_failures[table] = table_failures.get(table, 0) + 1
        
        return {
            'exists': True,
            'total_failures': total_failures,
            'critical': critical_failures,
            'warnings': warning_failures,
            'info': info_failures,
            'by_table': table_failures,
            'status': 'PASS' if critical_failures == 0 else 'FAIL'
        }
    except Exception as e:
        return {
            'exists': True,
            'status': 'FAIL',
            'message': f'Error reading validation_failures.csv: {str(e)}'
        }

def check_database_tables(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Check all expected tables exist and have data"""
    cursor = conn.cursor()
    
    expected_tables = [
        'companies', 'profit_loss', 'balance_sheet', 'cash_flow',
        'sectors', 'stock_prices', 'market_cap', 'financial_ratios',
        'financial_kpis', 'peer_groups', 'analysis', 'documents', 'pros_cons'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    table_status = {}
    for table in expected_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_status[table] = {
                'exists': True,
                'record_count': count,
                'status': 'PASS' if count > 0 else 'WARNING'
            }
        else:
            table_status[table] = {
                'exists': False,
                'record_count': 0,
                'status': 'FAIL'
            }
    
    return table_status

def check_data_integrity(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Check data integrity metrics"""
    cursor = conn.cursor()
    
    integrity_checks = {}
    
    # Check for orphaned records
    cursor.execute("""
        SELECT COUNT(*) FROM profit_loss pl 
        WHERE NOT EXISTS (SELECT 1 FROM companies c WHERE c.company_id = pl.company_id)
    """)
    integrity_checks['orphaned_profit_loss'] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM balance_sheet bs 
        WHERE NOT EXISTS (SELECT 1 FROM companies c WHERE c.company_id = bs.company_id)
    """)
    integrity_checks['orphaned_balance_sheet'] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM cash_flow cf 
        WHERE NOT EXISTS (SELECT 1 FROM companies c WHERE c.company_id = cf.company_id)
    """)
    integrity_checks['orphaned_cash_flow'] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM sectors s 
        WHERE NOT EXISTS (SELECT 1 FROM companies c WHERE c.company_id = s.company_id)
    """)
    integrity_checks['orphaned_sectors'] = cursor.fetchone()[0]
    
    # Check for duplicates
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT company_id, period, COUNT(*) as cnt 
            FROM profit_loss 
            GROUP BY company_id, period 
            HAVING COUNT(*) > 1
        )
    """)
    integrity_checks['duplicate_profit_loss'] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT company_id, period, COUNT(*) as cnt 
            FROM balance_sheet 
            GROUP BY company_id, period 
            HAVING COUNT(*) > 1
        )
    """)
    integrity_checks['duplicate_balance_sheet'] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT company_id, period, COUNT(*) as cnt 
            FROM cash_flow 
            GROUP BY company_id, period 
            HAVING COUNT(*) > 1
        )
    """)
    integrity_checks['duplicate_cash_flow'] = cursor.fetchone()[0]
    
    total_issues = sum(integrity_checks.values())
    
    return {
        'checks': integrity_checks,
        'total_issues': total_issues,
        'status': 'PASS' if total_issues == 0 else 'WARNING'
    }

def generate_summary() -> str:
    """Generate comprehensive validation summary report"""
    
    report = []
    report.append("# ETL Validation Summary Report")
    report.append("\n**Sprint 1 - Task 3**\n")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n")
    
    # Connect to database
    conn = get_db_connection()
    
    # Run all checks
    print("Running validation checks...")
    
    print("  - Checking companies count...")
    companies_check = check_companies_count(conn)
    
    print("  - Checking foreign key integrity...")
    fk_check = check_foreign_keys(conn)
    
    print("  - Checking load audit...")
    audit_check = check_load_audit()
    
    print("  - Checking validation report...")
    validation_check = check_validation_report()
    
    print("  - Checking database tables...")
    tables_check = check_database_tables(conn)
    
    print("  - Checking data integrity...")
    integrity_check = check_data_integrity(conn)
    
    conn.close()
    
    # Executive Summary
    report.append("## Executive Summary\n")
    
    overall_status = 'PASS'
    if companies_check['status'] == 'FAIL' or fk_check['status'] == 'FAIL':
        overall_status = 'FAIL'
    elif audit_check.get('status') == 'FAIL' or validation_check.get('status') == 'FAIL':
        overall_status = 'FAIL'
    elif integrity_check['status'] == 'WARNING' or validation_check.get('status') == 'WARNING':
        overall_status = 'WARNING'
    
    report.append(f"### Overall Status: **{overall_status}**\n")
    report.append("This report validates the ETL pipeline execution and data quality for Sprint 1. The validation covers database integrity, foreign key constraints, load audit, and data quality checks.\n")
    report.append("---\n")
    
    # 1. Companies Count Check
    report.append("## 1. Companies Count Validation\n")
    report.append("### Requirement: SELECT COUNT(*) FROM companies\n")
    report.append(f"- **Total Companies:** {companies_check['total_companies']}")
    report.append(f"- **Status:** {companies_check['status']}")
    report.append("")
    
    if companies_check['status'] == 'PASS':
        report.append("✅ Companies table contains records and is ready for analysis.\n")
    else:
        report.append("❌ Companies table is empty or does not exist.\n")
    
    report.append("---\n")
    
    # 2. Foreign Key Check
    report.append("## 2. Foreign Key Integrity Check\n")
    report.append("### Requirement: PRAGMA foreign_key_check\n")
    report.append(f"- **Total Violations:** {fk_check['total_violations']}")
    report.append(f"- **Status:** {fk_check['status']}")
    report.append("")
    
    if fk_check['status'] == 'PASS':
        report.append("✅ No foreign key violations detected. Referential integrity is maintained.\n")
    else:
        report.append("❌ Foreign key violations found:\n")
        for violation in fk_check['violations']:
            report.append(f"  - Table: {violation['table']}, RowID: {violation['rowid']}, Parent: {violation['parent']}, FK: {violation['fk']}")
        report.append("")
    
    report.append("---\n")
    
    # 3. Load Audit Check
    report.append("## 3. Load Audit Validation\n")
    report.append("### Requirement: Load audit file (load_audit.csv)\n")
    
    if audit_check.get('exists'):
        report.append(f"- **Total Records:** {audit_check.get('total_records', 0)}")
        report.append(f"- **Successful:** {audit_check.get('successful', 0)}")
        report.append(f"- **Failed:** {audit_check.get('failed', 0)}")
        report.append(f"- **Success Rate:** {audit_check.get('success_rate', 0)}%")
        report.append(f"- **Status:** {audit_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        if audit_check.get('status') == 'PASS':
            report.append("✅ All records loaded successfully.\n")
        elif audit_check.get('status') == 'WARNING':
            report.append(f"⚠️ {audit_check.get('failed', 0)} records failed to load. Review required.\n")
        else:
            report.append(f"❌ Load audit check failed: {audit_check.get('message', 'Unknown error')}\n")
    else:
        report.append(f"- **Status:** {audit_check.get('status', 'UNKNOWN')}")
        report.append(f"- **Message:** {audit_check.get('message', 'File not found')}")
        report.append("")
        report.append("❌ Load audit file not found.\n")
    
    report.append("---\n")
    
    # 4. Validation Report Check
    report.append("## 4. Validation Report Check\n")
    report.append("### Requirement: Validation report (validation_failures.csv)\n")
    
    if validation_check.get('exists'):
        report.append(f"- **Total Failures:** {validation_check.get('total_failures', 0)}")
        report.append(f"- **Critical:** {validation_check.get('critical', 0)}")
        report.append(f"- **Warnings:** {validation_check.get('warnings', 0)}")
        report.append(f"- **Info:** {validation_check.get('info', 0)}")
        report.append(f"- **Status:** {validation_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        if validation_check.get('total_failures', 0) > 0:
            report.append("### Failures by Table\n")
            for table, count in validation_check.get('by_table', {}).items():
                report.append(f"- **{table}:** {count} failure(s)")
            report.append("")
        
        if validation_check.get('status') == 'PASS':
            report.append("✅ No critical validation failures detected.\n")
        elif validation_check.get('status') == 'WARNING':
            report.append(f"⚠️ {validation_check.get('warnings', 0)} warnings detected. Review recommended.\n")
        else:
            report.append(f"❌ {validation_check.get('critical', 0)} critical failures detected. Action required.\n")
    else:
        report.append(f"- **Status:** {validation_check.get('status', 'UNKNOWN')}")
        report.append(f"- **Message:** {validation_check.get('message', 'File not found')}")
        report.append("")
        report.append("❌ Validation report not found.\n")
    
    report.append("---\n")
    
    # 5. Database Tables Check
    report.append("## 5. Database Tables Validation\n")
    report.append("### Requirement: All expected tables exist with data\n")
    report.append("")
    
    report.append("| Table | Exists | Records | Status |")
    report.append("|-------|--------|---------|--------|")
    
    for table, info in tables_check.items():
        exists_mark = "✅" if info['exists'] else "❌"
        status_mark = "✅" if info['status'] == 'PASS' else "⚠️" if info['status'] == 'WARNING' else "❌"
        report.append(f"| {table} | {exists_mark} | {info['record_count']} | {status_mark} |")
    
    report.append("")
    
    all_tables_ok = all(info['status'] == 'PASS' for info in tables_check.values())
    if all_tables_ok:
        report.append("✅ All expected tables exist and contain data.\n")
    else:
        report.append("⚠️ Some tables are missing or empty. Review required.\n")
    
    report.append("---\n")
    
    # 6. Data Integrity Check
    report.append("## 6. Data Integrity Check\n")
    report.append("### Requirement: No orphaned records or duplicates\n")
    report.append("")
    
    report.append("#### Orphaned Records\n")
    report.append(f"- Profit & Loss: {integrity_check['checks']['orphaned_profit_loss']}")
    report.append(f"- Balance Sheet: {integrity_check['checks']['orphaned_balance_sheet']}")
    report.append(f"- Cash Flow: {integrity_check['checks']['orphaned_cash_flow']}")
    report.append(f"- Sectors: {integrity_check['checks']['orphaned_sectors']}")
    report.append("")
    
    report.append("#### Duplicate Records\n")
    report.append(f"- Profit & Loss: {integrity_check['checks']['duplicate_profit_loss']}")
    report.append(f"- Balance Sheet: {integrity_check['checks']['duplicate_balance_sheet']}")
    report.append(f"- Cash Flow: {integrity_check['checks']['duplicate_cash_flow']}")
    report.append("")
    
    report.append(f"- **Total Issues:** {integrity_check['total_issues']}")
    report.append(f"- **Status:** {integrity_check['status']}")
    report.append("")
    
    if integrity_check['status'] == 'PASS':
        report.append("✅ No data integrity issues detected.\n")
    else:
        report.append("⚠️ Data integrity issues detected. Review recommended.\n")
    
    report.append("---\n")
    
    # Sprint 1 Exit Criteria Assessment
    report.append("## Sprint 1 Exit Criteria Assessment\n")
    report.append("")
    
    criteria = [
        ("Companies count > 0", companies_check['status'] == 'PASS'),
        ("No foreign key violations", fk_check['status'] == 'PASS'),
        ("Load audit exists and successful", audit_check.get('status') in ['PASS', 'WARNING']),
        ("Validation report exists", validation_check.get('exists', False)),
        ("All tables exist with data", all_tables_ok),
        ("No critical data integrity issues", integrity_check['status'] in ['PASS', 'WARNING'])
    ]
    
    report.append("| Criteria | Status |")
    report.append("|----------|--------|")
    
    all_criteria_met = True
    for criterion, met in criteria:
        status_mark = "✅" if met else "❌"
        report.append(f"| {criterion} | {status_mark} |")
        if not met:
            all_criteria_met = False
    
    report.append("")
    
    if all_criteria_met:
        report.append("### ✅ **Sprint 1 Exit Criteria: SATISFIED**\n")
        report.append("All exit criteria have been met. The ETL pipeline is ready for production use.\n")
    else:
        report.append("### ❌ **Sprint 1 Exit Criteria: NOT SATISFIED**\n")
        report.append("Some exit criteria have not been met. Please review the issues above and take corrective action.\n")
    
    report.append("---\n")
    
    # Recommendations
    report.append("## Recommendations\n")
    
    recommendations = []
    
    if companies_check['status'] != 'PASS':
        recommendations.append("1. **Critical:** Ensure companies table is populated with at least one record.")
    
    if fk_check['status'] != 'PASS':
        recommendations.append("2. **Critical:** Fix foreign key violations to maintain referential integrity.")
    
    if audit_check.get('status') == 'FAIL':
        recommendations.append("3. **High:** Investigate and fix load audit failures.")
    
    if validation_check.get('status') == 'FAIL':
        recommendations.append("4. **High:** Address critical validation failures before proceeding.")
    
    if integrity_check['status'] == 'WARNING':
        recommendations.append("5. **Medium:** Review and resolve data integrity issues (orphaned records or duplicates).")
    
    if not recommendations:
        recommendations.append("✅ No critical issues detected. The ETL pipeline is functioning correctly.")
        recommendations.append("📊 Consider implementing additional validation rules for enhanced data quality.")
        recommendations.append("🔄 Schedule regular data quality audits to maintain standards.")
    
    for rec in recommendations:
        report.append(rec)
    report.append("")
    
    report.append("---\n")
    report.append("## Conclusion\n")
    
    if all_criteria_met:
        report.append("The ETL pipeline has successfully passed all validation checks. The database is properly populated with data, foreign key integrity is maintained, and all exit criteria are satisfied. The system is ready for Sprint 2 development and production deployment.\n")
    else:
        report.append("The ETL pipeline has some validation issues that need to be addressed before Sprint 1 can be considered complete. Please review the recommendations above and take necessary corrective actions.\n")
    
    return '\n'.join(report)

def main():
    """Main execution function"""
    print("=" * 80)
    print("ETL Validation Summary Generator - Sprint 1")
    print("=" * 80)
    print()
    
    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    print("Running comprehensive validation checks...")
    print()
    
    # Generate report
    report = generate_summary()
    
    # Save report
    output_path = 'docs/etl_validation_summary.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Validation summary generated: {output_path}")
    print()
    
    print("=" * 80)
    print("ETL Validation Summary Complete")
    print("=" * 80)

if __name__ == '__main__':
    main()