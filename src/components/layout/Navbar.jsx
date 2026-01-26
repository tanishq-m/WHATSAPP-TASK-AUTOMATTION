import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Clock, WifiOff } from 'lucide-react'
import { useState } from 'react'
import TimerSettingsModal from '../tasks/TimerSettingsModal'
import { useApp } from '../../context/useApp'

const Navbar = () => {
  const location = useLocation()
  const [showTimerSettings, setShowTimerSettings] = useState(false)
  const { isOffline } = useApp()

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
              
              {/* Offline Indicator - Only show when offline */}
              {isOffline && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 border border-red-200 rounded-lg">
                  <WifiOff className="w-4 h-4 text-red-600" />
                  <span className="text-xs font-medium text-red-700">Offline</span>
                </div>
              )}
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


