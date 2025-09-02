#!/usr/bin/env python3
"""
Enhanced Database Health Monitor - Runs continuously with scheduler and logging
Integrated with the new logging system and dashboard
"""

import json
import sys
from datetime import datetime
from rat.logger import get_logger
from rat.healthcheck import Health
from rat.dblist import DBList
from rat.config import config


def display_summary():
    """Display summary of all databases"""
    health = Health()
    db_list = DBList()

    # Get all databases
    all_dbs = db_list.crowldbgrab() + db_list.backlinkdbgrab()

    healthy_count = 0
    warning_count = 0
    critical_count = 0
    total_count = len(all_dbs)

    for db in all_dbs:
        if not db:
            continue

        try:
            usage = health.current_limit(db['name'], db['organization'], db['apikey'])
            if usage:
                storage_used = usage.get('storage_bytes', 0)
                writes_used = usage.get('rows_written', 0)
                storage_limit = db.get('storage_quota_gb', 5) * 1024**3
                write_limit = db.get('monthly_write_limit', 10000000)

                storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
                write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

                if storage_percent >= 90 or write_percent >= 90:
                    critical_count += 1
                elif storage_percent >= 75 or write_percent >= 75:
                    warning_count += 1
                else:
                    healthy_count += 1
            else:
                critical_count += 1  # Unknown status treated as critical
        except Exception:
            critical_count += 1

    print("🗄️ Database Summary")
    print("=" * 50)
    print(f"Total Databases: {total_count}")
    print(f"Healthy: {healthy_count} ✅")
    print(f"Warning: {warning_count} ⚠️")
    print(f"Critical: {critical_count} 🔴")
    print()


def display_detailed_status():
    """Display detailed status of all databases"""
    health = Health()
    db_list = DBList()

    # Get all databases
    all_dbs = db_list.crowldbgrab() + db_list.backlinkdbgrab()

    print("📊 Detailed Database Status")
    print("=" * 70)

    for db in all_dbs:
        if not db:
            continue

        try:
            usage = health.current_limit(db['name'], db['organization'], db['apikey'])

            if usage:
                storage_used = usage.get('storage_bytes', 0)
                writes_used = usage.get('rows_written', 0)
                storage_limit = db.get('storage_quota_gb', 5) * 1024**3
                write_limit = db.get('monthly_write_limit', 10000000)

                storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
                write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

                if storage_percent >= 90 or write_percent >= 90:
                    status = "critical"
                    status_icon = "🔴"
                elif storage_percent >= 75 or write_percent >= 75:
                    status = "warning"
                    status_icon = "⚠️"
                else:
                    status = "healthy"
                    status_icon = "✅"

                print(f"{status_icon} {db['name']}")
                print(f"   Type: {'crawler' if db in db_list.crowldbgrab() else 'backlink'} | Organization: {db['organization']}")
                print(f"   Status: {status.upper()}")
                print(f"   Storage: {format_bytes(storage_used)} / {format_bytes(storage_limit)} ({storage_percent:.1f}%)")
                print(f"   Writes: {format_number(writes_used)} / {format_number(write_limit)} ({write_percent:.1f}%)")

                if status in ['warning', 'critical']:
                    print(f"   ⚠️ Action Required: Database approaching limits")
            else:
                print(f"❓ {db['name']}")
                print(f"   Type: {'crawler' if db in db_list.crowldbgrab() else 'backlink'} | Organization: {db['organization']}")
                print(f"   Status: UNKNOWN")
                print(f"   Unable to retrieve usage information")

        except Exception as e:
            print(f"❌ {db['name']}")
            print(f"   Type: {'crawler' if db in db_list.crowldbgrab() else 'backlink'} | Organization: {db['organization']}")
            print(f"   Status: ERROR - {str(e)}")

        print()


def check_single_database(db_name):
    """Check status of a single database"""
    health = Health()
    db_list = DBList()

    # Get all databases
    all_dbs = db_list.crowldbgrab() + db_list.backlinkdbgrab()

    try:
        # Find the specific database
        db = next((d for d in all_dbs if d and d['name'] == db_name), None)

        if not db:
            available_dbs = [d['name'] for d in all_dbs if d]
            print(f"❌ Database '{db_name}' not found")
            print(f"Available databases: {', '.join(available_dbs)}")
            return

        # Get health information
        usage = health.current_limit(db['name'], db['organization'], db['apikey'])

        print(f"🔍 Database: {db_name}")
        print("=" * 40)
        print(f"Type: {'crawler' if db in db_list.crowldbgrab() else 'backlink'}")
        print(f"Organization: {db['organization']}")

        if usage:
            storage_used = usage.get('storage_bytes', 0)
            writes_used = usage.get('rows_written', 0)
            storage_limit = db.get('storage_quota_gb', 5) * 1024**3
            write_limit = db.get('monthly_write_limit', 10000000)

            storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
            write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

            if storage_percent >= 90 or write_percent >= 90:
                status = "CRITICAL"
            elif storage_percent >= 75 or write_percent >= 75:
                status = "WARNING"
            else:
                status = "HEALTHY"

            print(f"Status: {status}")
            print(f"Storage Usage: {storage_percent:.1f}%")
            print(f"Write Usage: {write_percent:.1f}%")
            print(f"Storage Used: {format_bytes(storage_used)}")
            print(f"Writes Used: {format_number(writes_used)}")

            if status != 'HEALTHY':
                print("\\n⚠️ Recommendations:")
                if storage_percent >= 85:
                    print("  • Consider rotating to a different database for storage")
                if write_percent >= 85:
                    print("  • Consider rotating to a different database for writes")
        else:
            print("Status: UNKNOWN")
            print("Unable to retrieve usage information")

    except Exception as e:
        print(f"❌ Error checking database '{db_name}': {e}")


def list_databases():
    """List all available databases"""
    db_list = DBList()

    print("📋 Available Databases")
    print("=" * 50)

    # Crawler databases
    crawler_dbs = db_list.crowldbgrab()
    if crawler_dbs:
        print("🌐 Crawler Databases:")
        for db in crawler_dbs:
            if db:
                print(f"  • {db['name']} (org: {db['organization']})")
        print()

    # Backlink databases
    backlink_dbs = db_list.backlinkdbgrab()
    if backlink_dbs:
        print("🔗 Backlink Databases:")
        for db in backlink_dbs:
            if db:
                print(f"  • {db['name']} (org: {db['organization']})")
        print()

    total_dbs = len([db for db in crawler_dbs + backlink_dbs if db])
    print(f"Total: {total_dbs} databases")


def get_rotation_recommendations():
    """Get database rotation recommendations"""
    print("🔄 Database Rotation Recommendations")
    print("=" * 50)

    health = Health()
    db_list = DBList()
    all_dbs = db_list.crowldbgrab() + db_list.backlinkdbgrab()

    recommendations = []

    for db in all_dbs:
        if not db:
            continue

        try:
            usage = health.current_limit(db['name'], db['organization'], db['apikey'])
            if usage:
                storage_used = usage.get('storage_bytes', 0)
                writes_used = usage.get('rows_written', 0)
                storage_limit = db.get('storage_quota_gb', 5) * 1024**3
                write_limit = db.get('monthly_write_limit', 10000000)

                storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
                write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

                if storage_percent >= 75 or write_percent >= 75:
                    # Find alternative databases of same type
                    db_type = 'crawler' if db in db_list.crowldbgrab() else 'backlink'
                    same_type_dbs = db_list.crowldbgrab() if db_type == 'crawler' else db_list.backlinkdbgrab()

                    alternatives = []
                    for alt_db in same_type_dbs:
                        if alt_db and alt_db['name'] != db['name']:
                            try:
                                alt_usage = health.current_limit(alt_db['name'], alt_db['organization'], alt_db['apikey'])
                                if alt_usage:
                                    alt_storage = alt_usage.get('storage_bytes', 0)
                                    alt_writes = alt_usage.get('rows_written', 0)
                                    alt_storage_percent = (alt_storage / storage_limit) * 100 if storage_limit > 0 else 0
                                    alt_write_percent = (alt_writes / write_limit) * 100 if write_limit > 0 else 0

                                    if alt_storage_percent < 75 and alt_write_percent < 75:
                                        alternatives.append({
                                            'name': alt_db['name'],
                                            'storage_percent': alt_storage_percent,
                                            'write_percent': alt_write_percent
                                        })
                            except:
                                continue

                    if alternatives:
                        best_alternative = min(alternatives, key=lambda x: x['storage_percent'] + x['write_percent'])
                        recommendations.append({
                            "current": db["name"],
                            "recommended": best_alternative["name"],
                            "reason": ".1f",
                            "alternative_health": ".1f"
                        })

        except Exception:
            continue

    if recommendations:
        for rec in recommendations:
            print(f"🔄 Rotate: {rec['current']} → {rec['recommended']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Alternative Health: {rec['alternative_health']}")
            print()
    else:
        print("✅ No rotation needed - all databases are healthy!")


def export_status_report():
    """Export detailed status report to JSON"""
    health = Health()
    db_list = DBList()

    # Create status data similar to the old format
    all_dbs = db_list.crowldbgrab() + db_list.backlinkdbgrab()
    db_status = []

    for db in all_dbs:
        if not db:
            continue

        try:
            usage = health.current_limit(db['name'], db['organization'], db['apikey'])
            if usage:
                storage_used = usage.get('storage_bytes', 0)
                writes_used = usage.get('rows_written', 0)
                storage_limit = db.get('storage_quota_gb', 5) * 1024**3
                write_limit = db.get('monthly_write_limit', 10000000)

                storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
                write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

                if storage_percent >= 90 or write_percent >= 90:
                    status = "critical"
                elif storage_percent >= 75 or write_percent >= 75:
                    status = "warning"
                else:
                    status = "healthy"

                db_status.append({
                    "name": db['name'],
                    "type": 'crawler' if db in db_list.crowldbgrab() else 'backlink',
                    "organization": db['organization'],
                    "status": status,
                    "storage_used": storage_used,
                    "storage_limit": int(storage_limit),
                    "storage_percent": storage_percent,
                    "writes_used": writes_used,
                    "monthly_limit": write_limit,
                    "writes_percent": write_percent
                })
        except:
            continue

    # Calculate summary
    healthy_count = len([db for db in db_status if db['status'] == 'healthy'])
    warning_count = len([db for db in db_status if db['status'] == 'warning'])
    critical_count = len([db for db in db_status if db['status'] == 'critical'])

    status_data = {
        "summary": {
            "total": len(db_status),
            "healthy": healthy_count,
            "warning": warning_count,
            "critical": critical_count
        },
        "databases": db_status
    }

    report = {
        "timestamp": datetime.now().isoformat(),
        "system_health": "healthy" if critical_count == 0 else "needs_attention",
        "database_status": status_data,
        "recommendations": []
    }

    # Add recommendations
    for db in db_status:
        if db["status"] != "healthy":
            report["recommendations"].append({
                "database": db["name"],
                "issue": f"{db['status']} status",
                "details": ".1f",
                "suggested_action": "Consider database rotation"
            })

    filename = f"database_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"📊 Status report exported to: {filename}")
    get_logger("monitor").info(f"Database health report exported to {filename}")


def format_bytes(bytes_val):
    """Format bytes to human readable format"""
    if bytes_val == 0:
        return "0 B"
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while bytes_val >= 1024 and i < len(sizes) - 1:
        bytes_val /= 1024
        i += 1
    return f"{bytes_val:.2f} {sizes[i]}"


def format_number(num):
    """Format number with thousands separators"""
    return f"{num:,}"


def main():
    """Automatic database monitoring - no arguments needed"""
    logger = get_logger("monitor")

    print("🤖 Automated Database Health Monitor")
    print("=" * 50)
    logger.info("Starting automated database health monitoring")

    try:
        # Auto-run all monitoring functions
        display_summary()
        display_detailed_status()
        get_rotation_recommendations()
        export_status_report()

        print("✅ Automated monitoring complete!")
        logger.info("Automated database health monitoring completed successfully")

    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        logger.error(f"Error during database monitoring: {e}")
        raise


if __name__ == "__main__":
    main()
