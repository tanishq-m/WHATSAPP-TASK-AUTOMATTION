import { Calendar, MessageCircle, Check, Clock } from 'lucide-react'
import { useState } from 'react'
import { formatDate, isOverdue } from '../../utils/helpers'
import { useApp } from '../../context/useApp'
import TaskPriorityBadge from './TaskPriorityBadge'
import EmployeeAvatar from '../employees/EmployeeAvatar'

const TaskCard = ({ task, onClick, isDragging = false }) => {
  const { getEmployeeById, getProjectById, sendTaskToWhatsApp } = useApp()
  const [sending, setSending] = useState(false)
  
  const employee = getEmployeeById(task.assignedTo)
  const project = getProjectById(task.projectId)
  const overdue = isOverdue(task.dueDate) && task.status !== 'completed'

  const handleSendToWhatsApp = async (e) => {
    e.stopPropagation() // Prevent opening task modal
    
    if (!task.assignedTo) {
      return // No employee assigned
    }

    setSending(true)
    try {
      // Use taskId for API call
      await sendTaskToWhatsApp(task.taskId)
    } finally {
      setSending(false)
    }
  }

  return (
    <div
      onClick={onClick}
      className={`card p-3 cursor-pointer hover:shadow-md transition-smooth ${isDragging ? 'opacity-50' : ''}`}
      style={{ borderLeftWidth: '3px', borderLeftColor: project?.color || '#3B82F6' }}
    >
      {/* Header: Priority Badge + WhatsApp Status */}
      <div className="flex items-center justify-between mb-2">
        <TaskPriorityBadge priority={task.priority} />
        
        {/* WhatsApp Status Indicators */}
        {task.whatsappSent && (
          <div className="flex items-center gap-1">
            {task.whatsappResponse === 'completed' && (
              <span className="text-xs text-green-600 flex items-center gap-1">
                <Check className="w-3 h-3" />
                Done
              </span>
            )}
            {task.whatsappResponse === 'not_completed' && (
              <span className="text-xs text-yellow-600 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Pending
              </span>
            )}
            {!task.whatsappResponse && (
              <span className="text-xs text-blue-600 flex items-center gap-1">
                <MessageCircle className="w-3 h-3" />
                Sent
              </span>
            )}
          </div>
        )}
      </div>

      {/* Task Title */}
      <h4 className="font-medium text-gray-900 mb-2 line-clamp-2">
        {task.title}
      </h4>

      {/* Assigned Employee */}
      {employee && (
        <div className="mb-2">
          <EmployeeAvatar employee={employee} size="xs" showName />
        </div>
      )}

      {/* Footer: Due Date + WhatsApp Button */}
      <div className="flex items-center justify-between mt-2">
        {/* Due Date */}
        <div className={`flex items-center gap-1 text-xs ${overdue ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
          <Calendar className="w-3 h-3" />
          <span>{formatDate(task.dueDate)}</span>
          {overdue && <span className="ml-1">(Overdue)</span>}
        </div>

        {/* WhatsApp Send Button */}
        {task.assignedTo && employee?.phone && (
          <button
            onClick={handleSendToWhatsApp}
            disabled={sending}
            className={`text-xs px-2 py-1 rounded flex items-center gap-1 transition-smooth ${
              task.whatsappSent
                ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                : 'bg-green-500 text-white hover:bg-green-600'
            } ${sending ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={task.whatsappSent ? 'Resend to WhatsApp' : 'Send to WhatsApp'}
          >
            <MessageCircle className="w-3 h-3" />
            {sending ? 'Sending...' : task.whatsappSent ? 'Resend' : 'Send'}
          </button>
        )}
      </div>
    </div>
  )
}

export default TaskCard


