-- Migration: Add file_hash column for deduplication
-- Date: 2026-01-30
-- Purpose: Add file hash column to detect and prevent duplicate file storage

-- Note: SQLite doesn't support adding columns with constraints after creation,
-- so we use a simple ALTER TABLE. The migration runner handles idempotency.

-- Add file_hash column if it doesn't exist
-- The migration runner will catch the error if column already exists
