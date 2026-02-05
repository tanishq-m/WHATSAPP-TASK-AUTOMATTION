# Dashboard Overview Implementation Guide
## "Bird's Eye View" Owner Dashboard - Multi-Phase Implementation

**Purpose:** This guide implements a new Overview dashboard page with "Needs Attention" alerts, project summaries, and quick actions. Designed for LLM code generation with comprehensive testing after each phase.

**Current Status:** Phase 1 MVP complete (Projects + Kanban)  
**New Feature:** Owner Dashboard with bird's eye view of all projects  
**Approach:** Multi-phase implementation with testing between phases

---

## ⚠️ **CRITICAL: ALWAYS PREPEND `TECHNICAL_DESIGN_SPEC.md` TO ALL PROMPTS**

Before using any LLM prompt in this guide:
1. Copy entire `TECHNICAL_DESIGN_SPEC.md`
2. Copy phase/stage-specific prompt
3. Combine: Design Spec + Prompt
4. Send to LLM

---

## 🎯 **FEATURE OVERVIEW**

### **Business Problem**
- Owner has multiple projects/branches
- Needs to see which projects need attention
- Currently must click through each project
- Wants quick actions (call, remind, view)
- Needs mobile-first design for on-the-go monitoring

### **Solution: Overview Dashboard**
- Single-page view of all projects
- "Needs Attention" alerts with priority
- Quick stats per project
- One-tap actions (call, remind, view)
- Mobile-optimized with bottom navigation

### **User Flow**
```
Owner opens app
  ↓
Lands on Overview page (new home)
  ↓
Sees all projects with stats
  ↓
Sees "Needs Attention" section at top
  ↓
Taps action: Call/Remind/View
  ↓
Or taps project to see Kanban board (existing)
```

---

## 📐 **ARCHITECTURE DECISIONS**

### **Reusable System Design**
- Not branch-specific (works for any business type)
- Uses "projects" as core unit
- Configurable labels via `dashboard_labels.json`
- Works for: retail chains, events, factories, construction, etc.

### **Two-Page Structure**
| Page | Route | Purpose | Status |
|------|-------|---------|--------|
| Overview | `/` (home) | Bird's eye view, needs attention | **NEW** |
| Projects | `/projects` | Project list + Kanban boards | **EXISTS** |

### **Navigation Structure**
- Desktop: Top navbar (keep existing)
- Mobile: Bottom navigation (add new)
  - Overview (home icon)
  - Projects (folder icon)
  - Team (users icon)
  - Settings (gear icon)

---

## 🧪 **TESTING STRATEGY**

### **Testing Approach**
1. **Unit Tests:** Test each function independently
2. **Integration Tests:** Test API + frontend together
3. **Edge Case Tests:** Test error scenarios
4. **Regression Tests:** Ensure existing features still work
5. **Manual Tests:** UI/UX testing in browser

### **Test Framework**
- **Backend:** pytest (Python)
- **Frontend:** React Testing Library (optional for MVP)
- **Manual:** curl + browser testing
- **Test File:** `backend/tests/test_dashboard.py` (new)

### **Testing Between Phases**
After each phase:
1. Run existing tests → Ensure nothing broke
2. Run new tests → Verify new feature works
3. Manual testing → Check UI/UX
4. Fix any issues before next phase

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase Overview**

| Phase | What Gets Built | Testing | Time |
|-------|----------------|---------|------|
| **Phase 1** | Backend API for dashboard data | API tests | 2 hours |
| **Phase 2** | "Needs Attention" logic | Logic tests | 2 hours |
| **Phase 3** | Overview page UI | UI tests | 2 hours |
| **Phase 4** | Bottom navigation | Navigation tests | 1 hour |
| **Phase 5** | Quick actions | Action tests | 1.5 hours |
| **Phase 6** | Polish & edge cases | Comprehensive tests | 1 hour |

**Total Time:** ~10 hours (1-2 days)

---

## 🚀 **PHASE 1: Backend API for Dashboard Data (2 hours)**

### **Goal:** Create API endpoints that aggregate project/task data for overview

### **What Gets Built:**
1. `/api/dashboard/summary` - Overall stats
2. `/api/dashboard/projects-overview` - Project summaries with stats
3. `backend/services/dashboard_service.py` - Business logic
4. Test file: `backend/tests/test_dashboard_api.py`

---

### **STAGE 1.1: Dashboard Service Layer (45 minutes)**

#### **Manual Steps:**
1. Create `backend/services/` folder
2. Create `backend/tests/` folder
3. Activate venv: `source venv/bin/activate`

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Create dashboard_service.py to aggregate project and task data for owner overview.

CONTEXT:
- We have existing database.py with: get_projects(), get_tasks(), get_employees()
- We need to aggregate data from these functions for dashboard overview
- Owner needs to see: total stats, per-project stats, attention items

REQUIREMENTS:
1. Create backend/services/dashboard_service.py with:

   - Function: get_dashboard_summary()
     """
     Get overall dashboard statistics.
     
     Returns:
         dict: {
             "total_projects": int,
             "total_tasks": int,
             "tasks_by_status": {
                 "ready_to_start": int,
                 "in_progress": int,
                 "pending_verification": int,
                 "completed": int
             },
             "total_employees": int,
             "completion_rate": float  # Percentage of completed tasks
         }
     """
     * Call get_projects() from database.py
     * Call get_tasks() from database.py
     * Count projects
     * Count tasks by each status
     * Calculate completion rate = (completed / total) * 100
     * Return aggregated data

   - Function: get_projects_overview()
     """
     Get per-project statistics for dashboard cards.
     
     Returns:
         list: [{
             "project_id": str,
             "project_name": str,
             "project_color": str,
             "total_tasks": int,
             "completed_tasks": int,
             "in_progress_tasks": int,
             "pending_tasks": int,
             "overdue_tasks": int,
             "completion_rate": float,
             "start_date": str,
             "end_date": str,
             "assigned_employees": list[int],
             "last_activity": str  # ISO timestamp of last task update
         }]
     """
     * For each project:
       - Get all tasks for that project
       - Count tasks by status
       - Count overdue tasks (due_date < today AND status != completed)
       - Calculate completion rate
       - Get last activity timestamp
     * Sort by last_activity (most recent first)
     * Return list of project summaries

   - Function: calculate_completion_rate(completed, total)
     """Helper to calculate percentage."""
     * Return 0 if total is 0
     * Return (completed / total) * 100
     * Round to 1 decimal place

   - Function: is_task_overdue(task)
     """Check if task is overdue."""
     * Import datetime
     * If task.status == "completed", return False
     * Parse task.due_date
     * Compare with today's date
     * Return True if due_date < today, else False

2. Add imports:
   - from database import get_projects, get_tasks, get_employees, get_project_by_id
   - from datetime import datetime, date

3. Add heavy comments explaining each function
4. Add error handling with try/except
5. Add print statements for debugging
6. Follow Python naming conventions (snake_case)

EXAMPLE OUTPUT:
get_dashboard_summary() returns:
{
  "total_projects": 3,
  "total_tasks": 15,
  "tasks_by_status": {
    "ready_to_start": 3,
    "in_progress": 5,
    "pending_verification": 2,
    "completed": 5
  },
  "total_employees": 3,
  "completion_rate": 33.3
}

get_projects_overview() returns:
[
  {
    "project_id": "proj_001",
    "project_name": "Website Redesign",
    "project_color": "#3B82F6",
    "total_tasks": 10,
    "completed_tasks": 4,
    "in_progress_tasks": 3,
    "pending_tasks": 2,
    "overdue_tasks": 1,
    "completion_rate": 40.0,
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "assigned_employees": [1, 2],
    "last_activity": "2025-01-23T15:30:00Z"
  },
  ...
]

Keep functions pure (no side effects). Add docstrings. Handle edge cases.
```

#### **Testing Stage 1.1:**

After LLM generates code, create test file manually:

**Create `backend/tests/test_dashboard_service.py`:**

```python
"""
Test cases for dashboard_service.py
Run with: pytest backend/tests/test_dashboard_service.py
"""

import sys
sys.path.append('../')

from services import dashboard_service
from database import init_db, create_task, create_project
from datetime import datetime, timedelta

def test_get_dashboard_summary():
    """Test dashboard summary returns correct aggregated data."""
    init_db()  # Initialize test database
    summary = dashboard_service.get_dashboard_summary()
    
    # Verify structure
    assert "total_projects" in summary
    assert "total_tasks" in summary
    assert "tasks_by_status" in summary
    assert "completion_rate" in summary
    
    # Verify types
    assert isinstance(summary["total_projects"], int)
    assert isinstance(summary["completion_rate"], float)
    
    print("✅ test_get_dashboard_summary passed")

def test_projects_overview():
    """Test projects overview returns per-project stats."""
    projects = dashboard_service.get_projects_overview()
    
    # Verify it's a list
    assert isinstance(projects, list)
    
    # If projects exist, check structure
    if len(projects) > 0:
        project = projects[0]
        assert "project_id" in project
        assert "total_tasks" in project
        assert "completion_rate" in project
    
    print("✅ test_projects_overview passed")

def test_overdue_detection():
    """Test overdue task detection."""
    # Test completed task (should not be overdue)
    completed_task = {
        "status": "completed",
        "due_date": "2025-01-01"  # Past date
    }
    assert dashboard_service.is_task_overdue(completed_task) == False
    
    # Test overdue task
    overdue_task = {
        "status": "in_progress",
        "due_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    assert dashboard_service.is_task_overdue(overdue_task) == True
    
    print("✅ test_overdue_detection passed")

def test_completion_rate_calculation():
    """Test completion rate edge cases."""
    # Normal case
    assert dashboard_service.calculate_completion_rate(5, 10) == 50.0
    
    # Zero total (edge case)
    assert dashboard_service.calculate_completion_rate(0, 0) == 0
    
    # 100% completion
    assert dashboard_service.calculate_completion_rate(10, 10) == 100.0
    
    print("✅ test_completion_rate_calculation passed")

if __name__ == "__main__":
    test_get_dashboard_summary()
    test_projects_overview()
    test_overdue_detection()
    test_completion_rate_calculation()
    print("\n🎉 All Stage 1.1 tests passed!")
```

**Run tests:**
```bash
cd backend
source venv/bin/activate
python tests/test_dashboard_service.py
```

#### **✅ Stage 1.1 Complete When:**
- [ ] `dashboard_service.py` created
- [ ] All functions have docstrings
- [ ] Functions return correct data structure
- [ ] All 4 tests pass
- [ ] No errors in terminal

---

### **STAGE 1.2: Dashboard API Endpoints (45 minutes)**

#### **Manual Steps:**
1. Restart Flask server after generating code
2. Test endpoints with curl

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Add dashboard API endpoints to Flask backend.

CONTEXT:
- dashboard_service.py already exists with get_dashboard_summary() and get_projects_overview()
- We need to expose these via REST API for React frontend

REQUIREMENTS:
1. Update backend/app.py:

   Add endpoint: GET /api/dashboard/summary
   """
   Get overall dashboard statistics.
   
   Returns:
       JSON: {
           "success": true,
           "data": {
               "total_projects": 3,
               "total_tasks": 15,
               "tasks_by_status": {...},
               "total_employees": 3,
               "completion_rate": 33.3
           }
       }
   """
   Implementation:
   - Import dashboard_service
   - Call dashboard_service.get_dashboard_summary()
   - Return JSON with success=true and data
   - Handle errors with try/except
   - Return 500 on error with error message

   Add endpoint: GET /api/dashboard/projects-overview
   """
   Get per-project summaries for dashboard cards.
   
   Returns:
       JSON: {
           "success": true,
           "data": [
               {
                   "project_id": "proj_001",
                   "project_name": "Website Redesign",
                   ...
               }
           ]
       }
   """
   Implementation:
   - Import dashboard_service
   - Call dashboard_service.get_projects_overview()
   - Return JSON with success=true and data
   - Handle errors
   - Return 500 on error

2. Add imports at top:
   - from services import dashboard_service

3. Add logging:
   - print(f"📊 Dashboard summary requested")
   - print(f"📊 Projects overview requested")

Follow existing API patterns in app.py. Add error handling. Return consistent JSON format.
```

#### **Testing Stage 1.2:**

**Create `backend/tests/test_dashboard_api.py`:**

```python
"""
Test cases for dashboard API endpoints.
Run with: pytest backend/tests/test_dashboard_api.py
Or manually: python tests/test_dashboard_api.py
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def test_health_endpoint():
    """Test that server is running."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ Server is running")

def test_dashboard_summary():
    """Test /api/dashboard/summary endpoint."""
    response = requests.get(f"{BASE_URL}/dashboard/summary")
    
    # Check status code
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Check response structure
    data = response.json()
    assert "success" in data
    assert data["success"] == True
    assert "data" in data
    
    # Check data structure
    summary = data["data"]
    assert "total_projects" in summary
    assert "total_tasks" in summary
    assert "tasks_by_status" in summary
    assert "completion_rate" in summary
    
    # Check types
    assert isinstance(summary["total_projects"], int)
    assert isinstance(summary["total_tasks"], int)
    assert isinstance(summary["completion_rate"], (int, float))
    
    print(f"✅ Dashboard summary: {summary['total_projects']} projects, {summary['total_tasks']} tasks")

def test_projects_overview():
    """Test /api/dashboard/projects-overview endpoint."""
    response = requests.get(f"{BASE_URL}/dashboard/projects-overview")
    
    # Check status code
    assert response.status_code == 200
    
    # Check response structure
    data = response.json()
    assert data["success"] == True
    assert isinstance(data["data"], list)
    
    # If projects exist, check first project structure
    if len(data["data"]) > 0:
        project = data["data"][0]
        required_fields = [
            "project_id", "project_name", "total_tasks",
            "completed_tasks", "completion_rate"
        ]
        for field in required_fields:
            assert field in project, f"Missing field: {field}"
    
    print(f"✅ Projects overview: {len(data['data'])} projects")

def test_error_handling():
    """Test that non-existent endpoints return proper errors."""
    response = requests.get(f"{BASE_URL}/dashboard/nonexistent")
    assert response.status_code == 404
    print("✅ Error handling works")

if __name__ == "__main__":
    print("🧪 Testing Dashboard API Endpoints...")
    print("=" * 60)
    
    try:
        test_health_endpoint()
        test_dashboard_summary()
        test_projects_overview()
        test_error_handling()
        print("\n🎉 All Phase 1 Stage 1.2 tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Make sure Flask is running on port 5001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
```

**Run tests:**
```bash
# Terminal 1: Start Flask server
cd backend
source venv/bin/activate
python app.py

# Terminal 2: Run tests
cd backend
source venv/bin/activate
pip install pytest requests  # If not installed
python tests/test_dashboard_api.py
```

#### **✅ Stage 1.2 Complete When:**
- [ ] API endpoints added to `app.py`
- [ ] `GET /api/dashboard/summary` returns correct data
- [ ] `GET /api/dashboard/projects-overview` returns correct data
- [ ] All 4 tests pass
- [ ] No errors in Flask terminal

---

### **STAGE 1.3: API Service for Frontend (30 minutes)**

#### **Manual Steps:**
1. Make sure React dev server is running: `npm run dev`
2. Test in browser console after generating code

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Add dashboard API calls to React frontend API service.

CONTEXT:
- src/services/api.service.js exists with API_BASE_URL and other functions
- We need to add new functions for dashboard endpoints
- Backend endpoints: /api/dashboard/summary and /api/dashboard/projects-overview

REQUIREMENTS:
1. Update src/services/api.service.js:

   Add function: async getDashboardSummary()
   """
   Fetch overall dashboard statistics.
   
   Returns:
       Promise<Object>: Dashboard summary data
   """
   Implementation:
   - Fetch from /api/dashboard/summary
   - Check response.ok
   - Parse JSON
   - Return data.data (the actual summary object)
   - Throw error if fails

   Add function: async getProjectsOverview()
   """
   Fetch per-project overview statistics.
   
   Returns:
       Promise<Array>: Array of project summaries
   """
   Implementation:
   - Fetch from /api/dashboard/projects-overview
   - Check response.ok
   - Parse JSON
   - Return data.data (the projects array)
   - Throw error if fails

2. Add error handling:
   - Use try/catch
   - Log errors to console
   - Throw meaningful error messages

3. Follow existing patterns in api.service.js
4. Add JSDoc comments

Keep consistent with existing code style in api.service.js.
```

#### **Testing Stage 1.3:**

**Manual testing in browser console:**

```javascript
// Open browser: http://localhost:3000
// Open console (F12)
// Run these commands:

// Import api service
import { getDashboardSummary, getProjectsOverview } from './services/api.service.js'

// Test dashboard summary
getDashboardSummary().then(data => console.log('Summary:', data))

// Test projects overview
getProjectsOverview().then(data => console.log('Projects:', data))

// Both should return data without errors
```

**Or test via React Context:**

Add temporary button to test:
```jsx
// In src/pages/Dashboard.jsx, add:
<button onClick={async () => {
  const summary = await apiService.getDashboardSummary()
  console.log('Dashboard Summary:', summary)
}}>
  Test Dashboard API
</button>
```

#### **✅ Stage 1.3 Complete When:**
- [ ] API functions added to `api.service.js`
- [ ] Functions follow existing patterns
- [ ] Can call from browser console without errors
- [ ] Returns correct data structure

---

### **PHASE 1 TESTING: Run All Tests**

After completing all Stage 1 stages:

```bash
# Backend tests
cd backend
source venv/bin/activate
python tests/test_dashboard_service.py
python tests/test_dashboard_api.py

# All should pass ✅

# Manual frontend test
# Open browser: http://localhost:3000
# Console: Test API calls
```

### **✅ Phase 1 Complete When:**
- [ ] All backend functions work
- [ ] All API endpoints work
- [ ] All tests pass
- [ ] Frontend can fetch dashboard data
- [ ] No existing features broken

**If all pass, proceed to Phase 2. If any fail, fix before continuing.**

---

## 🚨 **PHASE 2: "Needs Attention" Logic (2 hours)**

### **Goal:** Implement smart alerts for tasks/projects that need owner's attention

### **What Gets Built:**
1. Attention detection rules
2. `/api/dashboard/attention-items` endpoint
3. Priority sorting
4. Test cases for all attention scenarios

---

### **STAGE 2.1: Attention Detection Service (1 hour)**

#### **Manual Steps:**
1. Review existing task statuses and timestamps in database
2. Decide on attention thresholds (can be configured later)

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Create attention detection service for "Needs Attention" dashboard alerts.

CONTEXT:
- Owner needs to know which tasks/projects need immediate attention
- Tasks have: status, due_date, updated_at, assigned employee
- Need to prioritize by urgency: High (red), Medium (yellow), Low (none)

ATTENTION RULES:
1. Overdue tasks (High Priority - Red):
   - due_date < today
   - status != "completed"
   - Priority: HIGH

2. No response for > 4 hours (High Priority - Red):
   - Task sent to employee (whatsapp_sent = True)
   - status = "in_progress" OR "pending_verification"
   - updated_at > 4 hours ago
   - Priority: HIGH

3. No response for > 2 hours (Medium Priority - Yellow):
   - Task sent to employee
   - status = "in_progress"
   - updated_at > 2 hours ago
   - Priority: MEDIUM

4. Pending verification > 6 hours (Medium Priority - Yellow):
   - status = "pending_verification"
   - updated_at > 6 hours ago
   - Priority: MEDIUM

REQUIREMENTS:
1. Create backend/services/attention_service.py:

   - Function: get_attention_items()
     """
     Get all tasks that need owner's attention.
     
     Returns:
         list: [{
             "task_id": str,
             "task_title": str,
             "project_id": str,
             "project_name": str,
             "employee_id": int,
             "employee_name": str,
             "employee_phone": str,
             "priority": str,  # "high" or "medium"
             "reason": str,  # Why it needs attention
             "due_date": str,
             "hours_since_update": float,
             "status": str
         }]
     """
     Implementation:
     - Get all tasks from database
     - For each task, check if it matches any attention rule
     - If yes, add to attention_items list with priority and reason
     - Sort by priority (high first) then by hours_since_update (oldest first)
     - Return list

   - Function: check_if_overdue(task)
     """Check if task is overdue."""
     * Return tuple: (is_overdue: bool, reason: str)
     * If due_date < today AND status != "completed":
       - return (True, "Task overdue")
     * Else: return (False, "")

   - Function: check_no_response(task)
     """Check if task has no response for long time."""
     * Calculate hours_since_update = (now - task.updated_at) in hours
     * If whatsapp_sent AND status in ["in_progress", "pending_verification"]:
       - If hours_since_update > 4: return ("high", "No response for 4+ hours")
       - If hours_since_update > 2: return ("medium", "No response for 2+ hours")
     * Return (None, "")

   - Function: check_pending_verification(task)
     """Check if task stuck in pending verification."""
     * Calculate hours_since_update
     * If status == "pending_verification" AND hours_since_update > 6:
       - return ("medium", "Pending verification for 6+ hours")
     * Return (None, "")

   - Function: calculate_hours_since_update(updated_at)
     """Calculate hours between updated_at and now."""
     * Parse updated_at timestamp
     * Get current time
     * Calculate difference in hours
     * Return float (rounded to 1 decimal)

2. Add imports:
   - from database import get_tasks, get_projects, get_employee_by_id
   - from datetime import datetime, timedelta

3. Add helper function to enrich task with project/employee info:
   - Function: enrich_task_with_details(task)
     * Get project info
     * Get employee info
     * Return task dict with added fields

4. Add heavy comments explaining logic
5. Handle edge cases (missing fields, None values)
6. Add print statements for debugging

EXAMPLE OUTPUT:
get_attention_items() returns:
[
  {
    "task_id": "task_001",
    "task_title": "Complete inventory",
    "project_id": "proj_001",
    "project_name": "Store A",
    "employee_id": 1,
    "employee_name": "Rajesh Kumar",
    "employee_phone": "+919876543210",
    "priority": "high",
    "reason": "Task overdue",
    "due_date": "2025-01-20",
    "hours_since_update": 8.5,
    "status": "in_progress"
  },
  {
    "task_id": "task_002",
    "priority": "medium",
    "reason": "No response for 2+ hours",
    ...
  }
]

Sorted by: priority (high first), then hours_since_update (descending).
```

#### **Testing Stage 2.1:**

**Create `backend/tests/test_attention_service.py`:**

```python
"""
Test cases for attention detection logic.
Run with: python tests/test_attention_service.py
"""

import sys
sys.path.append('../')

from services import attention_service
from datetime import datetime, timedelta

def test_overdue_detection():
    """Test overdue task detection."""
    # Create test task - overdue
    overdue_task = {
        "task_id": "task_001",
        "status": "in_progress",
        "due_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    is_overdue, reason = attention_service.check_if_overdue(overdue_task)
    assert is_overdue == True
    assert "overdue" in reason.lower()
    
    # Create test task - not overdue
    current_task = {
        "task_id": "task_002",
        "status": "in_progress",
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    }
    is_overdue, reason = attention_service.check_if_overdue(current_task)
    assert is_overdue == False
    
    # Completed task (even if due_date passed)
    completed_task = {
        "task_id": "task_003",
        "status": "completed",
        "due_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    }
    is_overdue, reason = attention_service.check_if_overdue(completed_task)
    assert is_overdue == False
    
    print("✅ Overdue detection tests passed")

def test_no_response_detection():
    """Test no response detection."""
    # No response for 5 hours (should be HIGH priority)
    task_5h = {
        "whatsapp_sent": True,
        "status": "in_progress",
        "updated_at": (datetime.now() - timedelta(hours=5)).isoformat()
    }
    priority, reason = attention_service.check_no_response(task_5h)
    assert priority == "high"
    assert "4+" in reason
    
    # No response for 3 hours (should be MEDIUM priority)
    task_3h = {
        "whatsapp_sent": True,
        "status": "in_progress",
        "updated_at": (datetime.now() - timedelta(hours=3)).isoformat()
    }
    priority, reason = attention_service.check_no_response(task_3h)
    assert priority == "medium"
    assert "2+" in reason
    
    # No response for 1 hour (should be None - not enough time)
    task_1h = {
        "whatsapp_sent": True,
        "status": "in_progress",
        "updated_at": (datetime.now() - timedelta(hours=1)).isoformat()
    }
    priority, reason = attention_service.check_no_response(task_1h)
    assert priority is None
    
    print("✅ No response detection tests passed")

def test_pending_verification_detection():
    """Test pending verification detection."""
    # Pending for 7 hours (should need attention)
    task_7h = {
        "status": "pending_verification",
        "updated_at": (datetime.now() - timedelta(hours=7)).isoformat()
    }
    priority, reason = attention_service.check_pending_verification(task_7h)
    assert priority == "medium"
    assert "6+" in reason
    
    # Pending for 2 hours (should be fine)
    task_2h = {
        "status": "pending_verification",
        "updated_at": (datetime.now() - timedelta(hours=2)).isoformat()
    }
    priority, reason = attention_service.check_pending_verification(task_2h)
    assert priority is None
    
    print("✅ Pending verification detection tests passed")

def test_hours_calculation():
    """Test hours since update calculation."""
    # 5 hours ago
    time_5h_ago = (datetime.now() - timedelta(hours=5)).isoformat()
    hours = attention_service.calculate_hours_since_update(time_5h_ago)
    assert 4.9 <= hours <= 5.1  # Allow small margin
    
    # 30 minutes ago
    time_30m_ago = (datetime.now() - timedelta(minutes=30)).isoformat()
    hours = attention_service.calculate_hours_since_update(time_30m_ago)
    assert 0.4 <= hours <= 0.6
    
    print("✅ Hours calculation tests passed")

def test_attention_items_sorting():
    """Test that attention items are sorted correctly."""
    items = attention_service.get_attention_items()
    
    # Should be a list
    assert isinstance(items, list)
    
    # If items exist, check sorting
    if len(items) > 1:
        # Check high priority items come before medium
        high_items = [item for item in items if item["priority"] == "high"]
        medium_items = [item for item in items if item["priority"] == "medium"]
        
        if high_items and medium_items:
            # Find index of last high priority item
            last_high_idx = items.index(high_items[-1])
            # Find index of first medium priority item
            first_medium_idx = items.index(medium_items[0])
            # Last high should come before first medium
            assert last_high_idx < first_medium_idx
    
    print(f"✅ Attention items sorting: {len(items)} items found")

if __name__ == "__main__":
    print("🧪 Testing Attention Detection Logic...")
    print("=" * 60)
    
    try:
        test_overdue_detection()
        test_no_response_detection()
        test_pending_verification_detection()
        test_hours_calculation()
        test_attention_items_sorting()
        print("\n🎉 All Phase 2 Stage 2.1 tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
```

**Run tests:**
```bash
cd backend
source venv/bin/activate
python tests/test_attention_service.py
```

#### **✅ Stage 2.1 Complete When:**
- [ ] `attention_service.py` created
- [ ] All attention detection functions work
- [ ] All 6 tests pass
- [ ] Sorting logic correct

---

### **STAGE 2.2: Attention API Endpoint (30 minutes)**

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Add attention items API endpoint to Flask backend.

CONTEXT:
- attention_service.py exists with get_attention_items()
- Need REST API endpoint for React frontend

REQUIREMENTS:
1. Update backend/app.py:

   Add endpoint: GET /api/dashboard/attention-items
   """
   Get tasks that need owner's attention.
   
   Returns:
       JSON: {
           "success": true,
           "data": [
               {
                   "task_id": "task_001",
                   "priority": "high",
                   "reason": "Task overdue",
                   ...
               }
           ]
       }
   """
   Implementation:
   - Import attention_service
   - Call attention_service.get_attention_items()
   - Return JSON with success=true and data
   - Handle errors with try/except
   - Add logging: print(f"🚨 Attention items requested: {len(items)} items")

2. Follow existing API patterns
3. Return 500 on error with error message

Add to existing app.py following the patterns for other endpoints.
```

#### **Testing Stage 2.2:**

**Create `backend/tests/test_attention_api.py`:**

```python
"""
Test attention items API endpoint.
"""

import requests

BASE_URL = "http://localhost:5001/api"

def test_attention_items_endpoint():
    """Test /api/dashboard/attention-items endpoint."""
    response = requests.get(f"{BASE_URL}/dashboard/attention-items")
    
    # Check status
    assert response.status_code == 200
    
    # Check structure
    data = response.json()
    assert data["success"] == True
    assert isinstance(data["data"], list)
    
    # If items exist, check structure
    if len(data["data"]) > 0:
        item = data["data"][0]
        assert "task_id" in item
        assert "priority" in item
        assert "reason" in item
        assert item["priority"] in ["high", "medium"]
    
    print(f"✅ Attention items: {len(data['data'])} items need attention")

if __name__ == "__main__":
    print("🧪 Testing Attention API...")
    try:
        test_attention_items_endpoint()
        print("\n🎉 Attention API test passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
```

**Run test:**
```bash
cd backend
source venv/bin/activate
python tests/test_attention_api.py
```

#### **✅ Stage 2.2 Complete When:**
- [ ] API endpoint added
- [ ] Returns attention items correctly
- [ ] Test passes
- [ ] Logging shows correct count

---

### **STAGE 2.3: Frontend Attention API (30 minutes)**

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Add attention items API call to React frontend.

REQUIREMENTS:
1. Update src/services/api.service.js:

   Add function: async getAttentionItems()
   """
   Fetch tasks that need owner's attention.
   
   Returns:
       Promise<Array>: Array of attention items sorted by priority
   """
   Implementation:
   - Fetch from /api/dashboard/attention-items
   - Handle errors
   - Return data.data

Follow existing patterns in the file.
```

#### **✅ Stage 2.3 Complete When:**
- [ ] Function added to `api.service.js`
- [ ] Can be called from browser console
- [ ] Returns correct data

---

### **PHASE 2 TESTING: Run All Tests**

```bash
# Run all attention tests
cd backend
source venv/bin/activate
python tests/test_attention_service.py
python tests/test_attention_api.py

# Run Phase 1 tests again (regression)
python tests/test_dashboard_service.py
python tests/test_dashboard_api.py

# All should pass ✅
```

### **✅ Phase 2 Complete When:**
- [ ] Attention detection logic works
- [ ] API endpoint works
- [ ] All tests pass (Phase 1 + Phase 2)
- [ ] No regressions

**If all pass, proceed to Phase 3. If any fail, fix before continuing.**

---

## 🎨 **PHASE 3: Overview Page UI (2 hours)**

### **Goal:** Create the new Overview page with dashboard cards and attention section

### **What Gets Built:**
1. Overview page component
2. Dashboard summary cards
3. Attention items section
4. Project cards with stats
5. Responsive layout

---

### **STAGE 3.1: Overview Page Layout (1 hour)**

#### **Manual Steps:**
1. Create `src/pages/Overview.jsx` file
2. Update routing in `App.jsx` to make Overview the home page
3. Test in browser after generating code

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Create Overview page component for owner dashboard.

CONTEXT:
- This will be the new home page (replaces Dashboard as home)
- Shows bird's eye view of all projects
- Displays "Needs Attention" alerts at top
- Mobile-first design
- Uses existing components where possible (ProjectCard, etc.)

REQUIREMENTS:
1. Create src/pages/Overview.jsx:

Structure:
```jsx
import { useState, useEffect } from 'react'
import { useApp } from '../context/useApp'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, TrendingUp, CheckCircle, Clock } from 'lucide-react'

const Overview = () => {
  const { showToast } = useApp()
  const navigate = useNavigate()
  
  const [summary, setSummary] = useState(null)
  const [projects, setProjects] = useState([])
  const [attentionItems, setAttentionItems] = useState([])
  const [loading, setLoading] = useState(true)
  
  // Fetch data on mount
  useEffect(() => {
    loadDashboardData()
  }, [])
  
  const loadDashboardData = async () => {
    try {
      setLoading(true)
      // TODO: Call API service
      // const summaryData = await apiService.getDashboardSummary()
      // const projectsData = await apiService.getProjectsOverview()
      // const attentionData = await apiService.getAttentionItems()
      
      // For now, show empty state
      setSummary({
        total_projects: 0,
        total_tasks: 0,
        tasks_by_status: {},
        completion_rate: 0
      })
      setProjects([])
      setAttentionItems([])
    } catch (error) {
      console.error('Error loading dashboard:', error)
      showToast('Failed to load dashboard data', 'error')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Dashboard Overview
        </h1>
        <p className="text-gray-600 mt-1">
          Bird's eye view of all your projects
        </p>
      </div>
      
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : (
        <>
          {/* Summary Stats - 4 cards in grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {/* Card 1: Total Projects */}
            <div className="card p-4">
              <div className="text-sm text-gray-600 mb-1">Projects</div>
              <div className="text-2xl font-bold text-gray-900">
                {summary?.total_projects || 0}
              </div>
            </div>
            
            {/* Card 2: Total Tasks */}
            <div className="card p-4">
              <div className="text-sm text-gray-600 mb-1">Total Tasks</div>
              <div className="text-2xl font-bold text-gray-900">
                {summary?.total_tasks || 0}
              </div>
            </div>
            
            {/* Card 3: In Progress */}
            <div className="card p-4">
              <div className="text-sm text-gray-600 mb-1">In Progress</div>
              <div className="text-2xl font-bold text-blue-600">
                {summary?.tasks_by_status?.in_progress || 0}
              </div>
            </div>
            
            {/* Card 4: Completion Rate */}
            <div className="card p-4">
              <div className="text-sm text-gray-600 mb-1">Completion</div>
              <div className="text-2xl font-bold text-green-600">
                {summary?.completion_rate?.toFixed(0) || 0}%
              </div>
            </div>
          </div>
          
          {/* Needs Attention Section - Placeholder for now */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Needs Attention
            </h2>
            {attentionItems.length === 0 ? (
              <div className="card p-6 text-center">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                <p className="text-gray-600">All caught up! 🎉</p>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Attention items will be added in next stage */}
                <p>Attention items coming soon...</p>
              </div>
            )}
          </div>
          
          {/* Projects Overview Section - Placeholder */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              All Projects
            </h2>
            {projects.length === 0 ? (
              <div className="card p-6 text-center">
                <p className="text-gray-600">No projects yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Project cards will be added in next stage */}
                <p>Projects coming soon...</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Overview
```

2. Update src/App.jsx:
   - Import Overview component
   - Change route "/" to render <Overview />
   - Move existing Dashboard to "/projects" route
   - Update: <Route path="/" element={<Overview />} />
   - Update: <Route path="/projects" element={<Dashboard />} />

3. Keep mobile-first:
   - Use Tailwind responsive classes
   - Grid adapts: 2 cols mobile, 4 cols desktop
   - Touch-friendly spacing

Add loading states. Handle empty states. Follow existing component patterns.
```

#### **Testing Stage 3.1:**

**Manual testing:**
```bash
# Make sure Flask backend is running
cd backend && source venv/bin/activate && python app.py

# Make sure React is running
npm run dev

# Open browser: http://localhost:3000
# Should see:
# - New Overview page (home)
# - 4 summary cards (will show 0 for now)
# - "Needs Attention" section (empty state)
# - "All Projects" section (empty state)

# Test navigation:
# - Should land on Overview by default
# - Navigate to /projects - should show existing project list
```

#### **✅ Stage 3.1 Complete When:**
- [ ] Overview.jsx created
- [ ] Routing updated (/ → Overview, /projects → Dashboard)
- [ ] Page loads without errors
- [ ] Shows 4 summary cards
- [ ] Shows empty states
- [ ] No console errors

---

### **STAGE 3.2: Connect Overview to API (30 minutes)**

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Connect Overview page to dashboard APIs.

CONTEXT:
- Overview.jsx exists with placeholder data
- api.service.js has getDashboardSummary(), getProjectsOverview(), getAttentionItems()
- Need to fetch real data from backend

REQUIREMENTS:
1. Update src/pages/Overview.jsx:

   In loadDashboardData():
   - Import: import * as apiService from '../services/api.service'
   - Replace TODO comments:
     ```javascript
     const summaryData = await apiService.getDashboardSummary()
     const projectsData = await apiService.getProjectsOverview()
     const attentionData = await apiService.getAttentionItems()
     
     setSummary(summaryData)
     setProjects(projectsData)
     setAttentionItems(attentionData)
     ```
   - Keep try/catch error handling
   - Show toast on error
   - Set loading = false in finally block

2. Add data refresh:
   - Add refresh button (optional)
   - Or auto-refresh every 30 seconds (optional)

Follow existing patterns in other pages. Handle errors gracefully.
```

#### **Testing Stage 3.2:**

```bash
# Flask backend running
# React running
# Open browser: http://localhost:3000

# Should see:
# - Real data in summary cards
# - Real project count
# - Completion rate calculated
# - No loading state after fetch

# Check browser console (F12):
# - No errors
# - Network tab shows API calls to /api/dashboard/*
# - All return 200 status

# Check Flask terminal:
# - Should show API calls being logged
# - No errors
```

#### **✅ Stage 3.2 Complete When:**
- [ ] API calls connected
- [ ] Real data displayed
- [ ] No errors in console
- [ ] Loading state works
- [ ] Error handling works

---

### **PHASE 3 TESTING**

```bash
# Run all previous tests (regression)
cd backend
source venv/bin/activate
python tests/test_dashboard_service.py
python tests/test_dashboard_api.py
python tests/test_attention_service.py
python tests/test_attention_api.py

# All should pass ✅

# Manual UI testing:
# - Overview page loads
# - Shows real data
# - No broken layouts
# - Mobile responsive (test in DevTools mobile view)
```

### **✅ Phase 3 Complete When:**
- [ ] Overview page shows real data
- [ ] All backend tests pass
- [ ] No regressions in existing features
- [ ] UI looks clean on mobile and desktop

**Continue to Phase 4 only if all tests pass.**

---

## 📱 **PHASE 4: Bottom Navigation (1 hour)**

### **Goal:** Add mobile-friendly bottom navigation with 4 tabs

### **What Gets Built:**
1. Bottom navigation component
2. Active tab detection
3. Route integration
4. Mobile-only display (hidden on desktop)

---

### **STAGE 4.1: Bottom Navigation Component (1 hour)**

#### **Manual Steps:**
1. Test on mobile viewport after generating
2. Use Chrome DevTools → Toggle device toolbar

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Create mobile bottom navigation component.

CONTEXT:
- React app has routes: /, /projects, /project/:id, /employees
- Need bottom nav for mobile with 4 tabs
- Should hide on desktop (≥768px)
- Should be fixed at bottom on mobile

REQUIREMENTS:
1. Update src/components/layout/MobileNav.jsx:

   Replace entire file with:
   ```jsx
   import { Link, useLocation } from 'react-router-dom'
   import { Home, FolderKanban, Users, Settings } from 'lucide-react'
   
   const MobileNav = () => {
     const location = useLocation()
     
     const navItems = [
       { path: '/', icon: Home, label: 'Overview' },
       { path: '/projects', icon: FolderKanban, label: 'Projects' },
       { path: '/employees', icon: Users, label: 'Team' },
       // Settings route doesn't exist yet, disable for now
       // { path: '/settings', icon: Settings, label: 'Settings' }
     ]
     
     const isActive = (path) => {
       if (path === '/') {
         return location.pathname === '/'
       }
       return location.pathname.startsWith(path)
     }
     
     return (
       <div className="mobile-nav md:hidden">
         <div className="flex items-center justify-around">
           {navItems.map((item) => {
             const Icon = item.icon
             const active = isActive(item.path)
             
             return (
               <Link
                 key={item.path}
                 to={item.path}
                 className={`flex flex-col items-center gap-1 py-3 px-4 tap-target transition-smooth ${
                   active ? 'text-blue-600' : 'text-gray-600'
                 }`}
               >
                 <Icon className="w-6 h-6" />
                 <span className="text-xs font-medium">{item.label}</span>
               </Link>
             )
           })}
         </div>
       </div>
     )
   }
   
   export default MobileNav
   ```

2. Verify existing CSS:
   - Check index.css has `.mobile-nav` styles
   - Should be: fixed bottom, bg-white, border-top, z-30
   - Hidden on desktop: md:hidden class

3. App.jsx should already import and use <MobileNav />

Mobile-first. Touch-friendly. Active state clear.
```

#### **Testing Stage 4.1:**

**Manual testing:**
```bash
# React running
# Open browser: http://localhost:3000

# Desktop view:
# - Bottom nav should NOT appear
# - Top navbar should work

# Mobile view (DevTools):
# - Press F12
# - Toggle device toolbar (phone icon)
# - Select iPhone or Android device
# - Bottom nav should appear
# - Tap each tab:
#   * Overview → goes to /
#   * Projects → goes to /projects
#   * Team → goes to /employees
# - Active tab should be highlighted in blue
# - Icons and labels should be visible
```

#### **✅ Stage 4.1 Complete When:**
- [ ] MobileNav updated
- [ ] Shows on mobile (<768px)
- [ ] Hidden on desktop (≥768px)
- [ ] All tabs navigate correctly
- [ ] Active tab highlighted
- [ ] Touch-friendly (44px min)

---

### **PHASE 4 TESTING**

```bash
# Run all previous tests (regression)
cd backend && source venv/bin/activate
python tests/test_dashboard_service.py
python tests/test_dashboard_api.py
python tests/test_attention_service.py
python tests/test_attention_api.py

# Manual testing:
# - Test all pages still work
# - Test navigation on mobile and desktop
# - Test Projects page still works
# - Test creating project still works
# - Test Kanban board still works
```

### **✅ Phase 4 Complete When:**
- [ ] Bottom nav works on mobile
- [ ] All routes accessible
- [ ] No regressions in existing features
- [ ] All backend tests pass

---

## 👆 **PHASE 5: Quick Actions & Attention Cards (1.5 hours)**

### **Goal:** Implement attention item cards with quick action buttons

### **What Gets Built:**
1. AttentionCard component
2. Quick action buttons (Call, Remind, View)
3. Project summary cards for Overview
4. Action handlers

---

### **STAGE 5.1: Attention Card Component (45 minutes)**

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Create AttentionCard component for "Needs Attention" items.

CONTEXT:
- Displays task that needs owner's attention
- Shows priority (red=high, yellow=medium), reason, employee, time
- Has 3 action buttons: Call, Remind, View
- Mobile-first design

REQUIREMENTS:
1. Create src/components/dashboard/AttentionCard.jsx:

```jsx
import { Phone, Bell, Eye, Clock, AlertCircle } from 'lucide-react'
import { useApp } from '../../context/useApp'
import { useNavigate } from 'react-router-dom'
import EmployeeAvatar from '../employees/EmployeeAvatar'

const AttentionCard = ({ item, onActionComplete }) => {
  const { getEmployeeById, showToast } = useApp()
  const navigate = useNavigate()
  
  const employee = getEmployeeById(item.employee_id)
  
  // Priority styling
  const priorityStyles = {
    high: {
      bg: 'bg-red-50 border-red-200',
      icon: 'text-red-600',
      badge: 'bg-red-100 text-red-800'
    },
    medium: {
      bg: 'bg-yellow-50 border-yellow-200',
      icon: 'text-yellow-600',
      badge: 'bg-yellow-100 text-yellow-800'
    }
  }
  
  const style = priorityStyles[item.priority] || priorityStyles.medium
  
  // Action handlers
  const handleCall = () => {
    // Open phone dialer
    window.location.href = `tel:${employee?.phone}`
    showToast(`Calling ${employee?.name}...`, 'info')
  }
  
  const handleRemind = async () => {
    try {
      // TODO: Call API to send WhatsApp reminder
      // await apiService.sendTaskReminder(item.task_id)
      showToast('Reminder sent to employee', 'success')
      if (onActionComplete) onActionComplete()
    } catch (error) {
      showToast('Failed to send reminder', 'error')
    }
  }
  
  const handleView = () => {
    // Navigate to project and open task
    navigate(`/project/${item.project_id}`)
  }
  
  return (
    <div className={`card border-l-4 p-4 ${style.bg}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        {/* Priority badge */}
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${style.badge}`}>
          <AlertCircle className="w-3 h-3" />
          {item.priority.toUpperCase()}
        </span>
        
        {/* Time info */}
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{item.hours_since_update}h ago</span>
        </div>
      </div>
      
      {/* Task info */}
      <h3 className="font-semibold text-gray-900 mb-1">{item.task_title}</h3>
      <p className="text-sm text-gray-600 mb-2">{item.reason}</p>
      
      {/* Employee and project info */}
      <div className="flex items-center justify-between mb-3">
        {employee && (
          <EmployeeAvatar employee={employee} size="xs" showName />
        )}
        <span className="text-xs text-gray-500">{item.project_name}</span>
      </div>
      
      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleCall}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-smooth tap-target"
        >
          <Phone className="w-4 h-4" />
          Call
        </button>
        
        <button
          onClick={handleRemind}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-200 text-gray-900 rounded-lg text-sm font-medium hover:bg-gray-300 transition-smooth tap-target"
        >
          <Bell className="w-4 h-4" />
          Remind
        </button>
        
        <button
          onClick={handleView}
          className="px-3 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-smooth tap-target"
        >
          <Eye className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default AttentionCard
```

2. Create src/components/dashboard/ folder if it doesn't exist

3. Use existing components:
   - EmployeeAvatar (already exists)
   - Icons from lucide-react
   - Styling from index.css

Mobile-first. Touch-friendly buttons. Clear visual hierarchy.
```

#### **Testing Stage 5.1:**

**Manual testing:**
```bash
# Create test data first (if no attention items exist)
# In Python:
cd backend
source venv/bin/activate
python

>>> from database import update_task
>>> from datetime import datetime, timedelta
>>> # Make a task overdue
>>> update_task('task_001', {
...   'due_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
...   'status': 'in_progress'
... })
>>> exit()

# Restart Flask
python app.py

# In browser: http://localhost:3000
# Should see attention card for overdue task
# Test buttons:
# - Click "Call" → Should open phone dialer
# - Click "Remind" → Should show toast (reminder sent)
# - Click "View" → Should navigate to project page
```

#### **✅ Stage 5.1 Complete When:**
- [ ] AttentionCard component created
- [ ] Shows priority badge (red/yellow)
- [ ] Shows task info
- [ ] All 3 buttons work
- [ ] Mobile-friendly layout

---

### **STAGE 5.2: Project Summary Cards (45 minutes)**

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Create ProjectSummaryCard component for Overview page.

CONTEXT:
- Overview page needs to show all projects with quick stats
- Different from existing ProjectCard (simpler, more stats-focused)
- Shows: name, tasks count, completion rate, overdue count
- Click to navigate to project Kanban

REQUIREMENTS:
1. Create src/components/dashboard/ProjectSummaryCard.jsx:

```jsx
import { useNavigate } from 'react-router-dom'
import { Calendar, CheckCircle, AlertTriangle } from 'lucide-react'
import ProgressBar from '../common/ProgressBar'
import { formatDate } from '../../utils/helpers'

const ProjectSummaryCard = ({ project }) => {
  const navigate = useNavigate()
  
  const handleClick = () => {
    navigate(`/project/${project.project_id}`)
  }
  
  return (
    <div
      onClick={handleClick}
      className="card-hover p-4 cursor-pointer"
      style={{ borderLeftWidth: '4px', borderLeftColor: project.project_color }}
    >
      {/* Project name */}
      <h3 className="font-semibold text-gray-900 mb-2 truncate">
        {project.project_name}
      </h3>
      
      {/* Stats row */}
      <div className="flex items-center gap-4 mb-3 text-sm">
        <div className="flex items-center gap-1 text-gray-600">
          <CheckCircle className="w-4 h-4" />
          <span>{project.completed_tasks}/{project.total_tasks}</span>
        </div>
        
        {project.overdue_tasks > 0 && (
          <div className="flex items-center gap-1 text-red-600 font-medium">
            <AlertTriangle className="w-4 h-4" />
            <span>{project.overdue_tasks} overdue</span>
          </div>
        )}
      </div>
      
      {/* Progress bar */}
      <ProgressBar 
        progress={project.completion_rate} 
        size="sm"
        showLabel={false}
      />
      
      {/* Date range (optional) */}
      <div className="flex items-center gap-1 text-xs text-gray-500 mt-2">
        <Calendar className="w-3 h-3" />
        <span>{formatDate(project.start_date)} - {formatDate(project.end_date)}</span>
      </div>
    </div>
  )
}

export default ProjectSummaryCard
```

2. Update src/pages/Overview.jsx:
   - Import ProjectSummaryCard
   - In "All Projects" section, replace placeholder:
     ```jsx
     <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
       {projects.map((project) => (
         <ProjectSummaryCard
           key={project.project_id}
           project={project}
         />
       ))}
     </div>
     ```

3. Update "Needs Attention" section in Overview.jsx:
   - Import AttentionCard (from Stage 5.1)
   - Replace placeholder:
     ```jsx
     <div className="space-y-3">
       {attentionItems.map((item) => (
         <AttentionCard
           key={item.task_id}
           item={item}
           onActionComplete={() => loadDashboardData()}
         />
       ))}
     </div>
     ```

Reuse existing components. Follow Tailwind patterns. Mobile-first.
```

#### **Testing Stage 5.2:**

**Manual testing:**
```bash
# Browser: http://localhost:3000
# Should see:
# - Attention items (if any) with action buttons
# - All projects as cards
# - Click project card → navigates to Kanban
# - Progress bars show correctly
# - Overdue count (if any) shown in red

# Test mobile view:
# - Cards stack vertically
# - Touch-friendly
# - Bottom nav accessible

# Test desktop:
# - Cards in grid (2-3 columns)
# - Bottom nav hidden
# - Top navbar visible
```

#### **✅ Stage 5.2 Complete When:**
- [ ] ProjectSummaryCard created
- [ ] Shows project stats correctly
- [ ] Click navigates to project
- [ ] AttentionCard integrated
- [ ] All cards render correctly

---

### **PHASE 5 TESTING**

```bash
# Backend tests (regression)
cd backend && source venv/bin/activate
python tests/test_dashboard_service.py
python tests/test_dashboard_api.py
python tests/test_attention_service.py

# Manual UI testing:
# - All cards display correctly
# - Navigation works
# - Buttons functional
# - Mobile responsive
# - No layout breaks
```

### **✅ Phase 5 Complete When:**
- [ ] Attention cards show and work
- [ ] Project cards show and work
- [ ] All actions functional
- [ ] No regressions
- [ ] All tests pass

---

## ✨ **PHASE 6: Polish & Edge Cases (1 hour)**

### **Goal:** Handle edge cases, add error states, polish UI

### **Edge Cases to Handle:**

1. **Empty states:**
   - No projects exist
   - No tasks exist
   - No attention items
   - All tasks completed

2. **Error states:**
   - API call fails
   - Network error
   - Invalid data

3. **Loading states:**
   - Initial load
   - Refresh
   - Action in progress

4. **Data edge cases:**
   - Project with 0 tasks
   - Task with no due date
   - Task with no employee assigned
   - Invalid timestamps

---

### **STAGE 6.1: Edge Case Tests (30 minutes)**

#### **Create Comprehensive Test Suite:**

**`backend/tests/test_edge_cases.py`:**

```python
"""
Edge case tests for dashboard.
"""

from services import dashboard_service, attention_service
from datetime import datetime

def test_empty_database():
    """Test when no projects/tasks exist."""
    # Test with empty database
    summary = dashboard_service.get_dashboard_summary()
    assert summary["total_projects"] == 0
    assert summary["total_tasks"] == 0
    assert summary["completion_rate"] == 0
    print("✅ Empty database handled")

def test_project_with_no_tasks():
    """Test project with zero tasks."""
    # This shouldn't crash
    projects = dashboard_service.get_projects_overview()
    # Should return list (possibly empty)
    assert isinstance(projects, list)
    print("✅ Empty projects handled")

def test_task_with_no_due_date():
    """Test task without due date."""
    task = {
        "task_id": "test",
        "status": "in_progress",
        "due_date": None
    }
    is_overdue = attention_service.is_task_overdue(task)
    # Should return False (not crash)
    assert is_overdue == False
    print("✅ Missing due date handled")

def test_task_with_invalid_timestamp():
    """Test task with invalid updated_at."""
    task = {
        "updated_at": "invalid-date"
    }
    try:
        hours = attention_service.calculate_hours_since_update(task["updated_at"])
        # Should handle gracefully (return large number or 0)
        assert isinstance(hours, (int, float))
        print("✅ Invalid timestamp handled")
    except:
        print("❌ Invalid timestamp not handled - needs fix")

def test_completion_rate_edge_cases():
    """Test completion rate calculation edge cases."""
    # Division by zero
    assert dashboard_service.calculate_completion_rate(0, 0) == 0
    # More completed than total (shouldn't happen but test anyway)
    rate = dashboard_service.calculate_completion_rate(10, 5)
    # Should cap at 100 or handle gracefully
    print(f"✅ Edge case: {rate}% (10 completed, 5 total)")

def test_attention_items_with_missing_employee():
    """Test attention items when employee doesn't exist."""
    # This tests if enrichment handles missing employees
    items = attention_service.get_attention_items()
    # Shouldn't crash if employee missing
    assert isinstance(items, list)
    print("✅ Missing employee data handled")

if __name__ == "__main__":
    print("🧪 Testing Edge Cases...")
    print("=" * 60)
    
    test_empty_database()
    test_project_with_no_tasks()
    test_task_with_no_due_date()
    test_task_with_invalid_timestamp()
    test_completion_rate_edge_cases()
    test_attention_items_with_missing_employee()
    
    print("\n🎉 Edge case tests complete!")
```

**Run edge case tests:**
```bash
cd backend
source venv/bin/activate
python tests/test_edge_cases.py
```

**Fix any failures before continuing.**

---

### **STAGE 6.2: Error Handling & Polish (30 minutes)**

#### **LLM Prompt:**

**⚠️ PREPEND `TECHNICAL_DESIGN_SPEC.md` BEFORE THIS PROMPT**

```
Add error handling and polish to Overview page.

REQUIREMENTS:
1. Update src/pages/Overview.jsx:

   Add error state:
   - const [error, setError] = useState(null)
   - In loadDashboardData(), catch errors:
     ```javascript
     catch (error) {
       console.error('Error loading dashboard:', error)
       setError(error.message)
       showToast('Failed to load dashboard', 'error')
       // Fall back to empty data (don't crash)
       setSummary({ total_projects: 0, total_tasks: 0, ... })
     }
     ```
   
   Add error display:
   - If error exists, show error card:
     ```jsx
     {error && (
       <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
         <p className="text-red-800">Error: {error}</p>
         <button
           onClick={() => { setError(null); loadDashboardData(); }}
           className="mt-2 text-sm text-red-600 underline"
         >
           Retry
         </button>
       </div>
     )}
     ```

2. Handle null/undefined data:
   - Use optional chaining: summary?.total_projects || 0
   - Default empty arrays: projects || []
   - Safe navigation: item?.employee?.name || 'Unknown'

3. Add refresh functionality:
   - Add refresh button in header (optional)
   - Or pull-to-refresh on mobile (future)

4. Add empty states with helpful messages:
   - No projects: "Create your first project to get started"
   - No attention items: "All caught up! 🎉"

Follow React best practices. Handle all edge cases gracefully.
```

#### **Testing Stage 6.2:**

**Test error scenarios:**

```bash
# Test 1: Stop Flask backend
# In browser, refresh Overview page
# Should show error message
# Click "Retry" → should show "cannot connect" error

# Test 2: Start Flask backend
# Click "Retry" → should load data successfully

# Test 3: Test with empty database
# Delete database.db, restart Flask
# Should show "No projects yet" empty state

# Test 4: Test with network delay
# Add slow response in backend (time.sleep(5))
# Should show loading state during fetch
```

#### **✅ Stage 6.2 Complete When:**
- [ ] Error states handled
- [ ] Empty states friendly
- [ ] Retry functionality works
- [ ] No crashes on bad data
- [ ] Loading states clear

---

### **PHASE 6 FINAL TESTING**

Run complete test suite:

```bash
# All backend tests
cd backend
source venv/bin/activate
python tests/test_dashboard_service.py
python tests/test_dashboard_api.py
python tests/test_attention_service.py
python tests/test_attention_api.py
python tests/test_edge_cases.py

# Manual comprehensive testing:
# 1. Overview page loads
# 2. Shows real data
# 3. Attention items display
# 4. Action buttons work (Call, Remind, View)
# 5. Project cards clickable
# 6. Bottom nav works on mobile
# 7. Top nav works on desktop
# 8. Can still create projects
# 9. Can still manage tasks in Kanban
# 10. No console errors
# 11. Mobile responsive
# 12. Error handling works
```

### **✅ Phase 6 Complete When:**
- [ ] All 5 test files pass
- [ ] All edge cases handled
- [ ] Error states work
- [ ] Empty states friendly
- [ ] No regressions
- [ ] UI polished and responsive

---

## 🎉 **DASHBOARD FEATURE COMPLETE!**

### **Final Verification:**

1. **Backend:**
   - [ ] 5 test files, all passing
   - [ ] 3 new API endpoints working
   - [ ] Attention logic correct
   - [ ] No errors

2. **Frontend:**
   - [ ] Overview page as home (/)
   - [ ] Projects moved to /projects
   - [ ] Bottom nav on mobile
   - [ ] Attention cards functional
   - [ ] Project cards functional
   - [ ] All actions work

3. **Integration:**
   - [ ] Frontend fetches from backend
   - [ ] WhatsApp reminder (mock) works
   - [ ] Phone call links work
   - [ ] Navigation works

4. **Quality:**
   - [ ] Mobile-first responsive
   - [ ] No console errors
   - [ ] Clean, minimal UI
   - [ ] Loading states
   - [ ] Error handling
   - [ ] Edge cases covered

---

## 📊 **TEST CASE SUMMARY**

Total test files created: 5

1. `test_dashboard_service.py` — 4 tests
2. `test_dashboard_api.py` — 4 tests
3. `test_attention_service.py` — 6 tests
4. `test_attention_api.py` — 1 test
5. `test_edge_cases.py` — 6 tests

**Total: 21 automated tests + manual UI testing**

---

## 🚀 **DEPLOYMENT CHECKLIST**

Before showing to investors:

- [ ] All tests pass
- [ ] Test on real mobile device
- [ ] Test with real employee data
- [ ] Test attention alerts with actual delays
- [ ] Test calling from mobile
- [ ] Test WhatsApp reminders work
- [ ] Deploy backend to cloud (if not already)
- [ ] Test with production data
- [ ] Document any limitations

---

## 📝 **PHASE SUMMARY**

| Phase | Features Added | Tests | Time |
|-------|---------------|-------|------|
| 1 | Dashboard API, data aggregation | 8 tests | 2h |
| 2 | Attention detection, priority logic | 7 tests | 2h |
| 3 | Overview UI, layout, routing | Manual | 2h |
| 4 | Bottom navigation | Manual | 1h |
| 5 | Action buttons, cards | Manual | 1.5h |
| 6 | Edge cases, error handling | 6 tests | 1h |

**Total:** 21 automated tests, 9.5 hours development

---

**Good luck with the dashboard implementation! Follow one phase at a time, test thoroughly, fix any issues before proceeding. You've got this! 🚀**
