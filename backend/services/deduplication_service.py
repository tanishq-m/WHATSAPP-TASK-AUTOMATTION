"""
Deduplication Service
Prevents duplicate processing of webhooks, activities, and file downloads.

This service ensures:
- Webhooks are not processed multiple times
- Activities are not created duplicately 
- Files are not downloaded/stored multiple times
- Database remains clean and consistent
"""

import hashlib
import json
from datetime import datetime, timedelta
import os
import db


def compute_payload_hash(payload):
    """
    Compute SHA-256 hash of webhook payload for verification.
    
    Args:
        payload (dict): Webhook payload
        
    Returns:
        str: Hex digest of payload hash
    """
    if not payload:
        return None
    
    try:
        # Sort keys for consistent hashing
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()
    except Exception as e:
        print(f"❌ Error computing payload hash: {e}")
        return None


def is_webhook_processed(webhook_id, phone=None):
    """
    Check if webhook has already been processed.
    
    Args:
        webhook_id (str): Unique webhook ID from payload
        phone (str): Phone number (optional, for additional filtering)
        
    Returns:
        bool: True if already processed, False otherwise
    """
    if not webhook_id:
        print("⚠️ No webhook ID provided for deduplication check")
        return False
    
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            if phone:
                cursor.execute("""
                    SELECT id, processed_at 
                    FROM webhook_deduplication 
                    WHERE webhook_id = ? AND phone = ?
                """, (webhook_id, phone))
            else:
                cursor.execute("""
                    SELECT id, processed_at 
                    FROM webhook_deduplication 
                    WHERE webhook_id = ?
                """, (webhook_id,))
            
            result = cursor.fetchone()
            
            if result:
                print(f"⚠️ Duplicate webhook detected: {webhook_id}")
                print(f"   Originally processed at: {result['processed_at']}")
                return True
            
            return False
            
    except Exception as e:
        print(f"❌ Error checking webhook duplication: {e}")
        # Fail open - allow processing if check fails to avoid blocking legitimate requests
        return False


def mark_webhook_processed(webhook_id, webhook_type, phone=None, payload=None):
    """
    Mark webhook as processed to prevent future duplicates.
    
    Args:
        webhook_id (str): Unique webhook ID
        webhook_type (str): Type of webhook (message|status|button_click)
        phone (str): Phone number involved (optional)
        payload (dict): Full webhook payload (optional)
        
    Returns:
        dict: Success response
    """
    if not webhook_id:
        return {'success': False, 'error': 'No webhook ID provided'}
    
    try:
        payload_hash = compute_payload_hash(payload) if payload else None
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO webhook_deduplication 
                (webhook_id, webhook_type, phone, payload_hash)
                VALUES (?, ?, ?, ?)
            """, (webhook_id, webhook_type, phone, payload_hash))
            
            conn.commit()
            
            print(f"✅ Marked webhook as processed: {webhook_id}")
            return {'success': True, 'webhook_id': webhook_id}
            
    except Exception as e:
        print(f"❌ Error marking webhook as processed: {e}")
        return {'success': False, 'error': str(e)}


def is_activity_duplicate(task_id, author_id, message, author_type='employee', created_at_threshold_seconds=60):
    """
    Check if activity is a duplicate based on task, author, and message.
    
    Detects duplicates if same author posted identical message to same task
    within threshold window (default 60 seconds).
    
    Args:
        task_id (str): Task ID
        author_id (int): Author ID
        message (str): Activity message/content
        author_type (str): Type of author (employee|admin)
        created_at_threshold_seconds (int): Time window for duplicate detection
        
    Returns:
        bool: True if duplicate detected, False otherwise
    """
    if not task_id or not author_id or not message:
        return False
    
    try:
        # Calculate threshold timestamp (SQLite format)
        # Note: SQLite datetime('now') returns UTC, so we must use UTC here too
        from datetime import timezone
        threshold_time = datetime.now(timezone.utc) - timedelta(seconds=created_at_threshold_seconds)
        threshold_str = threshold_time.strftime('%Y-%m-%d %H:%M:%S')
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, created_at 
                FROM task_activities 
                WHERE task_id = ? 
                  AND author_id = ?
                  AND author_type = ?
                  AND message = ?
                  AND datetime(created_at) >= datetime(?)
                ORDER BY created_at DESC
                LIMIT 1
            """, (task_id, author_id, author_type, message, threshold_str))
            
            result = cursor.fetchone()
            
            if result:
                print(f"⚠️ Duplicate activity detected for task {task_id}")
                print(f"   Author: {author_id} ({author_type}), Recent activity at: {result['created_at']}")
                return True
            
            return False
            
    except Exception as e:
        print(f"❌ Error checking activity duplication: {e}")
        # Fail open - allow creation if check fails
        return False


def compute_file_hash(file_path):
    """
    Compute SHA-256 hash of file for duplicate detection.
    
    Args:
        file_path (str): Path to file
        
    Returns:
        str: Hex digest of file hash, or None if error
    """
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in 64kb chunks for memory efficiency
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"❌ Error computing file hash: {e}")
        return None


def is_file_duplicate(file_hash, task_id=None):
    """
    Check if file with same hash already exists in database.
    
    Args:
        file_hash (str): SHA-256 hash of file
        task_id (str): Optional task ID to scope check to specific task
        
    Returns:
        bool: True if duplicate found, False otherwise
    """
    if not file_hash:
        return False
    
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            if task_id:
                cursor.execute("""
                    SELECT file_path 
                    FROM task_activity_attachments 
                    WHERE file_hash = ? AND task_id = ?
                    LIMIT 1
                """, (file_hash, task_id))
            else:
                cursor.execute("""
                    SELECT file_path 
                    FROM task_activity_attachments 
                    WHERE file_hash = ?
                    LIMIT 1
                """, (file_hash,))
            
            result = cursor.fetchone()
            
            if result:
                print(f"⚠️ Duplicate file detected: {file_hash[:16]}...")
                print(f"   Existing file: {result['file_path']}")
                return True
            
            return False
            
    except Exception as e:
        print(f"❌ Error checking file duplication: {e}")
        # Fail open - allow storage if check fails
        return False


def cleanup_old_deduplication_records(days_to_keep=7):
    """
    Clean up old deduplication records to prevent table bloat.
    Should be run periodically (e.g., daily cron job).
    
    Args:
        days_to_keep (int): Number of days to keep records
        
    Returns:
        dict: Cleanup statistics
    """
    try:
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Count records to be deleted
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM webhook_deduplication 
                WHERE datetime(processed_at) < datetime(?)
            """, (cutoff_str,))
            
            count = cursor.fetchone()['count']
            
            # Delete old records
            cursor.execute("""
                DELETE FROM webhook_deduplication 
                WHERE datetime(processed_at) < datetime(?)
            """, (cutoff_str,))
            
            conn.commit()
            
            print(f"✅ Cleaned up {count} old deduplication records (older than {days_to_keep} days)")
            
            # Get remaining count
            cursor.execute("SELECT COUNT(*) as remaining FROM webhook_deduplication")
            remaining = cursor.fetchone()['remaining']
            
            return {
                'success': True,
                'deleted_count': count,
                'remaining_count': remaining,
                'cutoff_date': cutoff_str,
                'days_kept': days_to_keep
            }
            
    except Exception as e:
        print(f"❌ Error cleaning up deduplication records: {e}")
        return {'success': False, 'error': str(e)}


def get_deduplication_stats():
    """
    Get statistics about deduplication table.
    Useful for monitoring and debugging.
    
    Returns:
        dict: Statistics including total records, oldest/newest, types breakdown
    """
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) as total FROM webhook_deduplication")
            total = cursor.fetchone()['total']
            
            # Oldest record
            cursor.execute("SELECT MIN(processed_at) as oldest FROM webhook_deduplication")
            oldest = cursor.fetchone()['oldest']
            
            # Newest record
            cursor.execute("SELECT MAX(processed_at) as newest FROM webhook_deduplication")
            newest = cursor.fetchone()['newest']
            
            # Breakdown by type
            cursor.execute("""
                SELECT webhook_type, COUNT(*) as count 
                FROM webhook_deduplication 
                GROUP BY webhook_type
            """)
            types = {row['webhook_type']: row['count'] for row in cursor.fetchall()}
            
            # Count specific types for convenience
            webhook_count = sum(count for wtype, count in types.items() 
                              if wtype in ('button_reply', 'text_reply', 'media_image', 'media_video', 'media_document', 'media_audio'))
            activity_count = types.get('activity', 0)
            file_count = types.get('file', 0)
            
            return {
                'success': True,
                'total_records': total,
                'webhook_count': webhook_count,
                'activity_count': activity_count,
                'file_count': file_count,
                'oldest_record': oldest,
                'newest_record': newest,
                'by_type': types
            }
            
    except Exception as e:
        print(f"❌ Error getting deduplication stats: {e}")
        return {'success': False, 'error': str(e)}
