# Technical Design Specification
## WhatsApp Task Manager MVP - Backend Integration

**Purpose:** This document should be prepended to ALL LLM prompts when generating code for this project. It provides context, architecture decisions, coding standards, and best practices to ensure consistent, high-quality code generation.

**Target:** Senior Engineer-level code quality  
**Language:** Python (Backend) + JavaScript (Frontend)  
**Framework:** Flask (Backend) + React (Frontend)  
**Database:** SQLite (MVP) → PostgreSQL (Future)

---

## 🎯 PROJECT OVERVIEW

### **Business Context**
- **MVP Goal:** Proof-of-concept for WhatsApp-based task management
- **Users:** 1 Manager (admin dashboard) + 3 Employees (WhatsApp only)
- **Budget:** Free tier only (no paid services)
- **Timeline:** Fast MVP development (1-2 days)

### **Core Features**
1. Manager creates projects and assigns tasks via web dashboard
2. Tasks sent to employees via WhatsApp (Kapso API)
3. End-of-day workflow collects task status (Yes/No + notes)
4. Manager views all tasks with status updates on dashboard
5. Kanban board for task management (4 statuses)

### **Non-Goals (Out of Scope for MVP)**
- ❌ Photo handling (Phase 2)
- ❌ Multiple managers
- ❌ Task editing/deletion
- ❌ Advanced analytics
- ❌ Email notifications
- ❌ Employee management UI (hardcoded 3 employees)

---

## 🏗️ ARCHITECTURE DECISIONS

### **Backend Architecture**
```
Flask Backend (Python)
├── RESTful API endpoints
├── SQLite database (file-based)
├── Kapso API integration (WhatsApp)
└── APScheduler (daily 5 PM trigger)
```

**Why Flask?**
- Simple, lightweight framework
- Perfect for MVP with minimal dependencies
- Easy to understand and debug
- Can scale to Django/FastAPI later if needed

**Why SQLite?**
- Zero configuration
- File-based (no separate server)
- Perfect for MVP (<100 employees)
- Easy to migrate to PostgreSQL later

### **Frontend Architecture**
```
React Frontend (Already Built)
├── React Context API (state management)
├── React Router (navigation)
├── localStorage (Phase 1) → API calls (Phase 2)
└── @dnd-kit (drag-and-drop)
```

**Current State:** Frontend is complete with localStorage mock data  
**Goal:** Replace localStorage calls with API calls to Flask backend

### **Integration Pattern**
- **Frontend → Backend:** RESTful API calls (fetch/axios)
- **Backend → Kapso:** HTTP API calls (requests library)
- **Kapso → Backend:** Webhooks (POST to /api/webhook/task-status)
- **Data Flow:** Frontend → Flask API → SQLite → Kapso → WhatsApp → Webhook → SQLite → Frontend

---

## 📐 DATABASE SCHEMA

### **Table: employees**
```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    role TEXT,  -- "Developer", "Designer", "Tester"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Hardcoded Data (MVP):**
- id=1: "Rajesh Kumar", "+919876543210", "Developer"
- id=2: "Priya Singh", "+919876543211", "Designer"
- id=3: "Amit Patel", "+919876543212", "Tester"

### **Table: projects**
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,  -- Format: "proj_001", "proj_002"
    name TEXT NOT NULL,
    start_date TEXT,  -- ISO format: "2025-01-01"
    end_date TEXT,    -- ISO format: "2025-03-31"
    color TEXT,       -- Hex color: "#3B82F6"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Table: project_employees** (Junction Table)
```sql
CREATE TABLE project_employees (
    project_id TEXT NOT NULL,
    employee_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    PRIMARY KEY (project_id, employee_id)
);
```

### **Table: tasks**
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,  -- Format: "task_001", "task_002"
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    employee_id INTEGER NOT NULL,
    due_date TEXT,  -- ISO format: "2025-01-25"
    priority TEXT,  -- "high", "medium", "low"
    status TEXT DEFAULT 'ready_to_start',  -- "ready_to_start", "in_progress", "pending_verification", "completed"
    whatsapp_sent BOOLEAN DEFAULT 0,
    completion_notes TEXT,
    incomplete_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

**Status Values:**
- `ready_to_start` - Task created, not started
- `in_progress` - Employee working on it
- `pending_verification` - Awaiting admin review
- `completed` - Task finished

---

## 🔌 API DESIGN CONVENTIONS

### **RESTful Endpoints**

**Base URL:** `http://localhost:5000/api` (development)

**Conventions:**
- Use plural nouns for resources: `/api/employees`, `/api/projects`, `/api/tasks`
- Use HTTP methods correctly: GET (read), POST (create), PUT (update), DELETE (delete)
- Return JSON for all responses
- Use proper HTTP status codes: 200 (success), 201 (created), 400 (bad request), 404 (not found), 500 (server error)

### **Response Format**

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message here",
  "details": "Optional detailed error info"
}
```

### **Endpoint List**

**Employees:**
- `GET /api/employees` - Get all employees
- `GET /api/employees/:id` - Get single employee

**Projects:**
- `GET /api/projects` - Get all projects
- `GET /api/projects/:id` - Get single project
- `POST /api/projects` - Create project
- `PUT /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project

**Tasks:**
- `GET /api/tasks?projectId=X` - Get tasks (optional filter by project)
- `GET /api/tasks/:id` - Get single task
- `POST /api/tasks` - Create task
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task
- `POST /api/tasks/:id/send-whatsapp` - Send task via WhatsApp

**Webhooks:**
- `POST /api/webhook/task-status` - Receive status from Kapso workflow

**Utilities:**
- `GET /api/health` - Health check
- `POST /api/trigger-eod` - Manual trigger for EOD workflow (testing)

---

## 💻 CODING STANDARDS

### **Python (Backend) Standards**

**Code Style:**
- Follow PEP 8 (Python style guide)
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use descriptive variable names (no abbreviations)
- Add docstrings to all functions

**Function Naming:**
- Use snake_case: `get_employees()`, `create_task()`
- Be descriptive: `get_task_by_id()` not `get_task()`
- Prefix database functions: `db_get_employees()`, `db_create_task()`

**Error Handling:**
```python
# Always use try/except for external operations
try:
    result = some_operation()
    return {"success": True, "data": result}
except Exception as e:
    print(f"Error in some_operation: {e}")  # Log for debugging
    return {"success": False, "error": str(e)}
```

**Database Operations:**
```python
# Always close connections
conn = sqlite3.connect(DATABASE_PATH)
try:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    result = cursor.fetchall()
    conn.commit()
    return result
except Exception as e:
    conn.rollback()
    raise e
finally:
    conn.close()
```

**API Endpoints:**
```python
@app.route('/api/resource', methods=['POST'])
def create_resource():
    try:
        data = request.json
        # Validate data
        if not data.get('required_field'):
            return jsonify({"success": False, "error": "Missing required_field"}), 400
        
        # Process
        result = create_resource_in_db(data)
        
        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        print(f"Error creating resource: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

**Configuration:**
- Store sensitive data in `config.py` (API keys, etc.)
- Use environment variables for production
- Never commit `config.py` with real credentials to Git
- Add `config.py` to `.gitignore`

### **JavaScript (Frontend) Standards**

**Code Style:**
- Use ES6+ features (async/await, arrow functions, destructuring)
- Use meaningful variable names
- Use camelCase for variables: `getEmployees()`, `taskData`
- Use PascalCase for components: `TaskCard`, `ProjectModal`

**API Service Pattern:**
```javascript
// api.service.js
const API_BASE_URL = "http://localhost:5000/api";

export const getEmployees = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/employees`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data.success ? data.data : [];
  } catch (error) {
    console.error("Error fetching employees:", error);
    throw error; // Let caller handle
  }
};
```

**Error Handling:**
```javascript
// Always handle errors gracefully
try {
  const result = await apiService.getData();
  setData(result);
} catch (error) {
  console.error("Error:", error);
  showToast("Failed to load data. Please try again.", "error");
  // Fallback to localStorage or show empty state
}
```

**React Patterns:**
- Use functional components with hooks
- Keep components small and focused (single responsibility)
- Extract reusable logic into custom hooks
- Use Context API for global state
- Handle loading and error states

---

## 🔒 SECURITY CONSIDERATIONS

### **Input Validation**
- Always validate user input on backend (never trust frontend)
- Check required fields
- Validate data types
- Sanitize strings (prevent SQL injection)
- Validate phone numbers format

### **SQL Injection Prevention**
```python
# ✅ GOOD: Use parameterized queries
cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))

# ❌ BAD: String concatenation (vulnerable)
cursor.execute(f"SELECT * FROM tasks WHERE id = {task_id}")
```

### **API Security**
- Use CORS properly (allow only frontend origin in production)
- Validate request body structure
- Check authentication (add in Phase 2)
- Rate limiting (add in Phase 2)

### **Sensitive Data**
- Never log API keys or passwords
- Store credentials in `config.py` (not in code)
- Use environment variables in production
- Add `.env` to `.gitignore`

---

## 🧪 TESTING APPROACH

### **Manual Testing (MVP)**
- Test each endpoint with curl commands
- Test in browser (React frontend)
- Test WhatsApp flow end-to-end
- Check database after operations

### **Error Scenarios to Test**
- Missing required fields
- Invalid data types
- Non-existent IDs (404 errors)
- Database connection failures
- Kapso API failures
- Network timeouts

### **Test Commands**
```bash
# Health check
curl http://localhost:5000/api/health

# Create project
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "startDate": "2025-01-01", "endDate": "2025-03-31"}'

# Get projects
curl http://localhost:5000/api/projects
```

---

## 📦 DEPENDENCIES

### **Backend (requirements.txt)**
```
Flask==3.0.0
flask-cors==4.0.0
python-dotenv==1.0.0
requests==2.31.0
APScheduler==3.10.4
```

**Why These Versions:**
- Flask 3.0.0: Latest stable, well-tested
- flask-cors: Enable CORS for frontend
- python-dotenv: Load environment variables
- requests: HTTP client for Kapso API
- APScheduler: Schedule daily 5 PM trigger

### **Virtual Environment Setup (CRITICAL!)**

**Always use Python virtual environment (venv) for backend:**

```bash
# Create venv in backend folder
cd backend
python3 -m venv venv  # Mac/Linux
# OR
python -m venv venv   # Windows

# Activate venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies (only in venv)
pip install -r requirements.txt

# When done working
deactivate
```

**Why venv?**
- ✅ Isolates project dependencies
- ✅ Prevents conflicts with other Python projects
- ✅ Easy to recreate environment
- ✅ Best practice for Python development

**Important:** Always activate venv before:
- Installing packages (`pip install`)
- Running Flask (`python app.py`)
- Running any Python scripts

### **Frontend (Already Installed)**
- React 18.2.0
- React Router 6.20.0
- @dnd-kit (drag-and-drop)
- lucide-react (icons)

---

## 🔄 COMMON PATTERNS

### **Database Function Pattern**
```python
def get_employees():
    """Get all employees from database.
    
    Returns:
        list: List of employee dictionaries
    """
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, role FROM employees")
        rows = cursor.fetchall()
        
        employees = []
        for row in rows:
            employees.append({
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "role": row[3]
            })
        
        return employees
    except Exception as e:
        print(f"Error getting employees: {e}")
        return []
    finally:
        conn.close()
```

### **API Endpoint Pattern**
```python
@app.route('/api/resource', methods=['GET'])
def get_resource():
    """Get all resources.
    
    Returns:
        JSON: List of resources or error message
    """
    try:
        resources = get_resources_from_db()
        return jsonify({
            "success": True,
            "data": resources
        }), 200
    except Exception as e:
        print(f"Error getting resources: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch resources"
        }), 500
```

### **Frontend API Call Pattern**
```javascript
// In api.service.js
export const getResource = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/resource`);
    const data = await response.json();
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || "Failed to fetch resource");
    }
    
    return data.data;
  } catch (error) {
    console.error("Error fetching resource:", error);
    throw error;
  }
};

// In component/context
const loadResource = async () => {
  try {
    const data = await apiService.getResource();
    setResource(data);
  } catch (error) {
    showToast("Failed to load resource", "error");
    // Fallback or show empty state
  }
};
```

---

## 🚨 ERROR HANDLING GUIDELINES

### **Backend Error Handling**
1. **Always use try/except** for database operations
2. **Log errors** with print statements (for debugging)
3. **Return user-friendly messages** (don't expose internal errors)
4. **Use proper HTTP status codes**
5. **Rollback database transactions** on error

### **Frontend Error Handling**
1. **Always use try/catch** for API calls
2. **Show user-friendly error messages** (toast notifications)
3. **Handle network errors** gracefully
4. **Provide fallback** (localStorage or empty state)
5. **Log errors** to console for debugging

### **Kapso API Error Handling**
```python
def send_whatsapp_message(phone, message):
    try:
        response = requests.post(
            url,
            headers={"X-API-Key": API_KEY},
            json=payload,
            timeout=10  # 10 second timeout
        )
        response.raise_for_status()  # Raise exception for bad status codes
        return {"success": True, "data": response.json()}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        print(f"Kapso API error: {e}")
        return {"success": False, "error": "Failed to send message"}
```

---

## 📝 CODE COMMENTS & DOCUMENTATION

### **Python Docstrings**
```python
def create_task(task_data):
    """Create a new task in the database.
    
    Args:
        task_data (dict): Task information containing:
            - title (str): Task title
            - description (str): Task description
            - project_id (str): Project ID
            - employee_id (int): Employee ID
            - due_date (str): Due date in ISO format
            - priority (str): "high", "medium", or "low"
            - status (str): Task status
    
    Returns:
        dict: Created task with task_id, or None if error
    
    Raises:
        ValueError: If required fields are missing
    """
    # Implementation here
```

### **JavaScript Comments**
```javascript
/**
 * Fetches all employees from the backend API
 * Falls back to localStorage if API call fails
 * 
 * @returns {Promise<Array>} Array of employee objects
 * @throws {Error} If API call fails and no localStorage fallback
 */
const getEmployees = async () => {
  // Implementation here
};
```

---

## 🎨 NAMING CONVENTIONS

### **Python**
- **Functions:** `snake_case` - `get_employees()`, `create_task()`
- **Variables:** `snake_case` - `employee_id`, `task_data`
- **Constants:** `UPPER_SNAKE_CASE` - `API_BASE_URL`, `DATABASE_PATH`
- **Classes:** `PascalCase` - `TaskService`, `DatabaseManager`

### **JavaScript**
- **Functions:** `camelCase` - `getEmployees()`, `createTask()`
- **Variables:** `camelCase` - `employeeId`, `taskData`
- **Constants:** `UPPER_SNAKE_CASE` - `API_BASE_URL`
- **Components:** `PascalCase` - `TaskCard`, `ProjectModal`
- **Files:** `camelCase` - `apiService.js`, `taskModal.jsx`

### **Database**
- **Tables:** `snake_case` - `employees`, `project_employees`
- **Columns:** `snake_case` - `employee_id`, `created_at`
- **Indexes:** `idx_table_column` - `idx_tasks_project_id`

---

## 🔧 CONFIGURATION MANAGEMENT

### **config.py Structure**
```python
# Development Configuration
FLASK_ENV = "development"
PORT = 5000
DEBUG = True

# Database
DATABASE_PATH = "database.db"

# Kapso API (Update with real values from Stage 5.5)
KAPSO_API_KEY = "your_api_key_here"
PHONE_NUMBER_ID = "your_phone_number_id_here"
KAPSO_API_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
WORKFLOW_ID = "your_workflow_id_here"  # From Stage 7

# CORS
ALLOWED_ORIGINS = ["http://localhost:3000"]  # React dev server
```

### **Environment Variables (Future)**
```python
import os
from dotenv import load_dotenv

load_dotenv()

KAPSO_API_KEY = os.getenv("KAPSO_API_KEY")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
```

---

## 📊 DATA VALIDATION

### **Backend Validation**
```python
def validate_task_data(data):
    """Validate task creation data.
    
    Args:
        data (dict): Task data to validate
    
    Returns:
        tuple: (is_valid, errors_dict)
    """
    errors = {}
    
    # Required fields
    if not data.get('title'):
        errors['title'] = "Title is required"
    
    if not data.get('project_id'):
        errors['project_id'] = "Project ID is required"
    
    if not data.get('employee_id'):
        errors['employee_id'] = "Employee ID is required"
    
    # Validate priority
    if data.get('priority') not in ['high', 'medium', 'low']:
        errors['priority'] = "Priority must be high, medium, or low"
    
    # Validate status
    valid_statuses = ['ready_to_start', 'in_progress', 'pending_verification', 'completed']
    if data.get('status') and data.get('status') not in valid_statuses:
        errors['status'] = f"Status must be one of: {', '.join(valid_statuses)}"
    
    return len(errors) == 0, errors
```

---

## 🎯 BEST PRACTICES SUMMARY

### **DO:**
✅ Use descriptive variable and function names  
✅ Add comments explaining "why", not "what"  
✅ Handle errors gracefully with try/except  
✅ Validate all user input on backend  
✅ Use parameterized SQL queries  
✅ Return consistent JSON response format  
✅ Log errors for debugging  
✅ Keep functions small and focused  
✅ Use meaningful HTTP status codes  
✅ Test each endpoint after creation  

### **DON'T:**
❌ Use abbreviations in variable names  
❌ Ignore errors silently  
❌ Trust frontend validation alone  
❌ Use string concatenation for SQL  
❌ Expose internal errors to users  
❌ Commit API keys to Git  
❌ Create functions longer than 50 lines  
❌ Return inconsistent response formats  
❌ Skip error handling  
❌ Hardcode values that should be configurable  

---

## 🚀 PERFORMANCE CONSIDERATIONS

### **Database**
- Use indexes on frequently queried columns
- Close database connections properly
- Use transactions for multiple operations
- Limit query results when possible

### **API**
- Return only necessary data (don't over-fetch)
- Use pagination for large lists (future)
- Cache frequently accessed data (future)
- Use connection pooling (future, with PostgreSQL)

### **Frontend**
- Handle loading states
- Show empty states gracefully
- Debounce search inputs (future)
- Lazy load components (future)

---

## 📚 REFERENCE IMPLEMENTATIONS

### **Complete Database Function Example**
```python
def create_task(task_data):
    """Create a new task in database."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        
        # Generate task_id
        cursor.execute("SELECT COUNT(*) FROM tasks")
        count = cursor.fetchone()[0]
        task_id = f"task_{count + 101}"
        
        # Insert task
        cursor.execute("""
            INSERT INTO tasks (
                task_id, project_id, title, description,
                employee_id, due_date, priority, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            task_data['project_id'],
            task_data['title'],
            task_data.get('description', ''),
            task_data['employee_id'],
            task_data.get('due_date', ''),
            task_data.get('priority', 'medium'),
            task_data.get('status', 'ready_to_start')
        ))
        
        conn.commit()
        
        # Return created task
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        
        return {
            "task_id": row[1],
            "project_id": row[2],
            "title": row[3],
            # ... map all fields
        }
    except Exception as e:
        conn.rollback()
        print(f"Error creating task: {e}")
        return None
    finally:
        conn.close()
```

### **Complete API Endpoint Example**
```python
@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    try:
        data = request.json
        
        # Validate
        is_valid, errors = validate_task_data(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": "Validation failed",
                "details": errors
            }), 400
        
        # Create task
        task = create_task_in_db(data)
        if not task:
            return jsonify({
                "success": False,
                "error": "Failed to create task"
            }), 500
        
        return jsonify({
            "success": True,
            "data": task
        }), 201
        
    except Exception as e:
        print(f"Error in create_task endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500
```

---

## 🎓 LEARNING RESOURCES

**Python/Flask:**
- Flask Quickstart: https://flask.palletsprojects.com/quickstart/
- SQLite Tutorial: https://www.sqlitetutorial.net/
- PEP 8 Style Guide: https://pep8.org/

**JavaScript/React:**
- React Docs: https://react.dev
- Fetch API: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- Async/Await: https://javascript.info/async-await

**Kapso API:**
- Kapso Docs: https://docs.kapso.ai
- WhatsApp API: https://docs.kapso.ai/docs/whatsapp

---

## ✅ CODE QUALITY CHECKLIST

Before submitting code, ensure:
- [ ] All functions have docstrings
- [ ] Error handling is implemented
- [ ] Input validation is present
- [ ] Database connections are closed
- [ ] HTTP status codes are correct
- [ ] Response format is consistent
- [ ] No hardcoded credentials
- [ ] Comments explain complex logic
- [ ] Variable names are descriptive
- [ ] Code follows naming conventions

---

**END OF TECHNICAL DESIGN SPECIFICATION**

**Usage:** Prepend this entire document to every LLM prompt when generating code for this project. This ensures consistent, high-quality code that follows best practices and project standards.
