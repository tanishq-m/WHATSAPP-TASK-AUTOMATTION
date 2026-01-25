import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import MobileNav from './components/layout/MobileNav'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import Employees from './pages/Employees'
import Toast from './components/common/Toast'

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top Navigation */}
      <Navbar />
      
      {/* Main Content */}
      <main className="flex-1 pb-20 md:pb-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/:projectId" element={<ProjectDetail />} />
          <Route path="/employees" element={<Employees />} />
        </Routes>
      </main>
      
      {/* Bottom Mobile Navigation */}
      <MobileNav />
      
      {/* Toast Notifications */}
      <Toast />
    </div>
  )
}

export default App


