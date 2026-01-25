import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Clock } from 'lucide-react'
import { useState } from 'react'
import TimerSettingsModal from '../tasks/TimerSettingsModal'

const Navbar = () => {
  const location = useLocation()
  const [showTimerSettings, setShowTimerSettings] = useState(false)

  return (
    <>
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <LayoutDashboard className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-gray-900 hidden sm:block">
                Task Manager
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <Link
                to="/"
                className={`text-sm font-medium transition-smooth ${
                  location.pathname === '/'
                    ? 'text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Projects
              </Link>
              <Link
                to="/employees"
                className={`text-sm font-medium transition-smooth ${
                  location.pathname === '/employees'
                    ? 'text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Team
              </Link>
              <button
                onClick={() => setShowTimerSettings(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-smooth"
                title="Timer Settings"
              >
                <Clock className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Timer Settings Modal */}
      <TimerSettingsModal 
        isOpen={showTimerSettings}
        onClose={() => setShowTimerSettings(false)}
      />
    </>
  )
}

export default Navbar


