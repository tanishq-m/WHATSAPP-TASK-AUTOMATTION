import { useState, useEffect } from 'react'
import { Send } from 'lucide-react'
import Modal from '../common/Modal'
import Input from '../common/Input'
import Select from '../common/Select'
import DatePicker from '../common/DatePicker'
import Button from '../common/Button'
import ActivityFeed from './ActivityFeed'
import { useApp } from '../../context/useApp'
import { generateId } from '../../utils/helpers'
import { PRIORITY, STATUS, PRIORITY_LABELS, STATUS_LABELS } from '../../utils/constants'
import { validateTask } from '../../utils/validators'

const TaskModal = ({ isOpen, onClose, task = null, projectId = null }) => {
  const { employees, projects, addTask, updateTask, sendTaskToWhatsApp, setModalOpen } = useApp()
  
  const isEditing = !!task
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    projectId: projectId || '',
    assignedTo: null,  // Changed to null for optional field
    dueDate: null,     // Changed to null for optional field
    priority: PRIORITY.MEDIUM,
    status: STATUS.UNASSIGNED  // Updated from READY_TO_START
  })
  
  const [errors, setErrors] = useState({})

  // Track modal state for auto-refresh pausing
  useEffect(() => {
    setModalOpen(isOpen)
  }, [isOpen, setModalOpen])

  // Pre-fill form only when modal opens, not on every task update
  useEffect(() => {
    if (isOpen && task) {
      setFormData({
        title: task.title,
        description: task.description || '',
        projectId: task.projectId,
        assignedTo: task.assignedTo || null,  // Handle null/undefined properly
        dueDate: task.dueDate || null,        // Handle null/undefined properly
        priority: task.priority,
        status: task.status
      })
    } else if (isOpen && projectId && !task) {
      setFormData(prev => ({ ...prev, projectId }))
    }
  }, [isOpen, task?.id, projectId])

  const handleChange = (field, value) => {
    // If project changes, clear the assigned employee
    // (they might not be part of the new project)
    if (field === 'projectId') {
      setFormData(prev => ({ 
        ...prev, 
        [field]: value,
        assignedTo: null  // Clear assignment when project changes
      }))
    } else {
      setFormData(prev => ({ ...prev, [field]: value }))
    }
    
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const validation = validateTask(formData)
    if (!validation.isValid) {
      setErrors(validation.errors)
      return
    }

    if (isEditing) {
      // Use task.id for consistency (toCamelCase ensures id === taskId)
      const taskId = task.id || task.taskId
      updateTask(taskId, formData)
    } else {
      const newTask = {
        id: generateId('task'),
        ...formData,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        comments: [],
        whatsappSent: false,
        lastWhatsappSent: null
      }
      addTask(newTask)
    }

    handleClose()
  }

  const handleSendToWhatsApp = () => {
    if (task) {
      // Use consistent ID pattern (toCamelCase ensures id === taskId)
      const taskId = task.id || task.taskId
      sendTaskToWhatsApp(taskId)
    }
  }

  const handleClose = () => {
    setFormData({
      title: '',
      description: '',
      projectId: projectId || '',
      assignedTo: null,
      dueDate: null,
      priority: PRIORITY.MEDIUM,
      status: STATUS.UNASSIGNED  // Updated from READY_TO_START
    })
    setErrors({})
    onClose()
  }

  const projectOptions = projects.map(p => ({ value: p.id, label: p.name }))
  
  // Filter employees to show only those assigned to the selected project
  const getProjectEmployees = () => {
    if (!formData.projectId) return []
    
    const selectedProject = projects.find(p => p.id === formData.projectId)
    if (!selectedProject || !selectedProject.assignedEmployees) return []
    
    // Filter employees to only those in the project's assignedEmployees array
    return employees.filter(e => selectedProject.assignedEmployees.includes(e.id))
  }
  
  const employeeOptions = getProjectEmployees().map(e => ({ value: e.id, label: e.name }))
  
  const priorityOptions = Object.values(PRIORITY).map(p => ({ 
    value: p, 
    label: PRIORITY_LABELS[p] 
  }))
  const statusOptions = Object.values(STATUS).map(s => ({ 
    value: s, 
    label: STATUS_LABELS[s] 
  }))

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose} 
      title={isEditing ? 'Edit Task' : 'Create New Task'} 
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Task Title"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="e.g., Design homepage mockup"
          error={errors.title}
          required
        />

        <div>
          <label className="label">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Describe the task in detail..."
            rows={3}
            className="input resize-none"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Project"
            value={formData.projectId}
            onChange={(e) => handleChange('projectId', e.target.value)}
            options={projectOptions}
            error={errors.projectId}
            required
            disabled={!!projectId}
          />

          <Select
            label="Assign To"
            value={formData.assignedTo}
            onChange={(e) => handleChange('assignedTo', e.target.value)}
            options={employeeOptions}
            error={errors.assignedTo}
            placeholder="Select employee (optional)"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DatePicker
            label="Due Date"
            value={formData.dueDate}
            onChange={(e) => handleChange('dueDate', e.target.value)}
            error={errors.dueDate}
          />

          <Select
            label="Status"
            value={formData.status}
            onChange={(e) => handleChange('status', e.target.value)}
            options={statusOptions}
            required
          />
        </div>

        <div>
          <label className="label">Priority</label>
          <div className="flex gap-3">
            {priorityOptions.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-2 p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-smooth flex-1"
                style={{
                  borderColor: formData.priority === option.value ? '#3B82F6' : '#E5E7EB'
                }}
              >
                <input
                  type="radio"
                  name="priority"
                  value={option.value}
                  checked={formData.priority === option.value}
                  onChange={(e) => handleChange('priority', e.target.value)}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <span className="font-medium text-sm">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Activity Feed - Only show for existing tasks */}
        {isEditing && task && (
          <div className="pt-4 border-t border-gray-200">
            <ActivityFeed taskId={task.id || task.taskId} />
          </div>
        )}

        <div className="flex flex-col gap-3 pt-4 border-t border-gray-200">
          {isEditing && (
            <Button
              type="button"
              variant="outline"
              onClick={handleSendToWhatsApp}
              fullWidth
              className="flex items-center justify-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send to WhatsApp Now
            </Button>
          )}

          <div className="flex flex-col-reverse sm:flex-row gap-3">
            <Button 
              type="button" 
              variant="secondary" 
              onClick={handleClose}
              fullWidth
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              variant="primary"
              fullWidth
            >
              {isEditing ? 'Save Changes' : 'Create Task'}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  )
}

export default TaskModal


