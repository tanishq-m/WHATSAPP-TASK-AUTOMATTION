import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import MobileNav from './components/layout/MobileNav'
import Overview from './pages/Overview'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import Employees from './pages/Employees'
import TaskSubmission from './pages/TaskSubmission'
import SubmissionSuccess from './pages/SubmissionSuccess'
import Toast from './components/common/Toast'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Routes>
        {/* Public submission routes (no navigation) */}
        <Route path="/submit/:token" element={<TaskSubmission />} />
        <Route path="/submission-success" element={<SubmissionSuccess />} />
        
        {/* Main app routes (with navigation) */}
        <Route path="/*" element={
          <>
            {/* Top Navigation */}
            <Navbar />
            
            {/* Main Content */}
            <main className="flex-1 pb-20 md:pb-6">
              <Routes>
                <Route path="/" element={<Overview />} />
                <Route path="/projects" element={<Dashboard />} />
                <Route path="/project/:projectId" element={<ProjectDetail />} />
                <Route path="/employees" element={<Employees />} />
              </Routes>
            </main>
            
            {/* Bottom Mobile Navigation */}
            <MobileNav />
            
            {/* Toast Notifications */}
            <Toast />
          </>
        } />
      </Routes>
    </div>
  )
}

export default App


