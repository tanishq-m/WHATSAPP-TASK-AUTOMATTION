# Quick Reference Guide
## For Non-Developers Building MVP

---

## 🎯 **ARCHITECTURE DECISION**

**✅ Chosen: Option C (Hybrid)**
- Flask Backend (FREE hosting)
- Kapso WhatsApp (FREE tier)
- React Frontend (already built)
- **Total Cost: $0/month** ✅

**Why not Option B (Kapso Functions only)?**
- Less control
- Harder to debug
- Might hit free tier limits faster

---

## 📋 **IMPLEMENTATION STAGES**

| Stage | What You Build | Time | Test Command |
|-------|---------------|------|---------------|
| **0** | ✅ Frontend (Already Done) | - | `npm run dev` |
| **1** | Flask Server Setup | 30 min | `curl http://localhost:5000/api/health` |
| **2** | Database Setup | 45 min | `curl http://localhost:5000/api/employees` |
| **3** | Connect Employees API | 30 min | Check Employees page in React |
| **4** | Projects API | 1 hour | Create project from dashboard |
| **5** | Tasks API | 1.5 hours | Create task, drag in Kanban |
| **6** | Kapso WhatsApp Send | 45 min | Send test message |
| **7** | Kapso Workflow EOD | 1.5 hours | Trigger workflow, test Yes/No |
| **8** | Connect WhatsApp Button | 30 min | Click "Send to WhatsApp" in React |

**Total Time: ~6 hours** (spread over 1-2 days)

---

## 🚀 **QUICK START**

### **Before Starting:**
```bash
# Make sure React frontend works
cd whatsapp-task-manager
npm run dev
# Open http://localhost:3000 - should work
```

### **Stage 1: Flask Setup**
```bash
# Create backend folder
mkdir backend
cd backend

# Create virtual environment
python3 -m venv venv  # Mac/Linux
# OR
python -m venv venv   # Windows

# Activate venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Copy Stage 1 prompt to LLM
# Generate: app.py, requirements.txt, config.py

# Install dependencies (only in venv)
pip install -r requirements.txt

# Run Flask
python app.py

# Test
curl http://localhost:5000/api/health

# When done
deactivate
```

### **Continue with Stages 2-8**
- Copy each stage prompt from `COMPLETE_IMPLEMENTATION_GUIDE.md`
- Feed to LLM one at a time
- Test before moving to next stage

---

## 🔑 **KAPSO SETUP CHECKLIST**

### **Before Stage 6 (See Stage 5.5 in main guide for detailed steps):**

**For Development/Testing (Sandbox):**
- [ ] Sign up at kapso.ai
- [ ] Go to WhatsApp → Sandbox
- [ ] Add your test phone number
- [ ] Verify with code sent to WhatsApp
- [ ] Get API Key (Settings → API Keys)
- [ ] Get Phone Number ID (from Sandbox or Connected Numbers)

**For MVP Demo (Real Number):**
- [ ] Sign up at kapso.ai
- [ ] Connect WhatsApp Business → "Bring Your Own SIM"
- [ ] Log in with Facebook
- [ ] Enter your phone number
- [ ] Verify with SMS code
- [ ] Get API Key (Settings → API Keys)
- [ ] Get Phone Number ID (Connected Numbers)

### **Before Stage 7 (See Stage 7 Part A in main guide for detailed manual steps):**
- [ ] Create workflow in Kapso dashboard (MANUAL - detailed steps in guide)
- [ ] Configure all nodes (Start, Send Buttons, Wait, Decide, Webhook)
- [ ] Set up webhook URL (use ngrok for local: `ngrok http 5000`)
- [ ] Activate workflow
- [ ] Copy Workflow ID (save for config.py)

---

## 📁 **FILE STRUCTURE**

```
whatsapp-task-manager/
├── src/                          # React frontend (already done)
│   ├── pages/
│   ├── components/
│   ├── services/
│   └── context/
│
└── backend/                      # Flask backend (build this)
    ├── app.py                    # Main Flask app
    ├── database.py               # Database functions
    ├── config.py                 # Configuration
    ├── kapso_service.py         # Kapso API wrapper
    ├── scheduler.py              # 5 PM trigger
    ├── requirements.txt         # Python dependencies
    └── database.db              # SQLite database (auto-created)
```

---

## 🧪 **TESTING COMMANDS**

### **Backend Tests:**
```bash
# Health check
curl http://localhost:5000/api/health

# Get employees
curl http://localhost:5000/api/employees

# Create project
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "startDate": "2025-01-01", "endDate": "2025-03-31"}'

# Get projects
curl http://localhost:5000/api/projects

# Create task
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "projectId": "proj_001", "assignedTo": 1, ...}'

# Send WhatsApp
curl -X POST http://localhost:5000/api/tasks/task_001/send-whatsapp

# Trigger EOD
curl -X POST http://localhost:5000/api/trigger-eod
```

---

## 🐛 **COMMON ERRORS & FIXES**

| Error | Fix |
|-------|-----|
| `Port 5000 already in use` | Kill process: `lsof -ti:5000 \| xargs kill` |
| `CORS error` | Check flask-cors installed, enabled in app.py |
| `Module not found` | Run `pip install -r requirements.txt` |
| `Database locked` | Close other connections, restart Flask |
| `Kapso API error` | Check API key, phone number format (no +) |
| `Webhook not receiving` | Use ngrok, check URL in Kapso dashboard |
| `React can't connect` | Check Flask running, API_BASE_URL correct |

---

## 💰 **COST BREAKDOWN**

| Service | Plan | Cost | Usage |
|---------|------|------|-------|
| Flask Backend | PythonAnywhere Free | $0 | Unlimited |
| Kapso WhatsApp | Free Tier | $0 | 2,000 msgs/month |
| React Frontend | Vercel Free | $0 | Unlimited |
| **Total** | | **$0/month** | ✅ |

**For 3 employees:**
- ~30 task assignments/month
- ~30 EOD workflows/month
- ~60 total messages/month
- **Well under 2,000 limit** ✅

---

## 📞 **SUPPORT RESOURCES**

- **Kapso Docs:** https://docs.kapso.ai
- **Flask Docs:** https://flask.palletsprojects.com
- **React Docs:** https://react.dev
- **PythonAnywhere:** https://help.pythonanywhere.com

---

## ✅ **FINAL CHECKLIST**

Before considering MVP complete:

- [ ] All 8 stages completed
- [ ] Flask backend running locally
- [ ] React frontend connects to backend
- [ ] Can create projects and tasks
- [ ] WhatsApp messages sending
- [ ] EOD workflow working
- [ ] Webhook receiving responses
- [ ] Database updating correctly
- [ ] End-to-end test successful
- [ ] No errors in console/terminal

---

**Remember:** One stage at a time. Test thoroughly. Don't rush! 🚀
