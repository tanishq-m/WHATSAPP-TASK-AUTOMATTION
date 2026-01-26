/**
 * API Service
 * Handles all API calls to the Flask backend.
 * Replaces localStorage with real backend calls.
 */

// Base URL for Flask backend API
// Change port to 5001 (macOS Control Center uses 5000)
const API_BASE_URL = "http://localhost:5001/api";

/**
 * Transform snake_case keys from API to camelCase for frontend
 */
const toCamelCase = (obj) => {
  if (Array.isArray(obj)) {
    return obj.map(item => toCamelCase(item));
  }
  
  if (obj !== null && typeof obj === 'object') {
    const result = Object.keys(obj).reduce((acc, key) => {
      const camelKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
      acc[camelKey] = toCamelCase(obj[key]);
      return acc;
    }, {});
    
    // IMPORTANT: Unify ID handling for tasks
    // If this is a task object (has taskId), set id = taskId for consistency
    // This ensures drag-and-drop and API calls use the same ID
    if (result.taskId) {
      result.id = result.taskId;
    }
    
    // IMPORTANT: Unify employee field naming (Issue #9)
    // Backend uses employee_id → employeeId, but frontend forms use assignedTo
    // Map employeeId to assignedTo for consistency
    if ('employeeId' in result) {
      result.assignedTo = result.employeeId;
    }
    
    return result;
  }
  
  return obj;
};

/**
 * Fetches all employees from the backend API
 * @returns {Promise<Array>} Array of employee objects
 */
export const getEmployees = async () => {
  try {
    console.log("🔄 API: Fetching employees from backend...");
    
    const response = await fetch(`${API_BASE_URL}/employees`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Employees fetched successfully", result.data);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to fetch employees");
    }
  } catch (error) {
    console.error("❌ API: Error fetching employees:", error);
    throw error; // Re-throw to let caller handle it
  }
};

/**
 * Fetches a single employee by ID from the backend API
 * @param {number} id - Employee ID
 * @returns {Promise<Object>} Employee object
 */
export const getEmployeeById = async (id) => {
  try {
    console.log(`🔄 API: Fetching employee ${id} from backend...`);
    
    const response = await fetch(`${API_BASE_URL}/employees/${id}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Employee fetched successfully", result.data);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Employee not found");
    }
  } catch (error) {
    console.error(`❌ API: Error fetching employee ${id}:`, error);
    throw error;
  }
};

/**
 * Creates a new employee
 * @param {Object} employeeData - Employee data to create
 * @returns {Promise<Object>} Created employee object
 */
export const createEmployee = async (employeeData) => {
  try {
    console.log("🔄 API: Creating employee...", employeeData);
    
    const response = await fetch(`${API_BASE_URL}/employees`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(employeeData),
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      console.log("✅ API: Employee created successfully", result.data);
      return toCamelCase(result.data);
    } else {
      // Parse error message from backend
      const errorMessage = result.error || "Failed to create employee";
      throw new Error(errorMessage);
    }
  } catch (error) {
    console.error("❌ API: Error creating employee:", error);
    throw error;
  }
};

/**
 * Updates an existing employee
 * @param {number} id - Employee ID
 * @param {Object} updates - Employee data to update
 * @returns {Promise<Object>} Updated employee object
 */
export const updateEmployee = async (id, updates) => {
  try {
    console.log(`🔄 API: Updating employee ${id}...`, updates);
    
    const response = await fetch(`${API_BASE_URL}/employees/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      console.log("✅ API: Employee updated successfully", result.data);
      return toCamelCase(result.data);
    } else {
      // Parse error message from backend
      const errorMessage = result.error || "Failed to update employee";
      throw new Error(errorMessage);
    }
  } catch (error) {
    console.error(`❌ API: Error updating employee ${id}:`, error);
    throw error;
  }
};

/**
 * Deletes an employee
 * @param {number} id - Employee ID
 * @returns {Promise<Object>} Success response
 */
export const deleteEmployee = async (id) => {
  try {
    console.log(`🔄 API: Deleting employee ${id}...`);
    
    const response = await fetch(`${API_BASE_URL}/employees/${id}`, {
      method: 'DELETE',
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      console.log("✅ API: Employee deleted successfully");
      return result;
    } else {
      // Parse error message from backend
      const errorMessage = result.error || "Failed to delete employee";
      throw new Error(errorMessage);
    }
  } catch (error) {
    console.error(`❌ API: Error deleting employee ${id}:`, error);
    throw error;
  }
};

/**
 * Fetches all projects from the backend API
 * @returns {Promise<Array>} Array of project objects
 */
export const getProjects = async () => {
  try {
    console.log("🔄 API: Fetching projects from backend...");
    
    const response = await fetch(`${API_BASE_URL}/projects`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Projects fetched successfully", result.data);
      // Transform snake_case to camelCase for frontend compatibility
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to fetch projects");
    }
  } catch (error) {
    console.error("❌ API: Error fetching projects:", error);
    throw error;
  }
};

/**
 * Fetches a single project by ID from the backend API
 * @param {string} id - Project ID
 * @returns {Promise<Object>} Project object with employees
 */
export const getProjectById = async (id) => {
  try {
    console.log(`🔄 API: Fetching project ${id} from backend...`);
    
    const response = await fetch(`${API_BASE_URL}/projects/${id}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Project fetched successfully", result.data);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Project not found");
    }
  } catch (error) {
    console.error(`❌ API: Error fetching project ${id}:`, error);
    throw error;
  }
};

/**
 * Creates a new project in the backend
 * @param {Object} projectData - Project information
 * @returns {Promise<Object>} Created project object
 */
export const createProject = async (projectData) => {
  try {
    console.log("🔄 API: Creating project...", projectData);
    
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(projectData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Project created successfully", result.data);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to create project");
    }
  } catch (error) {
    console.error("❌ API: Error creating project:", error);
    throw error;
  }
};

/**
 * Updates an existing project in the backend
 * @param {string} id - Project ID
 * @param {Object} updates - Updated project information
 * @returns {Promise<Object>} Updated project object
 */
export const updateProject = async (id, updates) => {
  try {
    console.log(`🔄 API: Updating project ${id}...`, updates);
    
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Project updated successfully");
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to update project");
    }
  } catch (error) {
    console.error(`❌ API: Error updating project ${id}:`, error);
    throw error;
  }
};

/**
 * Deletes a project from the backend
 * @param {string} id - Project ID
 * @returns {Promise<void>}
 */
export const deleteProject = async (id) => {
  try {
    console.log(`🔄 API: Deleting project ${id}...`);
    
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Project deleted successfully");
      return;
    } else {
      throw new Error(result.error || "Failed to delete project");
    }
  } catch (error) {
    console.error(`❌ API: Error deleting project ${id}:`, error);
    throw error;
  }
};

/**
 * Fetches all tasks, optionally filtered by project ID
 * @param {string} projectId - Optional project ID to filter tasks
 * @returns {Promise<Array>} Array of task objects
 */
export const getTasks = async (projectId = null) => {
  try {
    const url = projectId 
      ? `${API_BASE_URL}/tasks?projectId=${projectId}`
      : `${API_BASE_URL}/tasks`;
    
    console.log(`🔄 API: Fetching tasks from backend... ${projectId ? `(project: ${projectId})` : ''}`);
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      console.log("✅ API: Tasks fetched successfully", result.data);
      // Transform snake_case to camelCase for frontend compatibility
      // Handle null/undefined data by returning empty array
      return toCamelCase(result.data || []);
    } else {
      throw new Error(result.error || "Failed to fetch tasks");
    }
  } catch (error) {
    console.error("❌ API: Error fetching tasks:", error);
    throw error;
  }
};

/**
 * Get a single task by ID
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} Task data
 */
export const getTaskById = async (taskId) => {
  try {
    console.log(`📡 API: Fetching task ${taskId}`);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`);
    const result = await response.json();

    if (result.success) {
      console.log(`✅ API: Task ${taskId} fetched successfully`);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to fetch task");
    }
  } catch (error) {
    console.error("❌ API: Error fetching task:", error);
    throw error;
  }
};

/**
 * Create a new task
 * @param {Object} taskData - Task data
 * @returns {Promise<Object>} Created task
 */
export const createTask = async (taskData) => {
  try {
    console.log("📡 API: Creating task:", taskData.title);
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(taskData),
    });

    const result = await response.json();

    if (result.success) {
      console.log(`✅ API: Task created: ${result.data.task_id}`);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to create task");
    }
  } catch (error) {
    console.error("❌ API: Error creating task:", error);
    throw error;
  }
};

/**
 * Update a task
 * @param {string} taskId - Task ID
 * @param {Object} updates - Fields to update
 * @returns {Promise<Object>} Updated task
 */
export const updateTask = async (taskId, updates) => {
  try {
    console.log(`📡 API: Updating task ${taskId}`);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    });

    const result = await response.json();

    if (result.success) {
      console.log(`✅ API: Task ${taskId} updated successfully`);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to update task");
    }
  } catch (error) {
    console.error("❌ API: Error updating task:", error);
    throw error;
  }
};

/**
 * Delete a task
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} Success response
 */
export const deleteTask = async (taskId) => {
  try {
    console.log(`📡 API: Deleting task ${taskId}`);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: "DELETE",
    });

    const result = await response.json();

    if (result.success) {
      console.log(`✅ API: Task ${taskId} deleted successfully`);
      return result;
    } else {
      throw new Error(result.error || "Failed to delete task");
    }
  } catch (error) {
    console.error("❌ API: Error deleting task:", error);
    throw error;
  }
};

/**
 * Send task to employee via WhatsApp with interactive buttons
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} Success response with WhatsApp data
 */
export const sendTaskToWhatsApp = async (taskId) => {
  try {
    console.log(`📡 API: Sending task ${taskId} to WhatsApp`);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/send-whatsapp-buttons`, {
      method: "POST",
    });

    const result = await response.json();

    if (result.success) {
      console.log(`✅ API: Task ${taskId} sent to WhatsApp successfully`);
      return toCamelCase(result.data || {});
    } else {
      throw new Error(result.error || "Failed to send task to WhatsApp");
    }
  } catch (error) {
    console.error("❌ API: Error sending task to WhatsApp:", error);
    throw error;
  }
};

/**
 * Get WhatsApp status for a task
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} WhatsApp status data
 */
export const getTaskWhatsAppStatus = async (taskId) => {
  try {
    console.log(`📡 API: Getting WhatsApp status for task ${taskId}`);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/whatsapp-status`);

    const result = await response.json();

    if (result.success) {
      console.log(`✅ API: WhatsApp status retrieved for task ${taskId}`);
      return toCamelCase(result.data);
    } else {
      throw new Error(result.error || "Failed to get WhatsApp status");
    }
  } catch (error) {
    console.error("❌ API: Error getting WhatsApp status:", error);
    throw error;
  }
};

// Export all API functions
export default {
  getEmployees,
  getEmployeeById,
  getProjects,
  getProjectById,
  createProject,
  updateProject,
  deleteProject,
  getTasks,
  getTaskById,
  createTask,
  updateTask,
  deleteTask,
  sendTaskToWhatsApp,
  getTaskWhatsAppStatus,
};
