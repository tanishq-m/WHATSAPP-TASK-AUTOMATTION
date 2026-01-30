-- Migration: Add Activity Tables for Rich Task Communication
-- Created: 2026-01-27
-- Description: Adds tables for task activities, attachments, and submission tokens

-- ============================================================================
-- TASK SUBMISSION TOKENS
-- Generates unique URLs for form-based task submission
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_submission_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    employee_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    submitted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_submission_tokens_token ON task_submission_tokens(token);
CREATE INDEX IF NOT EXISTS idx_submission_tokens_task_id ON task_submission_tokens(task_id);
CREATE INDEX IF NOT EXISTS idx_submission_tokens_employee_id ON task_submission_tokens(employee_id);

-- ============================================================================
-- TASK ACTIVITIES
-- Stores all activity/interaction on a task (comments, status changes, mentions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_activities (
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
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (author_id) REFERENCES employees(id),
    FOREIGN KEY (mentioned_user_id) REFERENCES employees(id)
);

CREATE INDEX IF NOT EXISTS idx_activities_task_id ON task_activities(task_id);
CREATE INDEX IF NOT EXISTS idx_activities_author_id ON task_activities(author_id);
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON task_activities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activities_whatsapp_message_id ON task_activities(whatsapp_message_id);

-- ============================================================================
-- TASK ACTIVITY ATTACHMENTS
-- Stores files (images, documents, videos) linked to activities
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_activity_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL,
    task_id TEXT NOT NULL,
    
    -- File metadata
    media_type TEXT NOT NULL CHECK(media_type IN ('image', 'video', 'document', 'audio')),
    file_path TEXT NOT NULL,
    filename TEXT,
    content_type TEXT,
    file_size INTEGER,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (activity_id) REFERENCES task_activities(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

CREATE INDEX IF NOT EXISTS idx_attachments_activity_id ON task_activity_attachments(activity_id);
CREATE INDEX IF NOT EXISTS idx_attachments_task_id ON task_activity_attachments(task_id);

-- ============================================================================
-- TASK MESSAGES (for WhatsApp reply threading)
-- Maps WhatsApp message IDs to tasks for reply threading
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    whatsapp_message_id TEXT NOT NULL UNIQUE,
    employee_phone TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT 'eod_check',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

CREATE INDEX IF NOT EXISTS idx_task_messages_whatsapp_id ON task_messages(whatsapp_message_id);
CREATE INDEX IF NOT EXISTS idx_task_messages_task_id ON task_messages(task_id);
