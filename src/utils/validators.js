// ============================================================================
// HELPER VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validate that a value is not empty
 */
export const validateRequired = (value) => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim() !== '';
  return true;
};

/**
 * Validate phone number format (basic validation for international numbers)
 */
export const validatePhone = (phone) => {
  if (!phone || phone.trim() === '') return false;
  // Allow international format with + and digits, minimum 10 digits
  const phoneRegex = /^\+?[\d\s-]{10,}$/;
  return phoneRegex.test(phone.replace(/\s/g, ''));
};

/**
 * Validate date string format (YYYY-MM-DD)
 */
export const validateDate = (dateStr) => {
  if (!dateStr || dateStr.trim() === '') return true; // Empty is allowed
  const date = new Date(dateStr);
  return !isNaN(date.getTime()) && /^\d{4}-\d{2}-\d{2}$/.test(dateStr);
};

/**
 * Validate priority value
 */
export const validatePriority = (priority) => {
  const validPriorities = ['high', 'medium', 'low'];
  return validPriorities.includes(priority);
};

/**
 * Validate task status value
 */
export const validateStatus = (status) => {
  const validStatuses = ['unassigned', 'in_progress', 'pending_verification', 'completed'];
  return validStatuses.includes(status);
};


// ============================================================================
// OBJECT VALIDATION FUNCTIONS
// ============================================================================

export const validateProject = (project) => {
  const errors = {}
  
  if (!project.name || project.name.trim() === '') {
    errors.name = 'Project name is required'
  }
  
  // Dates are optional, but if both are provided, validate relationship
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


