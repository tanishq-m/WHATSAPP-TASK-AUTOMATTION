import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Modal from '../common/Modal'
import Input from '../common/Input'
import DatePicker from '../common/DatePicker'
import Button from '../common/Button'
import { useApp } from '../../context/useApp'
import { generateId, getRandomColor } from '../../utils/helpers'
import { PROJECT_COLORS } from '../../utils/constants'
import { validateProject } from '../../utils/validators'

const CreateProjectModal = ({ isOpen, onClose, project = null }) => {
  const navigate = useNavigate()
  const { employees, addProject, updateProject } = useApp()
  const isEditing = !!project
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    startDate: '',
    endDate: '',
    assignedEmployees: []
  })
  
  const [errors, setErrors] = useState({})

  // Pre-fill form when editing
  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name || '',
        description: project.description || '',
        startDate: project.startDate || '',
        endDate: project.endDate || '',
        assignedEmployees: project.assignedEmployees || []
      })
    }
  }, [project])

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleEmployeeToggle = (employeeId) => {
    setFormData(prev => {
      const isSelected = prev.assignedEmployees.includes(employeeId)
      return {
        ...prev,
        assignedEmployees: isSelected
          ? prev.assignedEmployees.filter(id => id !== employeeId)
          : [...prev.assignedEmployees, employeeId]
      }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const validation = validateProject(formData)
    if (!validation.isValid) {
      setErrors(validation.errors)
      return
    }

    if (isEditing) {
      // Update existing project
      const updates = {
        name: formData.name,
        description: formData.description,
        startDate: formData.startDate,
        endDate: formData.endDate,
        assignedEmployees: formData.assignedEmployees
      }
      await updateProject(project.id, updates)
    } else {
      // Create new project
      const newProject = {
        id: generateId('proj'),
        name: formData.name,
        description: formData.description,
        startDate: formData.startDate,
        endDate: formData.endDate,
        color: getRandomColor(PROJECT_COLORS),
        assignedEmployees: formData.assignedEmployees,
        createdAt: new Date().toISOString()
      }
      // Wait for project creation to complete
      await addProject(newProject)
      // Stay on the dashboard - don't navigate
    }
    
    // Reset form
    setFormData({
      name: '',
      description: '',
      startDate: '',
      endDate: '',
      assignedEmployees: []
    })
    setErrors({})
    onClose()
  }

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      startDate: '',
      endDate: '',
      assignedEmployees: []
    })
    setErrors({})
    onClose()
  }

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose} 
      title={isEditing ? "Edit Project" : "Create New Project"} 
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Project Name"
          value={formData.name}
          onChange={(e) => handleChange('name', e.target.value)}
          placeholder="e.g., Website Redesign"
          error={errors.name}
          required
        />

        <div>
          <label className="label">Description (Optional)</label>
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Brief description of the project..."
            rows={3}
            className="input-field resize-none"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DatePicker
            label="Start Date (Optional)"
            value={formData.startDate}
            onChange={(e) => handleChange('startDate', e.target.value)}
            error={errors.startDate}
          />

          <DatePicker
            label="End Date (Optional)"
            value={formData.endDate}
            onChange={(e) => handleChange('endDate', e.target.value)}
            min={formData.startDate}
            error={errors.endDate}
          />
        </div>

        <div>
          <label className="label">Assign Team Members</label>
          {isEditing && formData.assignedEmployees.length > 0 && (
            <p className="text-sm text-gray-600 mb-2">
              {formData.assignedEmployees.length} team member{formData.assignedEmployees.length !== 1 ? 's' : ''} currently assigned
            </p>
          )}
          <div className="space-y-2 mt-2">
            {employees.map((employee) => (
              <label
                key={employee.id}
                className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-smooth"
              >
                <input
                  type="checkbox"
                  checked={formData.assignedEmployees.includes(employee.id)}
                  onChange={() => handleEmployeeToggle(employee.id)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{employee.name}</div>
                  <div className="text-sm text-gray-500">{employee.role}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
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
            {isEditing ? 'Save Changes' : 'Create Project'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default CreateProjectModal


