# Complete Step-by-Step Implementation Guide
## WhatsApp Task Manager MVP - Backend Integration

**Purpose:** This guide is designed to be fed to an LLM (like Claude, GPT-4, etc.) to generate code incrementally, one stage at a time. Each stage builds on the previous one, minimizing bugs and errors.

**Target User:** Non-developer building MVP proof-of-concept  
**Current Status:** ✅ Frontend complete (React + localStorage)  
**Goal:** Connect frontend to backend + WhatsApp integration  
**Budget:** Free tier only (no paid services)

---

## ⚠️ **IMPORTANT: READ THIS FIRST!**

### **Before Using Any LLM Prompt:**

**ALWAYS prepend the Technical Design Specification to your LLM prompts!**

**How to use:**
1. **Copy the entire `TECHNICAL_DESIGN_SPEC.md` file**
2. **Then copy the stage-specific prompt from this guide**
3. **Combine them:** Paste Design Spec first, then stage prompt
4. **Send to LLM** (Claude, GPT-4, etc.)

**Why?** The Technical Design Spec provides:
- ✅ Project context and architecture
- ✅ Coding standards and best practices
- ✅ Database schema and API conventions
- ✅ Error handling patterns
- ✅ Security guidelines

**Result:** Senior engineer-level code quality, consistent with project standards.

---

## 🎯 **ARCHITECTURE DECISION: Option C (Hybrid)**

### **Why Option C (Flask Backend + Kapso WhatsApp) is Best for Free Tier:**

**Option B (Kapso Functions Only):**
- ❌ Limited by Kapso platform
- ❌ Harder to debug
- ❌ Less control over data
- ❌ Might hit free tier limits faster

**Option C (Flask + Kapso):**
- ✅ Flask runs FREE on PythonAnywhere/Render/Railway free tiers
- ✅ Only use Kapso for WhatsApp (minimal API calls)
- ✅ Full control over your data
- ✅ Easy to debug and test locally
- ✅ Can upgrade later without being locked in

### **Free Tier Strategy:**
- **Flask Backend:** Free hosting (PythonAnywhere free tier = $0/month)
- **Kapso WhatsApp:** Free tier (usually 2,000 messages/month)
- **For 3 employees:** ~90 messages/month (well under limit)
- **Total Cost: $0/month** ✅

### **Sandbox vs Real Number:**
- **Development/Testing:** Use Kapso Sandbox (free, works with your test number)
- **MVP Demo:** Use "Bring Your Own SIM" (free, works with real employees)
- **No paid number needed** for MVP ✅

### **When to Pay $25/month:**
- Only if you exceed free tier limits
- Only after MVP proves successful
- Start free, upgrade if needed

---

## 📋 **STAGE-BY-STAGE IMPLEMENTATION**

**Total Stages: 8**  
**Time per Stage: 1-2 hours**  
**Total Time: 1-2 days**

---

## ⚠️ **MANUAL STEPS SUMMARY (What You Must Do vs What LLM Generates)**

**Quick Reference - All Manual Steps Across All Stages:**

| Stage | Manual Steps (You Do) | Code Steps (LLM Generates) |
|-------|----------------------|---------------------------|
| **1** | Create `backend/` folder<br>Install Python/pip<br>Run `pip install`<br>Run Flask server | `app.py`, `requirements.txt`, `config.py` |
| **2** | Restart Flask server<br>Verify `database.db` created | `database.py` + updates |
| **3** | Start Flask server<br>Start React server<br>Test in browser | `api.service.js` + updates |
| **4** | Restart Flask server<br>Test API with curl<br>Test in React | Database + API updates |
| **5** | Restart Flask server<br>Test API with curl<br>Test Kanban drag-drop | Task API + frontend updates |
| **5.5** | ⚠️ **ALL MANUAL**<br>Kapso dashboard setup<br>Get API key<br>Connect WhatsApp<br>Get Phone Number ID | None (all manual) |
| **6** | Update `config.py` with credentials<br>Restart Flask server<br>Test sending message | `kapso_service.py` + updates |
| **7 Part A** | ⚠️ **ALL MANUAL**<br>Create workflow in Kapso<br>Configure all nodes<br>Set webhook URLs<br>Activate workflow<br>Copy Workflow ID | None (all manual) |
| **7 Part B** | Update `config.py` with Workflow ID<br>Set up ngrok<br>Update webhook URLs in Kapso<br>Restart Flask server<br>Test workflow | `scheduler.py` + updates |
| **8** | Start both servers<br>Test WhatsApp button in React | Frontend updates |

**Key Points:**
- ✅ **Stages 1-5, 8:** Mostly code (LLM generates), you just run/test
- ⚠️ **Stage 5.5:** 100% manual (Kapso dashboard)
- ⚠️ **Stage 7 Part A:** 100% manual (Kapso workflow creation)
- ⚠️ **Stage 6 & 7 Part B:** Mix of manual (config updates) + code (LLM generates)

---

## ✅ **STAGE 0: PREREQUISITES**

### **What You Already Have:**
- ✅ React frontend with 27 components
- ✅ Dashboard, Projects, Kanban board
- ✅ localStorage service (mock data)
- ✅ Task management UI
- ✅ Employee management UI
- ✅ Timer settings UI

### **What You Need to Install (Manual Steps):**

**Before Starting Stage 1:**

1. **Python 3.8+ (if not installed):**
   ```bash
   # Check if installed:
   python --version
   
   # If not installed:
   # Mac: brew install python3
   # Windows: Download from python.org
   # Linux: sudo apt-get install python3
   ```

2. **pip (Python package manager):**
   ```bash
   # Usually comes with Python
   # Check: pip --version
   
   # If not installed:
   # Mac: python3 -m ensurepip --upgrade
   # Linux: sudo apt-get install python3-pip
   ```

3. **curl (for testing APIs):**
   ```bash
   # Check if installed:
   curl --version
   
   # Usually pre-installed on Mac/Linux
   # Windows: Comes with Git Bash or download separately
   ```

4. **Webhook Testing Tool (for Stage 7 - ONLY if testing locally):**
   
   **⚠️ You ONLY need this if testing webhooks locally!**
   
   **Option A: ngrok (if you choose this)**
   ```bash
   # Install:
   # Mac: brew install ngrok
   # Windows: choco install ngrok
   # Or download from: https://ngrok.com/download
   
   # Sign up for free account at ngrok.com
   # Get authtoken from dashboard
   # Run: ngrok config add-authtoken YOUR_TOKEN
   ```
   
   **Option B: localtunnel (easier, no signup)**
   ```bash
   npm install -g localtunnel
   # Then run: lt --port 5000
   ```
   
   **Option C: Deploy to cloud (BEST for MVP demo)**
   - Use PythonAnywhere, Render, or Railway (all free)
   - Get permanent public URL
   - No tunneling needed!
   - See Stage 7, Step 10 for details
   
   **Recommendation:** For MVP demo, use Option C (deploy to cloud). Skip ngrok entirely!

**Optional but Recommended:**
- **Postman** (GUI for API testing instead of curl)
- **VS Code** or any code editor

### **Virtual Environment Setup (Important!)**

**Why use venv?**
- ✅ Isolates Python packages (won't conflict with other projects)
- ✅ Keeps project dependencies separate
- ✅ Easy to recreate environment
- ✅ Best practice for Python projects

**How to set up (will be done in Stage 1):**
```bash
# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate    # Windows

# Install packages
pip install -r requirements.txt

# When done
deactivate
```

### **What's Next:**
Replace localStorage with real backend API calls, one stage at a time.

---

## 📋 **STAGE 1: Flask Backend Setup (30 minutes)**

### **Goal:** Create basic Flask server that runs locally

### **⚠️ MANUAL STEPS (You Do These):**
1. **Create backend folder:**
   ```bash
   mkdir backend
   cd backend
   ```

2. **Verify Python is installed:**
   ```bash
   python --version
   # Should show Python 3.8 or higher
   # Or try: python3 --version
   ```

3. **Create Python virtual environment (venv):**
   ```bash
   # Mac/Linux:
   python3 -m venv venv
   
   # Windows:
   python -m venv venv
   
   # This creates a 'venv' folder in backend/
   ```

4. **Activate virtual environment:**
   ```bash
   # Mac/Linux:
   source venv/bin/activate
   
   # Windows (Command Prompt):
   venv\Scripts\activate
   
   # Windows (PowerShell):
   venv\Scripts\Activate.ps1
   
   # You should see (venv) in your terminal prompt
   ```

5. **Verify pip is installed:**
   ```bash
   pip --version
   # Should show pip version
   ```

6. **After LLM generates code, install dependencies:**
   ```bash
   pip install -r requirements.txt
   # This installs packages ONLY in venv, not system-wide
   ```

7. **Run Flask server:**
   ```bash
   python app.py
   ```

8. **When done working, deactivate venv:**
   ```bash
   deactivate
   # Removes (venv) from prompt
   ```

**✅ LLM will generate:** `app.py`, `requirements.txt`, `config.py` files

### **Files to Create:**
1. `backend/app.py` - Main Flask application
2. `backend/requirements.txt` - Python dependencies
3. `backend/config.py` - Configuration file

### **LLM Prompt for Stage 1:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Create a basic Flask backend application for a task management system.

REQUIREMENTS:
1. Create backend/app.py with:
   - Flask app initialization
   - CORS enabled (allow all origins for development)
   - One test route: GET /api/health that returns {"status": "ok"}
   - Run on port 5000
   - Add print statements for debugging

2. Create backend/requirements.txt with:
   - Flask==3.0.0
   - flask-cors==4.0.0
   - python-dotenv==1.0.0

3. Create backend/config.py with:
   - FLASK_ENV = "development"
   - PORT = 5000
   - Comments for future Kapso API keys

4. Add .gitignore to backend/ folder:
   - __pycache__/
   - *.pyc
   - .env
   - database.db
   - venv/          # Virtual environment folder
   - *.pyc
   - __pycache__/

Keep code simple with heavy comments. Add error handling.
```

### **How to Test Stage 1:**

```bash
# Navigate to backend folder
cd backend

# Activate virtual environment (if not already activated)
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies (installs only in venv)
pip install -r requirements.txt

# Run Flask server
python app.py

# In another terminal, test:
curl http://localhost:5000/api/health

# Should return: {"status": "ok"}

# When done, deactivate venv:
deactivate
```

### **✅ Stage 1 Complete When:**
- [ ] Flask server starts without errors
- [ ] `/api/health` returns `{"status": "ok"}`
- [ ] No errors in terminal

---

## 📋 **STAGE 2: Database Setup (45 minutes)**

### **Goal:** Create SQLite database with employees and tasks tables

### **⚠️ MANUAL STEPS (You Do These):**
1. **After LLM generates code, restart Flask server:**
   ```bash
   # Stop current server (Ctrl+C)
   # Start again
   python backend/app.py
   ```

2. **Verify database file is created:**
   ```bash
   # Check if database.db exists
   ls backend/database.db
   # Should show the file
   ```

**✅ LLM will generate:** `database.py` and update `app.py`, `config.py`

### **Files to Create:**
1. `backend/database.py` - Database functions
2. Update `backend/config.py` - Add database path

### **LLM Prompt for Stage 2:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Create database.py for SQLite database operations.

REQUIREMENTS:
1. Create backend/database.py with:

   - Function: init_db()
     * Creates two tables: employees and tasks
     * Hardcodes 3 employees:
       - id=1, name="Rajesh Kumar", phone="+919876543210"
       - id=2, name="Priya Singh", phone="+919876543211"
       - id=3, name="Amit Patel", phone="+919876543212"
     * Prints success message

   - Function: get_employees()
     * Returns list of all 3 employees as list of dicts
     * Format: [{"id": 1, "name": "...", "phone": "..."}, ...]

   - Function: get_employee_by_id(employee_id)
     * Returns single employee dict or None

   - Function: get_projects()
     * Returns empty list for now (we'll add projects later)

   - Function: get_tasks(project_id=None)
     * Returns empty list for now (we'll add tasks later)

2. Update backend/config.py:
   - Add: DATABASE_PATH = "database.db"

3. Update backend/app.py:
   - Import database module
   - Call init_db() when app starts
   - Add route: GET /api/employees
     * Calls get_employees()
     * Returns JSON: {"employees": [...]}

DATABASE SCHEMA:
employees table:
- id (INTEGER PRIMARY KEY)
- name (TEXT NOT NULL)
- phone (TEXT NOT NULL UNIQUE)
- role (TEXT) - "Developer", "Designer", "Tester"
- created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

tasks table:
- id (INTEGER PRIMARY KEY)
- task_id (TEXT UNIQUE) - e.g., "Task_101"
- project_id (TEXT) - matches frontend project.id
- title (TEXT NOT NULL)
- description (TEXT)
- employee_id (INTEGER) - foreign key to employees
- due_date (TEXT) - ISO date string
- priority (TEXT) - "high", "medium", "low"
- status (TEXT) - "ready_to_start", "in_progress", "pending_verification", "completed"
- whatsapp_sent (BOOLEAN DEFAULT 0)
- created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- updated_at (TIMESTAMP)

projects table:
- id (TEXT PRIMARY KEY) - matches frontend project.id format
- name (TEXT NOT NULL)
- start_date (TEXT) - ISO date string
- end_date (TEXT) - ISO date string
- color (TEXT) - hex color code
- created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

Add heavy comments explaining each function. Include error handling.
```

### **How to Test Stage 2:**

```bash
# Restart Flask server
python backend/app.py

# Test employees endpoint
curl http://localhost:5000/api/employees

# Should return JSON with 3 employees
```

### **✅ Stage 2 Complete When:**
- [ ] `database.db` file is created
- [ ] GET /api/employees returns 3 employees
- [ ] No errors in terminal

---

## 📋 **STAGE 3: Connect Frontend to Backend - Employees (30 minutes)**

### **Goal:** Replace localStorage employee calls with API calls

### **⚠️ MANUAL STEPS (You Do These):**
1. **Make sure Flask backend is running:**
   ```bash
   # In backend folder
   python app.py
   # Should show: * Running on http://127.0.0.1:5000
   ```

2. **Start React frontend (in separate terminal):**
   ```bash
   # In whatsapp-task-manager folder
   npm run dev
   # Should show: Local: http://localhost:3000
   ```

3. **Open browser and test:**
   - Go to http://localhost:3000
   - Navigate to Employees page
   - Check browser console (F12) for any errors

**✅ LLM will generate:** `api.service.js` and update `AppContext.jsx`

### **Files to Update:**
1. `src/services/api.service.js` - New API service
2. `src/context/AppContext.jsx` - Replace localStorage with API calls

### **LLM Prompt for Stage 3:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Update React frontend to fetch employees from Flask backend instead of localStorage.

REQUIREMENTS:
1. Create src/services/api.service.js:
   - Base URL: const API_BASE_URL = "http://localhost:5000/api"
   - Function: async getEmployees()
     * Fetches from GET /api/employees
     * Returns array of employees
     * Handles errors with try/catch

2. Update src/context/AppContext.jsx:
   - Import apiService from './services/api.service'
   - In loadData(), replace:
     * OLD: setEmployees(storageService.getEmployees())
     * NEW: const employees = await apiService.getEmployees()
     *       setEmployees(employees)
   - Make loadData() async
   - Add error handling (show toast on error)

3. Keep localStorage as fallback:
   - If API call fails, use localStorage data
   - Show warning toast: "Using offline data"

Add console.log for debugging. Handle loading states.
```

### **How to Test Stage 3:**

```bash
# Start Flask backend
python backend/app.py

# Start React frontend (in another terminal)
cd whatsapp-task-manager
npm run dev

# Open browser: http://localhost:3000
# Navigate to Employees page
# Should show 3 employees from database
```

### **✅ Stage 3 Complete When:**
- [ ] Employees page loads data from Flask API
- [ ] No errors in browser console
- [ ] Data matches database

---

## 📋 **STAGE 4: Projects API & Frontend Connection (1 hour)**

### **Goal:** Add projects CRUD endpoints and connect frontend

### **⚠️ MANUAL STEPS (You Do These):**
1. **After LLM generates code, restart Flask server:**
   ```bash
   # Stop server (Ctrl+C) and restart
   python backend/app.py
   ```

2. **Test API endpoints manually (optional but recommended):**
   ```bash
   # Test creating project
   curl -X POST http://localhost:5000/api/projects \
     -H "Content-Type: application/json" \
     -d '{"name": "Test", "startDate": "2025-01-01", "endDate": "2025-03-31", "assignedEmployees": [1]}'
   
   # Test getting projects
   curl http://localhost:5000/api/projects
   ```

3. **Test in React frontend:**
   - Make sure both Flask and React are running
   - Open http://localhost:3000
   - Try creating a new project from dashboard
   - Check if it appears in the list

**✅ LLM will generate:** Updates to `database.py`, `app.py`, `api.service.js`, `AppContext.jsx`

### **Files to Create/Update:**
1. `backend/database.py` - Add project functions
2. `backend/app.py` - Add project routes
3. `src/services/api.service.js` - Add project API calls
4. `src/context/AppContext.jsx` - Replace project localStorage calls

### **LLM Prompt for Stage 4:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Add projects API endpoints and connect React frontend.

REQUIREMENTS:
1. Update backend/database.py:
   - Function: create_project(project_data)
     * project_data = {id, name, start_date, end_date, color, assigned_employees}
     * Insert into projects table
     * Also insert into project_employees junction table (if needed)
     * Return created project

   - Function: get_projects()
     * Return all projects with assigned employee IDs
     * Format: [{id, name, start_date, end_date, color, assigned_employees: [1,2,3], ...}]

   - Function: get_project_by_id(project_id)
     * Return single project or None

   - Function: update_project(project_id, updates)
     * Update project fields
     * Return updated project

   - Function: delete_project(project_id)
     * Delete project and related tasks

2. Update backend/app.py:
   - POST /api/projects
     * Body: {name, start_date, end_date, assignedEmployees}
     * Generate project.id (e.g., "proj_001")
     * Generate random color
     * Call create_project()
     * Return created project

   - GET /api/projects
     * Call get_projects()
     * Return {"projects": [...]}

   - GET /api/projects/:projectId
     * Call get_project_by_id()
     * Return project or 404

   - PUT /api/projects/:projectId
     * Update project
     * Return updated project

   - DELETE /api/projects/:projectId
     * Call delete_project()
     * Return success

3. Update src/services/api.service.js:
   - async getProjects()
   - async getProjectById(id)
   - async createProject(projectData)
   - async updateProject(id, updates)
   - async deleteProject(id)

4. Update src/context/AppContext.jsx:
   - Replace all storageService project calls with apiService calls
   - Keep localStorage as fallback for offline mode

Add error handling. Return proper HTTP status codes.
```

### **How to Test Stage 4:**

```bash
# Test creating project via API
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "startDate": "2025-01-01",
    "endDate": "2025-03-31",
    "assignedEmployees": [1, 2]
  }'

# Test getting projects
curl http://localhost:5000/api/projects

# Test in React frontend:
# - Create new project from dashboard
# - Should appear in project list
```

### **✅ Stage 4 Complete When:**
- [ ] Can create project from React frontend
- [ ] Projects appear in dashboard
- [ ] Projects persist in database
- [ ] Can view project details

---

## 📋 **STAGE 5: Tasks API & Frontend Connection (1.5 hours)**

### **Goal:** Add tasks CRUD endpoints and connect Kanban board

### **⚠️ MANUAL STEPS (You Do These):**
1. **After LLM generates code, restart Flask server:**
   ```bash
   python backend/app.py
   ```

2. **Test API endpoints manually (optional):**
   ```bash
   # Test creating task (replace proj_001 with actual project ID)
   curl -X POST http://localhost:5000/api/tasks \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test Task",
       "description": "Test",
       "projectId": "proj_001",
       "assignedTo": 1,
       "dueDate": "2025-01-25",
       "priority": "high",
       "status": "ready_to_start"
     }'
   
   # Test getting tasks
   curl "http://localhost:5000/api/tasks?projectId=proj_001"
   ```

3. **Test in React frontend:**
   - Make sure both Flask and React are running
   - Open a project in React
   - Create a new task
   - Try dragging task between Kanban columns
   - Verify task updates persist

**✅ LLM will generate:** Updates to `database.py`, `app.py`, `api.service.js`, `AppContext.jsx`, `ProjectDetail.jsx`

### **Files to Create/Update:**
1. `backend/database.py` - Add task functions
2. `backend/app.py` - Add task routes
3. `src/services/api.service.js` - Add task API calls
4. `src/context/AppContext.jsx` - Replace task localStorage calls

### **LLM Prompt for Stage 5:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Add tasks API endpoints and connect React Kanban board.

REQUIREMENTS:
1. Update backend/database.py:
   - Function: create_task(task_data)
     * task_data = {title, description, projectId, assignedTo, dueDate, priority, status}
     * Generate task_id (e.g., "task_001")
     * Insert into tasks table
     * Return created task

   - Function: get_tasks(project_id=None)
     * If project_id provided, filter by project
     * Join with employees table to get employee name
     * Return list of tasks with employee info

   - Function: get_task_by_id(task_id)
     * Return single task with employee info

   - Function: update_task(task_id, updates)
     * Update task fields
     * Set updated_at timestamp
     * Return updated task

   - Function: delete_task(task_id)
     * Delete task

2. Update backend/app.py:
   - POST /api/tasks
     * Body: {title, description, projectId, assignedTo, dueDate, priority, status}
     * Call create_task()
     * Return created task

   - GET /api/tasks?projectId=X
     * Query param: projectId (optional)
     * Call get_tasks(project_id)
     * Return {"tasks": [...]}

   - GET /api/tasks/:taskId
     * Call get_task_by_id()
     * Return task or 404

   - PUT /api/tasks/:taskId
     * Body: {status, title, description, ...} (partial updates)
     * Call update_task()
     * Return updated task

   - DELETE /api/tasks/:taskId
     * Call delete_task()
     * Return success

3. Update src/services/api.service.js:
   - async getTasks(projectId)
   - async getTaskById(id)
   - async createTask(taskData)
   - async updateTask(id, updates)
   - async deleteTask(id)

4. Update src/context/AppContext.jsx:
   - Replace all storageService task calls with apiService calls
   - Update KanbanBoard to fetch tasks from API
   - Update TaskModal to save via API

5. Update src/pages/ProjectDetail.jsx:
   - Fetch tasks on component mount
   - Refresh tasks after create/update

Add error handling. Handle loading states in UI.
```

### **How to Test Stage 5:**

```bash
# Test creating task
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Test description",
    "projectId": "proj_001",
    "assignedTo": 1,
    "dueDate": "2025-01-25",
    "priority": "high",
    "status": "ready_to_start"
  }'

# Test getting tasks
curl "http://localhost:5000/api/tasks?projectId=proj_001"

# Test in React:
# - Open project
# - Create task
# - Drag task between columns
# - Should update via API
```

### **✅ Stage 5 Complete When:**
- [ ] Can create tasks from React
- [ ] Tasks appear in Kanban board
- [ ] Can drag tasks between columns (updates via API)
- [ ] Tasks persist in database

---

## 📋 **STAGE 5.5: Kapso Dashboard Setup (Manual Steps - 30 minutes)**

### **Goal:** Set up Kapso account, connect WhatsApp, and get API credentials

### **⚠️ IMPORTANT: These steps are MANUAL - Do them in Kapso Dashboard (not via LLM)**

**Summary:**
- ✅ **What you'll do:** Manual steps in Kapso web dashboard
- ❌ **What LLM CANNOT do:** Kapso dashboard operations (must be done by you)
- ✅ **What LLM WILL do:** Generate backend code in Stage 6 (after you provide credentials)

**You'll get:**
1. API Key (for `backend/config.py`)
2. Phone Number ID (for `backend/config.py`)
3. Connected WhatsApp (sandbox or real number)

**Then:** Use these credentials in Stage 6 (LLM generates code)

---

### **Step 1: Create Kapso Account & Get API Key**

1. **Sign up for Kapso:**
   - Go to https://kapso.ai
   - Click "Sign Up" or "Get Started"
   - Create account (use free tier)

2. **Get API Key:**
   - Log into Kapso dashboard
   - Navigate to **Settings** → **API Keys**
   - Click **"Create API Key"**
   - Name it: `task_management_backend`
   - **Copy the API key** - Save it securely (you'll need it for `backend/config.py`)
   - ⚠️ **Important:** API keys are only shown once! Copy it immediately.

---

### **Step 2: Set Up WhatsApp - Choose Your Method**

You have **TWO options** for MVP:

#### **Option A: Sandbox Mode (For Development/Testing) - RECOMMENDED FOR NOW**

**Use this for:** Testing and development before MVP demo

**Steps:**
1. In Kapso dashboard, go to **WhatsApp** → **Sandbox**
2. Click **"Add Test Number"**
3. Enter **your personal WhatsApp phone number** (the one you'll test from)
   - Format: Include country code, e.g., `919876543210` (no + sign)
4. Click **"Create"**
5. You'll receive a verification code on WhatsApp
6. Enter the code to verify
7. ✅ **Done!** You can now send/receive test messages

**Limitations:**
- Only works with your test number (the one you added)
- Can't send to real employees yet
- Perfect for development and testing

**For MVP Demo:** You'll need to switch to Option B below.

---

#### **Option B: Bring Your Own SIM (For MVP Demo)**

**Use this for:** Real MVP demo with actual employees

**Steps:**
1. In Kapso dashboard, go to **Connected Numbers** → **Connect WhatsApp Business**
2. Select **"Bring your own SIM"**
3. **Log in with Facebook** account
   - You need a Facebook account linked to WhatsApp Business
   - If you don't have one, create it first
4. **Enter your phone number** (the SIM card you'll use for WhatsApp Business)
   - Format: Include country code, e.g., `919876543210` (no + sign)
5. **Verify with SMS code** sent to your SIM
6. Enter the verification code
7. ✅ **Done!** You now have API access with a real WhatsApp Business number

**Benefits:**
- Can send to any WhatsApp number
- Works for real MVP demo
- Free (just need Kapso free tier)

---

### **Step 3: Get Phone Number ID**

After connecting WhatsApp (either sandbox or real):

1. In Kapso dashboard, go to **Connected Numbers**
2. Find your connected WhatsApp number
3. Click on it to view details
4. **Copy the Phone Number ID** - It looks like: `647015955153740`
5. Save it - you'll need it for `backend/config.py`

**Where to find it:**
- Sometimes shown as `phone_number_id` in the number details
- Or in the API response when connecting
- Check the URL when viewing number details

---

### **Step 4: Test Sending a Message (Optional)**

Before moving to code, test manually:

1. In Kapso dashboard, go to **WhatsApp** → **Send Message** (or similar)
2. Select your connected number
3. Enter a test phone number (your own if using sandbox)
4. Send a test message
5. Check WhatsApp - you should receive it
6. ✅ If this works, you're ready for Stage 6!

---

### **✅ Stage 5.5 Complete When:**
- [ ] Kapso account created
- [ ] API key obtained and saved
- [ ] WhatsApp connected (sandbox OR real number)
- [ ] Phone Number ID copied and saved
- [ ] Test message sent successfully (optional but recommended)

**Save these values - you'll need them in Stage 6:**
- `KAPSO_API_KEY` = Your API key from Step 1
- `PHONE_NUMBER_ID` = Your phone number ID from Step 3

---

## ⚠️ **KAPSO SANDBOX LIMITATIONS (Important!)**

### **What You CAN Do in Sandbox:**
| Feature | Supported | Notes |
|---------|-----------|-------|
| **Text Messages** | ✅ Yes | Send plain text to authorized test numbers |
| **Interactive Buttons** | ✅ Yes | Up to 3 reply buttons (Yes/No/Maybe) |
| **Interactive Lists** | ✅ Yes | Dropdown menus with options |
| **CTA URL Buttons** | ✅ Yes | Buttons that open URLs |
| **Location Requests** | ✅ Yes | Request user's current location |
| **Media Messages** | ✅ Yes | Images, videos, documents, audio |
| **Receive Messages** | ✅ Yes | Via webhooks (whatsapp.message.received) |

### **What You CANNOT Do in Sandbox:**
| Feature | Supported | Workaround |
|---------|-----------|------------|
| **Template Messages** | ❌ No | Use text + interactive buttons instead |
| **Multiple Recipients** | ❌ No | Only pre-authorized test numbers |
| **Business-Initiated Templates** | ❌ No | User must message first within 24hrs |
| **WhatsApp Flows (Forms)** | ⚠️ Limited | Use interactive buttons for simple choices |
| **Broadcast Messages** | ❌ No | Send individually in sandbox |

### **Recommended Approach for MVP:**
Since sandbox doesn't support templates, use this pattern:

1. **Send Task with Interactive Buttons:**
   ```
   📋 New Task Assigned!
   
   Task: Fix login bug
   Priority: 🔴 HIGH
   Due: 2025-01-20
   
   Have you completed this task?
   
   [✅ Yes, Completed] [❌ No, Not Yet]
   ```

2. **Receive Button Response via Webhook:**
   - User clicks "Yes, Completed" → webhook receives button_id = "completed"
   - Update task status in database
   - Send confirmation message

3. **No Complex Workflows Needed:**
   - Direct API calls work perfectly
   - Simpler to debug and maintain
   - Free tier friendly

### **When You Need Real Templates:**
- Upgrade to "Bring Your Own SIM" (free with your phone)
- OR use Kapso's paid tier with Meta-approved templates
- Templates required for: 24hr+ messaging, notifications, marketing

---

## 📋 **STAGE 6: Kapso WhatsApp Integration - Setup (45 minutes)**

### **Goal:** Configure Kapso API in code and send first test message

### **⚠️ PREREQUISITE:** Complete Stage 5.5 first (Kapso dashboard setup)

### **⚠️ MANUAL STEPS (You Do These):**
1. **Update config.py with your Kapso credentials:**
   - Open `backend/config.py`
   - Replace placeholders with values from Stage 5.5:
     ```python
     KAPSO_API_KEY = "paste_your_api_key_here"
     PHONE_NUMBER_ID = "paste_your_phone_number_id_here"
     ```
   - Save the file
   - ⚠️ **Never commit this file to Git** (it's in .gitignore)

2. **After LLM generates code, restart Flask server:**
   ```bash
   python backend/app.py
   ```

3. **Test sending message:**
   ```bash
   # Make sure you have a task in database first
   # Replace task_001 with actual task ID
   curl -X POST http://localhost:5000/api/tasks/task_001/send-whatsapp
   ```

4. **Check WhatsApp:**
   - If using sandbox: Check your authorized test number
   - If using real number: Check employee's WhatsApp
   - Should receive task assignment message

**✅ LLM will generate:** `kapso_service.py` and updates to `app.py`, `config.py`

### **Files to Create/Update:**
1. `backend/config.py` - Add Kapso credentials
2. `backend/kapso_service.py` - Kapso API wrapper
3. `backend/app.py` - Add WhatsApp send endpoint

### **LLM Prompt for Stage 6:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Add Kapso WhatsApp API integration for sending task messages.

REQUIREMENTS:
1. Update backend/config.py:
   - KAPSO_API_KEY = "your_api_key_here" (from Kapso dashboard)
   - PHONE_NUMBER_ID = "your_phone_number_id" (from Kapso)
   - KAPSO_API_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
   - Add comments explaining where to find these values

2. Create backend/kapso_service.py:
   - Function: send_text_message(phone_number, message_text)
     * Endpoint: POST {KAPSO_API_BASE}/{PHONE_NUMBER_ID}/messages
     * Headers: X-API-Key: {KAPSO_API_KEY}
     * Body: {
         "messaging_product": "whatsapp",
         "to": phone_number (without +, e.g., "919876543210"),
         "type": "text",
         "text": {"body": message_text}
       }
     * Return success/error response
     * Add error handling

   - Function: send_task_assignment(employee_phone, task_data)
     * Format message: "Hi {employee_name}, new task assigned:\n\nTask: {title}\nDescription: {description}\nDue: {due_date}\nPriority: {priority}"
     * Call send_text_message()
     * Return success/error

3. Update backend/app.py:
   - POST /api/tasks/:taskId/send-whatsapp
     * Get task from database
     * Get employee phone number
     * Call kapso_service.send_task_assignment()
     * Update task.whatsapp_sent = True
     * Return success/error

4. Add error handling:
   - If Kapso API fails, log error but don't crash
   - Return user-friendly error messages

Add print statements for debugging. Test with your own phone number first.
```


### **How to Test Stage 6:**

```bash
# Make sure Flask server is running
python backend/app.py

# In another terminal, test sending message
curl -X POST http://localhost:5000/api/tasks/task_001/send-whatsapp

# Check your WhatsApp - should receive message
# Check Flask terminal for logs
# If using sandbox, make sure you're testing with your authorized test number
```

### **✅ Stage 6 Complete When:**
- [ ] `config.py` updated with real Kapso credentials
- [ ] Can send WhatsApp message from API
- [ ] Message received on WhatsApp (sandbox or real number)
- [ ] No errors in terminal
- [ ] Task marked as whatsapp_sent in database

---

## 📋 **STAGE 7: Kapso Workflow Setup - EOD Status Collection (1.5 hours)**

### **Goal:** Create Kapso workflow for end-of-day status collection

### **⚠️ IMPORTANT: This stage has MANUAL steps (Kapso dashboard) + CODE steps (LLM)**

### **Files to Create/Update:**
1. `backend/kapso_service.py` - Add workflow trigger function
2. `backend/app.py` - Add webhook endpoint
3. `backend/scheduler.py` - Daily 5 PM trigger

---

### **PART A: Manual Steps - Create Workflow in Kapso Dashboard (30 minutes)**

**⚠️ These steps MUST be done manually in Kapso dashboard - LLM cannot do this!**

**Summary:**
- ✅ **What you'll do:** Create workflow visually in Kapso dashboard
- ❌ **What LLM CANNOT do:** Kapso workflow creation (must be done by you)
- ✅ **What LLM WILL do:** Generate backend code in Part B (after you provide Workflow ID)

**You'll create:**
- Workflow with nodes: Start → Send Buttons → Wait → Decide → Webhook
- Two paths: Completed (Yes) and Not Completed (No)
- Webhook URLs pointing to your backend

**Then:** Use Workflow ID in Part B (LLM generates code to trigger workflow)

#### **Step 1: Create New Workflow**

1. **Go to Kapso Dashboard:**
   - Navigate to **Workflows** (or **Functions** → **Workflows**)
   - Click **"Create Workflow"** or **"New Workflow"**

2. **Basic Setup:**
   - **Name:** `eod_task_status`
   - **Description:** "End of day task status collection workflow"
   - **Trigger Type:** Select **"API Call"** (so your backend can trigger it)
   - Click **"Create"** or **"Next"**

---

#### **Step 2: Configure Start Node**

1. **Start Node** (should be auto-created):
   - This node receives variables from your API call
   - **Variables to accept:**
     - `task_id` (text)
     - `employee_phone` (text)
     - `employee_name` (text)
   - These will be passed when your backend triggers the workflow

---

#### **Step 3: Add "Send Interactive Buttons" Node**

1. **Add Node:**
   - Click **"Add Node"** or drag from node palette
   - Select **"Send Interactive"** or **"Send Buttons"**

2. **Configure Buttons:**
   - **Type:** Select **"Buttons"**
   - **Body Text:** 
     ```
     Hi {{vars.employee_name}}, did you complete task {{vars.task_id}}?
     ```
   - **Footer Text (optional):** `Please respond by end of day`

3. **Add Buttons:**
   - **Button 1:**
     - **ID:** `btn_yes`
     - **Title:** `✅ Yes`
   - **Button 2:**
     - **ID:** `btn_no`
     - **Title:** `❌ No`
   - Click **"Save"** or **"Next"**

4. **Connect:** Draw line from Start node → Send Buttons node

---

#### **Step 4: Add "Wait for Response" Node**

1. **Add Node:**
   - Click **"Add Node"**
   - Select **"Wait for Response"** or **"Wait"**

2. **Configure:**
   - **Save response to variable:** `user_response`
   - **Timeout (optional):** 24 hours (or leave default)
   - Click **"Save"**

3. **Connect:** Send Buttons node → Wait for Response node

---

#### **Step 5: Add "Decide" Node (Route Based on Response)**

1. **Add Node:**
   - Click **"Add Node"**
   - Select **"Decide"** or **"Condition"**

2. **Configure Logic:**
   - **Logic Type:** Select **"Custom Function"** or **"Expression"**
   - **Function/Expression:**
     ```javascript
     // Check if user clicked "Yes" button
     if (context.vars.user_response && context.vars.user_response.includes('btn_yes')) {
       return 'completed';
     } else if (context.vars.user_response && context.vars.user_response.includes('btn_no')) {
       return 'not_completed';
     }
     return 'unknown';
     ```
   - Or use simpler expression if available:
     - If `user_response` contains `btn_yes` → return `completed`
     - If `user_response` contains `btn_no` → return `not_completed`

3. **Create Paths:**
   - **Path 1:** Label it `completed` (for Yes response)
   - **Path 2:** Label it `not_completed` (for No response)

4. **Connect:** Wait for Response node → Decide node

---

#### **Step 6: Path A - If Task Completed (Yes)**

1. **Add "Send Text" Node:**
   - Click **"Add Node"**
   - Select **"Send Text"** or **"Send Message"**
   - **Text:** `Great! Any notes? (Reply 'skip' if none)`
   - Connect from Decide node → `completed` path → Send Text node

2. **Add "Wait for Response" Node:**
   - Click **"Add Node"**
   - Select **"Wait for Response"**
   - **Save response to:** `completion_notes`
   - Connect: Send Text node → Wait for Response node

3. **Add "Webhook" Node:**
   - Click **"Add Node"**
   - Select **"Webhook"** or **"HTTP Request"**
   - **URL:** `https://your-backend-url.com/api/webhook/task-status`
     - ⚠️ **For local testing:** Use ngrok: `ngrok http 5000` → copy HTTPS URL
   - **Method:** `POST`
   - **Headers:**
     ```
     Content-Type: application/json
     ```
   - **Body Template (JSON):**
     ```json
     {
       "task_id": "{{vars.task_id}}",
       "employee_phone": "{{vars.employee_phone}}",
       "employee_name": "{{vars.employee_name}}",
       "status": "completed",
       "notes": "{{vars.completion_notes}}",
       "timestamp": "{{system.started_at}}"
     }
     ```
   - Connect: Wait for Response node → Webhook node

---

#### **Step 7: Path B - If Task Not Completed (No)**

1. **Add "Send Text" Node:**
   - Click **"Add Node"**
   - Select **"Send Text"**
   - **Text:** `Please explain why the task was not completed:`
   - Connect from Decide node → `not_completed` path → Send Text node

2. **Add "Wait for Response" Node:**
   - Click **"Add Node"**
   - Select **"Wait for Response"**
   - **Save response to:** `incomplete_reason`
   - Connect: Send Text node → Wait for Response node

3. **Add "Webhook" Node:**
   - Click **"Add Node"**
   - Select **"Webhook"**
   - **URL:** Same as Path A: `https://your-backend-url.com/api/webhook/task-status`
   - **Method:** `POST`
   - **Headers:** `Content-Type: application/json`
   - **Body Template:**
     ```json
     {
       "task_id": "{{vars.task_id}}",
       "employee_phone": "{{vars.employee_phone}}",
       "employee_name": "{{vars.employee_name}}",
       "status": "not_completed",
       "reason": "{{vars.incomplete_reason}}",
       "timestamp": "{{system.started_at}}"
     }
     ```
   - Connect: Wait for Response node → Webhook node

---

#### **Step 8: Add Confirmation Message (Optional)**

1. **Add "Send Text" Node** after webhook:
   - **Text:** `Thank you! Your response has been recorded. ✅`
   - Connect: Webhook node → Send Text node (for both paths)

---

#### **Step 9: Activate Workflow**

1. **Review Workflow:**
   - Check all nodes are connected correctly
   - Verify paths are correct
   - Test the flow visually

2. **Save Workflow:**
   - Click **"Save"** or **"Save Workflow"**

3. **Activate Workflow:**
   - Click **"Activate"** or toggle **"Active"** switch
   - ⚠️ **Important:** Workflow must be ACTIVE to work

4. **Copy Workflow ID:**
   - Find the **Workflow ID** in the URL or workflow details
   - It looks like: `wf_abc123xyz` or similar
   - **Copy and save it** - you'll need it for `backend/config.py`

---

#### **Step 10: Set Up Webhook URL (For Local Testing)**

**⚠️ Why You Need This:**
- Your Flask backend runs on `localhost:5000` (only accessible on your computer)
- Kapso workflow needs to send webhooks to your backend
- Kapso is on the internet and **cannot reach `localhost:5000` directly**
- You need a **public URL** that tunnels to your localhost

**You have 3 options:**

---

### **Option 1: ngrok (Recommended for Local Testing)**

**Pros:** Easy, reliable, HTTPS included  
**Cons:** Requires signup, free tier has limitations

1. **Install ngrok:**
   ```bash
   # Mac:
   brew install ngrok
   
   # Windows:
   choco install ngrok
   # OR download from https://ngrok.com/download
   ```

2. **Sign up (free):**
   - Go to https://ngrok.com
   - Create free account
   - Get authtoken from dashboard

3. **Configure:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

4. **Start ngrok:**
   ```bash
   ngrok http 5000
   # Keep this terminal open!
   ```

5. **Copy HTTPS URL:**
   - You'll see: `Forwarding: https://abc123.ngrok.io -> http://localhost:5000`
   - Copy: `https://abc123.ngrok.io`

6. **Update Webhook URLs in Kapso Workflow:**
   - Edit Webhook nodes in your workflow
   - Set URL to: `https://abc123.ngrok.io/api/webhook/task-status`
   - Save workflow

**⚠️ Note:** ngrok URL changes each time you restart (unless you pay). For MVP testing, this is fine.

---

### **Option 2: localtunnel (Free Alternative, No Signup)**

**Pros:** Free, no signup needed, simpler  
**Cons:** Less reliable, URLs change each time

1. **Install:**
   ```bash
   npm install -g localtunnel
   ```

2. **Start tunnel:**
   ```bash
   lt --port 5000
   # Keep this terminal open!
   ```

3. **Copy URL:**
   - You'll see: `your url is: https://random-name.loca.lt`
   - Copy this URL

4. **Update Webhook URLs in Kapso Workflow:**
   - Set URL to: `https://random-name.loca.lt/api/webhook/task-status`
   - Save workflow

**⚠️ Note:** URL changes each time. Free tier requires clicking "Continue" in browser once.

---

### **Option 3: Deploy Backend to Cloud (Best for MVP Demo)**

**Pros:** Permanent URL, no tunneling needed, works for demos  
**Cons:** Requires deployment setup

**Free Hosting Options:**

1. **PythonAnywhere (Easiest):**
   - Go to https://www.pythonanywhere.com
   - Sign up (free tier available)
   - Upload your backend code
   - Get URL: `https://yourusername.pythonanywhere.com`
   - Update webhook to: `https://yourusername.pythonanywhere.com/api/webhook/task-status`

2. **Render (Easy):**
   - Go to https://render.com
   - Connect GitHub repo
   - Auto-deploy
   - Get URL: `https://your-app.onrender.com`

3. **Railway (Easy):**
   - Go to https://railway.app
   - Connect GitHub
   - Auto-deploy
   - Get URL: `https://your-app.railway.app`

**For MVP Demo:** This is actually the BEST option because:
- ✅ Permanent URL (no changing URLs)
- ✅ Works for investor demos
- ✅ No need to keep ngrok running
- ✅ Free tier available

---

### **Which Option Should You Choose?**

| Scenario | Recommended Option |
|----------|-------------------|
| **Just testing locally** | Option 1 (ngrok) or Option 2 (localtunnel) |
| **MVP demo for investors** | Option 3 (Deploy to cloud) |
| **Quick testing** | Option 2 (localtunnel - fastest) |
| **Production later** | Option 3 (Cloud hosting) |

**For MVP:** I recommend **Option 3 (Deploy to cloud)** because:
- You'll need a public URL for demos anyway
- No need to keep ngrok running
- More professional for investors
- Free tier is enough for MVP

**For quick local testing:** Use **Option 2 (localtunnel)** - it's the fastest to set up.

---

### **✅ Part A Complete When:**
- [ ] Workflow created in Kapso dashboard
- [ ] All nodes configured correctly
- [ ] Workflow is ACTIVE
- [ ] Workflow ID copied and saved
- [ ] Webhook URL configured (ngrok for local, real URL for production)

---

### **PART B: Code Steps - LLM Prompt for Stage 7**

**⚠️ MANUAL STEPS BEFORE USING LLM:**

1. **Update config.py with Workflow ID:**
   - Open `backend/config.py`
   - Add/update:
     ```python
     WORKFLOW_ID = "paste_workflow_id_from_kapso_dashboard"
     ```
   - Paste the Workflow ID you copied from Kapso dashboard (Part A, Step 9)
   - Save the file

2. **Set up webhook URL (choose one option):**
   
   **Option A: Use ngrok (if testing locally)**
   ```bash
   # Start ngrok (in separate terminal):
   ngrok http 5000
   # Copy HTTPS URL and update webhook in Kapso
   ```
   
   **Option B: Use localtunnel (easier, no signup)**
   ```bash
   lt --port 5000
   # Copy URL and update webhook in Kapso
   ```
   
   **Option C: Deploy backend to cloud (RECOMMENDED for MVP)**
   - Deploy to PythonAnywhere/Render/Railway
   - Get permanent URL (e.g., https://your-app.onrender.com)
   - Update webhook to: https://your-app.onrender.com/api/webhook/task-status
   - No tunneling needed!
   
   **For MVP Demo:** Option C is best - permanent URL, no ngrok needed!

3. **Update webhook URLs in Kapso workflow:**
   - Go back to your workflow in Kapso dashboard
   - Edit the Webhook nodes (both Completed and Not Completed paths)
   - Update URL to: `https://your-ngrok-url.ngrok.io/api/webhook/task-status`
   - Save workflow again

**✅ LLM will generate:** Updates to `kapso_service.py`, `app.py`, and new `scheduler.py`

**Now use LLM to generate the backend code:**

### **LLM Prompt for Stage 7:**

2. Update backend/config.py:
   - WORKFLOW_ID = "your_workflow_id_from_kapso"

3. Update backend/kapso_service.py:
   - Function: trigger_eod_workflow(employee_phone, task_data)
     * Endpoint: POST https://api.kapso.ai/platform/v1/workflows/{WORKFLOW_ID}/executions
     * Headers: Authorization: Bearer {KAPSO_API_KEY}
     * Body: {
         "workflow_execution": {
           "phone_number": employee_phone,
           "phone_number_id": PHONE_NUMBER_ID,
           "variables": {
             "task_id": task_data.task_id,
             "employee_name": task_data.employee_name,
             "employee_phone": employee_phone
           }
         }
       }
     * Return success/error

4. Update backend/app.py:
   - POST /api/webhook/task-status
     * Receives from Kapso workflow:
       {
         "task_id": "...",
         "status": "completed" or "not_completed",
         "notes": "...",
         "reason": "..."
       }
     * Update task in database:
       - Set status to "completed" or "pending_verification"
       - Save notes/reason
     * Return {"success": true}

   - POST /api/trigger-eod (manual trigger for testing)
     * Get all pending tasks
     * For each task, trigger workflow
     * Return list of triggered tasks

5. Create backend/scheduler.py:
   - Use APScheduler
   - Schedule job: daily at 5:00 PM
   - Function: trigger_eod_for_all_pending_tasks()
     * Get all tasks with status="pending"
     * For each, call trigger_eod_workflow()
   - Start scheduler when Flask app starts

6. Update backend/app.py:
   - Import scheduler
   - Start scheduler on app startup

Add error handling. Test workflow manually first before scheduling.
```

---

### **How to Test Stage 7:**

#### **Test 1: Test Webhook Endpoint (Before Testing Full Workflow)**

```bash
# Make sure Flask server is running
python backend/app.py

# Test webhook manually (simulate Kapso sending data)
curl -X POST http://localhost:5000/api/webhook/task-status \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task_001",
    "status": "completed",
    "notes": "Task done!",
    "employee_phone": "919876543210",
    "employee_name": "Test Employee"
  }'

# Check Flask terminal - should show success
# Check database - task_001 should be updated
```

#### **Test 2: Test Workflow Trigger (Full Flow)**

**Prerequisites:**
- Flask server running
- ngrok running (if testing locally): `ngrok http 5000`
- Webhook URL updated in Kapso workflow to ngrok URL

```bash
# Test manual trigger (triggers workflow for all pending tasks)
curl -X POST http://localhost:5000/api/trigger-eod

# Check Flask terminal - should show "Workflow triggered for task_001"
# Check your WhatsApp (or employee's WhatsApp if using real number):
#   - Should receive message: "Hi [name], did you complete task [id]?"
#   - Should see Yes/No buttons
#   - Click "Yes" → Should ask for notes
#   - Type notes and send → Should call webhook
#   - Check database - task should be updated to "completed"
```

#### **Test 3: Test Scheduler (Optional - Wait for 5 PM or Change Time)**

The scheduler will automatically trigger at 5 PM daily. To test without waiting:

1. **Option A:** Change scheduler time temporarily to current time + 1 minute
2. **Option B:** Use manual trigger endpoint (above)
3. **Option C:** Wait until 5 PM and monitor

---

### **✅ Stage 7 Complete When:**
- [ ] ✅ Part A: Workflow created in Kapso dashboard (MANUAL)
- [ ] ✅ Part B: Backend code generated and working (LLM)
- [ ] `config.py` updated with WORKFLOW_ID
- [ ] Webhook endpoint receives data correctly
- [ ] Can trigger workflow via API
- [ ] Employee receives Yes/No buttons on WhatsApp
- [ ] Employee clicks Yes → Asked for notes → Webhook called → Database updated
- [ ] Employee clicks No → Asked for reason → Webhook called → Database updated
- [ ] Scheduler configured (will trigger at 5 PM daily)

---

## 📋 **STAGE 8: Frontend Integration - WhatsApp Send Button (30 minutes)**

### **Goal:** Connect "Send to WhatsApp" button in React to backend

### **⚠️ MANUAL STEPS (You Do These):**
1. **Make sure Flask backend is running:**
   ```bash
   python backend/app.py
   ```

2. **Make sure React frontend is running:**
   ```bash
   npm run dev
   ```

3. **Test in browser:**
   - Open http://localhost:3000
   - Open a project
   - Click on a task to edit it
   - Click "Send to WhatsApp Now" button
   - Check your WhatsApp (sandbox or real number) - should receive message
   - Check Flask terminal for logs

**✅ LLM will generate:** Updates to `api.service.js` and `TaskModal.jsx`

### **Files to Update:**
1. `src/services/api.service.js` - Add send WhatsApp function
2. `src/components/tasks/TaskModal.jsx` - Connect button to API

### **LLM Prompt for Stage 8:**

**⚠️ REMINDER: Prepend `TECHNICAL_DESIGN_SPEC.md` to this prompt before sending to LLM!**

```
Connect React frontend "Send to WhatsApp" button to backend API.

REQUIREMENTS:
1. Update src/services/api.service.js:
   - async sendTaskToWhatsApp(taskId)
     * POST /api/tasks/${taskId}/send-whatsapp
     * Return success/error

2. Update src/components/tasks/TaskModal.jsx:
   - Import apiService
   - Update handleSendToWhatsApp():
     * Call apiService.sendTaskToWhatsApp(task.id)
     * Show success toast: "Task sent to WhatsApp!"
     * Show error toast if fails
     * Update task.whatsappSent = true in UI

3. Update src/context/AppContext.jsx:
   - Update sendTaskToWhatsApp():
     * Call apiService instead of mock
     * Show toast based on result

Add loading state while sending. Disable button during send.
```

### **How to Test Stage 8:**

```bash
# In React frontend:
# - Open a task
# - Click "Send to WhatsApp Now"
# - Should show success toast
# - Check WhatsApp - should receive message
# - Check database - whatsapp_sent should be true
```

### **✅ Stage 8 Complete When:**
- [ ] "Send to WhatsApp" button works from React
- [ ] Message sent successfully
- [ ] UI updates correctly
- [ ] Error handling works

---

## 🎉 **MVP COMPLETE CHECKLIST**

### **End-to-End Test:**
1. ✅ Create project from React dashboard
2. ✅ Create task and assign to employee
3. ✅ Click "Send to WhatsApp" → Employee receives message
4. ✅ At 5 PM (or manual trigger) → Employee receives Yes/No buttons
5. ✅ Employee clicks Yes → Adds notes → Task updates in database
6. ✅ Dashboard shows updated task status

### **All Files Created:**
- [ ] `backend/app.py`
- [ ] `backend/database.py`
- [ ] `backend/config.py`
- [ ] `backend/kapso_service.py`
- [ ] `backend/scheduler.py`
- [ ] `backend/requirements.txt`
- [ ] `src/services/api.service.js` (updated)
- [ ] `src/context/AppContext.jsx` (updated)

### **Kapso Setup:**
- [ ] WhatsApp connected in Kapso
- [ ] API key obtained
- [ ] Phone number ID obtained
- [ ] Workflow created and activated
- [ ] Webhook URL configured in Kapso

---

## 🚀 **DEPLOYMENT (Optional for MVP)**

### **Free Hosting Options:**

**Option 1: PythonAnywhere (Easiest)**
- Free tier: pythonanywhere.com
- Upload code via web interface
- Get URL: `yourusername.pythonanywhere.com`
- ✅ Free HTTPS included

**Option 2: Render**
- Free tier: render.com
- Connect GitHub repo
- Auto-deploy on push
- ✅ Free HTTPS included

**Option 3: Railway**
- Free tier: railway.app
- Connect GitHub
- Auto-deploy
- ✅ Free HTTPS included

**For MVP:** Test locally first. Deploy only if needed for demos.

---

## 🐛 **TROUBLESHOOTING GUIDE**

### **Common Issues:**

**1. Flask server won't start**
- Check port 5000 is not in use
- Try: `python app.py` instead of `flask run`
- Check Python version (need 3.8+)

**2. CORS errors in browser**
- Make sure flask-cors is installed
- Check Flask app has CORS enabled
- Verify API URL in frontend matches Flask port

**3. Database errors**
- Delete `database.db` and restart (will recreate)
- Check file permissions
- Verify SQLite is installed

**4. Kapso API errors**
- Check API key is correct
- Verify phone number format (no +, just digits)
- Check phone_number_id matches Kapso dashboard
- Print API response to see error details

**5. Webhook not receiving**
- Use ngrok for local testing: `ngrok http 5000`
- Update webhook URL in Kapso to ngrok URL
- Check webhook is active in Kapso dashboard
- Print incoming request: `print(request.json)`

**6. React not connecting to backend**
- Check Flask is running on port 5000
- Check API_BASE_URL in api.service.js
- Check browser console for errors
- Verify CORS is enabled

---

## 📝 **NEXT STEPS AFTER MVP**

### **Phase 2 Features (Add Later):**
- [ ] Photo handling (employee proof)
- [ ] Task editing/deletion
- [ ] Employee management UI
- [ ] Advanced filtering
- [ ] Analytics dashboard
- [ ] Email notifications

### **Scaling Considerations:**
- Upgrade Kapso plan if exceeding free tier
- Add PostgreSQL if SQLite becomes slow
- Add authentication for multiple managers
- Add rate limiting for API endpoints

---

## 💡 **PRO TIPS**

**For Non-Developers:**
1. **Test each stage before moving on** - Don't skip ahead
2. **Use print statements** - They help debug
3. **Test with curl first** - Before testing in React
4. **Check terminal logs** - Errors show there first
5. **One stage at a time** - Don't rush

**Working with LLM:**
1. Copy ONE stage prompt at a time
2. Test generated code before next stage
3. If error, paste error message to LLM: "This code gave error: [paste]"
4. Don't generate all files at once

**Kapso Testing:**
1. Test workflow manually in Kapso dashboard first
2. Use your own phone number for testing
3. Check webhook logs in Kapso dashboard
4. Verify phone number format (no spaces, no +)

---

## ✅ **SUCCESS CRITERIA**

**MVP is successful if:**
- ✅ Manager can assign task from React dashboard
- ✅ Task saved in database
- ✅ Employee receives WhatsApp message
- ✅ At 5 PM, employee receives Yes/No buttons
- ✅ Employee responds → Task updates in database
- ✅ Dashboard shows updated status
- ✅ All works end-to-end without errors
- ✅ Total cost: $0/month (free tier)

---

**Good luck with your MVP! 🚀**

**Remember:** Work one stage at a time. Test thoroughly. Don't rush. You've got this!
