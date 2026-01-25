# WhatsApp Task Manager - Full Stack MVP

A full-stack task management system with WhatsApp integration. Admins can manage projects, assign tasks to employees, and send task notifications via WhatsApp with interactive Yes/No buttons for status updates.

## 🎯 Overview

A complete task management solution with:
- **React Frontend**: Mobile-first dashboard with Kanban board
- **Flask Backend**: REST API with SQLite database
- **WhatsApp Integration**: Send tasks with interactive buttons via Kapso API
- **Real-time Updates**: Webhook-based task status tracking

## ✨ Features

### ✅ Completed Features

- ✅ **Project Management**: Create, view, and track multiple projects
- ✅ **Kanban Board**: Drag-and-drop task management with 4 columns:
  - Ready to Start
  - In Progress  
  - Pending Verification
  - Completed
- ✅ **Task Management**: Full CRUD operations with:
  - Title & Description
  - Assigned employee
  - Due date & Priority (High/Medium/Low)
  - Status tracking
- ✅ **Employee Management**: SQLite database with 3 employees
- ✅ **WhatsApp Integration**: 
  - Send tasks with interactive buttons (✅ Completed / ❌ Not Yet)
  - Receive responses via webhooks
  - Auto-update task status from employee responses
  - Visual status indicators on task cards
- ✅ **Backend API**: Flask REST API with SQLite
- ✅ **Mobile-First Design**: Optimized for mobile devices

### 🔜 Future Enhancements

- 🔜 User authentication & authorization
- 🔜 Add/edit/delete employees from UI
- 🔜 Task comments and attachments
- 🔜 Email notifications
- 🔜 Analytics dashboard
- 🔜 Production deployment

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16+)
- **Python 3.8+**
- **ngrok** (for webhook testing)
- **Kapso Account** (free tier: https://app.kapso.ai)

### Installation & Setup

#### 1. Clone & Install Dependencies

```bash
cd whatsapp-task-manager

# Install frontend dependencies
npm install

# Install backend dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure Backend

Edit `backend/config.py` with your Kapso credentials:

```python
KAPSO_API_KEY = "your_api_key_here"
PHONE_NUMBER_ID = "your_phone_number_id_here"
```

Get these from: https://app.kapso.ai → WhatsApp → Sandbox

#### 3. Start All Services

Open **3 separate terminals**:

**Terminal 1 - Backend (Flask):**
```bash
cd backend
source ../venv/bin/activate
python3 app.py
```
Flask runs on http://localhost:5001

**Terminal 2 - Frontend (React):**
```bash
npm run dev
```
Frontend runs on http://localhost:3000

**Terminal 3 - Webhook Tunnel (ngrok):**
```bash
ngrok http 5001
```
Copy the https URL (e.g., `https://abc123.ngrok-free.app`)

#### 4. Configure Webhook in Kapso

1. Go to https://app.kapso.ai
2. Navigate to **Webhooks** → **Add Webhook**
3. Set URL: `https://your-ngrok-url.ngrok-free.app/api/webhook/whatsapp`
4. Subscribe to event: `whatsapp.message.received`
5. Save

#### 5. Authorize Test Numbers (Sandbox Only)

In Kapso dashboard → WhatsApp Sandbox:
- Add test phone numbers (employees)
- They'll receive a confirmation message
- Have them reply to activate 24-hour messaging window

## 📱 Usage

### Creating a Project

1. Click **"New Project"** on dashboard
2. Fill in project name, dates, and assign team members
3. Click **"Create Project"**
4. You'll see the project's Kanban board

### Managing Tasks

1. Open a project from the dashboard
2. Click **"New Task"**
3. Fill in task details and assign to an employee
4. Click **"Save"**
5. **Drag tasks between columns** to update status
6. Click task card to edit

### Sending Tasks via WhatsApp

**Option 1: From Task Card**
- Click the green **"Send"** button on any task card
- Employee receives WhatsApp message with Yes/No buttons

**Option 2: From Task Modal**
- Open a task → Click **"Send to WhatsApp"** button

**Receiving Responses:**
- Employee clicks ✅ "Yes, Completed" or ❌ "No, Not Yet"
- Webhook updates database automatically
- Task card shows status: ✅ Done / ⏰ Pending / 📱 Sent

## 🧪 Testing

The project includes comprehensive test suites for both backend and frontend.

### Quick Test Commands

```bash
# Run ALL tests (recommended)
./run_tests.sh

# Run only backend tests (Python/Flask)
./run_tests.sh backend

# Run only frontend tests (React/Vitest)
./run_tests.sh frontend

# Run with coverage reports
./run_tests.sh coverage
```

### Alternative Commands

```bash
# Backend tests with pytest
cd backend
source ../venv/bin/activate
python -m pytest test_api.py -v

# Frontend tests with Vitest
npm test

# Frontend tests with coverage
npm run test:coverage
```

### Test Coverage

**Backend (32 tests):**
- ✅ Health check endpoint
- ✅ Employee CRUD operations
- ✅ Project CRUD operations  
- ✅ Task CRUD operations
- ✅ WhatsApp send & webhook
- ✅ Database operations
- ✅ Error handling
- ✅ Full task lifecycle integration

**Frontend (44 tests):**
- ✅ API service functions
- ✅ Utility helpers & validators
- ✅ Component imports
- ✅ LocalStorage service
- ✅ Context providers
- ✅ Data transformations (snake_case → camelCase)
- ✅ Error handling
- ✅ Edge cases

### Adding New Tests

When adding new functionality:

1. **Backend**: Add tests to `backend/test_api.py`
2. **Frontend**: Add tests to `src/__tests__/app.test.js`
3. Run `./run_tests.sh` to verify nothing is broken

## 🏗️ Project Structure

```
whatsapp-task-manager/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── database.py            # SQLite CRUD operations
│   ├── kapso_service.py       # WhatsApp API wrapper
│   ├── config.py              # Configuration (API keys)
│   ├── requirements.txt       # Python dependencies
│   └── database.db            # SQLite database (auto-created)
├── src/
│   ├── components/            # React components
│   │   ├── tasks/            # Task components (Kanban, TaskCard)
│   │   ├── projects/         # Project components
│   │   └── employees/        # Employee components
│   ├── pages/                # Page components
│   ├── services/             # API service layer
│   │   └── api.service.js    # Backend API calls
│   ├── context/              # React Context (state management)
│   └── utils/                # Helpers and constants
├── COMPLETE_IMPLEMENTATION_GUIDE.md  # Detailed implementation guide
├── TECHNICAL_DESIGN_SPEC.md          # Technical specifications
└── README.md                          # This file
```

## 🛠️ Technology Stack

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Utility-first styling
- **React Router v6** - Client-side routing
- **@dnd-kit** - Drag & drop functionality
- **lucide-react** - Icon library

### Backend
- **Flask 3.0** - Python web framework
- **SQLite** - Database
- **Flask-CORS** - Cross-origin resource sharing
- **Requests** - HTTP library for API calls

### WhatsApp Integration
- **Kapso API** - WhatsApp Business API wrapper
- **ngrok** - Webhook tunneling for local development

## 🗄️ Database Schema

### employees
- `id` (INTEGER, PRIMARY KEY)
- `name` (TEXT)
- `phone` (TEXT)
- `role` (TEXT)
- `created_at` (TIMESTAMP)

### projects
- `id` (TEXT, PRIMARY KEY, e.g., "proj_123")
- `name` (TEXT)
- `description` (TEXT)
- `start_date` (TEXT)
- `end_date` (TEXT)
- `color` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### project_employees (many-to-many)
- `id` (INTEGER, PRIMARY KEY)
- `project_id` (TEXT, FOREIGN KEY)
- `employee_id` (INTEGER, FOREIGN KEY)

### tasks
- `id` (INTEGER, PRIMARY KEY)
- `task_id` (TEXT, UNIQUE, e.g., "task_001")
- `title` (TEXT)
- `description` (TEXT)
- `project_id` (TEXT, FOREIGN KEY)
- `employee_id` (INTEGER, FOREIGN KEY)
- `due_date` (TEXT)
- `priority` (TEXT: high/medium/low)
- `status` (TEXT: todo/in_progress/pending_verification/done)
- `whatsapp_sent` (BOOLEAN)
- `whatsapp_response` (TEXT: completed/not_completed)
- `response_notes` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## 📡 API Endpoints

### Employees
- `GET /api/employees` - Get all employees
- `GET /api/employees/<id>` - Get employee by ID

### Projects
- `GET /api/projects` - Get all projects
- `GET /api/projects/<id>` - Get project by ID
- `POST /api/projects` - Create project
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### Tasks
- `GET /api/tasks` - Get all tasks (optional: ?projectId=proj_123)
- `GET /api/tasks/<task_id>` - Get task by ID
- `POST /api/tasks` - Create task
- `PUT /api/tasks/<task_id>` - Update task
- `DELETE /api/tasks/<task_id>` - Delete task

### WhatsApp
- `POST /api/tasks/<task_id>/send-whatsapp-buttons` - Send task with interactive buttons
- `GET /api/tasks/<task_id>/whatsapp-status` - Get WhatsApp status
- `POST /api/webhook/whatsapp` - Receive webhook from Kapso

## 🐛 Troubleshooting

### Port Already in Use
```bash
# macOS Control Center uses port 5000, so we use 5001
lsof -ti :5001 | xargs kill -9
```

### Tasks Not Appearing
- Hard refresh browser (Cmd+Shift+R)
- Check Flask logs for API errors
- Verify database has tasks: `sqlite3 backend/database.db "SELECT * FROM tasks;"`

### WhatsApp Not Sending
- Verify Kapso credentials in `backend/config.py`
- Check employee has phone number
- For sandbox: User must message first (24-hour window)
- Check Flask logs for Kapso API errors

### Webhook Not Working
- Verify ngrok is running
- Check ngrok URL in Kapso dashboard matches
- Test webhook: `curl -X GET https://your-ngrok-url.ngrok-free.app/api/webhook/whatsapp`
- Check Flask logs when clicking WhatsApp button

### Database Locked Error
```bash
# Stop Flask, then:
cd backend
rm database.db
python3 app.py  # Will recreate with seed data
```

## 🔐 Security Notes

**⚠️ For Development Only**
- `config.py` contains hardcoded API keys
- CORS is wide open (`*`)
- No authentication implemented
- SQLite is not production-ready at scale

**Before Production:**
- Use environment variables for secrets
- Implement proper authentication (JWT)
- Switch to PostgreSQL/MySQL
- Add rate limiting
- Use HTTPS everywhere
- Implement proper error handling

## 📚 Documentation

- **COMPLETE_IMPLEMENTATION_GUIDE.md** - Step-by-step setup guide
- **TECHNICAL_DESIGN_SPEC.md** - Architecture and design decisions
- **QUICK_REFERENCE.md** - Quick command reference

## 🤝 Contributing

This is an MVP project. Known issues to fix:
- [ ] Task update causes page reload
- [ ] Need proper error boundaries
- [ ] Add loading states
- [ ] Improve mobile UX
- [ ] Add task filtering/search
- [ ] Implement batch operations

## 📝 License

MIT License - Feel free to use for learning and projects

## 👥 Current Employees (Seeded Data)

1. **Rajesh Kumar** - Developer - +918005800336
2. **Raghav** - Developer - +917017712424
3. **Vibhu** - Developer - +919909679043

## 🎉 Success Checklist

After setup, you should be able to:
- [x] Create projects from React UI
- [x] Create and edit tasks
- [x] Drag tasks between Kanban columns
- [x] Assign tasks to employees
- [x] Send tasks to WhatsApp with buttons
- [x] Receive employee responses via webhook
- [x] See task status update automatically

---

**Built with ❤️ for learning full-stack development + WhatsApp Business API**

## 💾 Data Storage

All data is stored in the browser's localStorage using these keys:

- `wtm_projects` - All projects
- `wtm_tasks` - All tasks
- `wtm_employees` - Employee data
- `wtm_timer_config` - Timer settings

**Note**: Clearing browser data will reset the app. In Phase 2, data will be stored in a backend database.

## 🧪 Mock Data

The app comes pre-loaded with:

- **3 Employees**: Rajesh Kumar (Developer), Priya Singh (Designer), Amit Patel (Tester)
- **2 Projects**: Website Redesign, Mobile App Development
- **5 Sample Tasks**: Distributed across different statuses and priorities

## 🔮 Phase 2 Roadmap

### Backend Integration
- Node.js + Express API
- MongoDB/PostgreSQL database
- JWT authentication
- RESTful API endpoints

### WhatsApp Integration
- Twilio WhatsApp API or WhatsApp Business API
- Automated message scheduling (cron jobs)
- Webhook for receiving employee responses
- Parse yes/no responses and update task status
- Handle image/file uploads from employees

### Additional Features
- User authentication (admin login)
- Add/edit/delete employees
- Project templates
- Task comments and attachments
- Activity logs
- Analytics dashboard
- Export reports
- Notifications

## 📝 Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

## 🐛 Known Limitations (MVP)

- No backend (localStorage only)
- Employees are hardcoded (3 employees)
- No actual WhatsApp integration
- No authentication
- No data export/import
- Limited to single browser/device
- No real-time collaboration

## 🤝 Contributing

This is an MVP for proof of concept. Contributions and feedback are welcome for Phase 2!

## 📄 License

This project is private and proprietary.

## 👨‍💻 Developer

Built with ❤️ for WhatsApp-based task management

---

**Note**: This is a Phase 1 MVP (Minimum Viable Product) designed as a proof of concept. Full functionality including WhatsApp integration will be implemented in Phase 2 after securing funding.


