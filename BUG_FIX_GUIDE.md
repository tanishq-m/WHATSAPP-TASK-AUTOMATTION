# Bug Fix Guide - WhatsApp Task Manager

> **Purpose:** Direct instructions for fixing bugs. Each issue has the exact file, line, current code, and fixed code.

---

## CRITICAL BUGS (Fix First)

### BUG-1: Task Status Default is Wrong

**File:** `backend/app.py`  
**Line:** ~447 (in `create_task` function)

**Current Code:**
```python
data.setdefault('status', 'todo')
```

**Fixed Code:**
```python
data.setdefault('status', 'unassigned')
```

**Why:** Valid statuses are `unassigned`, `in_progress`, `pending_verification`, `completed`. The value `'todo'` is invalid and tasks won't appear in Kanban.

---

### BUG-2: WhatsApp Update Uses Wrong Field Name

**File:** `backend/app.py`  
**Line:** ~632 (in `send_task_to_whatsapp` function)

**Current Code:**
```python
database.update_task(task_id, {'whatsapp_sent': 1})
```

**Fixed Code:**
```python
database.update_task(task_id, {'whatsappSent': 1})
```

**Why:** The `database.update_task()` field_mapping expects camelCase keys. Using snake_case causes the update to fail silently.

---

### BUG-3: Project ID Collision Risk

**File:** `backend/app.py`  
**Line:** ~240 (in `create_project` function)

**Current Code:**
```python
import random
project_id = f"proj_{random.randint(100, 999)}"
```

**Fixed Code:**
```python
# Use sequence table like tasks (add to database.py first, then use here)
# Quick fix: Use timestamp-based ID
import time
project_id = f"proj_{int(time.time() * 1000) % 1000000}"
```

**Better Fix:** Add a project sequence to `database.py` similar to task sequence:
```python
# In database.py init_database(), add:
cursor.execute("INSERT OR IGNORE INTO sequences (name, current_value) VALUES ('project', 0)")

# Then in create_project:
cursor.execute("UPDATE sequences SET current_value = current_value + 1 WHERE name = 'project'")
cursor.execute("SELECT current_value FROM sequences WHERE name = 'project'")
next_id = cursor.fetchone()['current_value']
project_id = f"proj_{str(next_id).zfill(3)}"
```

**Why:** Random 3-digit IDs (100-999) have high collision probability after ~30 projects.

---

## MEDIUM BUGS (Fix Second)

### BUG-4: API Keys Hardcoded (Security)

**Files:** 
- `backend/config.py` (lines 8-10)
- `backend/kapso_service.py` (lines 12-14)

**Current Code (both files):**
```python
KAPSO_API_KEY = "7819cb622458c2ca2e3300008d391d85d39b962ee2b9996e8a562fa9408a5f81"
PHONE_NUMBER_ID = "597907523413541"
```

**Fixed Code in `config.py`:**
```python
import os

KAPSO_API_KEY = os.environ.get('KAPSO_API_KEY', '')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID', '')
KAPSO_API_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
```

**Fixed Code in `kapso_service.py`:**
```python
from config import KAPSO_API_KEY, PHONE_NUMBER_ID, KAPSO_API_BASE
# Remove the hardcoded lines 12-14
```

**Why:** Secrets should never be in source code. Use environment variables.

---

### BUG-5: Employee Endpoint Missing not_found Check

**File:** `backend/app.py`  
**Line:** ~130-143 (in `get_employee` function)

**Current Code:**
```python
if result['success']:
    return jsonify(result), 200
else:
    return jsonify(result), 404
```

**Fixed Code:**
```python
if result['success']:
    return jsonify(result), 200
elif result.get('not_found'):
    return jsonify(result), 404
else:
    return jsonify(result), 500
```

**Why:** Consistent error handling pattern with other endpoints (delete_project, delete_task).

---

## MINOR ISSUES (Fix Last)

### ISSUE-6: Duplicate ID Handling Pattern

**Files:** Multiple components use `task.id || task.taskId`

**Locations:**
- `src/components/tasks/TaskCard.jsx` (lines 28, 36, 77)
- `src/components/tasks/TaskModal.jsx` (lines 60, 79)
- `src/components/tasks/SortableTaskCard.jsx` (line 8)

**This is currently a workaround.** The root fix is ensuring `toCamelCase()` in `api.service.js` always sets both `id` and `taskId`. This is already done (line 27-29 of api.service.js), so no change needed.

---

### ISSUE-7: formatDate Returns Empty String

**File:** `src/utils/helpers.js`  
**Line:** ~5

**Current Code:**
```javascript
export const formatDate = (dateString) => {
  if (!dateString) return ''
```

**Optional Fix (if you want "No date" displayed):**
```javascript
export const formatDate = (dateString) => {
  if (!dateString) return 'No date'
```

**Note:** This is a design choice. Current behavior (empty string) is valid.

---

### ISSUE-8: LocalStorage Fallback Can Cause Data Sync Issues

**File:** `src/context/AppContext.jsx`  
**Lines:** ~40-90 (in `loadData` function) and throughout CRUD operations

**Problem:** When API fails, the app falls back to localStorage. When API comes back online, there's no reconciliation - localStorage data may be stale or conflict with backend.

**Current Pattern (repeated for projects, tasks, employees):**
```javascript
try {
  const data = await apiService.getProjects()
  setProjects(data)
  storageService.setProjects(data)  // Sync to localStorage
} catch (error) {
  // Fallback to localStorage
  setProjects(storageService.getProjects())
  showToast("Using offline data", "warning")
}
```

**Recommended Fix Options:**

**Option A - Remove localStorage fallback entirely (simplest):**
```javascript
try {
  const data = await apiService.getProjects()
  setProjects(data)
} catch (error) {
  setProjects([])
  showToast("Cannot connect to server", "error")
}
```

**Option B - Add explicit offline mode with no writes:**
```javascript
const [isOffline, setIsOffline] = useState(false)

// In loadData:
try {
  const data = await apiService.getProjects()
  setProjects(data)
  setIsOffline(false)
} catch (error) {
  setProjects(storageService.getProjects())
  setIsOffline(true)
  showToast("Offline mode - changes won't be saved", "warning")
}

// In addProject, updateProject, etc:
if (isOffline) {
  showToast("Cannot save while offline", "error")
  return
}
```

**Why:** Current pattern allows users to make changes in "offline mode" that write to localStorage but never sync to backend when connection returns. This causes data loss/confusion.

**Impact:** Medium - causes confusion when backend is temporarily unavailable.

---

## VALIDATION AFTER FIXES

Run these commands to verify:

```bash
# Backend tests
cd backend && pytest -v

# Frontend tests  
cd .. && npm test

# Manual test: Create task via API
curl -X POST http://localhost:5001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "projectId": "proj_001", "priority": "medium"}'

# Verify response has status: "unassigned" (not "todo")
```

---

## ISSUE-8: LocalStorage Fallback Causes Data Loss ✅ FIXED

**File:** `src/context/AppContext.jsx`  
**Lines:** Multiple locations (loadData, addProject, updateProject, deleteProject, addTask, updateTask, deleteTask)

**Problem:** 
When backend API fails, all CRUD operations fall back to localStorage writes. This causes:
- Data written to localStorage never syncs back when backend comes online
- Users see stale/random data when switching between online/offline
- No clear indication that changes won't be persisted

**Solution:**
1. Added explicit `isOffline` state to track backend connectivity
2. Block all write operations when offline (prevent data loss)
3. Updated loadData to set offline state and show clear warning
4. LocalStorage is now read-only cache (updated only on successful API calls)

**Changes Made:**

1. **Added offline state tracking:**
```jsx
const [isOffline, setIsOffline] = useState(false)
```

2. **Updated loadData to set offline state:**
```jsx
if (apiSuccess) {
  console.log("✅ All data synced from backend to localStorage")
  setIsOffline(false)
} else {
  setIsOffline(true)
  if (!toast.show) {
    showToast("⚠️ Offline Mode - Cannot save changes until reconnected", "warning")
  }
}
```

3. **Added offline checks to all write operations:**
```jsx
const addProject = async (project) => {
  if (isOffline) {
    showToast('⚠️ Cannot create project while offline', 'error')
    return null
  }
  // ... rest of implementation
}
```

4. **Updated error handlers to set offline state:**
```jsx
} catch (error) {
  console.error("❌ Failed to create project via API:", error)
  setIsOffline(true)
  showToast('⚠️ Connection lost - Cannot save changes', 'error')
  return null
}
```

**Behavior:**
- ✅ Online → Backend API + localStorage cache updated
- ✅ Offline → Read-only mode, clear error messages, no writes
- ✅ Offline → Online → Auto-sync on next loadData() call
- ✅ All 123 frontend tests passing

---

## FIX ORDER SUMMARY

1. **BUG-1:** ✅ Change `'todo'` → `'unassigned'` in app.py create_task
2. **BUG-2:** ✅ Change `'whatsapp_sent'` → `'whatsappSent'` in app.py send_task_to_whatsapp  
3. **BUG-3:** ✅ Replace random project ID with sequence-based ID
4. **BUG-4:** ⏭️ SKIPPED (user requested revert - API keys remain hardcoded)
5. **BUG-5:** ✅ Add not_found check to employee endpoint
6. **ISSUE-6:** ✅ No change needed (already fixed)
7. **ISSUE-7:** ⏭️ Optional design choice
8. **ISSUE-8:** ✅ Added explicit offline mode with read-only localStorage

---

## VALID STATUS VALUES REFERENCE

```python
# Backend (database.py, app.py)
'unassigned'           # Default for new tasks
'in_progress'          # Task being worked on  
'pending_verification' # Employee marked complete, awaiting admin review
'completed'            # Admin verified complete
```

```javascript
// Frontend (constants.js)
STATUS.UNASSIGNED = 'unassigned'
STATUS.IN_PROGRESS = 'in_progress'
STATUS.PENDING_VERIFICATION = 'pending_verification'
STATUS.COMPLETED = 'completed'
```

---

## FIELD NAMING REFERENCE

| Backend (snake_case) | Frontend (camelCase) | API Accepts Both |
|---------------------|---------------------|------------------|
| `task_id` | `taskId` | ✓ |
| `project_id` | `projectId` | ✓ |
| `employee_id` | `employeeId` / `assignedTo` | ✓ |
| `due_date` | `dueDate` | ✓ |
| `whatsapp_sent` | `whatsappSent` | ✓ |
| `whatsapp_response` | `whatsappResponse` | ✓ |
| `assigned_employees` | `assignedEmployees` | ✓ |

**Rule:** Backend stores snake_case. Frontend uses camelCase. `toCamelCase()` in api.service.js handles transformation.
