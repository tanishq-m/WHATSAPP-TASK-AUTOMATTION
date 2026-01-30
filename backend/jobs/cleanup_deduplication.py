#!/usr/bin/env python3
"""
Deduplication Cleanup Job

This script removes old deduplication records to prevent the webhook_deduplication
table from growing indefinitely. Should be run periodically (e.g., via cron).

Default retention: 7 days
Records older than 7 days are deleted.

Usage:
    python jobs/cleanup_deduplication.py [--days DAYS] [--dry-run]

Examples:
    python jobs/cleanup_deduplication.py              # Default: 7 days
    python jobs/cleanup_deduplication.py --days 14    # Keep 14 days
    python jobs/cleanup_deduplication.py --dry-run    # Preview without deleting

Cron Example (daily at 2 AM):
    0 2 * * * cd /path/to/whatsapp-task-manager/backend && python jobs/cleanup_deduplication.py >> logs/cleanup.log 2>&1
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.deduplication_service as dedup_service


def main():
    """Main cleanup function"""
    parser = argparse.ArgumentParser(
        description='Clean up old deduplication records',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to retain records (default: 7)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview records to be deleted without actually deleting'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"Deduplication Cleanup Job - {datetime.now().isoformat()}")
    print("=" * 80)
    print(f"Retention period: {args.days} days")
    print(f"Dry run: {args.dry_run}")
    print()
    
    # Get stats before cleanup
    print("📊 Current deduplication statistics:")
    stats = dedup_service.get_deduplication_stats()
    print(f"  Total records: {stats['total_records']}")
    print(f"  Webhooks: {stats['webhook_count']}")
    print(f"  Activities: {stats['activity_count']}")
    print(f"  Files: {stats['file_count']}")
    print(f"  Records older than {args.days} days: {stats.get('old_records', 0)}")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No records will be deleted")
        print(f"Would delete records older than {args.days} days")
        print()
        return 0
    
    # Perform cleanup
    print(f"🧹 Cleaning up records older than {args.days} days...")
    result = dedup_service.cleanup_old_deduplication_records(days_to_keep=args.days)
    
    if result['success']:
        print(f"✅ Cleanup completed successfully")
        print(f"  Deleted records: {result['deleted_count']}")
        print(f"  Remaining records: {result['remaining_count']}")
        print()
        
        # Show updated stats
        print("📊 Updated deduplication statistics:")
        new_stats = dedup_service.get_deduplication_stats()
        print(f"  Total records: {new_stats['total_records']}")
        print(f"  Webhooks: {new_stats['webhook_count']}")
        print(f"  Activities: {new_stats['activity_count']}")
        print(f"  Files: {new_stats['file_count']}")
        print()
        
        return 0
    else:
        print(f"❌ Cleanup failed: {result.get('error')}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
