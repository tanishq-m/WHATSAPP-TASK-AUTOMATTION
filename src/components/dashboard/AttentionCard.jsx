import { Phone, Bell, Eye, Clock, AlertCircle } from 'lucide-react'
import { useApp } from '../../context/useApp'
import { useNavigate } from 'react-router-dom'
import EmployeeAvatar from '../employees/EmployeeAvatar'

const AttentionCard = ({ item, onActionComplete }) => {
  const { getEmployeeById, showToast } = useApp()
  const navigate = useNavigate()
  
  const employee = getEmployeeById(item.employeeId)
  
  // Priority styling
  const priorityStyles = {
    high: {
      bg: 'bg-red-50 border-red-200',
      icon: 'text-red-600',
      badge: 'bg-red-100 text-red-800'
    },
    medium: {
      bg: 'bg-yellow-50 border-yellow-200',
      icon: 'text-yellow-600',
      badge: 'bg-yellow-100 text-yellow-800'
    }
  }
  
  const style = priorityStyles[item.priority] || priorityStyles.medium
  
  // Action handlers
  const handleCall = () => {
    // Open phone dialer
    window.location.href = `tel:${employee?.phone}`
    showToast(`Calling ${employee?.name}...`, 'info')
  }
  
  const handleRemind = async () => {
    try {
      // TODO: Call API to send WhatsApp reminder when implemented
      // await apiService.sendTaskReminder(item.taskId)
      showToast('Reminder sent to employee', 'success')
      if (onActionComplete) onActionComplete()
    } catch (error) {
      showToast('Failed to send reminder', 'error')
    }
  }
  
  const handleView = () => {
    // Navigate to project and open task
    navigate(`/project/${item.projectId}`)
  }
  
  return (
    <div className={`card border-l-4 p-4 ${style.bg}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        {/* Priority badge */}
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${style.badge}`}>
          <AlertCircle className="w-3 h-3" />
          {item.priority.toUpperCase()}
        </span>
        
        {/* Time info */}
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{item.hoursSinceUpdate}h ago</span>
        </div>
      </div>
      
      {/* Task info */}
      <h3 className="font-semibold text-gray-900 mb-1">{item.taskTitle}</h3>
      <p className="text-sm text-gray-600 mb-2">{item.reason}</p>
      
      {/* Employee and project info */}
      <div className="flex items-center justify-between mb-3">
        {employee && (
          <EmployeeAvatar employee={employee} size="xs" showName />
        )}
        <span className="text-xs text-gray-500">{item.projectName}</span>
      </div>
      
      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleCall}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-smooth tap-target"
        >
          <Phone className="w-4 h-4" />
          Call
        </button>
        
        <button
          onClick={handleRemind}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-200 text-gray-900 rounded-lg text-sm font-medium hover:bg-gray-300 transition-smooth tap-target"
        >
          <Bell className="w-4 h-4" />
          Remind
        </button>
        
        <button
          onClick={handleView}
          className="px-3 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-smooth tap-target"
        >
          <Eye className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export default AttentionCard
