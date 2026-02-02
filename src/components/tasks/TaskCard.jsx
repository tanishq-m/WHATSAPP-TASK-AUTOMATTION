import { Calendar, MessageCircle, Check, Clock, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { formatDate, isOverdue } from '../../utils/helpers'
import { useApp } from '../../context/useApp'
import TaskPriorityBadge from './TaskPriorityBadge'
import EmployeeAvatar from '../employees/EmployeeAvatar'
import ConfirmDialog from '../common/ConfirmDialog'
import CommentBox from './CommentBox'
import ActivityFeed from './ActivityFeed'

const TaskCard = ({ task, onClick, isDragging = false }) => {
  const { getEmployeeById, getProjectById, sendTaskToWhatsApp, deleteTask } = useApp()
  const [sending, setSending] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  
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
      // Use consistent ID pattern (toCamelCase ensures id === taskId)
      const taskId = task.id || task.taskId
      await sendTaskToWhatsApp(taskId)
    } finally {
      setSending(false)
    }
  }

  const handleDelete = async () => {
    try {
      // Use consistent ID pattern (toCamelCase ensures id === taskId)
      const taskId = task.id || task.taskId
      await deleteTask(taskId)
      // Don't call setShowDeleteConfirm here - ConfirmDialog handles closing
    } catch (error) {
      console.error('Failed to delete task:', error)
      // Only close dialog on error so user knows something went wrong
      setShowDeleteConfirm(false)
    }
  }

  return (
    <>
      <div
        onClick={onClick}
        className={`card p-4 cursor-pointer hover:shadow-md transition-smooth ${isDragging ? 'opacity-50' : ''}`}
        style={{ borderLeftWidth: '3px', borderLeftColor: project?.color || '#3B82F6' }}
      >
      {/* Header: Priority Badge + Delete Button + WhatsApp Status */}
      <div className="flex items-center justify-between mb-3">
        <TaskPriorityBadge priority={task.priority} />
        
        <div className="flex items-center gap-2">
          {/* Delete Button */}
          <button
            onClick={(e) => { 
              e.stopPropagation()
              setShowDeleteConfirm(true)
            }}
            className="p-1 hover:bg-red-50 rounded transition-smooth"
            title="Delete task"
          >
            <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-red-500" />
          </button>

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
      </div>

      {/* Task Title */}
      <h4 className="font-medium text-gray-900 mb-3 line-clamp-2 text-base">
        {task.title}
      </h4>

      {/* Assigned Employee */}
      {employee && (
        <div className="mb-3">
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

      {/* Delete Confirmation Dialog - outside card to prevent click propagation issues */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Task"
        message="Are you sure you want to delete this task? This action cannot be undone."
        confirmText="Delete"
        variant="danger"
      />
    </>
  )
}

export default TaskCard


