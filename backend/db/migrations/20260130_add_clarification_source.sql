-- Migration: Add 'whatsapp_clarification' to source CHECK constraint
-- Date: 2026-01-30
-- Stage: 2.4 - Clarification flow support

-- SQLite doesn't support ALTER TABLE to modify CHECK constraints
-- We need to recreate the table with the new constraint

-- Step 1: Create new table with updated constraint
CREATE TABLE task_activities_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    
    -- Author information
    author_type TEXT NOT NULL CHECK(author_type IN ('employee', 'admin', 'system')),
    author_id INTEGER,
    author_name TEXT,
    
    -- Activity classification
    activity_type TEXT NOT NULL CHECK(activity_type IN ('comment', 'attachment', 'status_change', 'mention', 'system')),
    source TEXT NOT NULL CHECK(source IN ('whatsapp_reply', 'whatsapp_reply_unlinked', 'whatsapp_clarification', 'form_submission', 'web_dashboard', 'system')),
    
    -- Content
    message TEXT,
    
    -- WhatsApp threading support
    mentioned_user_id INTEGER,
    whatsapp_sent BOOLEAN DEFAULT 0,
    whatsapp_message_id TEXT,
    
    -- Stage 2.1 - Phase 2 enhancements
    mention_notification_sent BOOLEAN DEFAULT 0,
    mention_notification_message_id TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (mentioned_user_id) REFERENCES employees(id) ON DELETE SET NULL
);

-- Step 2: Copy all data from old table
INSERT INTO task_activities_new 
SELECT * FROM task_activities;

-- Step 3: Drop old table
DROP TABLE task_activities;

-- Step 4: Rename new table to original name
ALTER TABLE task_activities_new RENAME TO task_activities;

-- Step 5: Recreate indexes
CREATE INDEX idx_task_activities_task_id ON task_activities(task_id);
CREATE INDEX idx_task_activities_author ON task_activities(author_type, author_id);
CREATE INDEX idx_task_activities_created_at ON task_activities(created_at);
CREATE INDEX idx_task_activities_whatsapp_msg ON task_activities(whatsapp_message_id);
CREATE INDEX idx_task_activities_mention_msg ON task_activities(mention_notification_message_id);
