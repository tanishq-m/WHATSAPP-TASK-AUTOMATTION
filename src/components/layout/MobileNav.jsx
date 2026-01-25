import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Clock } from 'lucide-react'
import { useState } from 'react'
import TimerSettingsModal from '../tasks/TimerSettingsModal'

const MobileNav = () => {
  const location = useLocation()
  const [showTimerSettings, setShowTimerSettings] = useState(false)

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
      <div className="mobile-nav md:hidden">
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


