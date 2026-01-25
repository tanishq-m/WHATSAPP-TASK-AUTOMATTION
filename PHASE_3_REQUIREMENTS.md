# Phase 3: Feature Requirements Documentation

> **Document Purpose**: This document provides comprehensive specifications for an LLM to implement Phase 3 features. It includes detailed requirements, UI/UX guidelines, existing code patterns to follow, and implementation steps.

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Design Principles](#design-principles)
3. [Technical Context](#technical-context)
4. [Feature Specifications](#feature-specifications)
   - [P3-1: Task Filtering by Team Member](#p3-1-task-filtering-by-team-member)
   - [P3-2: Task Sorting](#p3-2-task-sorting)
   - [P3-3: Delete Task from GUI](#p3-3-delete-task-from-gui)
   - [P3-4: Delete Project from GUI](#p3-4-delete-project-from-gui)
   - [P3-5: Edit Project Improvements](#p3-5-edit-project-improvements)
   - [P3-6: Mandatory Dates Validation](#p3-6-mandatory-dates-validation)
   - [P3-7: Task Stage Duration Tracking](#p3-7-task-stage-duration-tracking)
   - [P3-8: CSV Bulk Import for Tasks](#p3-8-csv-bulk-import-for-tasks)
   - [P3-9: Team Member Count Display](#p3-9-team-member-count-display)
5. [Testing Requirements](#testing-requirements)
6. [Priority Order](#priority-order)

---

## Executive Summary

### Project Overview
- **Application**: WhatsApp Task Manager - An admin dashboard for managing projects, tasks, and team members with WhatsApp integration
- **Frontend**: React 18 + Vite + Tailwind CSS + @dnd-kit (drag-and-drop)
- **Backend**: Flask 3.0 + SQLite
- **Testing**: Vitest (75 tests) + pytest (34 tests)

### Target Users
- **Primary Audience**: Non-technical managers and administrators (40+ years old)
- **Device Priority**: Mobile/iPad first, then desktop
- **Interaction**: Touch-responsive, tap-friendly targets

---

## Design Principles

### 1. Mobile-First, Touch-Responsive Design

```
CRITICAL: All new UI elements MUST follow these guidelines:

- Minimum touch target: 44x44px (Apple Human Interface Guidelines)
- Use Tailwind class "tap-target" for interactive elements
- Buttons: Full-width on mobile (fullWidth prop), side-by-side on desktop
- Spacing: Generous padding (p-4 minimum for touch targets)
- Font sizes: Minimum 16px to prevent iOS zoom on input focus
```

### 2. Simple, Clear UI

```
- Use clear, action-oriented labels (e.g., "Delete Task" not just "Delete")
- Confirmation dialogs for destructive actions (delete)
- Visual feedback on interactions (loading states, success messages)
- Icons paired with text labels for clarity
- Error messages in plain language
```

### 3. Existing Tailwind Classes to Use

```css
/* Cards and containers */
.card { @apply bg-white rounded-lg shadow-sm border border-gray-200; }

/* Buttons (use Button component) */
- variant="primary" (blue, primary actions)
- variant="secondary" (gray, cancel/back)
- variant="danger" (red, delete actions)

/* Animations */
.animate-fade-in { opacity animation }
.animate-slide-in { slide up animation }
.transition-smooth { all transitions 200ms ease }

/* Touch targets */
.tap-target { min-height: 44px; min-width: 44px; }
```

---

## Technical Context

### Key File References

| Purpose | File | Notes |
|---------|------|-------|
| State Management | `src/context/AppContext.jsx` | All CRUD operations, API calls |
| API Service | `src/services/api.service.js` | toCamelCase transforms |
| Validators | `src/utils/validators.js` | validateProject, validateTask |
| Helpers | `src/utils/helpers.js` | formatDate, groupTasksByStatus |
| Constants | `src/utils/constants.js` | STATUS enum |
| Modal Pattern | `src/components/common/Modal.jsx` | Reusable modal |
| Button Pattern | `src/components/common/Button.jsx` | variants: primary, secondary, danger |

### ID and Field Conventions

```javascript
// Task ID: Use taskId for API calls
await apiService.updateTask(task.taskId, updates)

// Status values (use constants)
import { STATUS } from '../utils/constants'
STATUS.UNASSIGNED          // 'unassigned'
STATUS.IN_PROGRESS         // 'in_progress'
STATUS.PENDING_VERIFICATION // 'pending_verification'
STATUS.COMPLETED           // 'completed'

// Field mapping: Backend → Frontend
employee_id → employeeId → assignedTo
task_id → taskId
project_id → projectId
```

### API Patterns

```javascript
// GET request pattern
const response = await fetch(`${API_BASE_URL}/endpoint`)
const result = await response.json()
if (result.success) return result.data

// POST/PUT/DELETE pattern
const response = await fetch(`${API_BASE_URL}/endpoint`, {
  method: 'POST', // or 'PUT', 'DELETE'
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})

// Error handling in AppContext
try {
  const result = await apiService.operation()
  showToast('Success message', 'success')
} catch (error) {
  console.error(error)
  showToast('Error message', 'error')
}
```

---

## Feature Specifications

---

### P3-1: Task Filtering by Team Member

**Priority**: High | **Complexity**: Medium

#### Description
Add ability to filter tasks on the Kanban board by assigned team member, similar to Jira's filter functionality.

#### Expected Behavior
1. Filter dropdown appears above the Kanban columns
2. User can select "All Members" (default) or a specific team member
3. When a member is selected, only their tasks appear in the columns
4. Filter persists during drag-and-drop operations
5. Clear visual indication of active filter

#### UI/UX Requirements

```
+--------------------------------------------------+
|  [👤 Filter by: All Members ▼]  [Sort by... ▼]   |  ← Mobile: Stack vertically
+--------------------------------------------------+
|  UNASSIGNED | IN PROGRESS | PENDING | COMPLETED  |
+--------------------------------------------------+

Mobile Filter Modal (on tap):
+---------------------------+
|  Filter by Team Member    |
+---------------------------+
|  ○ All Members            |  ← Radio button style
|  ○ John Smith             |
|  ○ Jane Doe               |
|  ○ Bob Wilson             |
+---------------------------+
|     [Apply Filter]        |  ← Full-width button
+---------------------------+
```

#### Implementation Steps

1. **Add filter state to `KanbanBoard.jsx`**:
```jsx
const [filterEmployee, setFilterEmployee] = useState(null)

// Apply filter before grouping
const filteredTasks = filterEmployee 
  ? tasks.filter(t => t.assignedTo === filterEmployee)
  : tasks

const groupedTasks = groupTasksByStatus(filteredTasks)
```

2. **Create `FilterDropdown.jsx` component**:
   - Location: `src/components/tasks/FilterDropdown.jsx`
   - Props: `employees`, `selectedEmployee`, `onSelect`
   - Mobile: Use modal/bottom sheet for selection
   - Desktop: Use dropdown

3. **Update `KanbanBoard.jsx` to include filter UI**:
```jsx
<div className="flex flex-col sm:flex-row gap-3 mb-4">
  <FilterDropdown 
    employees={employees}
    selectedEmployee={filterEmployee}
    onSelect={setFilterEmployee}
  />
</div>
```

#### Existing Patterns to Follow

- Reference: `src/components/common/Select.jsx` for dropdown styling
- Reference: `src/components/employees/EmployeeCard.jsx` for employee display
- Use `getEmployeeById` from AppContext for employee lookup

#### Test Cases

```javascript
describe('P3-1: Task Filtering', () => {
  it('shows all tasks when no filter is applied')
  it('filters tasks by selected employee')
  it('shows empty columns when no tasks match filter')
  it('persists filter when task is dragged')
  it('shows "All Members" option to clear filter')
})
```

---

### P3-2: Task Sorting

**Priority**: High | **Complexity**: Medium

#### Description
Add ability to sort tasks within Kanban columns by due date, priority, or assigned team member.

#### Expected Behavior
1. Sort dropdown appears next to filter dropdown
2. Sort options: Due Date (earliest first), Due Date (latest first), Priority (high to low), Assigned To (A-Z)
3. Sorting applies to all columns simultaneously
4. Sorting persists during session

#### UI/UX Requirements

```
Sort Dropdown Options:
+---------------------------+
|  Sort Tasks By            |
+---------------------------+
|  ▲ Due Date (Earliest)    |  ← Arrow indicates direction
|  ▼ Due Date (Latest)      |
|  ★ Priority (High → Low)  |
|  👤 Assigned To (A-Z)     |
+---------------------------+
```

#### Implementation Steps

1. **Add sort state and function to `KanbanBoard.jsx`**:
```jsx
const [sortBy, setSortBy] = useState('priority') // default

const sortTasks = (tasksArray) => {
  switch (sortBy) {
    case 'dueDate-asc':
      return [...tasksArray].sort((a, b) => 
        new Date(a.dueDate) - new Date(b.dueDate))
    case 'dueDate-desc':
      return [...tasksArray].sort((a, b) => 
        new Date(b.dueDate) - new Date(a.dueDate))
    case 'priority':
      return sortByPriority(tasksArray) // from helpers.js
    case 'assignedTo':
      return [...tasksArray].sort((a, b) => 
        (getEmployeeById(a.assignedTo)?.name || '').localeCompare(
          getEmployeeById(b.assignedTo)?.name || ''))
    default:
      return tasksArray
  }
}

// Apply in columns
const columns = [
  { id: STATUS.UNASSIGNED, tasks: sortTasks(groupedTasks[STATUS.UNASSIGNED] || []) },
  // ... etc
]
```

2. **Create `SortDropdown.jsx` component**:
   - Location: `src/components/tasks/SortDropdown.jsx`
   - Props: `sortBy`, `onSortChange`
   - Use icons to indicate sort direction

3. **Add helper function to `helpers.js`**:
```javascript
export const sortTasksByDueDate = (tasks, ascending = true) => {
  return [...tasks].sort((a, b) => {
    const dateA = a.dueDate ? new Date(a.dueDate) : new Date('9999-12-31')
    const dateB = b.dueDate ? new Date(b.dueDate) : new Date('9999-12-31')
    return ascending ? dateA - dateB : dateB - dateA
  })
}
```

#### Test Cases

```javascript
describe('P3-2: Task Sorting', () => {
  it('sorts by priority by default')
  it('sorts by due date ascending')
  it('sorts by due date descending')
  it('sorts by assigned employee name')
  it('handles tasks without due dates')
  it('handles unassigned tasks when sorting by employee')
})
```

---

### P3-3: Delete Task from GUI

**Priority**: Critical | **Complexity**: Low

#### Description
Add ability to delete a task directly from the admin dashboard with confirmation.

#### Expected Behavior
1. Delete button visible on TaskCard (trash icon)
2. Delete option in TaskModal
3. Confirmation dialog before deletion
4. Task removed from UI and database
5. Success toast shown

#### UI/UX Requirements

```
TaskCard Delete Button:
+---------------------------+
| [High] Task Title         |
|                      [🗑️] |  ← Small trash icon, top-right
| 👤 John Smith             |
| 📅 Dec 15, 2024           |
+---------------------------+

Confirmation Dialog (Critical for touch):
+----------------------------------+
|  ⚠️  Delete Task?                |
+----------------------------------+
|  Are you sure you want to        |
|  delete "Task Title"?            |
|                                  |
|  This action cannot be undone.   |
+----------------------------------+
|  [Cancel]    [Delete Task]       |  ← Delete in red
+----------------------------------+
```

#### Implementation Steps

1. **Add `deleteTask` to AppContext.jsx**:
```jsx
const deleteTask = async (taskId) => {
  try {
    await apiService.deleteTask(taskId)
    setTasks(prev => prev.filter(t => t.taskId !== taskId))
    showToast('Task deleted successfully', 'success')
  } catch (error) {
    console.error('Failed to delete task:', error)
    showToast('Failed to delete task', 'error')
  }
}
```

2. **Add `deleteTask` to api.service.js**:
```javascript
export const deleteTask = async (taskId) => {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: 'DELETE'
  })
  const result = await response.json()
  if (!result.success) throw new Error(result.error)
  return result
}
```

3. **Add backend endpoint in `backend/app.py`**:
```python
@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        database.delete_task(task_id)
        return jsonify({'success': True, 'message': 'Task deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

4. **Create `ConfirmDialog.jsx` component**:
   - Location: `src/components/common/ConfirmDialog.jsx`
   - Props: `isOpen`, `onClose`, `onConfirm`, `title`, `message`, `confirmText`, `variant`
   - Use Modal component as base

5. **Update `TaskCard.jsx`** to add delete button:
```jsx
const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

// Add delete button
<button
  onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(true) }}
  className="p-2 hover:bg-red-50 rounded-lg transition-smooth tap-target"
  title="Delete task"
>
  <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
</button>

// Add ConfirmDialog
<ConfirmDialog
  isOpen={showDeleteConfirm}
  onClose={() => setShowDeleteConfirm(false)}
  onConfirm={() => deleteTask(task.taskId)}
  title="Delete Task?"
  message={`Are you sure you want to delete "${task.title}"? This action cannot be undone.`}
  confirmText="Delete Task"
  variant="danger"
/>
```

#### Test Cases

```javascript
describe('P3-3: Delete Task', () => {
  it('shows delete button on TaskCard')
  it('opens confirmation dialog on delete click')
  it('cancels deletion when Cancel is clicked')
  it('deletes task when confirmed')
  it('shows success toast after deletion')
  it('removes task from Kanban columns')
})
```

---

### P3-4: Delete Project from GUI

**Priority**: Critical | **Complexity**: Low

#### Description
Add ability to delete a project with all its associated tasks, with clear warning about task deletion.

#### Expected Behavior
1. Delete button on ProjectCard (Dashboard)
2. Delete button on ProjectDetail page
3. Confirmation dialog showing task count
4. Deletes project and ALL associated tasks
5. Redirects to Dashboard after deletion

#### UI/UX Requirements

```
Delete Confirmation (with warning):
+--------------------------------------+
|  ⚠️  Delete Project?                  |
+--------------------------------------+
|  Are you sure you want to delete     |
|  "Website Redesign"?                 |
|                                      |
|  ⚠️  WARNING: This will also delete  |
|  12 tasks associated with this       |
|  project.                            |
|                                      |
|  This action cannot be undone.       |
+--------------------------------------+
|  [Cancel]       [Delete Project]     |
+--------------------------------------+
```

#### Implementation Steps

1. **Add `deleteProject` to AppContext.jsx**:
```jsx
const deleteProject = async (projectId) => {
  try {
    await apiService.deleteProject(projectId)
    setProjects(prev => prev.filter(p => p.id !== projectId))
    setTasks(prev => prev.filter(t => t.projectId !== projectId))
    showToast('Project deleted successfully', 'success')
  } catch (error) {
    console.error('Failed to delete project:', error)
    showToast('Failed to delete project', 'error')
  }
}
```

2. **Add `deleteProject` to api.service.js**:
```javascript
export const deleteProject = async (projectId) => {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
    method: 'DELETE'
  })
  const result = await response.json()
  if (!result.success) throw new Error(result.error)
  return result
}
```

3. **Add backend endpoint in `backend/app.py`**:
```python
@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        # Delete all tasks for this project first
        database.delete_tasks_by_project(project_id)
        # Then delete the project
        database.delete_project(project_id)
        return jsonify({'success': True, 'message': 'Project and tasks deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

4. **Update `ProjectCard.jsx`** to add delete button:
```jsx
// Add three-dot menu or delete button
<button
  onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(true) }}
  className="p-2 hover:bg-red-50 rounded-lg tap-target"
>
  <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
</button>
```

5. **Update `ProjectDetail.jsx`** to add delete button:
```jsx
// Add delete button next to edit button
<Button
  variant="danger"
  onClick={() => setShowDeleteConfirm(true)}
  icon={<Trash2 className="w-4 h-4" />}
>
  Delete
</Button>
```

#### Test Cases

```javascript
describe('P3-4: Delete Project', () => {
  it('shows delete button on ProjectCard')
  it('shows delete button on ProjectDetail page')
  it('shows task count in confirmation dialog')
  it('deletes project and all tasks when confirmed')
  it('redirects to Dashboard after deletion')
  it('shows success toast after deletion')
})
```

---

### P3-5: Edit Project Improvements

**Priority**: Medium | **Complexity**: Low

#### Description
Ensure edit project functionality works consistently from both Dashboard and ProjectDetail page, with all existing data properly pre-filled.

#### Expected Behavior
1. Edit button available on ProjectCard (Dashboard)
2. Edit button available on ProjectDetail page ✓ (already implemented)
3. All fields pre-filled with current values
4. Team member selections preserved
5. Success toast on save

#### Implementation Steps

1. **Update `ProjectCard.jsx`** to add edit button:
```jsx
const [showEditModal, setShowEditModal] = useState(false)

// Add edit button
<button
  onClick={(e) => { e.stopPropagation(); setShowEditModal(true) }}
  className="p-2 hover:bg-gray-100 rounded-lg tap-target"
>
  <Pencil className="w-4 h-4 text-gray-500" />
</button>

// Add modal
<CreateProjectModal
  isOpen={showEditModal}
  onClose={() => setShowEditModal(false)}
  project={project}
/>
```

2. **Verify `CreateProjectModal.jsx` pre-fill logic** (already implemented):
```jsx
useEffect(() => {
  if (project) {
    setFormData({
      name: project.name || '',
      description: project.description || '',
      startDate: project.startDate || '',
      endDate: project.endDate || '',
      assignedEmployees: project.assignedEmployees || []
    })
  }
}, [project])
```

#### Test Cases

```javascript
describe('P3-5: Edit Project', () => {
  it('shows edit button on ProjectCard')
  it('opens CreateProjectModal in edit mode')
  it('pre-fills all project fields')
  it('preserves team member selections')
  it('updates project on save')
  it('shows success toast')
})
```

---

### P3-6: Optional Dates Validation

**Priority**: Medium | **Complexity**: Low

#### Description
Make start date and end date optional for projects while maintaining proper validation when dates are provided (end date must be after start date if both are set).

#### Current State
- Validators currently require dates (validateProject in validators.js)
- DatePicker has `required` prop
- Need to update validation to make dates optional

#### Expected Behavior
1. Projects can be created without start date and/or end date
2. If both dates are provided, validate that end date is after start date
3. No visual "required" indicator on date fields
4. Form can be submitted with empty date fields

#### Implementation Steps

1. **Update `validateProject` in `validators.js`**:
```jsx
export const validateProject = (project) => {
  const errors = {}
  
  if (!project.name || project.name.trim() === '') {
    errors.name = 'Project name is required'
  }
  
  // REMOVED: Start date and end date required validation
  // Only validate date relationship if BOTH dates are provided
  if (project.startDate && project.endDate) {
    if (new Date(project.startDate) > new Date(project.endDate)) {
      errors.endDate = 'End date must be after start date'
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}
```

2. **Update `CreateProjectModal.jsx` date fields**:
```jsx
// Remove required prop from DatePicker components
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <DatePicker
    label="Start Date (Optional)"  // Update label
    value={formData.startDate}
    onChange={(e) => handleChange('startDate', e.target.value)}
    error={errors.startDate}
    // required prop REMOVED
  />

  <DatePicker
    label="End Date (Optional)"  // Update label
    value={formData.endDate}
    onChange={(e) => handleChange('endDate', e.target.value)}
    min={formData.startDate}
    error={errors.endDate}
    // required prop REMOVED
  />
</div>
```

3. **Verify `DatePicker.jsx` handles optional fields**:
```jsx
// Should allow empty values
<input
  type="date"
  value={value || ''}  // Empty string for null/undefined
  onChange={onChange}
  className="input-field"
  // required prop should be optional
/>
```

#### Test Cases

```javascript
describe('P3-6: Optional Dates', () => {
  it('allows project creation without start date')
  it('allows project creation without end date')
  it('allows project creation without any dates')
  it('validates end date is after start date when both provided')
  it('shows error when end date is before start date')
  it('does not show required indicator on date fields')
  it('allows form submission with empty date fields')
})
```

---

### P3-7: Task Stage Duration Tracking

**Priority**: Medium | **Complexity**: Medium

#### Description
Track how long a task has been in each stage (like Jira's time tracking). Display "X days in this stage" on the task card.

#### Expected Behavior
1. Track timestamp when status changes
2. Display "3 days in this stage" on TaskCard
3. Store history of stage transitions (optional for Phase 3)

#### UI/UX Requirements

```
TaskCard with Duration:
+---------------------------+
| [High] Task Title         |
| 👤 John Smith             |
| 📅 Dec 15, 2024           |
| ⏱️ 3 days in this stage   |  ← New element
+---------------------------+
```

#### Database Changes

1. **Add `status_changed_at` column to tasks table**:
```python
# In database.py
CREATE TABLE IF NOT EXISTS tasks (
    ...
    status_changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    ...
)
```

2. **Update status change logic**:
```python
def update_task(task_id, updates, source='admin'):
    if 'status' in updates:
        updates['status_changed_at'] = datetime.utcnow().isoformat()
    # ... rest of update logic
```

#### Implementation Steps

1. **Add migration for existing tasks**:
```python
# In database.py
def migrate_add_status_changed_at():
    cursor.execute('''
        ALTER TABLE tasks ADD COLUMN status_changed_at TEXT
    ''')
    # Set current timestamp for existing tasks
    cursor.execute('''
        UPDATE tasks SET status_changed_at = datetime('now') 
        WHERE status_changed_at IS NULL
    ''')
```

2. **Add helper function**:
```javascript
// In helpers.js
export const getDaysInStage = (statusChangedAt) => {
  if (!statusChangedAt) return 0
  const changedDate = new Date(statusChangedAt)
  const now = new Date()
  const diffTime = Math.abs(now - changedDate)
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}
```

3. **Update `TaskCard.jsx`**:
```jsx
import { getDaysInStage } from '../../utils/helpers'

const daysInStage = getDaysInStage(task.statusChangedAt)

// Add to card
{daysInStage > 0 && (
  <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
    <Clock className="w-3 h-3" />
    <span>{daysInStage} day{daysInStage !== 1 ? 's' : ''} in this stage</span>
  </div>
)}
```

#### Test Cases

```javascript
describe('P3-7: Stage Duration', () => {
  it('displays days in current stage')
  it('updates status_changed_at when status changes')
  it('resets counter when task moves to new stage')
  it('handles tasks without status_changed_at')
})
```

---

### P3-8: CSV Bulk Import for Tasks

**Priority**: Low | **Complexity**: High

#### Description
Allow bulk import of tasks via CSV file upload with validation and preview.

#### Expected Behavior
1. Upload button on ProjectDetail page
2. CSV format: title, description, assignedTo (employee name/email), dueDate, priority
3. Preview imported tasks before confirmation
4. Show validation errors for each row
5. Batch create tasks on confirm

#### UI/UX Requirements

```
Upload Button:
+------------------------------+
| [📤 Import Tasks from CSV]   |
+------------------------------+

Import Modal:
+--------------------------------------+
|  Import Tasks from CSV               |
+--------------------------------------+
|  [📁 Choose File] tasks.csv          |
|                                      |
|  Preview (5 tasks found):            |
|  +--------------------------------+  |
|  | ✓ Task 1 | John | High | 12/15 |  |
|  | ✓ Task 2 | Jane | Med  | 12/16 |  |
|  | ⚠ Task 3 | Bob  | ??? | Error |  |  ← Invalid priority
|  +--------------------------------+  |
|                                      |
|  2 errors found. Fix CSV and retry.  |
+--------------------------------------+
|  [Cancel]        [Import 5 Tasks]    |
+--------------------------------------+
```

#### CSV Format

```csv
title,description,assignedTo,dueDate,priority
"Website Homepage","Design the main homepage","john@company.com","2024-12-15","high"
"Mobile Menu","Create responsive menu","jane@company.com","2024-12-16","medium"
```

#### Implementation Steps

1. **Create `CSVImportModal.jsx`**:
   - Location: `src/components/tasks/CSVImportModal.jsx`
   - File input for CSV
   - Parse CSV and validate
   - Preview table with error highlighting
   - Import button

2. **Add CSV parsing helper**:
```javascript
// In helpers.js
export const parseCSV = (csvText) => {
  const lines = csvText.split('\n')
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
  
  return lines.slice(1).filter(line => line.trim()).map((line, index) => {
    const values = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''))
    const row = {}
    headers.forEach((header, i) => {
      row[header] = values[i] || ''
    })
    row._rowNumber = index + 2 // 1-indexed, skip header
    return row
  })
}

export const validateCSVRow = (row, employees) => {
  const errors = []
  
  if (!row.title) errors.push('Title is required')
  if (row.priority && !['high', 'medium', 'low'].includes(row.priority.toLowerCase())) {
    errors.push('Invalid priority (must be high, medium, or low)')
  }
  if (row.assignedto) {
    const employee = employees.find(e => 
      e.email === row.assignedto || e.name.toLowerCase() === row.assignedto.toLowerCase()
    )
    if (!employee) errors.push(`Employee "${row.assignedto}" not found`)
  }
  
  return { isValid: errors.length === 0, errors }
}
```

3. **Add bulk create API**:
```javascript
// In api.service.js
export const bulkCreateTasks = async (tasks) => {
  const response = await fetch(`${API_BASE_URL}/tasks/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tasks })
  })
  const result = await response.json()
  if (!result.success) throw new Error(result.error)
  return result.data
}
```

4. **Add backend endpoint**:
```python
@app.route('/api/tasks/bulk', methods=['POST'])
def bulk_create_tasks():
    data = request.get_json()
    tasks = data.get('tasks', [])
    
    created_tasks = []
    for task_data in tasks:
        task = database.create_task(task_data)
        created_tasks.append(task)
    
    return jsonify({'success': True, 'data': created_tasks})
```

#### Test Cases

```javascript
describe('P3-8: CSV Import', () => {
  it('opens import modal from ProjectDetail')
  it('parses CSV file correctly')
  it('validates required fields')
  it('matches employee by email or name')
  it('shows preview with errors highlighted')
  it('creates tasks on confirmation')
  it('shows success message with count')
})
```

---

### P3-9: Team Member Count Display

**Priority**: Low | **Complexity**: Low

#### Description
Show the number of team members assigned when editing a project.

#### Expected Behavior
1. In edit mode, show "X team members assigned"
2. Count updates as members are added/removed
3. Clear visual feedback

#### UI/UX Requirements

```
Edit Project Modal - Team Members Section:
+--------------------------------------+
| Assign Team Members                  |
| 3 team members currently assigned    |  ← New text
+--------------------------------------+
| [✓] John Smith - Developer           |
| [✓] Jane Doe - Designer              |
| [✓] Bob Wilson - Manager             |
| [ ] Alice Brown - QA                 |
+--------------------------------------+
```

#### Implementation Steps

1. **Update `CreateProjectModal.jsx`**:
```jsx
<div>
  <label className="label">Assign Team Members</label>
  {isEditing && formData.assignedEmployees.length > 0 && (
    <p className="text-sm text-gray-600 mb-2">
      {formData.assignedEmployees.length} team member{formData.assignedEmployees.length !== 1 ? 's' : ''} currently assigned
    </p>
  )}
  <div className="space-y-2 mt-2">
    {/* ... employee checkboxes ... */}
  </div>
</div>
```

#### Test Cases

```javascript
describe('P3-9: Team Member Count', () => {
  it('shows member count in edit mode')
  it('updates count when members are toggled')
  it('does not show count in create mode')
  it('handles singular/plural grammar')
})
```

---

## Testing Requirements

### Test File Locations

- Frontend tests: `src/**/*.test.jsx` (Vitest)
- Backend tests: `backend/tests/` (pytest)

### Running Tests

```bash
# Frontend tests
npm test

# Backend tests
cd backend && python -m pytest tests/ -v
```

### Test Patterns to Follow

```javascript
// Frontend (Vitest + React Testing Library)
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

describe('ComponentName', () => {
  it('should render correctly', () => {
    render(<Component />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
  
  it('should handle user interaction', async () => {
    const mockFn = vi.fn()
    render(<Component onClick={mockFn} />)
    fireEvent.click(screen.getByRole('button'))
    expect(mockFn).toHaveBeenCalled()
  })
})
```

```python
# Backend (pytest)
def test_endpoint_name(client):
    response = client.get('/api/endpoint')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
```

---

## Priority Order

### Phase 3A: Core Functionality (Implement First)
1. **P3-3**: Delete Task from GUI
2. **P3-4**: Delete Project from GUI
3. **P3-1**: Task Filtering by Member
4. **P3-2**: Task Sorting

### Phase 3B: UX Improvements
5. **P3-5**: Edit Project Improvements
6. **P3-6**: Mandatory Dates Validation
7. **P3-9**: Team Member Count Display

### Phase 3C: Advanced Features
8. **P3-7**: Task Stage Duration Tracking
9. **P3-8**: CSV Bulk Import for Tasks

---

## Appendix: Component Reference

### Button Component Usage

```jsx
import Button from '../common/Button'

<Button variant="primary">Save</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="danger">Delete</Button>
<Button variant="primary" fullWidth>Full Width on Mobile</Button>
<Button icon={<Plus />}>Add Task</Button>
```

### Modal Component Usage

```jsx
import Modal from '../common/Modal'

<Modal 
  isOpen={isOpen} 
  onClose={onClose} 
  title="Modal Title" 
  size="md"  // sm, md, lg, xl
>
  {/* Content */}
</Modal>
```

### Toast Notifications

```jsx
const { showToast } = useApp()

showToast('Success message', 'success')
showToast('Error message', 'error')
showToast('Warning message', 'warning')
showToast('Info message', 'info')
```

---

*Document Version: 1.0*
*Last Updated: Phase 2 Completion*
*Total Current Tests: 109 (75 frontend + 34 backend)*
