# Phase 2 Requirements & Enhancement Documentation
## WhatsApp Task Manager - Post-MVP Improvements

**Document Version:** 1.1  
**Created:** January 24, 2026  
**Last Updated:** January 25, 2026  
**Status:** In Progress (6/8 Issues Complete)  
**Purpose:** Comprehensive documentation of identified issues and solutions for Phase 2 development

---

## 📋 Executive Summary

Phase 1 (MVP) has been successfully completed with:
- ✅ Flask backend with SQLite database
- ✅ React frontend with Kanban board
- ✅ WhatsApp integration via Kapso API
- ✅ Interactive buttons for task status collection
- ✅ Webhook-based response handling
- ✅ 77 passing tests (33 backend + 44 frontend)

### Phase 2 Progress

**Completed Issues (8/8):** ✅ **ALL ISSUES COMPLETE!**
- ✅ Issue #1: Drag-and-drop ID mismatch (4 files, 3 tests)
- ✅ Issue #9: Field mapping for assignedTo/employeeId (1 file, 3 tests)
- ✅ Issue #2: Optional fields validation (3 files, 6 tests)
- ✅ Issue #3: Kanban status rename (6 files, 3 tests + migration)
- ✅ Issue #5: Enhanced project statistics (3 files, 3 tests)
- ✅ Issue #6: Visual feedback for drag-and-drop (2 files, 4 tests)
- ✅ Issue #8: Update source separation (3 files, 4 tests + documentation)
- ✅ Issue #7: Edit project functionality (3 files, 5 tests)

**Deferred Issues:**
- ⏸️ Issue #4: Create & Send to WhatsApp button (deferred by user request)

**Test Suite Status:**
- Frontend: 75 tests passing (Vitest)
- Backend: 33 tests passing (pytest)
- Total: 108 tests passing

**Phase 2 Status:** ✅ **COMPLETE** (All planned issues resolved)

Phase 2 focuses on:
1. **Bug Fixes** - Critical issues affecting usability (Issue #1, #9)
2. **UX Improvements** - Better workflow for admins (Issues #2, #3, #4, #7)
3. **Feature Enhancements** - New functionality (Issues #5, #6)
4. **Architecture** - Clean separation of concerns (Issue #8)
5. **Code Quality** - Modular, maintainable architecture

---

## 🚨 CRITICAL ISSUES (Must Fix)

---

### Issue #1: Task Disappears After Drag-and-Drop (Page Refresh Bug)

**Severity:** 🔴 Critical  
**Component:** Frontend - KanbanBoard.jsx, AppContext.jsx  
**User Impact:** Tasks disappear completely when dragging to "Completed" column

#### Current Behavior
1. User drags task from "Pending Verification" to "Completed" column
2. Page appears to refresh/reload
3. All tasks disappear from the Kanban board
4. User cannot see any tasks

#### Root Cause Analysis
The issue has two parts:

**Part A: ID Mismatch**
- `KanbanBoard.jsx` uses `task.id` (internal frontend ID)
- `updateTask` API expects `task.taskId` (database task_id like "task_123")
- The SortableTaskCard uses `{ id: task.id }` for drag-and-drop
- When calling `updateTask(taskId, ...)`, it passes `task.id` instead of `task.taskId`

```javascript
// KanbanBoard.jsx - Line 51-53 (CURRENT - BROKEN)
const task = tasks.find(t => t.id === taskId)  // Finds by internal id
if (task && task.status !== newStatus) {
  updateTask(taskId, { status: newStatus })    // Passes internal id, not task_id!
}
```

**Part B: Data Refresh Issue**
- After `updateTask` call, `AppContext.jsx` calls `loadData()` or refreshes tasks
- If the API call fails (404 because wrong ID), the error handling may not preserve state
- The state gets cleared, showing no tasks

#### Solution

**Step 1: Normalize Task ID Usage**
Decide on a single ID field. Recommendation: Use `taskId` consistently.

```javascript
// Option A: Keep both IDs, use taskId for API calls
// In toCamelCase transformer, ensure both exist:
// task.id = task.taskId (make them the same)

// Option B (Recommended): Remove internal id, use taskId everywhere
// Update SortableTaskCard.jsx:
const { ... } = useSortable({ id: task.taskId })  // Use taskId

// Update KanbanBoard.jsx:
const handleDragStart = (event) => {
  const task = tasks.find(t => t.taskId === event.active.id)
  setActiveTask(task)
}

const handleDragEnd = (event) => {
  const taskId = active.id  // Now this is actually taskId
  const task = tasks.find(t => t.taskId === taskId)
  if (task && task.status !== newStatus) {
    updateTask(task.taskId, { status: newStatus })  // Correct!
  }
}
```

**Step 2: Fix State Management**
Don't clear state on API error, just show error toast.

```javascript
// AppContext.jsx - updateTask function
const updateTask = async (id, updates) => {
  // Optimistic update - update UI first
  setTasks(prev => prev.map(t => 
    t.taskId === id ? { ...t, ...updates } : t
  ))
  
  try {
    await apiService.updateTask(id, updates)
    // Success - keep the optimistic update
    showToast('Task updated!', 'success')
  } catch (error) {
    // Error - revert the optimistic update
    const tasksData = await apiService.getTasks()
    setTasks(tasksData)
    showToast('Failed to update task', 'error')
  }
}
```

#### Files to Modify
- `src/components/tasks/SortableTaskCard.jsx` - Use taskId for drag ID
- `src/components/tasks/KanbanBoard.jsx` - Find tasks by taskId
- `src/context/AppContext.jsx` - Optimistic updates, better error handling
- `src/services/api.service.js` - Ensure toCamelCase creates consistent IDs

#### Acceptance Criteria
- [ ] Dragging task between columns updates status in database
- [ ] Tasks remain visible after drag operation
- [ ] No page refresh or state loss
- [ ] Error toast shown if API fails (but tasks still visible)

---

### Issue #2: Required Fields Too Restrictive (AssignedTo & DueDate)

**Severity:** 🟠 High  
**Component:** Frontend - validators.js, TaskModal.jsx  
**User Impact:** Cannot create tasks without assigning employee or due date

#### Current Behavior
- Frontend validation requires `assignedTo` and `dueDate` fields
- User cannot save task without filling these fields
- Error message: "Please assign this task to an employee" / "Due date is required"

#### Desired Behavior
- Only `title` and `projectId` should be required
- Unassigned tasks should go to "Unassigned" column (renamed from "Ready to Start")
- Due date should be optional

#### Root Cause Analysis

**Frontend Validator (validators.js):**
```javascript
// CURRENT - Too restrictive
export const validateTask = (task) => {
  const errors = {}
  
  if (!task.title || task.title.trim() === '') {
    errors.title = 'Task title is required'
  }
  if (!task.projectId) {
    errors.projectId = 'Project is required'
  }
  if (!task.assignedTo) {
    errors.assignedTo = 'Please assign this task to an employee'  // REMOVE
  }
  if (!task.dueDate) {
    errors.dueDate = 'Due date is required'  // REMOVE
  }
  // ...
}
```

**Note:** Backend already fixed in Phase 1 to accept optional fields.

#### Solution

**Step 1: Update Frontend Validator**
```javascript
// validators.js - UPDATED
export const validateTask = (task) => {
  const errors = {}
  
  // Only title is truly required
  if (!task.title || task.title.trim() === '') {
    errors.title = 'Task title is required'
  }
  
  if (!task.projectId) {
    errors.projectId = 'Project is required'
  }
  
  // Priority has a default, so validate if provided
  if (task.priority && !['high', 'medium', 'low'].includes(task.priority)) {
    errors.priority = 'Invalid priority value'
  }
  
  // assignedTo - OPTIONAL (no validation)
  // dueDate - OPTIONAL (no validation)
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}
```

**Step 2: Update TaskModal Default Values**
```javascript
// TaskModal.jsx - Ensure defaults handle null/undefined
const [formData, setFormData] = useState({
  title: '',
  description: '',
  projectId: projectId || '',
  assignedTo: null,      // Changed from '' to null
  dueDate: null,         // Changed from '' to null
  priority: PRIORITY.MEDIUM,
  status: STATUS.UNASSIGNED  // New default status
})
```

#### Files to Modify
- `src/utils/validators.js` - Remove mandatory assignedTo, dueDate
- `src/components/tasks/TaskModal.jsx` - Handle null values for optional fields

#### Acceptance Criteria
- [ ] Can create task with only title
- [ ] Unassigned tasks appear in "Unassigned" column
- [ ] Due date field is optional
- [ ] Form shows no errors for empty optional fields

---

### Issue #3: Kanban Column Rename & Workflow Redesign

**Severity:** 🟠 High  
**Component:** Frontend - constants.js, KanbanBoard.jsx, Backend - database.py  
**User Impact:** Current column names don't match actual workflow

#### Current Kanban Columns
1. **Ready to Start** - Initial status
2. **In Progress** - Being worked on
3. **Pending Verification** - Awaiting review
4. **Completed** - Done

#### Desired Kanban Columns (New Workflow)

| Column | New Name | Auto-Population Logic |
|--------|----------|----------------------|
| 1 | **Unassigned Tasks** | Tasks with no employee assigned (`assignedTo = null`) |
| 2 | **In Progress** | Tasks assigned to employee + no WhatsApp response yet, OR response = "not_completed" |
| 3 | **Pending Verification** | Tasks where employee clicked "✅ Yes, Completed" (`whatsappResponse = 'completed'`) |
| 4 | **Completed** | Tasks admin manually moves here after verification |

#### Workflow Logic

```
[Create Task]
     ↓
     ├─ No employee assigned → "Unassigned Tasks"
     ├─ Employee assigned → "In Progress"
     ↓
[Send to WhatsApp]
     ↓
     ├─ Employee clicks "❌ No" → Stays in "In Progress"
     ├─ Employee clicks "✅ Yes" → Auto-moves to "Pending Verification"
     ↓
[Admin Reviews]
     ↓
     └─ Admin drags to "Completed" → Task done
```

#### Solution

**Step 1: Update Constants**
```javascript
// constants.js
export const STATUS = {
  UNASSIGNED: 'unassigned',           // Renamed from READY_TO_START
  IN_PROGRESS: 'in_progress',
  PENDING_VERIFICATION: 'pending_verification',
  COMPLETED: 'completed'
}

export const STATUS_LABELS = {
  [STATUS.UNASSIGNED]: 'Unassigned Tasks',
  [STATUS.IN_PROGRESS]: 'In Progress',
  [STATUS.PENDING_VERIFICATION]: 'Pending Verification',
  [STATUS.COMPLETED]: 'Completed'
}
```

**Step 2: Update Task Creation Logic**
```javascript
// AppContext.jsx - addTask function
const addTask = async (task) => {
  // Auto-set status based on assignedTo
  const status = task.assignedTo ? STATUS.IN_PROGRESS : STATUS.UNASSIGNED
  const taskWithStatus = { ...task, status }
  
  // ... create task via API
}
```

**Step 3: Update Webhook Handler (Backend)**
```python
# app.py - webhook handler
def handle_whatsapp_response(task_id, response):
    if response == 'completed':
        # Auto-move to pending_verification
        database.update_task(task_id, {
            'whatsappResponse': 'completed',
            'status': 'pending_verification'  # Auto-move!
        })
    elif response == 'not_completed':
        # Keep in in_progress
        database.update_task(task_id, {
            'whatsappResponse': 'not_completed',
            'status': 'in_progress'  # Stay in progress
        })
```

**Step 4: Database Migration**
```sql
-- Update existing tasks with old status
UPDATE tasks SET status = 'unassigned' WHERE status = 'ready_to_start';
UPDATE tasks SET status = 'in_progress' WHERE status = 'todo';
```

#### Files to Modify
- `src/utils/constants.js` - Rename STATUS values and labels
- `src/context/AppContext.jsx` - Auto-set status on task creation
- `backend/app.py` - Update webhook to auto-move tasks
- `backend/database.py` - Add migration for existing data

#### Acceptance Criteria
- [ ] Column shows "Unassigned Tasks" (not "Ready to Start")
- [ ] New tasks without employee go to "Unassigned"
- [ ] Assigned tasks start in "In Progress"
- [ ] WhatsApp "Yes" response moves task to "Pending Verification"
- [ ] WhatsApp "No" response keeps task in "In Progress"
- [ ] Admin can freely drag between all columns

---

### Issue #4: No WhatsApp Button When Creating Task

**Severity:** 🟡 Medium  
**Component:** Frontend - TaskModal.jsx  
**User Impact:** Must save task first, then reopen to send WhatsApp

#### Current Behavior
- WhatsApp "Send" button only appears when editing an existing task
- Users must: Create task → Close modal → Click task → Send to WhatsApp

#### Desired Behavior
- After creating a task (if employee is assigned), show option to send immediately
- "Create & Send to WhatsApp" button alongside "Create Task"

#### Solution

**Option A: Two Buttons on Create**
```jsx
// TaskModal.jsx
{!isEditing && formData.assignedTo && (
  <Button
    type="button"
    variant="success"
    onClick={handleSubmitAndSend}
    className="flex items-center gap-2"
  >
    <Send className="w-4 h-4" />
    Create & Send to WhatsApp
  </Button>
)}

const handleSubmitAndSend = async (e) => {
  e.preventDefault()
  const validation = validateTask(formData)
  if (!validation.isValid) {
    setErrors(validation.errors)
    return
  }
  
  // Create task
  const newTask = await addTask({ ...formData, ... })
  
  // Immediately send to WhatsApp
  if (newTask && newTask.taskId) {
    await sendTaskToWhatsApp(newTask.taskId)
  }
  
  handleClose()
}
```

**Option B: Checkbox "Send to WhatsApp after creating"**
```jsx
const [sendAfterCreate, setSendAfterCreate] = useState(false)

// In form:
{!isEditing && formData.assignedTo && (
  <label className="flex items-center gap-2">
    <input
      type="checkbox"
      checked={sendAfterCreate}
      onChange={(e) => setSendAfterCreate(e.target.checked)}
    />
    Send to WhatsApp after creating
  </label>
)}

// In handleSubmit:
if (sendAfterCreate && newTask.taskId) {
  await sendTaskToWhatsApp(newTask.taskId)
}
```

#### Recommendation
Use **Option A** (two buttons) for clearer UX.

#### Files to Modify
- `src/components/tasks/TaskModal.jsx` - Add "Create & Send" button

#### Acceptance Criteria
- [ ] "Create & Send to WhatsApp" button visible when employee is assigned
- [ ] Button is disabled/hidden if no employee selected
- [ ] Task is created AND sent in single action
- [ ] Success toast confirms both actions

---

### Issue #5: Project Card Missing Task Statistics

**Severity:** 🟡 Medium  
**Component:** Frontend - ProjectCard.jsx, Dashboard.jsx, AppContext.jsx  
**User Impact:** Cannot see task breakdown without opening project

#### Current Behavior
- Project card shows: "X/Y tasks completed"
- Missing: Breakdown by status (unassigned, in progress, pending)

#### Desired Behavior
Show task counts like:
```
📋 Unassigned: 2
🔄 In Progress: 5  
⏳ Pending: 3
✅ Completed: 8/18
```

#### Solution

**Step 1: Calculate Stats in AppContext**
```javascript
// AppContext.jsx
const getProjectsWithStats = () => {
  const projectsData = storageService.getProjects()
  const tasksData = storageService.getTasks()
  
  return projectsData.map(project => {
    const projectTasks = tasksData.filter(t => t.projectId === project.id)
    
    const stats = {
      unassigned: projectTasks.filter(t => t.status === STATUS.UNASSIGNED).length,
      inProgress: projectTasks.filter(t => t.status === STATUS.IN_PROGRESS).length,
      pending: projectTasks.filter(t => t.status === STATUS.PENDING_VERIFICATION).length,
      completed: projectTasks.filter(t => t.status === STATUS.COMPLETED).length,
      total: projectTasks.length
    }
    
    const progress = stats.total > 0 
      ? Math.round((stats.completed / stats.total) * 100) 
      : 0
    
    return {
      ...project,
      taskCount: stats.total,
      completedTasks: stats.completed,
      taskStats: stats,
      progress
    }
  })
}
```

**Step 2: Update ProjectCard Display**
```jsx
// ProjectCard.jsx
<div className="grid grid-cols-2 gap-2 text-sm mb-4">
  <div className="flex items-center gap-1 text-gray-500">
    <span className="w-2 h-2 rounded-full bg-gray-400"></span>
    Unassigned: {project.taskStats?.unassigned || 0}
  </div>
  <div className="flex items-center gap-1 text-blue-600">
    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
    In Progress: {project.taskStats?.inProgress || 0}
  </div>
  <div className="flex items-center gap-1 text-yellow-600">
    <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
    Pending: {project.taskStats?.pending || 0}
  </div>
  <div className="flex items-center gap-1 text-green-600">
    <span className="w-2 h-2 rounded-full bg-green-500"></span>
    Completed: {project.taskStats?.completed || 0}
  </div>
</div>
```

#### Files to Modify
- `src/context/AppContext.jsx` - Calculate detailed stats
- `src/components/projects/ProjectCard.jsx` - Display stats grid

#### Acceptance Criteria
- [ ] Project card shows 4 status counts
- [ ] Counts are color-coded to match Kanban columns
- [ ] Stats update when tasks change status
- [ ] Works with 0 tasks (shows all zeros)

---

### Issue #6: Admin Cannot Freely Move Tasks Between Columns

**Severity:** 🟡 Medium  
**Component:** Frontend - KanbanBoard.jsx, Backend - app.py  
**User Impact:** Drag-and-drop may be restricted or not working properly

#### Current Behavior
- Drag-and-drop implemented but has ID issues (see Issue #1)
- Status change may not persist correctly

#### Desired Behavior
- Admin can drag any task to any column
- Status updates immediately in database
- No restrictions on column transitions

#### Solution

Once Issue #1 (ID mismatch) is fixed, drag-and-drop should work. Additional improvements:

**Step 1: Remove Status Transition Restrictions**
Currently no restrictions exist, but ensure none are added.

**Step 2: Add Visual Feedback**
```jsx
// KanbanColumn.jsx - Show drop zone highlight
const { isOver, setNodeRef } = useDroppable({ id: status })

return (
  <div
    ref={setNodeRef}
    className={`kanban-column ${isOver ? 'bg-blue-50 ring-2 ring-blue-300' : ''}`}
  >
    {/* ... */}
  </div>
)
```

**Step 3: Ensure Backend Accepts All Transitions**
```python
# app.py - update_task endpoint
# No validation on status transitions - admin can set any status
# Already implemented correctly
```

#### Files to Modify
- Fix Issue #1 first (ID mismatch)
- `src/components/tasks/KanbanColumn.jsx` - Add drop zone visual feedback

#### Acceptance Criteria
- [ ] Can drag task from any column to any other column
- [ ] Status updates in database immediately
- [ ] Visual feedback during drag (drop zone highlight)
- [ ] No error messages for any transition

---

### Issue #7: Ability to Edit Project Name and Description

**Severity:** 🟡 Medium  
**Component:** Frontend - CreateProjectModal.jsx, ProjectDetail.jsx, AppContext.jsx  
**User Impact:** Cannot modify project details after creation; must delete and recreate

#### Current Behavior
- `CreateProjectModal.jsx` only supports creating new projects
- No way to edit project name, description, dates, or team members after creation
- `ProjectDetail.jsx` displays project name but no edit button/functionality
- Backend `updateProject` API exists but no frontend UI to invoke it

#### Root Cause Analysis

**Current CreateProjectModal:**
```jsx
// CreateProjectModal.jsx - Line 12
const CreateProjectModal = ({ isOpen, onClose }) => {
  // Only creates new projects, no edit mode
  const handleSubmit = (e) => {
    // ...
    const newProject = {
      id: generateId('proj'),  // Always generates new ID
      // ...
    }
    addProject(newProject)  // Only calls addProject, never updateProject
  }
}
```

**Backend Already Supports Updates:**
```python
# app.py - PUT /api/projects/<id> exists
@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project_route(project_id):
    # Fully implemented, accepts name, description, dates, team changes
```

**AppContext Has Update Method:**
```javascript
// AppContext.jsx - Line 120
const updateProject = async (id, updates) => {
  await apiService.updateProject(id, updates)
  // ... refresh and toast
}
```

#### Desired Behavior
1. **Edit Button on Project Detail Page** - Click to open edit modal
2. **Reuse CreateProjectModal with Edit Mode** - Pass existing project data
3. **Update All Fields** - Name, description, start/end dates, team members
4. **Visual Feedback** - Show "Edit Project" title instead of "Create New Project"

#### Solution

**Step 1: Update CreateProjectModal to Support Edit Mode**
```jsx
// CreateProjectModal.jsx - Accept project prop for edit mode
const CreateProjectModal = ({ isOpen, onClose, project = null }) => {
  const isEditing = !!project
  const { employees, addProject, updateProject } = useApp()
  
  const [formData, setFormData] = useState({
    name: project?.name || '',
    description: project?.description || '',
    startDate: project?.startDate || '',
    endDate: project?.endDate || '',
    assignedEmployees: project?.assignedEmployees || []
  })
  
  // Reset form when project changes (for edit mode)
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

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const validation = validateProject(formData)
    if (!validation.isValid) {
      setErrors(validation.errors)
      return
    }

    if (isEditing) {
      // Update existing project
      updateProject(project.id, {
        name: formData.name,
        description: formData.description,
        startDate: formData.startDate,
        endDate: formData.endDate,
        assignedEmployees: formData.assignedEmployees,
        updatedAt: new Date().toISOString()
      })
      onClose()
    } else {
      // Create new project (existing logic)
      const newProject = {
        id: generateId('proj'),
        name: formData.name,
        description: formData.description,
        startDate: formData.startDate,
        endDate: formData.endDate,
        color: getRandomColor(PROJECT_COLORS),
        assignedEmployees: formData.assignedEmployees,
        createdAt: new Date().toISOString()
      }
      addProject(newProject)
      onClose()
      navigate(`/project/${newProject.id}`)
    }
  }

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose} 
      title={isEditing ? "Edit Project" : "Create New Project"} 
      size="md"
    >
      {/* ... form with conditional button text */}
      <Button type="submit" variant="primary" fullWidth>
        {isEditing ? 'Save Changes' : 'Create Project'}
      </Button>
    </Modal>
  )
}
```

**Step 2: Add Description Field to Form**
```jsx
// Add textarea for description (currently missing)
<div>
  <label className="label">Description (Optional)</label>
  <textarea
    value={formData.description}
    onChange={(e) => handleChange('description', e.target.value)}
    placeholder="Project description..."
    className="input min-h-[100px]"
    rows={3}
  />
</div>
```

**Step 3: Add Edit Button to ProjectDetail Page**
```jsx
// ProjectDetail.jsx - Add edit button in header
import { Pencil } from 'lucide-react'

const [showEditProject, setShowEditProject] = useState(false)

// In header section:
<div className="flex items-center gap-2">
  <button
    onClick={() => setShowEditProject(true)}
    className="p-2 hover:bg-gray-100 rounded-lg transition-smooth"
    title="Edit Project"
  >
    <Pencil className="w-5 h-5 text-gray-600" />
  </button>
  <Button onClick={() => setShowCreateTask(true)} variant="primary">
    <Plus className="w-5 h-5" />
    New Task
  </Button>
</div>

// Add modal at bottom:
<CreateProjectModal
  isOpen={showEditProject}
  onClose={() => setShowEditProject(false)}
  project={project}  // Pass existing project for edit mode
/>
```

**Step 4: Rename Component (Optional)**
Consider renaming `CreateProjectModal.jsx` → `ProjectModal.jsx` to reflect dual purpose.

#### Files to Modify
- `src/components/projects/CreateProjectModal.jsx` - Add edit mode support, description field
- `src/pages/ProjectDetail.jsx` - Add edit button and modal trigger
- `src/utils/validators.js` - Update project validation (description optional)

#### Acceptance Criteria
- [ ] Edit button visible on project detail page header
- [ ] Clicking edit opens modal with existing project data pre-filled
- [ ] Can modify project name, description, dates, team members
- [ ] Save updates project in database
- [ ] UI reflects changes immediately
- [ ] "Cancel" closes modal without saving

---

### Issue #8: Task Status Update Separation - Webhook vs Admin Drag

**Severity:** 🟠 High  
**Component:** Frontend - KanbanBoard.jsx, AppContext.jsx, Backend - app.py  
**User Impact:** Admin moving tasks on Kanban board could trigger unintended WhatsApp messages to employees

#### Current Behavior
The current implementation has two ways to update task status:

1. **Webhook Update** (Employee Response)
   - Employee clicks "✅ Yes" or "❌ No" on WhatsApp
   - Kapso sends webhook to `/api/webhook/whatsapp`
   - Backend updates task status AND sends confirmation message
   ```python
   # app.py - Line 814-816
   if new_task_status:
       update_data['status'] = new_task_status
   # Line 830-833 - Sends confirmation
   kapso_service.send_text_message(clean_phone, confirm_msg)
   ```

2. **Admin Drag-and-Drop Update**
   - Admin drags task between Kanban columns
   - Calls `updateTask(taskId, { status: newStatus })`
   - Updates task via `PUT /api/tasks/<id>` endpoint
   - Currently NO WhatsApp message is sent (correct!)

**Potential Issue:**
- The separation currently works, but there's no explicit flag to differentiate sources
- If future code adds notifications to the task update endpoint, admin actions could trigger unwanted messages
- No clear documentation of this intentional behavior

#### Desired Behavior
1. **Webhook Updates** - Employee response via WhatsApp
   - Should auto-move task to appropriate column (pending_verification or stay in_progress)
   - Should send confirmation message to employee
   - Should record response in `whatsappResponse` field

2. **Admin Drag-and-Drop** - Manual status change
   - Should freely move tasks between ANY columns
   - Should NOT trigger any WhatsApp message
   - Should NOT affect `whatsappResponse` field
   - Should update only the `status` field

3. **Clear Separation** - Make it explicit in code
   - Add `source` parameter to differentiate update origins
   - Prevent accidental messaging on admin actions

#### Solution

**Step 1: Add Source Parameter to Update Task (Frontend)**
```javascript
// AppContext.jsx - Add source parameter
const updateTask = async (id, updates, source = 'admin') => {
  try {
    console.log(`📡 Updating task ${id} via API (source: ${source})...`)
    await apiService.updateTask(id, { ...updates, updateSource: source })
    // ... rest of logic
  } catch (error) {
    // ... error handling
  }
}

// KanbanBoard.jsx - Explicitly mark as admin action
const handleDragEnd = (event) => {
  // ...
  if (task && task.status !== newStatus) {
    // Admin is manually moving task - should NOT trigger WhatsApp
    updateTask(task.taskId, { status: newStatus }, 'admin')
  }
}
```

**Step 2: Handle Source in Backend (Optional but Recommended)**
```python
# app.py - update_task endpoint
@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task_route(task_id):
    data = request.get_json()
    
    # Extract and remove updateSource from data (don't save it)
    update_source = data.pop('updateSource', 'admin')
    
    print(f"📝 Task update source: {update_source}")
    
    # Only send notifications if source is 'webhook' or 'system'
    # Admin actions should never trigger messages
    if update_source == 'admin':
        # Just update, no messaging
        pass
    
    # Proceed with normal update
    result = database.update_task(task_id, data)
    # ...
```

**Step 3: Webhook Handler Already Correctly Isolated**
The current webhook handler at `/api/webhook/whatsapp` is separate from the task update endpoint. This is correct! Ensure this remains separate.

```python
# app.py - Webhook ONLY handles employee responses
# Line 722-858 - Completely separate from PUT /api/tasks/<id>
# This is intentional and correct!
```

**Step 4: Document the Behavior**
Add comments to clarify the intentional separation:

```python
# app.py - update_task endpoint
@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task_route(task_id):
    """
    Update task via API call (typically from admin frontend).
    
    NOTE: This endpoint does NOT send WhatsApp messages.
    WhatsApp messages are ONLY sent via:
    1. POST /api/tasks/<id>/send-whatsapp-buttons (manual send)
    2. Confirmation in /api/webhook/whatsapp (response handling)
    
    Admin can freely move tasks between columns without triggering messages.
    """
```

**Step 5: Enhance Webhook to Auto-Move Tasks**
Per Issue #3, webhook should auto-move tasks:

```python
# app.py - webhook handler updates
if response_status == 'completed':
    update_data['status'] = 'pending_verification'  # Auto-move for review
    new_task_status = 'pending_verification'
elif response_status == 'not_completed':
    update_data['status'] = 'in_progress'  # Keep in progress
    new_task_status = None  # Status already in_progress
```

#### Files to Modify
- `src/context/AppContext.jsx` - Add optional `source` parameter to updateTask
- `src/components/tasks/KanbanBoard.jsx` - Pass 'admin' source on drag
- `backend/app.py` - Add comments documenting separation, handle updateSource parameter
- No changes needed to webhook (already isolated correctly)

#### Acceptance Criteria
- [ ] Admin dragging task between columns does NOT send WhatsApp message
- [ ] Admin can move task from any column to any column freely
- [ ] Employee "Yes" response auto-moves task to "Pending Verification"
- [ ] Employee "No" response keeps task in "In Progress"
- [ ] WhatsApp confirmation only sent after employee button click (not admin action)
- [ ] Code has clear comments documenting this separation
- [ ] `updateSource` parameter logged for debugging

#### Workflow Summary
```
┌─────────────────────────────────────────────────────────────────┐
│                     TASK STATUS UPDATE FLOWS                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     Admin Drag      ┌──────────────────────┐  │
│  │ Admin (Web)  │ ──────────────────► │ PUT /api/tasks/<id>  │  │
│  └──────────────┘   source: 'admin'   │   NO MESSAGING       │  │
│                                       └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐   Button Click      ┌──────────────────────┐  │
│  │ Employee     │ ──────────────────► │ POST /api/webhook    │  │
│  │ (WhatsApp)   │   via Kapso         │   + Auto-move task   │  │
│  └──────────────┘                     │   + Confirmation msg │  │
│                                       └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐   "Send" Button     ┌──────────────────────┐  │
│  │ Admin (Web)  │ ──────────────────► │ POST /send-whatsapp  │  │
│  └──────────────┘                     │   + Send task msg    │  │
│                                       └──────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Issue #9: Task Updates Not Persisting (Field Mapping Mismatch)

**Severity:** 🔴 Critical  
**Component:** Frontend - TaskModal.jsx, api.service.js  
**User Impact:** When editing a task and saving, changes don't persist. Employee field shows empty when reopening.

#### Current Behavior
1. User opens an existing task in TaskModal
2. Selects an employee from dropdown
3. Clicks "Save Changes"
4. Toast shows "Task updated successfully!"
5. User reopens the same task → Employee field is empty

#### Root Cause Analysis
There is a **field name mismatch** between frontend and backend:

| Layer | Employee Field Name | Example Value |
|-------|---------------------|---------------|
| Database | `employee_id` | `1` |
| API Response (snake_case) | `employee_id` | `1` |
| Frontend (after toCamelCase) | `employeeId` | `1` |
| TaskModal form | `assignedTo` | `""` (empty!) |

**Problem 1: Loading Task Data**
```jsx
// TaskModal.jsx - useEffect
setFormData({
  // ...
  assignedTo: task.assignedTo,  // ❌ WRONG! Should be task.employeeId
  dueDate: task.dueDate,        // This works (names match)
})
```
The task object from API has `employeeId`, not `assignedTo`. So `task.assignedTo` is `undefined`.

**Problem 2: Sending Update**
```jsx
// TaskModal.jsx - handleSubmit
updateTask(task.taskId, formData)  // Sends { assignedTo: "1", ... }
```
The backend expects `assignedTo` in the update mapping (which works), but when loading, we read the wrong field.

#### Solution

**Option A (Recommended): Normalize in API service**
Add `assignedTo` field in toCamelCase transformation:

```javascript
// api.service.js - toCamelCase function
if (result.employeeId !== undefined) {
  result.assignedTo = result.employeeId;  // Add alias for frontend
}
```

**Option B: Update TaskModal to use employeeId**
```jsx
// TaskModal.jsx - useEffect
setFormData({
  assignedTo: task.employeeId || task.assignedTo || '',
  // ...
})
```

#### Files to Modify
- `src/services/api.service.js` - Add `assignedTo` alias in toCamelCase
- `src/components/tasks/TaskModal.jsx` - Ensure proper field reading

#### Acceptance Criteria
- [ ] Open task with assigned employee → employee shows in dropdown
- [ ] Change employee → save → reopen → new employee persists
- [ ] All task fields (title, description, priority, status, dueDate) persist after edit
- [ ] Works for both new tasks and existing tasks

---

## 🎨 UX IMPROVEMENTS

---

### Enhancement #1: Add WhatsApp Status Indicator Colors

Show clear visual indicator of WhatsApp status on task cards:
- 📱 **Not Sent** (gray) - No WhatsApp message sent
- 📤 **Sent** (blue) - Message sent, waiting for response
- ⏰ **Pending** (yellow) - Employee clicked "No, Not Yet"
- ✅ **Done** (green) - Employee clicked "Yes, Completed"

### Enhancement #2: Loading States

Add loading spinners/skeletons when:
- Fetching tasks from API
- Sending WhatsApp message
- Updating task status

### Enhancement #3: Empty State Improvements

When Kanban column is empty:
- Show helpful message: "No tasks in this column"
- For "Unassigned Tasks": "Create a task to get started"
- For "Completed": "Drag verified tasks here"

### Enhancement #4: Confirmation Dialogs

Add confirmation before:
- Deleting a task
- Moving task to "Completed" (optional)

---

## 🔧 CODE QUALITY IMPROVEMENTS

---

### Improvement #1: Consistent ID Handling

**Current Problem:**
- Frontend has `task.id` (internal) and `task.taskId` (from API)
- Confusion about which to use where
- Bug source for Issue #1

**Solution:**
Create a unified approach:
```javascript
// api.service.js - toCamelCase transformer
// After transformation, set id = taskId for backwards compatibility
const transformedTask = toCamelCase(task)
transformedTask.id = transformedTask.taskId  // Unify IDs
return transformedTask
```

### Improvement #2: Error Boundary Component

Add React Error Boundary to catch and display errors gracefully:
```jsx
// components/common/ErrorBoundary.jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />
    }
    return this.props.children
  }
}
```

### Improvement #3: Centralized API Error Handling

```javascript
// services/api.service.js
const handleApiError = (error, operation) => {
  console.error(`❌ API Error in ${operation}:`, error)
  
  if (error.message.includes('NetworkError')) {
    throw new Error('Network error. Please check your connection.')
  }
  if (error.message.includes('404')) {
    throw new Error('Resource not found.')
  }
  throw error
}
```

### Improvement #4: Type Safety (Optional - TypeScript)

Consider migrating to TypeScript for:
- Type-safe task objects
- Auto-completion in IDE
- Catch errors at compile time

---

## 📁 FILE MODIFICATION SUMMARY

| File | Changes |
|------|---------|
| `src/utils/constants.js` | Rename STATUS.READY_TO_START → STATUS.UNASSIGNED |
| `src/utils/validators.js` | Remove required validation for assignedTo, dueDate |
| `src/components/tasks/TaskModal.jsx` | Add "Create & Send" button, handle null optionals |
| `src/components/tasks/KanbanBoard.jsx` | Fix ID usage (taskId not id), pass 'admin' source |
| `src/components/tasks/SortableTaskCard.jsx` | Use taskId for drag ID |
| `src/components/tasks/KanbanColumn.jsx` | Add drop zone visual feedback |
| `src/components/projects/ProjectCard.jsx` | Add task stats display |
| `src/components/projects/CreateProjectModal.jsx` | Add edit mode, description field, rename to ProjectModal |
| `src/pages/ProjectDetail.jsx` | Add edit project button and modal |
| `src/context/AppContext.jsx` | Optimistic updates, better error handling, stats calculation, updateTask source param |
| `src/services/api.service.js` | Unify task.id = task.taskId, pass updateSource |
| `backend/app.py` | Webhook auto-moves tasks, document separation, handle updateSource |
| `backend/database.py` | Migration for status rename |

---

## 🧪 TEST UPDATES REQUIRED

Update tests to match new behavior:

### Backend Tests
- [ ] Test task creation without assignedTo (should succeed)
- [ ] Test task creation without dueDate (should succeed)
- [ ] Test webhook moves task to pending_verification on "completed"
- [ ] Test webhook keeps task in in_progress on "not_completed"
- [ ] Test project update (name, description, dates, team)
- [ ] Test task update with updateSource='admin' (no messaging)

### Frontend Tests
- [ ] Test validator accepts task without assignedTo
- [ ] Test validator accepts task without dueDate
- [ ] Test Kanban drag uses taskId
- [ ] Test ProjectCard displays stats
- [ ] Test ProjectModal in edit mode pre-fills data
- [ ] Test updateTask passes source parameter

---

## 📋 IMPLEMENTATION ORDER

**Recommended order for Phase 2 development:**

1. **Issue #1** (Critical) - Fix drag-and-drop / page refresh bug
2. **Issue #3** - Rename columns and update workflow
3. **Issue #2** - Make fields optional
4. **Issue #8** - Implement task update separation (webhook vs admin)
5. **Issue #4** - Add "Create & Send" button
6. **Issue #5** - Add project statistics
7. **Issue #6** - Verify free drag-and-drop works
8. **Issue #7** - Add project edit functionality

**Estimated Time:** 6-8 hours total

---

## ✅ PHASE 2 COMPLETION CHECKLIST

- [ ] All 8 issues resolved
- [ ] All tests passing (update tests as needed)
- [ ] No console errors
- [ ] Manual testing complete:
  - [ ] Create task without employee → goes to Unassigned
  - [ ] Assign employee → moves to In Progress
  - [ ] Send to WhatsApp → employee receives message
  - [ ] Employee clicks Yes → moves to Pending Verification
  - [ ] Admin drags to Completed → stays there (NO message sent)
  - [ ] Admin drags between any columns → works freely
  - [ ] Project card shows correct stats
  - [ ] Edit project → updates name, description, dates, team
- [ ] Code reviewed and clean
- [ ] README updated with new workflow

---

**END OF PHASE 2 REQUIREMENTS DOCUMENT**

---

*This document should be provided to the LLM along with the TECHNICAL_DESIGN_SPEC.md when implementing Phase 2 changes.*

---

# 🤖 LLM PROMPTS FOR PHASE 2 IMPLEMENTATION

Below are ready-to-use prompts for each issue. Copy the prompt for the issue you want to fix, and provide it to the LLM along with access to your codebase.

**Important:** Always provide `TECHNICAL_DESIGN_SPEC.md` as context before using these prompts.

---

## 📝 PROMPT: Issue #1 - Fix Drag-and-Drop Task Disappearing Bug

```
## TASK: Fix Critical Drag-and-Drop Bug in Kanban Board

### CONTEXT
I have a WhatsApp Task Manager application with a React frontend and Flask backend. The Kanban board uses @dnd-kit for drag-and-drop functionality. There is a critical bug where tasks disappear after dragging between columns.

### PROBLEM
When I drag a task from one Kanban column to another (e.g., "Pending Verification" to "Completed"):
1. The page appears to refresh
2. All tasks disappear from the board
3. The task status is not updated in the database

### ROOT CAUSE (Already Identified)
There is an ID mismatch between frontend and backend:
- `SortableTaskCard.jsx` uses `useSortable({ id: task.id })` - uses internal frontend ID
- `KanbanBoard.jsx` calls `updateTask(taskId, { status })` - passes wrong ID to API
- Backend expects `task.taskId` (format: "task_001") but receives `task.id` (internal number)
- API returns 404, error handling clears state

### FILES TO MODIFY
1. `src/components/tasks/SortableTaskCard.jsx` - Change drag ID from `task.id` to `task.taskId`
2. `src/components/tasks/KanbanBoard.jsx` - Find tasks by `taskId`, use `task.taskId` for API calls
3. `src/context/AppContext.jsx` - Add optimistic updates, improve error handling to not clear state on failure
4. `src/services/api.service.js` - In toCamelCase transformer, set `task.id = task.taskId` for consistency

### REQUIREMENTS
1. Use `taskId` consistently for all API operations
2. Implement optimistic updates (update UI immediately, then sync with backend)
3. If API fails, revert to previous state and show error toast (don't clear all tasks)
4. Ensure drag-and-drop visual feedback still works
5. Test by dragging tasks between all 4 columns

### EXPECTED BEHAVIOR AFTER FIX
- Dragging task updates status in database immediately
- Tasks remain visible after drag operation
- No page refresh or state loss
- Error toast shown if API fails (but tasks still visible)

Please analyze the relevant files and implement the fix. Show me the exact code changes needed.
```

---

## 📝 PROMPT: Issue #2 - Make AssignedTo and DueDate Optional

```
## TASK: Remove Mandatory Validation for AssignedTo and DueDate Fields

### CONTEXT
I have a WhatsApp Task Manager with React frontend. When creating a task, the form requires `assignedTo` (employee) and `dueDate` fields. These should be optional.

### PROBLEM
- Frontend validator requires `assignedTo` and `dueDate`
- User cannot create a task without assigning it to an employee
- Error messages: "Please assign this task to an employee" / "Due date is required"

### CURRENT CODE LOCATION
`src/utils/validators.js` - `validateTask()` function

### REQUIREMENTS
1. Remove mandatory validation for `assignedTo` field
2. Remove mandatory validation for `dueDate` field
3. Keep `title` as required
4. Keep `projectId` as required (when creating task within a project)
5. If `priority` is provided, validate it's one of: 'high', 'medium', 'low'
6. Update `TaskModal.jsx` to handle null values for optional fields

### BACKEND STATUS
Backend already accepts optional fields (fixed in Phase 1). Only frontend validation needs updating.

### EXPECTED BEHAVIOR AFTER FIX
- Can create task with only title
- Unassigned tasks should have `assignedTo: null`
- Tasks without due date should have `dueDate: null`
- Form shows no errors for empty optional fields

Please update the validator and TaskModal to make these fields optional.
```

---

## 📝 PROMPT: Issue #3 - Rename Kanban Columns and Update Workflow

```
## TASK: Rename Kanban Columns and Implement New Workflow Logic

### CONTEXT
I have a WhatsApp Task Manager with a Kanban board. The current column names don't match the actual workflow.

### CURRENT COLUMNS
1. "Ready to Start" (status: ready_to_start)
2. "In Progress" (status: in_progress)
3. "Pending Verification" (status: pending_verification)
4. "Completed" (status: completed)

### NEW COLUMNS (Desired)
1. "Unassigned Tasks" (status: unassigned) - Tasks with no employee assigned
2. "In Progress" (status: in_progress) - Tasks assigned to employee
3. "Pending Verification" (status: pending_verification) - Employee clicked "Yes, Completed" on WhatsApp
4. "Completed" (status: completed) - Admin verified and moved here

### NEW WORKFLOW LOGIC
1. Create task without employee → goes to "Unassigned Tasks"
2. Create task with employee OR assign employee to unassigned task → goes to "In Progress"
3. Employee clicks "✅ Yes, Completed" on WhatsApp → auto-moves to "Pending Verification"
4. Employee clicks "❌ No, Not Yet" on WhatsApp → stays in "In Progress"
5. Admin manually drags to "Completed" after verification

### FILES TO MODIFY
1. `src/utils/constants.js` - Rename STATUS.READY_TO_START to STATUS.UNASSIGNED, update STATUS_LABELS
2. `src/context/AppContext.jsx` - Auto-set status based on assignedTo when creating/updating tasks
3. `backend/app.py` - Update webhook handler to auto-move tasks on WhatsApp response
4. `backend/database.py` - Add migration to update existing tasks with old status values

### DATABASE MIGRATION NEEDED
```sql
UPDATE tasks SET status = 'unassigned' WHERE status = 'ready_to_start';
UPDATE tasks SET status = 'unassigned' WHERE status = 'todo';
```

### REQUIREMENTS
1. Update all STATUS constants and labels
2. Frontend auto-sets status based on assignedTo presence
3. Webhook "completed" response moves task to "pending_verification"
4. Webhook "not_completed" response keeps task in "in_progress"
5. Admin can freely drag between any columns
6. Existing data is migrated to new status values

Please implement these changes across frontend and backend.
```

---

## 📝 PROMPT: Issue #4 - Add "Create & Send to WhatsApp" Button

```
## TASK: Add "Create & Send to WhatsApp" Button in Task Creation Modal

### CONTEXT
I have a WhatsApp Task Manager where admins create tasks and send them to employees via WhatsApp. Currently, to send a task to WhatsApp, admin must: Create task → Close modal → Click task → Send to WhatsApp. This is inefficient.

### PROBLEM
- WhatsApp "Send" button only appears when editing an existing task
- No way to create task and immediately send to WhatsApp in one action

### DESIRED BEHAVIOR
- When creating a new task with an assigned employee, show TWO buttons:
  1. "Create Task" - Just creates the task
  2. "Create & Send to WhatsApp" - Creates task AND sends WhatsApp message

### FILE TO MODIFY
`src/components/tasks/TaskModal.jsx`

### REQUIREMENTS
1. Add new button "Create & Send to WhatsApp" (green color, with Send icon)
2. Button only visible when:
   - Creating a new task (not editing)
   - Employee is selected in `formData.assignedTo`
3. When clicked:
   - Validate form
   - Create task via API
   - Immediately call `sendTaskToWhatsApp(newTask.taskId)`
   - Show success toast: "Task created and sent to WhatsApp!"
4. Handle errors gracefully (task created but WhatsApp failed)
5. Use lucide-react `Send` icon

### API FUNCTIONS AVAILABLE
- `addTask(taskData)` - Creates task, returns new task with taskId
- `sendTaskToWhatsApp(taskId)` - Sends WhatsApp message (from api.service.js)

### EXPECTED UI
```
[Cancel]  [Create Task]  [Create & Send to WhatsApp 📤]
                         ↑ Only visible when employee selected
```

Please implement this feature in TaskModal.jsx.
```

---

## 📝 PROMPT: Issue #5 - Add Task Statistics to Project Cards

```
## TASK: Add Task Statistics Display on Project Cards

### CONTEXT
I have a WhatsApp Task Manager with project cards on the dashboard. Currently, project cards only show "X/Y tasks completed". I want to show a breakdown by status.

### CURRENT BEHAVIOR
Project card shows: "5/12 tasks completed"

### DESIRED BEHAVIOR
Project card shows:
```
📋 Unassigned: 2
🔄 In Progress: 5
⏳ Pending: 3
✅ Completed: 8/18
```

### FILES TO MODIFY
1. `src/context/AppContext.jsx` - Calculate detailed stats in `getProjectsWithStats()` function
2. `src/components/projects/ProjectCard.jsx` - Display stats grid with color-coded indicators

### STATS TO CALCULATE
For each project, count tasks by status:
- `unassigned`: tasks where status === 'unassigned'
- `inProgress`: tasks where status === 'in_progress'
- `pending`: tasks where status === 'pending_verification'
- `completed`: tasks where status === 'completed'
- `total`: total task count

### UI REQUIREMENTS
1. Display stats in a 2x2 grid layout
2. Color-code each status:
   - Unassigned: gray (#9CA3AF)
   - In Progress: blue (#3B82F6)
   - Pending: yellow (#F59E0B)
   - Completed: green (#10B981)
3. Show small colored dot indicator next to each stat
4. Stats should update automatically when tasks change

### EXPECTED OUTPUT
```jsx
<div className="grid grid-cols-2 gap-2 text-sm">
  <div className="flex items-center gap-1 text-gray-500">
    <span className="w-2 h-2 rounded-full bg-gray-400"></span>
    Unassigned: 2
  </div>
  <div className="flex items-center gap-1 text-blue-600">
    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
    In Progress: 5
  </div>
  ...
</div>
```

Please implement this feature.
```

---

## 📝 PROMPT: Issue #6 - Verify Free Drag-and-Drop Between Columns

```
## TASK: Verify and Enhance Admin Drag-and-Drop Functionality

### CONTEXT
After fixing Issue #1 (ID mismatch), I need to verify that admin can freely drag tasks between any Kanban columns without restrictions.

### REQUIREMENTS
1. Verify admin can drag task from ANY column to ANY other column
2. No status transition restrictions
3. Add visual feedback during drag (highlight drop zone)
4. Status updates immediately in database
5. No error messages for any valid transition

### FILE TO MODIFY
`src/components/tasks/KanbanColumn.jsx` - Add drop zone visual feedback

### VISUAL FEEDBACK ENHANCEMENT
When dragging a task over a column, the column should:
- Show a light blue background (`bg-blue-50`)
- Show a blue ring border (`ring-2 ring-blue-300`)

### CODE PATTERN
```jsx
const { isOver, setNodeRef } = useDroppable({ id: status })

return (
  <div
    ref={setNodeRef}
    className={`kanban-column ${isOver ? 'bg-blue-50 ring-2 ring-blue-300' : ''}`}
  >
    {/* column content */}
  </div>
)
```

### TESTING CHECKLIST
After implementation, verify:
- [ ] Can drag from Unassigned → In Progress
- [ ] Can drag from In Progress → Pending Verification
- [ ] Can drag from Pending Verification → Completed
- [ ] Can drag from Completed → Unassigned (reverse)
- [ ] Can drag from any column to any other column
- [ ] Visual feedback shows during drag
- [ ] Database is updated after each drag

Please implement the visual feedback enhancement and verify the drag functionality works correctly.
```

---

## 📝 PROMPT: Issue #7 - Add Project Edit Functionality

```
## TASK: Add Ability to Edit Project Name, Description, and Details

### CONTEXT
I have a WhatsApp Task Manager with project creation via `CreateProjectModal.jsx`. Currently, users cannot edit project details after creation - they must delete and recreate the project.

### PROBLEM
- `CreateProjectModal.jsx` only supports creating new projects
- No edit button on project detail page
- Backend `updateProject` API exists but no frontend UI to use it

### DESIRED BEHAVIOR
1. Add "Edit" button (pencil icon) on ProjectDetail page header
2. Clicking opens the same modal, but in "edit mode" with data pre-filled
3. Can edit: name, description, start date, end date, team members
4. Save calls `updateProject()` instead of `addProject()`
5. Modal title shows "Edit Project" instead of "Create New Project"

### FILES TO MODIFY
1. `src/components/projects/CreateProjectModal.jsx`:
   - Accept optional `project` prop for edit mode
   - Pre-fill form with existing project data when editing
   - Add `description` textarea field (currently missing)
   - Conditional submit: `updateProject()` for edit, `addProject()` for create
   - Change modal title and button text based on mode

2. `src/pages/ProjectDetail.jsx`:
   - Add edit button in header (Pencil icon from lucide-react)
   - Add state: `showEditProject`
   - Render `CreateProjectModal` with `project={project}` prop

### MODAL CHANGES
```jsx
// Accept project prop
const CreateProjectModal = ({ isOpen, onClose, project = null }) => {
  const isEditing = !!project
  
  // Initialize form with project data if editing
  const [formData, setFormData] = useState({
    name: project?.name || '',
    description: project?.description || '',
    startDate: project?.startDate || '',
    endDate: project?.endDate || '',
    assignedEmployees: project?.assignedEmployees || []
  })
  
  // Reset form when project prop changes
  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name,
        description: project.description || '',
        startDate: project.startDate,
        endDate: project.endDate,
        assignedEmployees: project.assignedEmployees || []
      })
    }
  }, [project])
  
  const handleSubmit = (e) => {
    if (isEditing) {
      updateProject(project.id, formData)
    } else {
      addProject({ id: generateId('proj'), ...formData })
    }
  }
  
  return (
    <Modal title={isEditing ? "Edit Project" : "Create New Project"}>
      {/* form fields */}
      <Button>{isEditing ? "Save Changes" : "Create Project"}</Button>
    </Modal>
  )
}
```

### ADD DESCRIPTION FIELD
```jsx
<div>
  <label className="label">Description (Optional)</label>
  <textarea
    value={formData.description}
    onChange={(e) => handleChange('description', e.target.value)}
    placeholder="Project description..."
    className="input min-h-[100px]"
    rows={3}
  />
</div>
```

Please implement edit mode for projects.
```

---

## 📝 PROMPT: Issue #8 - Implement Task Update Source Separation

```
## TASK: Separate Task Updates by Source (Admin vs Webhook)

### CONTEXT
I have a WhatsApp Task Manager where tasks can be updated in two ways:
1. **Admin drag-and-drop**: Admin drags task between Kanban columns
2. **Webhook response**: Employee clicks WhatsApp button, webhook updates task

### PROBLEM
Need to ensure admin drag-and-drop NEVER triggers WhatsApp messages, while webhook responses DO send confirmation messages. Currently this works by accident (separate endpoints), but it's not explicit and could break if someone adds notifications to the task update endpoint.

### REQUIREMENTS
1. Add explicit `source` parameter to differentiate update origins
2. Admin actions should NEVER send WhatsApp messages
3. Webhook actions should:
   - Auto-move task to appropriate column
   - Send confirmation message to employee
4. Add documentation comments in code

### FILES TO MODIFY
1. `src/context/AppContext.jsx`:
   - Add `source` parameter to `updateTask(id, updates, source = 'admin')`
   - Pass `updateSource` to API

2. `src/components/tasks/KanbanBoard.jsx`:
   - Call `updateTask(taskId, { status }, 'admin')` explicitly

3. `backend/app.py`:
   - In `update_task_route()`, extract and log `updateSource` parameter
   - Add documentation comments explaining the separation
   - Ensure webhook handler auto-moves tasks correctly

### FRONTEND CHANGES
```javascript
// AppContext.jsx
const updateTask = async (id, updates, source = 'admin') => {
  console.log(`📡 Updating task ${id} (source: ${source})`)
  await apiService.updateTask(id, { ...updates, updateSource: source })
  // ...
}

// KanbanBoard.jsx - handleDragEnd
if (task && task.status !== newStatus) {
  updateTask(task.taskId, { status: newStatus }, 'admin')
}
```

### BACKEND CHANGES
```python
@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task_route(task_id):
    """
    Update task via API call (typically from admin frontend).
    
    NOTE: This endpoint does NOT send WhatsApp messages.
    WhatsApp messages are ONLY sent via:
    1. POST /api/tasks/<id>/send-whatsapp-buttons (manual send)
    2. Confirmation in /api/webhook/whatsapp (response handling)
    
    Admin can freely move tasks between columns without triggering messages.
    """
    data = request.get_json()
    
    # Extract and log source (don't save to database)
    update_source = data.pop('updateSource', 'admin')
    print(f"📝 Task {task_id} update source: {update_source}")
    
    # Proceed with update (NO MESSAGING)
    result = database.update_task(task_id, data)
    # ...
```

### WEBHOOK SHOULD AUTO-MOVE TASKS
Update webhook handler to auto-move tasks based on response:
```python
# In webhook handler
if response_status == 'completed':
    update_data['status'] = 'pending_verification'  # Auto-move for review
elif response_status == 'not_completed':
    update_data['status'] = 'in_progress'  # Keep in progress
```

### EXPECTED BEHAVIOR
| Action | Source | WhatsApp Message? | Auto-Move? |
|--------|--------|-------------------|------------|
| Admin drags task | admin | NO | Manual only |
| Employee clicks Yes | webhook | YES (confirmation) | To pending_verification |
| Employee clicks No | webhook | YES (confirmation) | Stays in_progress |

Please implement this separation with clear documentation.
```

---

## 📝 COMBINED PROMPT: Fix All Issues At Once

If you want to fix all issues in one session, use this comprehensive prompt:

```
## TASK: Implement All Phase 2 Fixes for WhatsApp Task Manager

### CONTEXT
I have a WhatsApp Task Manager application (React frontend + Flask backend) that needs 8 issues fixed. Please implement all fixes in the recommended order.

### ISSUES TO FIX (in order)

1. **CRITICAL: Drag-and-drop bug** - Tasks disappear when dragging. Root cause: ID mismatch (`task.id` vs `task.taskId`). Fix in SortableTaskCard.jsx, KanbanBoard.jsx, AppContext.jsx.

2. **Kanban column rename** - Rename "Ready to Start" to "Unassigned Tasks". Update constants.js, implement auto-status logic based on assignedTo.

3. **Make fields optional** - Remove mandatory validation for assignedTo and dueDate in validators.js.

4. **Task update separation** - Add `source` parameter to updateTask() to differentiate admin actions from webhook responses. Admin = no messaging, webhook = auto-move + confirmation.

5. **"Create & Send" button** - Add "Create & Send to WhatsApp" button in TaskModal.jsx when employee is selected.

6. **Project statistics** - Show task count breakdown (unassigned/in-progress/pending/completed) on ProjectCard.jsx.

7. **Free drag-and-drop** - Add visual feedback for drop zones in KanbanColumn.jsx.

8. **Project edit** - Add edit mode to CreateProjectModal.jsx, add edit button to ProjectDetail.jsx.

### FILES TO MODIFY
- `src/utils/constants.js` - STATUS rename
- `src/utils/validators.js` - Remove mandatory fields
- `src/components/tasks/TaskModal.jsx` - Create & Send button
- `src/components/tasks/KanbanBoard.jsx` - Fix ID usage, pass source
- `src/components/tasks/SortableTaskCard.jsx` - Use taskId for drag
- `src/components/tasks/KanbanColumn.jsx` - Drop zone feedback
- `src/components/projects/ProjectCard.jsx` - Display stats
- `src/components/projects/CreateProjectModal.jsx` - Edit mode, description field
- `src/pages/ProjectDetail.jsx` - Edit button
- `src/context/AppContext.jsx` - Optimistic updates, source param, stats
- `src/services/api.service.js` - Unify IDs
- `backend/app.py` - Webhook auto-move, document separation
- `backend/database.py` - Status migration

### REQUIREMENTS
1. Implement each fix completely
2. Show exact code changes for each file
3. Maintain existing functionality
4. Follow the project's coding standards (see TECHNICAL_DESIGN_SPEC.md)
5. Add comments explaining key changes

### TESTING AFTER IMPLEMENTATION
- [ ] Drag task between columns → works, no disappearing
- [ ] Create task without employee → goes to Unassigned
- [ ] Create task with employee → goes to In Progress
- [ ] Click "Create & Send" → task created + WhatsApp sent
- [ ] Admin drags task → no WhatsApp message
- [ ] Employee clicks Yes → moves to Pending Verification
- [ ] Project card shows all 4 status counts
- [ ] Edit project → can change name, description, dates, team

Please implement all fixes and show the complete code changes.
```

---

## 🔑 TIPS FOR USING THESE PROMPTS

1. **Always provide TECHNICAL_DESIGN_SPEC.md first** - This gives the LLM context about coding standards, architecture, and conventions.

2. **Use one prompt at a time** - Fixing issues one by one is more reliable than trying to fix everything at once.

3. **Test after each fix** - Run the app and verify the fix works before moving to the next issue.

4. **Follow the recommended order** - Issue #1 is critical and blocks other issues. Issue #3 affects Issue #2.

5. **Provide file contents if asked** - The LLM may need to see current file contents to make accurate changes.

6. **Review changes before applying** - Always understand what changes are being made before applying them.

