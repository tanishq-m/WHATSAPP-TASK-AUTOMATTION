export const validateProject = (project) => {
  const errors = {}
  
  if (!project.name || project.name.trim() === '') {
    errors.name = 'Project name is required'
  }
  
  if (!project.startDate) {
    errors.startDate = 'Start date is required'
  }
  
  if (!project.endDate) {
    errors.endDate = 'End date is required'
  }
  
  if (project.startDate && project.endDate) {
    if (new Date(project.startDate) > new Date(project.endDate)) {
      errors.endDate = 'End date must be after start date'
    }
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}

export const validateTask = (task) => {
  const errors = {}
  
  // Required fields
  if (!task.title || task.title.trim() === '') {
    errors.title = 'Task title is required'
  }
  
  if (!task.projectId) {
    errors.projectId = 'Project is required'
  }
  
  if (!task.priority) {
    errors.priority = 'Priority is required'
  }
  
  // Optional fields - no validation needed for assignedTo and dueDate
  // Tasks can be created without an employee (unassigned)
  // Tasks can be created without a due date
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}

export const validateEmployee = (employee) => {
  const errors = {}
  
  if (!employee.name || employee.name.trim() === '') {
    errors.name = 'Employee name is required'
  }
  
  if (!employee.phone || employee.phone.trim() === '') {
    errors.phone = 'Phone number is required'
  }
  
  if (!employee.role || employee.role.trim() === '') {
    errors.role = 'Role is required'
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}


