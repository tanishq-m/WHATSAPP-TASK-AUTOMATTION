# Phase 2 Implementation Plan: Reliability & UX Enhancements

**Start Date**: 2026-01-29  
**Status**: In Progress  
**Phase 1 Completion**: ✅ All core features implemented and tested

> **Note**: Phase 3 implementation details have been moved to [`PHASE_3_DASHBOARD.md`](./PHASE_3_DASHBOARD.md) for better organization.

---

## Overview

Phase 2 focuses on reliability, user experience improvements, and production-ready features that make the system more robust and intuitive. This includes message status tracking, @mentions, bot clarification, duplicate prevention, and polling optimizations.

---

## Stage Breakdown

### **Stage 2.1: Database Schema Updates for Read/Delivery Status**

**Goal**: Extend database schema to track WhatsApp message delivery and read status, including inference logic.

**Changes**:
1. Add columns to `task_messages` table:
   - `delivered_at` (DATETIME)
   - `read_at` (DATETIME) 
   - `failed_at` (DATETIME)
   - `failure_reason` (TEXT)
   - `read_receipt_available` (BOOLEAN) - tracks if user has receipts enabled
   - `read_inferred` (BOOLEAN) - true if read status inferred from reply/action

2. Add `message_status_history` table for audit trail:
   - Track status transitions with timestamps
   - Store webhook payloads for debugging

**SQL**:
```sql
-- Extend task_messages table
ALTER TABLE task_messages ADD COLUMN delivered_at DATETIME;
ALTER TABLE task_messages ADD COLUMN read_at DATETIME;
ALTER TABLE task_messages ADD COLUMN failed_at DATETIME;
ALTER TABLE task_messages ADD COLUMN failure_reason TEXT;
ALTER TABLE task_messages ADD COLUMN read_receipt_available BOOLEAN DEFAULT NULL;
ALTER TABLE task_messages ADD COLUMN read_inferred BOOLEAN DEFAULT FALSE;

-- Create status history table
CREATE TABLE IF NOT EXISTS message_status_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  whatsapp_message_id TEXT,
  old_status TEXT,
  new_status TEXT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  webhook_payload TEXT,
  FOREIGN KEY(message_id) REFERENCES task_messages(id)
);
```

**Acceptance Criteria**:
- ✅ Database migration runs successfully
- ✅ New columns accept NULL values for backward compatibility
- ✅ Can insert and query message status data
- ✅ History table tracks all status changes

**Tests**:
- `test_message_status_schema_exists()`
- `test_message_status_insert_and_retrieve()`
- `test_message_status_history_tracking()`
- `test_backward_compatibility_with_existing_messages()`

---

### **Stage 2.2: Webhook Handlers for Delivery and Read Receipts**

**Goal**: Process WhatsApp status webhooks (delivered, read, failed) and update database accordingly.

**Implementation**:
1. Extend `backend/api/webhooks.py`:
   - Add `handle_status_update(payload)` function
   - Parse delivery, read, and failure status webhooks
   - Update `task_messages` table with timestamps
   - Create entries in `message_status_history`

2. Add inference logic:
   - When reply received without read receipt → mark as `read_inferred=True`
   - When task status changes after message sent → infer read
   - Track pattern to detect if user has receipts disabled

**Webhook Format** (from Kapso):
```json
{
  "statuses": [{
    "id": "wamid.xxx",
    "status": "delivered|read|failed",
    "timestamp": "1706544000",
    "recipient_id": "919876543210",
    "errors": [{"code": 131047, "title": "Re-engagement message"}]
  }]
}
```

**Code Structure**:
```python
def handle_status_update(payload):
    """Process delivery/read/failed status webhooks"""
    statuses = payload.get('statuses', [])
    for status_item in statuses:
        whatsapp_message_id = status_item.get('id')
        status = status_item.get('status')
        timestamp = status_item.get('timestamp')
        
        # Find message in database
        message = get_message_by_whatsapp_id(whatsapp_message_id)
        if not message:
            continue
            
        # Update status based on type
        if status == 'delivered':
            update_message_delivered(message.id, timestamp)
        elif status == 'read':
            update_message_read(message.id, timestamp)
        elif status == 'failed':
            update_message_failed(message.id, timestamp, status_item.get('errors'))
```

**Acceptance Criteria**:
- ✅ Delivery webhooks update `delivered_at` timestamp
- ✅ Read webhooks update `read_at` timestamp
- ✅ Failed webhooks update `failed_at` and `failure_reason`
- ✅ Status history entries created for all updates
- ✅ Inference logic detects read from replies

**Tests**:
- `test_webhook_delivery_status_update()`
- `test_webhook_read_status_update()`
- `test_webhook_failed_status_update()`
- `test_read_inference_from_reply()`
- `test_read_inference_from_task_status_change()`
- `test_detect_disabled_read_receipts()`
- `test_duplicate_status_webhooks_handled()`

---

### **Stage 2.3: Backend API for @Mentions and WhatsApp Notifications**

**Goal**: Allow admins to @mention employees in comments, triggering WhatsApp notifications.

**Implementation**:
1. Extend `task_activities` table (already has `mentioned_user_id`):
   - Add `mention_notification_sent` (BOOLEAN)
   - Add `mention_notification_message_id` (TEXT)

2. Add `services/mention_service.py`:
   - Parse @mentions from comment text (e.g., "@John Doe")
   - Match to employee by name
   - Send WhatsApp notification with context
   - Link notification message to activity

3. Notification message format:
   ```
   📌 You were mentioned in Task #123: "Website Redesign"
   
   By: Admin Name
   Comment: "Great work on the mockups! @John please review the color scheme"
   
   View task: [task_url]
   ```

4. Add API endpoint `POST /api/tasks/:taskId/activities/:activityId/notify-mention`:
   - Resend notification if failed
   - Admin can manually trigger if auto-send disabled

**Code Structure**:
```python
def process_mentions_in_comment(activity_id, comment_text, task_id):
    """Extract @mentions and send WhatsApp notifications"""
    mentions = extract_mentions(comment_text)  # Returns [(name, employee_id)]
    
    for name, employee_id in mentions:
        employee = get_employee_by_id(employee_id)
        if not employee or not employee.phone:
            continue
        
        # Send WhatsApp notification
        message_text = format_mention_notification(task_id, activity_id, comment_text, name)
        result = kapso_service.send_text_message(employee.phone, message_text)
        
        # Update activity with notification status
        if result.get('success'):
            update_activity_mention_notification(
                activity_id, 
                employee_id,
                result.get('whatsapp_message_id')
            )
```

**Acceptance Criteria**:
- ✅ @mentions parsed correctly from comment text
- ✅ WhatsApp notifications sent to mentioned employees
- ✅ Notification message includes task context
- ✅ Failed notifications logged and retryable
- ✅ Multiple mentions in one comment handled
- ✅ Invalid mentions (non-existent users) handled gracefully

**Tests**:
- `test_parse_mentions_from_comment()`
- `test_send_mention_notification_success()`
- `test_send_mention_notification_failure()`
- `test_multiple_mentions_in_single_comment()`
- `test_mention_nonexistent_user_handled()`
- `test_mention_notification_retry()`
- `test_mention_message_format()`

---

### **Stage 2.4: Enhanced Bot Clarification for Unlinked Replies**

**Goal**: Improve handling of WhatsApp messages that aren't threaded properly by asking clarifying questions.

**Implementation**:
1. Extend webhook handler for unlinked messages:
   - When media received without `context.id`
   - Send interactive message asking which task
   - Store pending clarification in `pending_clarifications` table

2. Create `pending_clarifications` table:
   ```sql
   CREATE TABLE IF NOT EXISTS pending_clarifications (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     employee_id INTEGER NOT NULL,
     phone TEXT NOT NULL,
     media_url TEXT,
     media_type TEXT,
     caption TEXT,
     clarification_message_id TEXT,
     status TEXT DEFAULT 'pending', -- pending|resolved|expired
     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
     expires_at DATETIME,
     resolved_task_id TEXT,
     FOREIGN KEY(employee_id) REFERENCES employees(id)
   );
   ```

3. Clarification flow:
   - Bot sends: "I received your [photo/document]. Which task is this for?"
   - Include buttons with recent tasks or "Other"
   - When user responds, link media to task and create activity
   - If no response in 24 hours, mark as expired and notify admin

4. Add endpoint `GET /api/clarifications/pending`:
   - Admins can see unresolved clarifications
   - Manual assignment option

**Clarification Message Example**:
```json
{
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": {
      "text": "📎 I received your photo. Which task is this for?"
    },
    "action": {
      "buttons": [
        {"id": "task_001", "title": "Task #001: Website"},
        {"id": "task_002", "title": "Task #002: Report"},
        {"id": "other", "title": "Something else"}
      ]
    }
  }
}
```

**Acceptance Criteria**:
- ✅ Unlinked media triggers clarification request
- ✅ Recent tasks shown as button options
- ✅ User response links media to correct task
- ✅ Expired clarifications flagged for admin review
- ✅ Admin can manually resolve clarifications

**Tests**:
- `test_unlinked_media_triggers_clarification()`
- `test_clarification_message_format()`
- `test_user_selects_task_from_buttons()`
- `test_clarification_expires_after_24_hours()`
- `test_admin_manual_clarification_assignment()`
- `test_clarification_with_multiple_media()`

---

### **Stage 2.5: Duplicate Prevention Improvements**

**Goal**: Prevent duplicate processing of webhooks, activities, and notifications.

**Implementation**:
1. Add `webhook_deduplication` table:
   ```sql
   CREATE TABLE IF NOT EXISTS webhook_deduplication (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     webhook_id TEXT UNIQUE NOT NULL,
     webhook_type TEXT NOT NULL, -- message|status|button_click
     phone TEXT,
     processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
     payload_hash TEXT
   );
   
   CREATE INDEX idx_webhook_id ON webhook_deduplication(webhook_id);
   CREATE INDEX idx_processed_at ON webhook_deduplication(processed_at);
   ```

2. Deduplication strategy:
   - Use webhook ID from payload as primary key
   - Hash payload content for extra verification
   - Check before processing any webhook
   - Clean up old entries (>7 days) periodically

3. Activity deduplication:
   - Check for duplicate activities by `whatsapp_message_id` + `employee_id`
   - Prevent duplicate file downloads by checking file hash
   - Use database constraints where appropriate

4. Add `services/deduplication_service.py`:
   ```python
   def is_webhook_processed(webhook_id, payload):
       """Check if webhook already processed"""
       existing = db.get_webhook_by_id(webhook_id)
       if existing:
           # Verify payload hash matches
           if hash_payload(payload) == existing.payload_hash:
               return True
       return False
   
   def mark_webhook_processed(webhook_id, webhook_type, phone, payload):
       """Mark webhook as processed"""
       db.insert_webhook_dedup(
           webhook_id=webhook_id,
           webhook_type=webhook_type,
           phone=phone,
           payload_hash=hash_payload(payload)
       )
   ```

**Acceptance Criteria**:
- ✅ Duplicate webhooks ignored without processing
- ✅ Duplicate activities not created
- ✅ Duplicate file downloads prevented
- ✅ Deduplication table cleaned up periodically
- ✅ Performance impact minimal (<10ms per request)

**Tests**:
- `test_duplicate_webhook_ignored()`
- `test_duplicate_activity_prevented()`
- `test_duplicate_file_download_skipped()`
- `test_deduplication_table_cleanup()`
- `test_different_webhooks_both_processed()`
- `test_deduplication_performance()`

---

### **Stage 2.6: Smart Polling Refinements**

**Goal**: Optimize frontend polling for better performance and responsiveness.

**Backend Changes**:
1. Add `GET /api/tasks/:taskId/changes-since`:
   - Accept `since` timestamp parameter
   - Return only activities created/updated after timestamp
   - Include `has_more` flag and `latest_timestamp`

2. Add `GET /api/tasks/activity-summary`:
   - Return counts of new activities per task
   - Lightweight endpoint for checking updates
   - Batched for multiple tasks

**Frontend Changes**:
1. Implement smart polling in `src/services/polling.service.js`:
   ```javascript
   class SmartPollingService {
     constructor() {
       this.intervals = {
         active: 5000,      // 5s for active tasks
         recent: 15000,     // 15s for recently updated
         idle: 60000        // 60s for idle tasks
       };
       this.lastActivity = {};
     }
     
     getPollingInterval(taskId) {
       const lastActivity = this.lastActivity[taskId] || 0;
       const timeSince = Date.now() - lastActivity;
       
       if (timeSince < 5 * 60 * 1000) return this.intervals.active;
       if (timeSince < 30 * 60 * 1000) return this.intervals.recent;
       return this.intervals.idle;
     }
     
     updateActivity(taskId) {
       this.lastActivity[taskId] = Date.now();
     }
   }
   ```

2. Add visibility detection:
   - Stop polling when tab not visible
   - Resume with immediate fetch when tab becomes visible
   - Use Page Visibility API

3. Batch requests:
   - Combine multiple task updates into single request
   - Use `Promise.all()` for parallel fetching
   - Cache responses with short TTL

**Acceptance Criteria**:
- ✅ Polling interval adjusts based on activity
- ✅ Polling stops when tab not visible
- ✅ Differential updates reduce data transfer
- ✅ Batch requests improve performance
- ✅ No increase in perceived latency

**Tests**:
- `test_changes_since_endpoint_returns_new_activities()`
- `test_changes_since_no_updates_returns_empty()`
- `test_activity_summary_endpoint_performance()`
- `test_smart_polling_interval_calculation()`
- `test_polling_stops_on_tab_hidden()`
- `test_batch_request_optimization()`

---

### **Stage 2.7: Frontend UI for Message Status and @Mentions**

**Goal**: Display message delivery/read status and implement @mention autocomplete.

**Implementation**:
1. Message Status Display Component:
   ```jsx
   const MessageStatus = ({ message }) => {
     const status = getMessageStatus(message);
     
     return (
       <div className="flex items-center gap-1 text-sm">
         {status === 'sent' && <span className="text-gray-500">✓ Sent</span>}
         {status === 'delivered' && <span className="text-gray-600">✓✓ Delivered</span>}
         {status === 'read' && <span className="text-blue-500">✓✓ Read</span>}
         {status === 'read_inferred' && (
           <span className="text-blue-400" title="Read status inferred from reply">
             ✓✓ Read*
           </span>
         )}
         {status === 'failed' && (
           <span className="text-red-500" title={message.failure_reason}>
             ✗ Failed
           </span>
         )}
         <span className="text-xs text-gray-400">
           {formatTime(message[`${status}_at`])}
         </span>
       </div>
     );
   };
   ```

2. @Mention Autocomplete:
   ```jsx
   const CommentBox = ({ taskId, employees, onSubmit }) => {
     const [text, setText] = useState('');
     const [showMentions, setShowMentions] = useState(false);
     const [mentionQuery, setMentionQuery] = useState('');
     
     const handleTextChange = (e) => {
       const value = e.target.value;
       setText(value);
       
       // Check for @mention trigger
       const cursorPos = e.target.selectionStart;
       const textBeforeCursor = value.slice(0, cursorPos);
       const match = textBeforeCursor.match(/@(\w*)$/);
       
       if (match) {
         setMentionQuery(match[1]);
         setShowMentions(true);
       } else {
         setShowMentions(false);
       }
     };
     
     const insertMention = (employee) => {
       const newText = text.replace(/@\w*$/, `@${employee.name} `);
       setText(newText);
       setShowMentions(false);
     };
     
     // ... render autocomplete dropdown
   };
   ```

3. Activity Feed Enhancements:
   - Show message status for WhatsApp activities
   - Highlight @mentions in comments
   - Add "mentioned you" badge for current user
   - Display clarification requests in feed

**Acceptance Criteria**:
- ✅ Message status icons displayed correctly
- ✅ @mention autocomplete works while typing
- ✅ Mentioned users highlighted in comments
- ✅ Status updates reflect in real-time (via polling)
- ✅ Failed messages show retry option

**Tests**:
- `test_message_status_display_component()`
- `test_mention_autocomplete_trigger()`
- `test_mention_insertion()`
- `test_mention_highlight_in_comment()`
- `test_failed_message_retry_button()`

---

### **Stage 2.8: Comprehensive Testing and Phase 2 Validation**

**Goal**: Ensure all Phase 2 features work together, test at scale, verify Phase 1 compatibility.

**Testing Strategy**:
1. **Integration Tests**:
   - End-to-end flows combining multiple features
   - Test mention → notification → delivery → read
   - Test clarification → resolution → activity creation

2. **Scale Testing**:
   - 100+ concurrent webhooks
   - 1000+ messages with status updates
   - 50+ simultaneous polling clients
   - Load test polling endpoints

3. **Regression Testing**:
   - Re-run all Phase 1 tests
   - Verify form submission still works
   - Verify activity feed still displays correctly
   - Check media upload/download functionality

4. **Performance Testing**:
   - Database query performance with large datasets
   - Polling overhead measurement
   - Webhook processing latency

**Test Suites**:
```python
# Backend integration tests
class TestPhase2Integration:
    def test_mention_to_whatsapp_to_read_receipt_flow(self):
        """Test complete mention flow with status tracking"""
        pass
    
    def test_unlinked_media_clarification_resolution(self):
        """Test bot clarification complete workflow"""
        pass
    
    def test_high_volume_webhook_processing(self):
        """Simulate 100+ concurrent webhooks"""
        pass
    
    def test_phase1_features_still_work(self):
        """Regression test for Phase 1 functionality"""
        pass
```

```javascript
// Frontend integration tests
describe('Phase 2 Integration', () => {
  it('should display message status and handle polling', async () => {
    // Test complete UI flow
  });
  
  it('should handle @mentions with autocomplete', async () => {
    // Test mention UI and submission
  });
  
  it('should not break Phase 1 activity feed', async () => {
    // Regression test
  });
});
```

**Acceptance Criteria**:
- ✅ All new tests pass (backend + frontend)
- ✅ All Phase 1 tests still pass
- ✅ Scale tests meet performance targets
- ✅ No memory leaks in polling service
- ✅ Manual QA checklist completed

**Manual QA Checklist**:
- [ ] Send message, verify delivery/read status
- [ ] @mention user, verify notification received
- [ ] Send unlinked media, verify clarification works
- [ ] Test with receipts on/off
- [ ] Test polling with network interruption
- [ ] Verify UI responsive on mobile
- [ ] Check database for orphaned records

---

## Success Metrics

**Reliability**:
- < 0.1% duplicate webhook processing
- < 5 second webhook processing time (95th percentile)
- 99.9% notification delivery success rate

**Performance**:
- < 100ms response time for changes-since endpoint
- < 50% reduction in polling data transfer
- < 10ms deduplication overhead

**User Experience**:
- @mentions sent within 2 seconds of posting
- Read status displayed within 5 seconds of receipt
- Clarifications resolved within 15 minutes on average

---

## Rollout Strategy

1. **Stage-by-stage deployment**: Deploy and test each stage in staging before production
2. **Feature flags**: Enable features gradually (start with @mentions, then status, etc.)
3. **Monitoring**: Track webhook processing times, notification success rates, polling efficiency
4. **Rollback plan**: Database changes are additive (no data loss on rollback)

---

## Next Steps

After Phase 2 completion:
- **Phase 3**: Owner Dashboard & Mobile-First Navigation (see `PHASE_3_DASHBOARD.md`)
- **Phase 4**: WebSockets, file previews, read receipts UI polish
- **Performance optimization**: Consider Redis for deduplication cache
- **Analytics**: Add tracking for feature usage and performance metrics

---

# Phase 3: See PHASE_3_DASHBOARD.md

Phase 3 implementation details have been moved to a separate document for better organization and clarity.

📄 **[View Phase 3 Implementation Plan →](./PHASE_3_DASHBOARD.md)**

**Phase 3 Overview**: Owner Dashboard & Mobile-First Navigation
- Phase 3A: Data & API Foundation (label config, summary endpoint, attention service)
- Phase 3B: Frontend Dashboard & Navigation (bottom nav, overview page, interactive actions)
- Phase 3C: Validation, Accessibility, and Launch (testing, polish, QA checklist)

**Start Date**: TBD (kick off after Phase 2 sign-off)  
**Status**: Draft  
**Goal**: Deliver a reusable, mobile-first Owner Dashboard that surfaces "Needs Attention" items, branch/event performance, and quick navigation without duplicating existing project/task logic. The implementation must be incremental, with automated tests added in every stage to protect Phase 1 & 2 features.

## Phase Overview

| Phase | Focus | Outcome |
|-------|-------|---------|
| **Phase 3A** | Data & API groundwork | Reliable summary endpoints + "needs attention" service reused by UI |
| **Phase 3B** | Frontend dashboard + navigation | New Overview screen + bottom navigation without breaking current pages |
| **Phase 3C** | Validation, polish, doc | Automated + manual QA, regression suite, launch checklist |

## Prerequisites & Dependencies

**Before Starting Phase 3**:
- ✅ Phase 1 & 2 tests passing (100% green)
- ✅ Database migrations completed and verified
- ✅ Existing project/task/employee data structure validated
- ✅ localStorage service working correctly
- ✅ Existing API routes documented and stable

**Required Knowledge**:
- Understanding of existing `AppContext` and state management
- Familiarity with current routing structure in `App.jsx`
- Knowledge of localStorage schema (see `services/localStorage.service.js`)
- Understanding of existing task/project/employee models

Each stage below describes:
- **Goal / Scope constraints** (keep code minimal, reuse existing services)
- **Implementation notes** (files, patterns to touch)
- **Tests to add** (unit + integration)
- **Regression checks** (which suites to rerun before proceeding)

LLMs can follow this structure stage-by-stage: implement → add tests → run pytest + npm test → manual smoke → move to next stage only when green.

---

## Phase 3A — Data & API Foundation

### **Stage 3A.1: Project & Label Audit**
- **Goal**: Ensure every project already stores the metadata the dashboard needs (name, color, completion stats). Introduce optional label config (e.g., "Store/Event/Unit") without forcing migrations.
- **Implementation**:
  
  **Backend Changes**:
  - Create `backend/config/dashboard_labels.json`:
    ```json
    {
      "defaults": {
        "project": "Project",
        "projects": "Projects",
        "assignee": "Team Member",
        "assignees": "Team Members",
        "task": "Task",
        "tasks": "Tasks"
      },
      "customizations": {
        "retail": {
          "project": "Store",
          "projects": "Stores",
          "assignee": "Staff Member"
        },
        "events": {
          "project": "Event",
          "projects": "Events",
          "assignee": "Team Member"
        }
      }
    }
    ```
  - Add `backend/services/label_service.py`:
    ```python
    def get_label_config(business_type='default'):
        """Load label config with fallback to defaults"""
        try:
            with open('config/dashboard_labels.json') as f:
                config = json.load(f)
            return config.get('customizations', {}).get(business_type, config['defaults'])
        except Exception:
            return {'project': 'Project', 'assignee': 'Team Member'}
    ```
  
  **Frontend Changes**:
  - Create `src/config/uiLabels.js`:
    ```javascript
    export const DEFAULT_LABELS = {
      project: 'Project',
      projects: 'Projects',
      assignee: 'Team Member',
      assignees: 'Team Members',
      task: 'Task',
      tasks: 'Tasks'
    };
    
    export const getLabels = (customizations = {}) => ({
      ...DEFAULT_LABELS,
      ...customizations
    });
    ```
  - Update `src/context/AppContext.jsx` to add `uiLabels` to context.
  
  **Data Audit Checklist**:
  - [ ] Verify all projects have `name`, `color`, `status` fields
  - [ ] Confirm task completion percentages calculate correctly
  - [ ] Check employee data has required fields (name, phone, avatar)
  - [ ] Validate existing localStorage schema matches expectations

- **Tests**:
  - Frontend unit: `uiLabels.test.js` (ensures overrides fall back to defaults).
  - Backend unit: `test_dashboard_labels_defaults()` (ensures config loader never crashes).
  - Backend unit: `test_label_config_missing_file_fallback()`.
  - Frontend unit: `test_context_exposes_ui_labels()`.
  
- **Regression**: `npm run build`, `pytest test_api.py::TestProjects -v`.

- **Acceptance Criteria**:
  - ✅ Label config loads without errors
  - ✅ Missing config files don't crash application
  - ✅ Custom labels override defaults correctly
  - ✅ Context provides labels to all components

### **Stage 3A.2: Summary Endpoint**
- **Goal**: Add lightweight endpoint to fetch aggregated metrics (today's totals, per-project stats, per-assignee stats) using existing services.
- **Implementation**:
  
  **Backend Changes**:
  - Create `backend/api/dashboard.py`:
    ```python
    from flask import Blueprint, request, jsonify
    from datetime import datetime, date
    from services.task_service import get_all_tasks
    from services.project_service import get_all_projects
    from services.employee_service import get_all_employees
    
    dashboard_bp = Blueprint('dashboard', __name__)
    
    @dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
    def get_dashboard_summary():
        """Get aggregated dashboard metrics"""
        target_date = request.args.get('date', date.today().isoformat())
        
        tasks = get_all_tasks()  # Reuse existing service
        projects = get_all_projects()
        employees = get_all_employees()
        
        # Calculate totals
        totals = calculate_task_totals(tasks, target_date)
        
        # Group by project
        project_stats = group_tasks_by_project(tasks, projects)
        
        # Group by assignee
        assignee_stats = group_tasks_by_assignee(tasks, employees)
        
        return jsonify({
            'date': target_date,
            'totals': totals,
            'projects': project_stats,
            'assignees': assignee_stats,
            'timestamp': datetime.now().isoformat()
        })
    ```
  
  - Add helper functions in same file:
    ```python
    def calculate_task_totals(tasks, target_date):
        """Calculate total task counts"""
        all_tasks = len(tasks)
        done = len([t for t in tasks if t.get('status') == 'done'])
        pending = len([t for t in tasks if t.get('status') == 'pending'])
        overdue = len([t for t in tasks if is_overdue(t, target_date)])
        
        return {
            'all': all_tasks,
            'done': done,
            'pending': pending,
            'overdue': overdue,
            'completion_rate': round((done / all_tasks * 100) if all_tasks > 0 else 0, 1)
        }
    
    def group_tasks_by_project(tasks, projects):
        """Group task stats by project"""
        project_map = {p['id']: p for p in projects}
        stats = {}
        
        for task in tasks:
            project_id = task.get('projectId')
            if project_id not in stats:
                stats[project_id] = {
                    'id': project_id,
                    'name': project_map.get(project_id, {}).get('name', 'Unknown'),
                    'color': project_map.get(project_id, {}).get('color', '#gray'),
                    'total': 0,
                    'done': 0,
                    'pending': 0
                }
            
            stats[project_id]['total'] += 1
            if task.get('status') == 'done':
                stats[project_id]['done'] += 1
            elif task.get('status') == 'pending':
                stats[project_id]['pending'] += 1
        
        return list(stats.values())
    ```
  
  - Register blueprint in `backend/app.py`:
    ```python
    from api.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    ```

  **Frontend Service**:
  - Create `src/services/dashboard.service.js`:
    ```javascript
    export const dashboardService = {
      async getSummary(date = null) {
        const params = date ? `?date=${date}` : '';
        const response = await fetch(`/api/dashboard/summary${params}`);
        if (!response.ok) throw new Error('Failed to fetch summary');
        return response.json();
      }
    };
    ```

- **Tests**:
  - Backend: `test_dashboard_summary_defaults()` (no date → today).
  - Backend: `test_dashboard_summary_filters_by_date()`.
  - Backend: `test_dashboard_summary_handles_no_projects()`.
  - Backend: `test_dashboard_summary_handles_no_tasks()`.
  - Backend: `test_dashboard_summary_completion_rate_calculation()`.
  - Backend: `test_dashboard_summary_performance_with_1000_tasks()`.
  - Frontend: `test_dashboard_service_fetch_summary()`.
  
- **Regression**: `pytest test_api.py::TestTasks -k project -v`.

- **Acceptance Criteria**:
  - ✅ Endpoint returns data in < 200ms with 100 tasks
  - ✅ Date filtering works correctly
  - ✅ Empty data returns valid structure (zeros)
  - ✅ Completion rates calculated accurately
  - ✅ Response includes all required fields

### **Stage 3A.3: Needs-Attention Service**
- **Goal**: Centralize logic that flags overdue / no-response tasks so UI, reminders, and future reports reuse same rules.
- **Implementation**:
  
  **Backend Service**:
  - Create `backend/services/attention_service.py`:
    ```python
    from datetime import datetime, timedelta
    from functools import lru_cache
    import time
    
    class AttentionService:
        def __init__(self):
            self._cache = {}
            self._cache_timeout = 60  # seconds
        
        def get_attention_items(self, reference_time=None):
            """Get tasks that need attention"""
            if reference_time is None:
                reference_time = datetime.now()
            
            # Check cache
            cache_key = reference_time.replace(second=0, microsecond=0)
            if cache_key in self._cache:
                cached_time, cached_data = self._cache[cache_key]
                if time.time() - cached_time < self._cache_timeout:
                    return cached_data
            
            # Calculate attention items
            tasks = get_all_tasks()  # Reuse existing service
            attention_items = []
            
            for task in tasks:
                reasons = []
                
                # Rule 1: Overdue tasks
                if self._is_overdue(task, reference_time):
                    reasons.append({
                        'type': 'overdue',
                        'severity': 'high',
                        'message': f'Due {self._format_overdue(task, reference_time)}'
                    })
                
                # Rule 2: No response after WhatsApp sent
                if self._has_no_response(task, reference_time):
                    reasons.append({
                        'type': 'no_response',
                        'severity': 'medium',
                        'message': 'No response for 2+ hours'
                    })
                
                # Rule 3: Pending too long
                if self._pending_too_long(task, reference_time):
                    reasons.append({
                        'type': 'pending_long',
                        'severity': 'low',
                        'message': 'Pending for 6+ hours'
                    })
                
                if reasons:
                    attention_items.append({
                        'task': task,
                        'reasons': reasons,
                        'priority': self._calculate_priority(reasons)
                    })
            
            # Sort by priority
            attention_items.sort(key=lambda x: x['priority'], reverse=True)
            
            # Cache result
            self._cache[cache_key] = (time.time(), attention_items)
            return attention_items
        
        def _is_overdue(self, task, reference_time):
            """Check if task is overdue"""
            if task.get('status') == 'done':
                return False
            due_date = task.get('dueDate')
            if not due_date:
                return False
            return datetime.fromisoformat(due_date) < reference_time
        
        def _has_no_response(self, task, reference_time):
            """Check if WhatsApp sent but no response"""
            if not task.get('whatsappSent'):
                return False
            if task.get('lastActivity'):
                return False
            sent_time = task.get('whatsappSentAt')
            if not sent_time:
                return False
            time_since = (reference_time - datetime.fromisoformat(sent_time)).total_seconds()
            return time_since > 7200  # 2 hours
        
        def _pending_too_long(self, task, reference_time):
            """Check if pending for too long"""
            if task.get('status') != 'pending':
                return False
            created = task.get('createdAt')
            if not created:
                return False
            time_since = (reference_time - datetime.fromisoformat(created)).total_seconds()
            return time_since > 21600  # 6 hours
        
        def _calculate_priority(self, reasons):
            """Calculate priority score from reasons"""
            severity_scores = {'high': 3, 'medium': 2, 'low': 1}
            return sum(severity_scores.get(r['severity'], 0) for r in reasons)
    
    # Singleton instance
    attention_service = AttentionService()
    ```
  
  - Add API endpoint in `backend/api/dashboard.py`:
    ```python
    @dashboard_bp.route('/api/dashboard/attention', methods=['GET'])
    def get_attention_items():
        """Get tasks needing attention"""
        from services.attention_service import attention_service
        items = attention_service.get_attention_items()
        return jsonify({
            'items': items,
            'count': len(items),
            'timestamp': datetime.now().isoformat()
        })
    ```

  **Frontend Integration**:
  - Add to `src/services/dashboard.service.js`:
    ```javascript
    export const dashboardService = {
      // ... existing methods
      
      async getAttentionItems() {
        const response = await fetch('/api/dashboard/attention');
        if (!response.ok) throw new Error('Failed to fetch attention items');
        return response.json();
      }
    };
    ```

- **Tests**:
  - Backend: `test_attention_flags_overdue_tasks()`.
  - Backend: `test_attention_flags_no_response_tasks()`.
  - Backend: `test_attention_flags_pending_long_tasks()`.
  - Backend: `test_attention_respects_cache_window()`.
  - Backend: `test_attention_priority_calculation()`.
  - Backend: `test_attention_ignores_completed_tasks()`.
  - Backend: `test_attention_cache_invalidation()`.
  - Backend: `test_attention_endpoint_returns_json()`.
  
- **Regression**: Run full `pytest test_api.py::TestWhatsAppIntegration -v` to ensure reminder logic unaffected.

- **Acceptance Criteria**:
  - ✅ All attention rules fire correctly
  - ✅ Cache reduces database queries
  - ✅ Priority sorting works as expected
  - ✅ Completed tasks never flagged
  - ✅ Performance acceptable with 500+ tasks

> ✅ **Phase 3A exit criteria**: All new backend tests pass, lint clean, existing suites untouched. Frontend still uses old navigation until Phase 3B.

---

## Phase 3B — Owner Dashboard UI & Navigation

### **Stage 3B.1: Navigation Shell**
- **Goal**: Introduce bottom navigation (mobile-first) with tabs: `Overview`, `Projects`, `Team`, `Settings` without breaking existing routes.
- **Implementation**:
  
  **Navigation Component**:
  - Create `src/layout/BottomNav.jsx`:
    ```jsx
    import { Link, useLocation } from 'react-router-dom';
    
    const BottomNav = () => {
      const location = useLocation();
      
      const tabs = [
        { id: 'overview', path: '/', label: 'Overview', icon: HomeIcon },
        { id: 'projects', path: '/projects', label: 'Projects', icon: FolderIcon },
        { id: 'team', path: '/employees', label: 'Team', icon: UsersIcon },
        { id: 'settings', path: '/settings', label: 'Settings', icon: CogIcon }
      ];
      
      return (
        <nav 
          className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-inset-bottom md:hidden"
          role="navigation"
          aria-label="Main navigation"
        >
          <div className="flex justify-around items-center h-16">
            {tabs.map(tab => {
              const isActive = location.pathname === tab.path;
              return (
                <Link
                  key={tab.id}
                  to={tab.path}
                  className={`flex flex-col items-center justify-center flex-1 h-full px-2 transition-colors ${
                    isActive 
                      ? 'text-blue-600' 
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={tab.label}
                >
                  <tab.icon className="w-6 h-6 mb-1" aria-hidden="true" />
                  <span className="text-xs font-medium">{tab.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      );
    };
    
    export default BottomNav;
    ```
  
  **Router Updates**:
  - Update `src/App.jsx`:
    ```jsx
    import BottomNav from './layout/BottomNav';
    import Overview from './pages/Overview';
    
    function App() {
      return (
        <AppProvider>
          <div className="min-h-screen bg-gray-50 pb-16 md:pb-0">
            <Navbar />
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/projects" element={<Dashboard />} />
              <Route path="/projects/:projectId" element={<ProjectDetail />} />
              <Route path="/employees" element={<Employees />} />
              <Route path="/settings" element={<Settings />} />
## Implementation Guardrails (For LLM + Humans)

1. **Reuse existing services**: do not duplicate task/project lookups—import utilities from `services/` or `context/`.
2. **Minimal diffs**: prefer small focused PRs per stage; no large refactors.
3. **Testing discipline**: every stage must add or update tests before moving on; always re-run suites mentioned above.
4. **Mobile-first UI**: prioritize iPad/phone breakpoints, ensure touch-friendly buttons, avoid desktop-only patterns.
5. **Configuration over customization**: label overrides via config files, not DB migrations, so feature remains optional.
6. **LLM-friendly tasks**: keep stage descriptions atomic (one file cluster per stage) so automated agents can follow without context switching.
7. **Error handling**: every API call must handle failures gracefully with user-friendly messages.
8. **Performance**: dashboard must load in <2s on 3G, queries must complete in <200ms.
9. **Accessibility**: WCAG 2.1 AA compliance, keyboard navigation, screen reader support.
10. **Backward compatibility**: never break existing localStorage data or API contracts.

## Risk Areas & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation with large datasets | High | Add pagination, implement caching, lazy load data |
| Breaking existing navigation flow | High | Keep old routes intact, add feature flag for new nav |
| localStorage schema conflicts | Medium | Version localStorage data, add migration helpers |
| Cache invalidation issues | Medium | Use time-based expiry, add manual refresh option |
| Mobile Safari touch issues | Medium | Test on real devices, add touch-action CSS |
| Attention logic false positives | Low | Make rules configurable, add dismiss/snooze |

## Rollout Plan

1. **Stage-by-stage deployment**: Each stage deployed to staging first
2. **Feature flag**: `ENABLE_DASHBOARD_V3` in config to toggle new UI
3. **A/B testing**: 10% users → 50% → 100% over 2 weeks
4. **Monitoring**: Track dashboard load times, API response times, error rates
5. **Rollback plan**: Feature flag off reverts to old navigation
6. **User feedback**: In-app survey after 1 week of usage

## Success Metrics

**Performance**:
- Dashboard loads in < 2 seconds (p95)
- Summary API responds in < 200ms (p95)
- Attention API responds in < 150ms (p95)
- Zero memory leaks in 24h browser session

**User Experience**:
- 80% of users find "Needs Attention" helpful (survey)
- 50% reduction in missed overdue tasks
- 30% faster navigation to task details
- Zero accessibility violations (axe audit)

**Technical Quality**:
- 100% test coverage on new code
- Zero regressions in Phase 1 & 2 tests
- < 5% increase in bundle size
- Lighthouse score > 90 (all categories)

Following this plan ensures we deliver a production-grade Owner Dashboard that small business owners can adopt immediately, while keeping the codebase clean, test-covered, and easy for LLM copilots to extend.
    ```css
    /* Safe area for iOS notch/home indicator */
    .safe-area-inset-bottom {
      padding-bottom: env(safe-area-inset-bottom);
    }
    
    /* Hide bottom nav on desktop */
    @media (min-width: 768px) {
      .bottom-nav-spacer {
        display: none;
      }
    }
    ```

- **Tests**:
  - Frontend: `BottomNav.test.jsx` (active tab highlights, ARIA labels).
  - Frontend: `test_navigation_keyboard_accessible()`.
  - Frontend: `test_navigation_active_state_updates()`.
  - E2E: Cypress test for tab switching and route changes.
  
- **Regression**: `npm run build`, manual check on iPad width, test existing routes still work.

- **Acceptance Criteria**:
  - ✅ Bottom nav visible only on mobile (<768px)
  - ✅ Active tab highlighted correctly
  - ✅ Keyboard navigation works (Tab, Enter)
  - ✅ Touch targets >= 44px
  - ✅ Screen reader announces current page
  - ✅ No layout shift when switching tabs

### **Stage 3B.2: Overview Screen Skeleton**
- **Goal**: New page `src/pages/Overview.jsx` that consumes summary API + attention service, but initially displays loading skeletons.
- **Implementation**:
  - Hook into `useApp` for auth + global state.
  - Fetch `/api/dashboard/summary` + `/api/dashboard/attention` via `dashboard.service.js`.
  - Render cards (Totals, Needs Attention, By Project, By Assignee) with placeholders.
- **Tests**:
  - RTL test verifying loading states + error toasts.
  - Snapshot test (stable card structure).
- **Regression**: Run `npm test -- Overview.test.jsx`.

### **Stage 3B.3: Interactive Actions**
- **Goal**: Wire up tap targets on Needs Attention cards: Call, Send Reminder, View Task. Buttons must reuse existing codepaths (e.g., WhatsApp send service, TaskModal).
- **Implementation**:
  - `Call` → `tel:` link from employee phone.
  - `Send Reminder` → reuse `sendTaskToWhatsApp(taskId)` with `reminder=true` flag.
  - `View Task` → open existing `TaskModal` with preloaded task.
  - Add haptic/touch feedback classes.
- **Tests**:
  - RTL test to ensure callbacks fire + disabled state while sending reminder.
  - Manual QA: iPad + mobile Safari tap tests.
- **Regression**: `npm run lint`, `npm run build`.

> ✅ **Phase 3B exit criteria**: Overview tab is fully functional, navigation stable, no regressions in existing Project detail pages.

---

## Phase 3C — Validation, Accessibility, and Launch

### **Stage 3C.1: Integration & Contract Tests**
- **Goal**: Ensure backend/ frontend contracts stay in sync and Phase 1/2 flows still work.
- **Implementation**:
  - Backend integration tests: `test_dashboard_summary_contract()` (JSON schema), `test_attention_endpoint_contract()`.
  - Frontend integration test (Cypress/Playwright) for “Assign task → mark done → dashboard updates”.
- **Regression**: Full `pytest test_api.py`, full `npm test`.

### **Stage 3C.2: Responsive & Accessibility Polish**
- **Goal**: Guarantee dashboard works on iPad + phone, respects touch targets, screen readers.
- **Implementation**:
  - Add responsive snapshots (Storybook or Chromatic) for 375px, 768px, 1024px.
  - Ensure buttons >= 44px, add ARIA labels (“Needs attention item”).
  - Optimize skeleton/loader for low-end devices (no heavy animations).
- **Tests**:
  - Automated Lighthouse run (performance + accessibility).
  - Jest axe test on Overview page.

### **Stage 3C.3: Manual QA & Release Checklist**
- **Goal**: Run through owner-focused scripts before tagging release.
- **Checklist**:
  - Create project, assign tasks, send WhatsApp, reply, see dashboard update.
  - Trigger overdue + no-response to confirm Needs Attention rules.
  - Add new project via Projects tab → ensure Overview reflects it.
  - Verify label overrides (if any) appear in UI.
- **Regression**: Re-run entire `pytest` + `npm run build`. Tag release only if green.

> ✅ **Phase 3C exit criteria**: All automated tests green, manual QA checklist signed, documentation updated (README dashboard section + release notes).

---

## Implementation Guardrails (For LLM + Humans)

1. **Reuse existing services**: do not duplicate task/project lookups—import utilities from `services/` or `context/`.
2. **Minimal diffs**: prefer small focused PRs per stage; no large refactors.
3. **Testing discipline**: every stage must add or update tests before moving on; always re-run suites mentioned above.
4. **Mobile-first UI**: prioritize iPad/phone breakpoints, ensure touch-friendly buttons, avoid desktop-only patterns.
5. **Configuration over customization**: label overrides via config files, not DB migrations, so feature remains optional.
6. **LLM-friendly tasks**: keep stage descriptions atomic (one file cluster per stage) so automated agents can follow without context switching.

Following this plan ensures we deliver a production-grade Owner Dashboard that small business owners can adopt immediately, while keeping the codebase clean, test-covered, and easy for LLM copilots to extend.
