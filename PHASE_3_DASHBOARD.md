# Phase 3 Implementation Plan: Owner Dashboard & Mobile-First Navigation

**Start Date**: TBD (kick off after Phase 2 sign-off)  
**Status**: Draft  
**Goal**: Deliver a reusable, mobile-first Owner Dashboard that surfaces "Needs Attention" items, branch/event performance, and quick navigation without duplicating existing project/task logic. The implementation must be incremental, with automated tests added in every stage to protect Phase 1 & 2 features.

---

## Phase Overview

| Phase | Focus | Outcome |
|-------|-------|---------|
| **Phase 3A** | Data & API groundwork | Reliable summary endpoints + "needs attention" service reused by UI |
| **Phase 3B** | Frontend dashboard + navigation | New Overview screen + bottom navigation without breaking current pages |
| **Phase 3C** | Validation, polish, doc | Automated + manual QA, regression suite, launch checklist |

---

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

**How to Use This Document**:

Each stage below describes:
- **Goal / Scope constraints** (keep code minimal, reuse existing services)
- **Implementation notes** (files, patterns to touch)
- **Tests to add** (unit + integration)
- **Regression checks** (which suites to rerun before proceeding)

LLMs can follow this structure stage-by-stage: implement → add tests → run pytest + npm test → manual smoke → move to next stage only when green.

---

## Phase 3A — Data & API Foundation

### **Stage 3A.1: Project & Label Audit**

**Goal**: Ensure every project already stores the metadata the dashboard needs (name, color, completion stats). Introduce optional label config (e.g., "Store/Event/Unit") without forcing migrations.

**Implementation**:
  
**Backend Changes**:

Create `backend/config/dashboard_labels.json`:
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

Add `backend/services/label_service.py`:
```python
import json
import os

def get_label_config(business_type='default'):
    """Load label config with fallback to defaults"""
    try:
        config_path = os.path.join('config', 'dashboard_labels.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if business_type != 'default':
            custom = config.get('customizations', {}).get(business_type)
            if custom:
                return custom
        
        return config.get('defaults', {
            'project': 'Project',
            'assignee': 'Team Member'
        })
    except Exception as e:
        # Fallback to safe defaults if config missing
        return {
            'project': 'Project',
            'projects': 'Projects',
            'assignee': 'Team Member',
            'assignees': 'Team Members'
        }
```

**Frontend Changes**:

Create `src/config/uiLabels.js`:
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

Update `src/context/AppContext.jsx` to add `uiLabels` to context:
```javascript
// Add to AppContext
const [uiLabels, setUiLabels] = useState(DEFAULT_LABELS);

// Expose in context value
const value = {
  // ... existing values
  uiLabels,
  setUiLabels
};
```

**Data Audit Checklist**:
- [ ] Verify all projects have `name`, `color`, `status` fields
- [ ] Confirm task completion percentages calculate correctly
- [ ] Check employee data has required fields (name, phone, avatar)
- [ ] Validate existing localStorage schema matches expectations

**Tests**:
- Frontend unit: `uiLabels.test.js` (ensures overrides fall back to defaults)
- Backend unit: `test_dashboard_labels_defaults()` (ensures config loader never crashes)
- Backend unit: `test_label_config_missing_file_fallback()`
- Frontend unit: `test_context_exposes_ui_labels()`

**Regression**: `npm run build`, `pytest test_api.py::TestProjects -v`

**Acceptance Criteria**:
- ✅ Label config loads without errors
- ✅ Missing config files don't crash application
- ✅ Custom labels override defaults correctly
- ✅ Context provides labels to all components

---

### **Stage 3A.2: Summary Endpoint**

**Goal**: Add lightweight endpoint to fetch aggregated metrics (today's totals, per-project stats, per-assignee stats) using existing services.

**Implementation**:

**Backend Changes**:

Create `backend/api/dashboard.py`:
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

def group_tasks_by_assignee(tasks, employees):
    """Group task stats by assignee"""
    employee_map = {e['id']: e for e in employees}
    stats = {}
    
    for task in tasks:
        assignee_id = task.get('assigneeId')
        if not assignee_id:
            continue
            
        if assignee_id not in stats:
            stats[assignee_id] = {
                'id': assignee_id,
                'name': employee_map.get(assignee_id, {}).get('name', 'Unknown'),
                'avatar': employee_map.get(assignee_id, {}).get('avatar'),
                'total': 0,
                'done': 0,
                'pending': 0
            }
        
        stats[assignee_id]['total'] += 1
        if task.get('status') == 'done':
            stats[assignee_id]['done'] += 1
        elif task.get('status') == 'pending':
            stats[assignee_id]['pending'] += 1
    
    return list(stats.values())

def is_overdue(task, target_date):
    """Check if task is overdue"""
    if task.get('status') == 'done':
        return False
    due_date = task.get('dueDate')
    if not due_date:
        return False
    try:
        due = datetime.fromisoformat(due_date).date()
        target = datetime.fromisoformat(target_date).date() if isinstance(target_date, str) else target_date
        return due < target
    except:
        return False
```

Register blueprint in `backend/app.py`:
```python
from api.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)
```

**Frontend Service**:

Create `src/services/dashboard.service.js`:
```javascript
export const dashboardService = {
  async getSummary(date = null) {
    const params = date ? `?date=${date}` : '';
    const response = await fetch(`/api/dashboard/summary${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch dashboard summary');
    }
    return response.json();
  }
};
```

**Tests**:
- Backend: `test_dashboard_summary_defaults()` (no date → today)
- Backend: `test_dashboard_summary_filters_by_date()`
- Backend: `test_dashboard_summary_handles_no_projects()`
- Backend: `test_dashboard_summary_handles_no_tasks()`
- Backend: `test_dashboard_summary_completion_rate_calculation()`
- Backend: `test_dashboard_summary_performance_with_1000_tasks()`
- Frontend: `test_dashboard_service_fetch_summary()`

**Regression**: `pytest test_api.py::TestTasks -k project -v`

**Acceptance Criteria**:
- ✅ Endpoint returns data in < 200ms with 100 tasks
- ✅ Date filtering works correctly
- ✅ Empty data returns valid structure (zeros)
- ✅ Completion rates calculated accurately
- ✅ Response includes all required fields

---

### **Stage 3A.3: Needs-Attention Service**

**Goal**: Centralize logic that flags overdue / no-response tasks so UI, reminders, and future reports reuse same rules.

**Implementation**:

**Backend Service**:

Create `backend/services/attention_service.py`:
```python
from datetime import datetime, timedelta
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
        from services.task_service import get_all_tasks
        tasks = get_all_tasks()
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
        try:
            due = datetime.fromisoformat(due_date)
            return due < reference_time
        except:
            return False
    
    def _has_no_response(self, task, reference_time):
        """Check if WhatsApp sent but no response"""
        if not task.get('whatsappSent'):
            return False
        if task.get('lastActivity'):
            return False
        sent_time = task.get('whatsappSentAt')
        if not sent_time:
            return False
        try:
            sent = datetime.fromisoformat(sent_time)
            time_since = (reference_time - sent).total_seconds()
            return time_since > 7200  # 2 hours
        except:
            return False
    
    def _pending_too_long(self, task, reference_time):
        """Check if pending for too long"""
        if task.get('status') != 'pending':
            return False
        created = task.get('createdAt')
        if not created:
            return False
        try:
            created_dt = datetime.fromisoformat(created)
            time_since = (reference_time - created_dt).total_seconds()
            return time_since > 21600  # 6 hours
        except:
            return False
    
    def _format_overdue(self, task, reference_time):
        """Format overdue message"""
        try:
            due = datetime.fromisoformat(task.get('dueDate'))
            delta = reference_time - due
            days = delta.days
            if days == 0:
                return 'today'
            elif days == 1:
                return 'yesterday'
            else:
                return f'{days} days ago'
        except:
            return 'overdue'
    
    def _calculate_priority(self, reasons):
        """Calculate priority score from reasons"""
        severity_scores = {'high': 3, 'medium': 2, 'low': 1}
        return sum(severity_scores.get(r['severity'], 0) for r in reasons)

# Singleton instance
attention_service = AttentionService()
```

Add API endpoint in `backend/api/dashboard.py`:
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

Add to `src/services/dashboard.service.js`:
```javascript
export const dashboardService = {
  // ... existing methods
  
  async getAttentionItems() {
    const response = await fetch('/api/dashboard/attention');
    if (!response.ok) {
      throw new Error('Failed to fetch attention items');
    }
    return response.json();
  }
};
```

**Tests**:
- Backend: `test_attention_flags_overdue_tasks()`
- Backend: `test_attention_flags_no_response_tasks()`
- Backend: `test_attention_flags_pending_long_tasks()`
- Backend: `test_attention_respects_cache_window()`
- Backend: `test_attention_priority_calculation()`
- Backend: `test_attention_ignores_completed_tasks()`
- Backend: `test_attention_cache_invalidation()`
- Backend: `test_attention_endpoint_returns_json()`

**Regression**: Run full `pytest test_api.py::TestWhatsAppIntegration -v` to ensure reminder logic unaffected

**Acceptance Criteria**:
- ✅ All attention rules fire correctly
- ✅ Cache reduces database queries
- ✅ Priority sorting works as expected
- ✅ Completed tasks never flagged
- ✅ Performance acceptable with 500+ tasks

> ✅ **Phase 3A exit criteria**: All new backend tests pass, lint clean, existing suites untouched. Frontend still uses old navigation until Phase 3B.

---

## Phase 3B — Owner Dashboard UI & Navigation

### **Stage 3B.1: Navigation Shell**

**Goal**: Introduce bottom navigation (mobile-first) with tabs: `Overview`, `Projects`, `Team`, `Settings` without breaking existing routes.

**Implementation**:

**Navigation Component**:

Create `src/layout/BottomNav.jsx`:
```jsx
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  FolderIcon, 
  UsersIcon, 
  CogIcon 
} from '@heroicons/react/24/outline';

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
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-inset-bottom md:hidden z-50"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex justify-around items-center h-16">
        {tabs.map(tab => {
          const isActive = location.pathname === tab.path;
          const Icon = tab.icon;
          
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
              <Icon className="w-6 h-6 mb-1" aria-hidden="true" />
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

Update `src/App.jsx`:
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
        </Routes>
        <BottomNav />
      </div>
    </AppProvider>
  );
}

export default App;
```

**Responsive Considerations**:

Add to `src/index.css`:
```css
/* Safe area for iOS notch/home indicator */
.safe-area-inset-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}

/* Ensure content doesn't hide under bottom nav */
@media (max-width: 767px) {
  main {
    padding-bottom: 4rem; /* 64px for nav height */
  }
}

/* Hide bottom nav on desktop */
@media (min-width: 768px) {
  .bottom-nav-spacer {
    display: none;
  }
}
```

**Tests**:
- Frontend: `BottomNav.test.jsx` (active tab highlights, ARIA labels)
- Frontend: `test_navigation_keyboard_accessible()`
- Frontend: `test_navigation_active_state_updates()`
- E2E: Cypress test for tab switching and route changes

**Regression**: `npm run build`, manual check on iPad width, test existing routes still work

**Acceptance Criteria**:
- ✅ Bottom nav visible only on mobile (<768px)
- ✅ Active tab highlighted correctly
- ✅ Keyboard navigation works (Tab, Enter)
- ✅ Touch targets >= 44px
- ✅ Screen reader announces current page
- ✅ No layout shift when switching tabs

---

### **Stage 3B.2: Overview Screen Skeleton**

**Goal**: New page `src/pages/Overview.jsx` that consumes summary API + attention service, but initially displays loading skeletons.

**Implementation**:

Create `src/pages/Overview.jsx`:
```jsx
import { useState, useEffect } from 'react';
import { useApp } from '../context/useApp';
import { dashboardService } from '../services/dashboard.service';
import Toast from '../components/common/Toast';

const Overview = () => {
  const { uiLabels } = useApp();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [attentionItems, setAttentionItems] = useState([]);
  
  useEffect(() => {
    loadDashboardData();
  }, []);
  
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [summaryData, attentionData] = await Promise.all([
        dashboardService.getSummary(),
        dashboardService.getAttentionItems()
      ]);
      
      setSummary(summaryData);
      setAttentionItems(attentionData.items);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold mb-6">Overview</h1>
        
        {/* Loading Skeletons */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
        
        <div className="bg-white rounded-lg shadow p-4 animate-pulse mb-6">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="container mx-auto px-4 py-6">
        <Toast type="error" message={error} />
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Overview</h1>
      
      {/* Totals Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="All Tasks" value={summary?.totals?.all || 0} />
        <StatCard label="Done" value={summary?.totals?.done || 0} color="green" />
        <StatCard label="Pending" value={summary?.totals?.pending || 0} color="yellow" />
        <StatCard label="Overdue" value={summary?.totals?.overdue || 0} color="red" />
      </div>
      
      {/* Needs Attention */}
      {attentionItems.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h2 className="text-lg font-semibold mb-4">Needs Attention</h2>
          <div className="space-y-3">
            {attentionItems.map((item, idx) => (
              <AttentionCard key={idx} item={item} />
            ))}
          </div>
        </div>
      )}
      
      {/* By Project */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <h2 className="text-lg font-semibold mb-4">By {uiLabels.project}</h2>
        <div className="space-y-3">
          {summary?.projects?.map(project => (
            <ProjectStatRow key={project.id} project={project} />
          ))}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ label, value, color = 'blue' }) => {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600'
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${colorClasses[color]}`}>{value}</p>
    </div>
  );
};

const AttentionCard = ({ item }) => {
  return (
    <div className="border border-orange-200 bg-orange-50 rounded-lg p-3">
      <p className="font-medium">{item.task.title}</p>
      <div className="flex flex-wrap gap-2 mt-2">
        {item.reasons.map((reason, idx) => (
          <span key={idx} className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
            {reason.message}
          </span>
        ))}
      </div>
    </div>
  );
};

const ProjectStatRow = ({ project }) => {
  const completion = project.total > 0 
    ? Math.round((project.done / project.total) * 100) 
    : 0;
  
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div 
          className="w-4 h-4 rounded-full" 
          style={{ backgroundColor: project.color }}
        />
        <span className="font-medium">{project.name}</span>
      </div>
      <div className="text-sm text-gray-600">
        {project.done}/{project.total} ({completion}%)
      </div>
    </div>
  );
};

export default Overview;
```

**Tests**:
- Frontend: `Overview.test.jsx` (loading states, error handling)
- Frontend: `test_overview_displays_stat_cards()`
- Frontend: `test_overview_handles_empty_data()`
- Snapshot test for stable card structure

**Regression**: Run `npm test -- Overview.test.jsx`

**Acceptance Criteria**:
- ✅ Loading skeletons display correctly
- ✅ Error states show user-friendly messages
- ✅ Data fetches on mount
- ✅ All cards render with correct data
- ✅ No console errors or warnings

---

### **Stage 3B.3: Interactive Actions**

**Goal**: Wire up tap targets on Needs Attention cards: Call, Send Reminder, View Task. Buttons must reuse existing codepaths (e.g., WhatsApp send service, TaskModal).

**Implementation**:

Update `src/pages/Overview.jsx` - enhance `AttentionCard`:
```jsx
import { useState } from 'react';
import { PhoneIcon, BellIcon, EyeIcon } from '@heroicons/react/24/outline';
import TaskModal from '../components/tasks/TaskModal';

const AttentionCard = ({ item, onAction }) => {
  const [showModal, setShowModal] = useState(false);
  const [sending, setSending] = useState(false);
  
  const handleCall = () => {
    const phone = item.task.assignee?.phone;
    if (phone) {
      window.location.href = `tel:${phone}`;
    }
  };
  
  const handleSendReminder = async () => {
    try {
      setSending(true);
      await onAction('reminder', item.task.id);
    } finally {
      setSending(false);
    }
  };
  
  return (
    <>
      <div className="border border-orange-200 bg-orange-50 rounded-lg p-3">
        <p className="font-medium mb-2">{item.task.title}</p>
        
        <div className="flex flex-wrap gap-2 mb-3">
          {item.reasons.map((reason, idx) => (
            <span key={idx} className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
              {reason.message}
            </span>
          ))}
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => setShowModal(true)}
            className="flex-1 flex items-center justify-center gap-2 bg-blue-500 text-white px-3 py-2 rounded-lg hover:bg-blue-600 transition-colors touch-manipulation"
            style={{ minHeight: '44px' }}
          >
            <EyeIcon className="w-5 h-5" />
            <span className="text-sm font-medium">View</span>
          </button>
          
          {item.task.assignee?.phone && (
            <button
              onClick={handleCall}
              className="flex items-center justify-center gap-2 bg-green-500 text-white px-3 py-2 rounded-lg hover:bg-green-600 transition-colors touch-manipulation"
              style={{ minHeight: '44px', minWidth: '44px' }}
              aria-label="Call assignee"
            >
              <PhoneIcon className="w-5 h-5" />
            </button>
          )}
          
          <button
            onClick={handleSendReminder}
            disabled={sending}
            className="flex items-center justify-center gap-2 bg-orange-500 text-white px-3 py-2 rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors touch-manipulation"
            style={{ minHeight: '44px', minWidth: '44px' }}
            aria-label="Send reminder"
          >
            <BellIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {showModal && (
        <TaskModal
          task={item.task}
          onClose={() => setShowModal(false)}
          onUpdate={() => {
            setShowModal(false);
            // Trigger refresh
          }}
        />
      )}
    </>
  );
};
```

Add action handler in Overview component:
```jsx
const handleAttentionAction = async (action, taskId) => {
  try {
    if (action === 'reminder') {
      // Reuse existing WhatsApp service
      await sendTaskToWhatsApp(taskId, { reminder: true });
      Toast.success('Reminder sent!');
    }
  } catch (err) {
    Toast.error('Failed to send reminder');
  }
};
```

**Tests**:
- Frontend: `test_attention_card_view_button_opens_modal()`
- Frontend: `test_attention_card_call_button_creates_tel_link()`
- Frontend: `test_attention_card_reminder_button_sends_whatsapp()`
- Frontend: `test_attention_card_buttons_disabled_while_loading()`
- Manual QA: iPad + mobile Safari tap tests

**Regression**: `npm run lint`, `npm run build`

**Acceptance Criteria**:
- ✅ All buttons >= 44px touch target
- ✅ Call button opens phone dialer
- ✅ Reminder button sends WhatsApp (reusing existing service)
- ✅ View button opens TaskModal
- ✅ Buttons show loading/disabled states
- ✅ Haptic feedback on touch devices

> ✅ **Phase 3B exit criteria**: Overview tab is fully functional, navigation stable, no regressions in existing Project detail pages.

---

## Phase 3C — Validation, Accessibility, and Launch

### **Stage 3C.1: Integration & Contract Tests**

**Goal**: Ensure backend/frontend contracts stay in sync and Phase 1/2 flows still work.

**Implementation**:

**Backend Integration Tests**:

Add to `backend/test_integration.py`:
```python
def test_dashboard_summary_contract():
    """Verify summary endpoint returns expected JSON schema"""
    response = client.get('/api/dashboard/summary')
    assert response.status_code == 200
    
    data = response.json
    assert 'date' in data
    assert 'totals' in data
    assert 'projects' in data
    assert 'assignees' in data
    
    # Verify totals structure
    totals = data['totals']
    assert 'all' in totals
    assert 'done' in totals
    assert 'pending' in totals
    assert 'overdue' in totals
    assert 'completion_rate' in totals

def test_attention_endpoint_contract():
    """Verify attention endpoint returns expected JSON schema"""
    response = client.get('/api/dashboard/attention')
    assert response.status_code == 200
    
    data = response.json
    assert 'items' in data
    assert 'count' in data
    assert 'timestamp' in data

def test_dashboard_updates_reflect_task_changes():
    """Test that dashboard reflects task status changes"""
    # Create task
    task = create_test_task(status='pending')
    
    # Get initial summary
    summary1 = client.get('/api/dashboard/summary').json
    pending_before = summary1['totals']['pending']
    
    # Mark task done
    update_task_status(task['id'], 'done')
    
    # Get updated summary
    summary2 = client.get('/api/dashboard/summary').json
    pending_after = summary2['totals']['pending']
    
    assert pending_after == pending_before - 1
```

**Frontend Integration Tests** (Cypress):

Create `cypress/e2e/dashboard.cy.js`:
```javascript
describe('Dashboard Integration', () => {
  it('should update dashboard when task marked done', () => {
    // Create task via UI
    cy.visit('/projects');
    cy.get('[data-testid="create-task"]').click();
    cy.get('[data-testid="task-title"]').type('Test Task');
    cy.get('[data-testid="submit"]').click();
    
    // Navigate to overview
    cy.get('[data-testid="nav-overview"]').click();
    
    // Verify task in pending count
    cy.get('[data-testid="stat-pending"]').should('contain', '1');
    
    // Mark task done
    cy.visit('/projects');
    cy.get('[data-testid="task-card"]').first().click();
    cy.get('[data-testid="status-done"]').click();
    
    // Verify dashboard updated
    cy.get('[data-testid="nav-overview"]').click();
    cy.get('[data-testid="stat-done"]').should('contain', '1');
    cy.get('[data-testid="stat-pending"]').should('contain', '0');
  });
});
```

**Regression**: Full `pytest test_api.py`, full `npm test`

**Acceptance Criteria**:
- ✅ All contract tests pass
- ✅ Dashboard updates reflect real-time changes
- ✅ Phase 1 & 2 tests still pass
- ✅ No API breaking changes

---

### **Stage 3C.2: Responsive & Accessibility Polish**

**Goal**: Guarantee dashboard works on iPad + phone, respects touch targets, screen readers.

**Implementation**:

**Responsive Testing**:
- Test breakpoints: 375px (iPhone SE), 768px (iPad), 1024px (Desktop)
- Ensure grid layouts adapt correctly
- Verify no horizontal scroll on mobile

**Accessibility Improvements**:

Update `src/pages/Overview.jsx`:
```jsx
// Add proper heading hierarchy
<main role="main" aria-label="Dashboard overview">
  <h1 className="text-2xl font-bold mb-6">Overview</h1>
  
  <section aria-labelledby="totals-heading">
    <h2 id="totals-heading" className="sr-only">Task Totals</h2>
    {/* Stat cards */}
  </section>
  
  <section aria-labelledby="attention-heading">
    <h2 id="attention-heading" className="text-lg font-semibold mb-4">
      Needs Attention
    </h2>
    {/* Attention items */}
  </section>
</main>

// Add ARIA labels to interactive elements
<button
  aria-label={`Send reminder for task: ${item.task.title}`}
  aria-busy={sending}
  // ...
/>
```

**Performance Optimization**:
```jsx
// Lazy load non-critical sections
const ProjectStats = lazy(() => import('./components/ProjectStats'));

// Reduce animation complexity on low-end devices
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
```

**Tests**:
- Automated Lighthouse run (target: 90+ all categories)
- Jest axe test on Overview page
- Manual screen reader test (VoiceOver/TalkBack)

**Acceptance Criteria**:
- ✅ All touch targets >= 44px
- ✅ Proper ARIA labels on interactive elements
- ✅ Heading hierarchy correct (h1 → h2 → h3)
- ✅ Color contrast meets WCAG AA
- ✅ Keyboard navigation works
- ✅ Screen reader announces content correctly

---

### **Stage 3C.3: Manual QA & Release Checklist**

**Goal**: Run through owner-focused scripts before tagging release.

**Manual QA Checklist**:

- [ ] **Data Accuracy**
  - [ ] Create 5 projects with different colors
  - [ ] Add 20 tasks across projects with mixed statuses
  - [ ] Verify dashboard totals match actual counts
  - [ ] Check completion percentages calculate correctly

- [ ] **Attention Logic**
  - [ ] Create overdue task → verify appears in Needs Attention
  - [ ] Send WhatsApp without response → verify flags after 2h
  - [ ] Mark attention task done → verify removes from list
  - [ ] Verify priority sorting (overdue before no-response)

- [ ] **Navigation**
  - [ ] Tap each bottom nav tab → verify correct page loads
  - [ ] Verify active tab highlights correctly
  - [ ] Test back button behavior
  - [ ] Verify deep links work (e.g., /projects/:id)

- [ ] **Interactive Actions**
  - [ ] Tap "View" → verify TaskModal opens
  - [ ] Tap "Call" → verify phone dialer opens
  - [ ] Tap "Send Reminder" → verify WhatsApp sent
  - [ ] Verify buttons disabled during loading

- [ ] **Responsive Design**
  - [ ] Test on iPhone SE (375px)
  - [ ] Test on iPad (768px)
  - [ ] Test on desktop (1024px+)
  - [ ] Rotate device → verify layout adapts

- [ ] **Accessibility**
  - [ ] Navigate with keyboard only
  - [ ] Test with VoiceOver (iOS) or TalkBack (Android)
  - [ ] Verify all buttons have ARIA labels
  - [ ] Check color contrast

- [ ] **Performance**
  - [ ] Dashboard loads in < 2s on 3G
  - [ ] No memory leaks after 30min usage
  - [ ] Smooth scrolling with 50+ tasks
  - [ ] No console errors

- [ ] **Regression**
  - [ ] Create task via form → still works
  - [ ] Activity feed updates → still works
  - [ ] WhatsApp integration → still works
  - [ ] File uploads → still works

**Final Steps**:
```bash
# Run all tests
npm test
pytest test_api.py -v
pytest test_integration.py -v

# Build production
npm run build

# Check bundle size
npm run analyze

# Tag release
git tag v3.0.0
git push origin v3.0.0
```

**Rollback Plan**:
If issues found in production:
1. Set feature flag `ENABLE_DASHBOARD_V3=false`
2. Deploy previous version
3. Investigate issues
4. Fix and re-deploy

**Acceptance Criteria**:
- ✅ All manual tests pass
- ✅ No critical bugs found
- ✅ Performance targets met
- ✅ Documentation updated (README, CHANGELOG)

> ✅ **Phase 3C exit criteria**: All automated tests green, manual QA checklist signed, documentation updated (README dashboard section + release notes).

---

## Implementation Guardrails (For LLM + Humans)

1. **Reuse existing services**: do not duplicate task/project lookups—import utilities from `services/` or `context/`
2. **Minimal diffs**: prefer small focused PRs per stage; no large refactors
3. **Testing discipline**: every stage must add or update tests before moving on; always re-run suites mentioned above
4. **Mobile-first UI**: prioritize iPad/phone breakpoints, ensure touch-friendly buttons, avoid desktop-only patterns
5. **Configuration over customization**: label overrides via config files, not DB migrations, so feature remains optional
6. **LLM-friendly tasks**: keep stage descriptions atomic (one file cluster per stage) so automated agents can follow without context switching
7. **Error handling**: every API call must handle failures gracefully with user-friendly messages
8. **Performance**: dashboard must load in <2s on 3G, queries must complete in <200ms
9. **Accessibility**: WCAG 2.1 AA compliance, keyboard navigation, screen reader support
10. **Backward compatibility**: never break existing localStorage data or API contracts

---

## Risk Areas & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation with large datasets | High | Add pagination, implement caching, lazy load data |
| Breaking existing navigation flow | High | Keep old routes intact, add feature flag for new nav |
| localStorage schema conflicts | Medium | Version localStorage data, add migration helpers |
| Cache invalidation issues | Medium | Use time-based expiry, add manual refresh option |
| Mobile Safari touch issues | Medium | Test on real devices, add touch-action CSS |
| Attention logic false positives | Low | Make rules configurable, add dismiss/snooze |

---

## Rollout Plan

1. **Stage-by-stage deployment**: Each stage deployed to staging first
2. **Feature flag**: `ENABLE_DASHBOARD_V3` in config to toggle new UI
3. **A/B testing**: 10% users → 50% → 100% over 2 weeks
4. **Monitoring**: Track dashboard load times, API response times, error rates
5. **Rollback plan**: Feature flag off reverts to old navigation
6. **User feedback**: In-app survey after 1 week of usage

---

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

---

## Next Steps After Phase 3

- **Phase 4**: Real-time updates via WebSockets
- **Phase 5**: Advanced analytics and reporting
- **Phase 6**: Mobile app (React Native)

Following this plan ensures we deliver a production-grade Owner Dashboard that small business owners can adopt immediately, while keeping the codebase clean, test-covered, and easy for LLM copilots to extend.
