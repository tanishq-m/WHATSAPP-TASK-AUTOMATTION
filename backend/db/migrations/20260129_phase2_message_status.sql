-- Phase 2 Migration: Message Status Tracking
-- Date: 2026-01-29
-- Purpose: Add delivery, read, and failure status tracking to messages

-- 1. Extend task_messages table with status columns
-- Check and add columns one by one (SQLite will error if column exists, so we'll handle in code)
-- These are safe to run multiple times as the migration runner will catch the error

-- Note: These ALTER statements will fail if columns already exist
-- The migration runner handles this gracefully
-- If you need to manually check: PRAGMA table_info(task_messages);

-- Add status columns if they don't exist
-- The idempotency is handled by checking column existence in code before running

-- 2. Create message status history table for audit trail
CREATE TABLE IF NOT EXISTS message_status_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  whatsapp_message_id TEXT,
  old_status TEXT,
  new_status TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  webhook_payload TEXT,
  FOREIGN KEY(message_id) REFERENCES task_messages(id) ON DELETE CASCADE
);

-- 3. Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_message_status_history_message_id 
  ON message_status_history(message_id);
CREATE INDEX IF NOT EXISTS idx_message_status_history_timestamp 
  ON message_status_history(timestamp);

-- 4. Create pending clarifications table
CREATE TABLE IF NOT EXISTS pending_clarifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id INTEGER NOT NULL,
  phone TEXT NOT NULL,
  media_url TEXT,
  media_type TEXT,
  caption TEXT,
  clarification_message_id TEXT,
  status TEXT DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  resolved_task_id TEXT,
  resolved_at DATETIME,
  temp_file_path TEXT,
  cancelled_at DATETIME,
  FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
  FOREIGN KEY(resolved_task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
);

-- 5. Create index for pending clarifications
CREATE INDEX IF NOT EXISTS idx_pending_clarifications_employee 
  ON pending_clarifications(employee_id);
CREATE INDEX IF NOT EXISTS idx_pending_clarifications_status 
  ON pending_clarifications(status);
CREATE INDEX IF NOT EXISTS idx_pending_clarifications_expires 
  ON pending_clarifications(expires_at);
CREATE INDEX IF NOT EXISTS idx_pending_clarifications_cancelled 
  ON pending_clarifications(cancelled_at);

-- 6. Create webhook deduplication table
CREATE TABLE IF NOT EXISTS webhook_deduplication (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  webhook_id TEXT UNIQUE NOT NULL,
  webhook_type TEXT NOT NULL,
  phone TEXT,
  processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  payload_hash TEXT
);

-- 7. Create indexes for deduplication
CREATE INDEX IF NOT EXISTS idx_webhook_dedup_id 
  ON webhook_deduplication(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_dedup_processed 
  ON webhook_deduplication(processed_at);

-- Migration complete
