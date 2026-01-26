import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Clock, WifiOff } from 'lucide-react'
import { useState } from 'react'
import TimerSettingsModal from '../tasks/TimerSettingsModal'
import { useApp } from '../../context/useApp'

const MobileNav = () => {
  const location = useLocation()
  const [showTimerSettings, setShowTimerSettings] = useState(false)
  const { isOffline } = useApp()

  const navItems = [
    {
      path: '/',
      icon: LayoutDashboard,
      label: 'Projects'
    },
    {
      path: '/employees',
      icon: Users,
      label: 'Team'
    }
  ]

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/' || location.pathname.startsWith('/project/')
    }
    return location.pathname === path
  }

  return (
    <>
      {/* Offline/Online status bar for mobile */}
      {isOffline && (
        <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-red-500 text-white px-4 py-2 flex items-center justify-center gap-2">
          <WifiOff className="w-4 h-4" />
          <span className="text-sm font-medium">Offline - Read Only</span>
        </div>
      )}
      
      <div className={`mobile-nav md:hidden ${isOffline ? 'mt-10' : ''}`}>
        <div className="flex items-center justify-around">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center gap-1 py-3 px-4 tap-target transition-smooth ${
                  active ? 'text-blue-600' : 'text-gray-600'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            )
          })}
          
          {/* Timer Settings Button */}
          <button
            onClick={() => setShowTimerSettings(true)}
            className="flex flex-col items-center gap-1 py-3 px-4 tap-target text-gray-600 transition-smooth"
          >
            <Clock className="w-6 h-6" />
            <span className="text-xs font-medium">Timer</span>
          </button>
        </div>
      </div>

      {/* Timer Settings Modal */}
      <TimerSettingsModal 
        isOpen={showTimerSettings}
        onClose={() => setShowTimerSettings(false)}
      />
    </>
  )
}

export default MobileNav


