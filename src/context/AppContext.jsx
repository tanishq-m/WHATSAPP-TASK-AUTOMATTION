import { createContext, useState, useEffect, useCallback, useRef } from 'react'
import storageService from '../services/localStorage.service'
import * as apiService from '../services/api.service'
import timerService from '../services/timer.service'
import { calculateProgress } from '../utils/helpers'
import { STATUS } from '../utils/constants'

export const AppContext = createContext()

const AppProvider = ({ children }) => {
  const [projects, setProjects] = useState([])
  const [tasks, setTasks] = useState([])
  const [employees, setEmployees] = useState([])
  const [timerConfig, setTimerConfig] = useState(null)
  const [toast, setToast] = useState({ show: false, message: '', type: 'info' })
  const [loading, setLoading] = useState(false)
  const [isOffline, setIsOffline] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  
  // Use ref to track modal state for interval callback without recreating interval
  const modalOpenRef = useRef(false)
  
  // Sync ref with state
  useEffect(() => {
    modalOpenRef.current = modalOpen
  }, [modalOpen])

  // Initialize data from localStorage
  useEffect(() => {
    storageService.init()
    loadData()
  }, [])

  // Auto-refresh data every 30 seconds for real-time updates
  // (e.g., WhatsApp updates, backend recovery)
  useEffect(() => {
    const POLL_INTERVAL = 30000 // 30 seconds - lightweight polling
    
    const intervalId = setInterval(() => {
      // Skip auto-refresh if a modal is open to prevent form data loss
      if (modalOpenRef.current) {
        console.log('⏸️ Auto-refresh skipped: Modal is open')
        return
      }
      console.log('🔄 Auto-refresh: Checking for updates...')
      loadData(true) // Pass silent flag to avoid showing loading spinner
    }, POLL_INTERVAL)

    // Cleanup interval on unmount
    return () => clearInterval(intervalId)
  }, [])

  const loadData = async (silent = false) => {
    // Don't show loading spinner for background refreshes
    if (!silent) {
      setLoading(true)
    }
    
    let loadedTasks = []
    let loadedProjects = []
    let loadedEmployees = []
    let apiSuccess = false
    const wasOffline = isOffline
    
    try {
      // Try to fetch employees from backend API
      console.log("🔄 Loading employees from backend API...")
      const employeesData = await apiService.getEmployees()
      loadedEmployees = employeesData || []
      setEmployees(loadedEmployees)
      console.log("✅ Employees loaded from API:", loadedEmployees.length)
      
      // Sync to localStorage
      storageService.setEmployees(employeesData)
    } catch (error) {
      // Fallback to localStorage if API fails
      console.warn("⚠️ API failed, falling back to localStorage for employees")
      console.error("Error:", error)
      loadedEmployees = storageService.getEmployees()
      setEmployees(loadedEmployees)
      showToast("Using offline data - backend not connected", "warning")
    }

    // Try to fetch tasks from backend API first (needed for project stats)
    try {
      console.log("🔄 Loading tasks from backend API...")
      const tasksData = await apiService.getTasks()
      loadedTasks = tasksData || []
      setTasks(loadedTasks)
      console.log("✅ Tasks loaded from API:", loadedTasks.length)
      
      // Sync to localStorage
      storageService.setTasks(loadedTasks)
    } catch (error) {
      console.warn("⚠️ API failed, falling back to localStorage for tasks")
      console.error("Error:", error)
      loadedTasks = storageService.getTasks()
      setTasks(loadedTasks)
      if (!toast.show) {
        showToast("Using offline data for tasks", "warning")
      }
    }

    // Try to fetch projects from backend API
    try {
      console.log("🔄 Loading projects from backend API...")
      const projectsData = await apiService.getProjects()
      loadedProjects = projectsData || []
      // Calculate stats for projects using loaded tasks
      const projectsWithStats = calculateProjectStats(loadedProjects, loadedTasks)
      setProjects(projectsWithStats)
      console.log("✅ Projects loaded from API:", loadedProjects.length)
      apiSuccess = true
      
      // Sync to localStorage
      storageService.setProjects(loadedProjects)
    } catch (error) {
      console.warn("⚠️ API failed, falling back to localStorage for projects")
      console.error("Error:", error)
      loadedProjects = storageService.getProjects()
      setProjects(getProjectsWithStats())
      if (!toast.show) { // Only show toast if not already showing
        showToast("Using offline data for projects", "warning")
      }
    }

    if (apiSuccess) {
      console.log("✅ All data synced from backend to localStorage")
      
      // Show recovery message if we were offline and now back online
      if (wasOffline && !silent) {
        showToast("✅ Back online - Data synced from server", "success")
      }
      
      setIsOffline(false)
    } else {
      setIsOffline(true)
      
      // Only show offline message for initial load or manual refresh
      if (!toast.show && !silent) {
        showToast("⚠️ Offline Mode - Cannot save changes until reconnected", "warning")
      }
    }

    setTimerConfig(storageService.getTimerConfig())
    
    // Don't hide loading for silent background refreshes
    if (!silent) {
      setLoading(false)
    }
  }

  // Calculate project stats from projects and tasks data
  const calculateProjectStats = (projectsData, tasksData) => {
    return projectsData.map(project => {
      const projectTasks = tasksData.filter(t => t.projectId === project.id)
      const completedTasks = projectTasks.filter(t => t.status === STATUS.COMPLETED).length
      const unassignedTasks = projectTasks.filter(t => t.status === STATUS.UNASSIGNED).length
      const inProgressTasks = projectTasks.filter(t => t.status === STATUS.IN_PROGRESS).length
      const pendingTasks = projectTasks.filter(t => t.status === STATUS.PENDING_VERIFICATION).length
      const taskCount = projectTasks.length
      const progress = calculateProgress(taskCount, completedTasks)
      
      // Count unique team members with assigned tasks
      const uniqueAssignedMembers = new Set(
        projectTasks
          .filter(t => t.assignedTo) // Only tasks with assigned members
          .map(t => t.assignedTo)
      )
      const activeTeamMembers = uniqueAssignedMembers.size
      
      return {
        ...project,
        taskCount,
        completedTasks,
        unassignedTasks,
        inProgressTasks,
        pendingTasks,
        progress,
        activeTeamMembers
      }
    })
  }

  // Calculate project stats
  const getProjectsWithStats = () => {
    const projectsData = storageService.getProjects()
    const tasksData = storageService.getTasks()
    
    return projectsData.map(project => {
      const projectTasks = tasksData.filter(t => t.projectId === project.id)
      const completedTasks = projectTasks.filter(t => t.status === STATUS.COMPLETED).length
      const unassignedTasks = projectTasks.filter(t => t.status === STATUS.UNASSIGNED).length
      const inProgressTasks = projectTasks.filter(t => t.status === STATUS.IN_PROGRESS).length
      const pendingTasks = projectTasks.filter(t => t.status === STATUS.PENDING_VERIFICATION).length
      const taskCount = projectTasks.length
      const progress = calculateProgress(taskCount, completedTasks)
      
      // Count unique team members with assigned tasks
      const uniqueAssignedMembers = new Set(
        projectTasks
          .filter(t => t.assignedTo) // Only tasks with assigned members
          .map(t => t.assignedTo)
      )
      const activeTeamMembers = uniqueAssignedMembers.size
      
      return {
        ...project,
        taskCount,
        completedTasks,
        unassignedTasks,
        inProgressTasks,
        pendingTasks,
        progress,
        activeTeamMembers
      }
    })
  }

  // Toast notifications
  const showToast = useCallback((message, type = 'info') => {
    setToast({ show: true, message, type })
    setTimeout(() => {
      setToast({ show: false, message: '', type: 'info' })
    }, 3000)
  }, [])

  // Project operations
  const addProject = async (project) => {
    if (isOffline) {
      showToast('⚠️ Cannot create project while offline', 'error')
      return null
    }
    
    try {
      console.log("🔄 Creating project via API...", project)
      const newProject = await apiService.createProject(project)
      await loadData() // Refresh all data
      showToast('Project created successfully!', 'success')
      return newProject
    } catch (error) {
      console.error("❌ Failed to create project via API:", error)
      setIsOffline(true)
      showToast('⚠️ Connection lost - Cannot save changes', 'error')
      return null
    }
  }

  const updateProject = async (id, updates) => {
    if (isOffline) {
      showToast('⚠️ Cannot update project while offline', 'error')
      return
    }
    
    try {
      console.log(`🔄 Updating project ${id} via API...`, updates)
      
      // If assignedEmployees is being updated, check for removed employees
      if (updates.assignedEmployees !== undefined) {
        const currentProject = projects.find(p => p.id === id)
        if (currentProject && currentProject.assignedEmployees) {
          // Find employees that were removed
          const removedEmployees = currentProject.assignedEmployees.filter(
            empId => !updates.assignedEmployees.includes(empId)
          )
          
          // If any employees were removed, unassign their tasks
          if (removedEmployees.length > 0) {
            console.log(`🔄 Unassigning tasks for removed employees:`, removedEmployees)
            
            // Get tasks for this project that are assigned to removed employees
            const tasksToUnassign = tasks.filter(
              task => task.projectId === id && removedEmployees.includes(task.assignedTo)
            )
            
            // Update each task to unassigned status
            for (const task of tasksToUnassign) {
              try {
                await apiService.updateTask(task.id, {
                  assignedTo: null,
                  status: STATUS.UNASSIGNED
                })
                console.log(`✅ Unassigned task ${task.id}`)
              } catch (taskError) {
                console.error(`❌ Failed to unassign task ${task.id}:`, taskError)
              }
            }
          }
        }
      }
      
      await apiService.updateProject(id, updates)
      await loadData() // Refresh all data
      showToast('Project updated successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to update project via API:", error)
      setIsOffline(true)
      showToast('⚠️ Connection lost - Cannot save changes', 'error')
    }
  }

  const deleteProject = async (id) => {
    if (isOffline) {
      showToast('⚠️ Cannot delete project while offline', 'error')
      return
    }
    
    try {
      console.log(`🔄 Deleting project ${id} via API...`)
      await apiService.deleteProject(id)
      await loadData() // Refresh all data
      showToast('Project deleted successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to delete project via API:", error)
      setIsOffline(true)
      showToast('⚠️ Connection lost - Cannot save changes', 'error')
    }
  }

  const getProjectById = (id) => {
    return projects.find(p => p.id === id)
  }

  // Task operations
  const addTask = async (task) => {
    if (isOffline) {
      showToast('⚠️ Cannot create task while offline', 'error')
      return null
    }
    
    try {
      console.log("📡 Creating task via API...")
      const newTask = await apiService.createTask(task)
      // Refresh tasks from API
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      
      // Update localStorage cache
      storageService.setTasks(tasksData)
      
      showToast('Task created successfully!', 'success')
      return newTask
    } catch (error) {
      console.error("❌ Failed to create task via API:", error)
      setIsOffline(true)
      showToast('⚠️ Connection lost - Cannot save changes', 'error')
      return null
    }
  }

  const updateTask = async (id, updates, source = 'admin') => {
    if (isOffline) {
      showToast('⚠️ Cannot update task while offline', 'error')
      return
    }
    
    // Store previous state for potential rollback
    const previousTasks = [...tasks]
    
    // Optimistic update - update UI immediately for better UX
    // ROBUST ID MATCHING: Match by taskId, id, or either field
    setTasks(prev => prev.map(t => {
      // Check all possible ID fields for maximum compatibility
      const matchesById = t.id === id || t.taskId === id
      const matchesByTaskId = t.id === id || t.taskId === id
      
      if (matchesById || matchesByTaskId) {
        return { ...t, ...updates }
      }
      return t
    }))
    
    try {
      console.log(`📡 Updating task ${id} via API... (source: ${source})`)
      // Add source to updates to track update origin
      const updateWithSource = { ...updates, updateSource: source }
      await apiService.updateTask(id, updateWithSource)
      // Refresh tasks from API to get latest data
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      
      // Update localStorage cache
      storageService.setTasks(tasksData)
      
      showToast('Task updated successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to update task via API:", error)
      // Revert optimistic update on error - restore previous state
      setTasks(previousTasks)
      setIsOffline(true)
      showToast('⚠️ Connection lost - Cannot save changes', 'error')
    }
  }

  const deleteTask = async (id) => {
    if (isOffline) {
      showToast('⚠️ Cannot delete task while offline', 'error')
      return
    }
    
    try {
      console.log(`📡 Deleting task ${id} via API...`)
      await apiService.deleteTask(id)
      // Refresh tasks from API
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      
      // Update localStorage cache
      storageService.saveTasks(tasksData)
      
      showToast('Task deleted successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to delete task via API:", error)
      setIsOffline(true)
      showToast('⚠️ Connection lost - Cannot save changes', 'error')
    }
  }

  const getTasksByProject = (projectId) => {
    return tasks.filter(t => t.projectId === projectId)
  }

  const getTaskById = (id) => {
    return tasks.find(t => t.id === id)
  }

  // Employee operations
  const getEmployeeById = (id) => {
    return employees.find(e => e.id === id)
  }

  const getEmployeesByIds = (ids) => {
    return employees.filter(e => ids.includes(e.id))
  }

  // Employee CRUD operations
  const addEmployee = async (employeeData) => {
    if (isOffline) {
      showToast('Cannot add employee while offline', 'error')
      return
    }

    try {
      setLoading(true)
      console.log('🔄 Creating employee:', employeeData.name)
      
      const newEmployee = await apiService.createEmployee(employeeData)
      
      // Update local state
      setEmployees(prev => [...prev, newEmployee])
      
      // Sync with localStorage
      const updatedEmployees = [...employees, newEmployee]
      storageService.setEmployees(updatedEmployees)
      
      showToast(`Employee "${employeeData.name}" created successfully!`, 'success')
      console.log('✅ Employee created:', newEmployee)
      
    } catch (error) {
      console.error('❌ Error creating employee:', error)
      showToast(error.message || 'Failed to create employee', 'error')
    } finally {
      setLoading(false)
    }
  }

  const updateEmployee = async (id, updates) => {
    if (isOffline) {
      showToast('Cannot update employee while offline', 'error')
      return
    }

    try {
      setLoading(true)
      console.log(`🔄 Updating employee ${id}:`, updates)
      
      const updatedEmployee = await apiService.updateEmployee(id, updates)
      
      // Update local state
      setEmployees(prev => prev.map(emp => 
        emp.id === id ? updatedEmployee : emp
      ))
      
      // Sync with localStorage
      const updatedEmployees = employees.map(emp => 
        emp.id === id ? updatedEmployee : emp
      )
      storageService.setEmployees(updatedEmployees)
      
      showToast(`Employee "${updatedEmployee.name}" updated successfully!`, 'success')
      console.log('✅ Employee updated:', updatedEmployee)
      
    } catch (error) {
      console.error('❌ Error updating employee:', error)
      showToast(error.message || 'Failed to update employee', 'error')
    } finally {
      setLoading(false)
    }
  }

  const deleteEmployee = async (id) => {
    if (isOffline) {
      showToast('Cannot delete employee while offline', 'error')
      return
    }

    try {
      setLoading(true)
      const employee = getEmployeeById(id)
      console.log(`🔄 Deleting employee ${id}: ${employee?.name}`)
      
      await apiService.deleteEmployee(id)
      
      // Update local state
      setEmployees(prev => prev.filter(emp => emp.id !== id))
      
      // Update tasks to remove deleted employee assignments
      setTasks(prev => prev.map(task => 
        task.assignedTo === id 
          ? { ...task, assignedTo: null, status: STATUS.UNASSIGNED }
          : task
      ))
      
      // Sync with localStorage
      const updatedEmployees = employees.filter(emp => emp.id !== id)
      const updatedTasks = tasks.map(task => 
        task.assignedTo === id 
          ? { ...task, assignedTo: null, status: STATUS.UNASSIGNED }
          : task
      )
      storageService.setEmployees(updatedEmployees)
      storageService.setTasks(updatedTasks)
      
      showToast(`Employee "${employee?.name}" deleted successfully!`, 'success')
      console.log('✅ Employee deleted and tasks updated')
      
    } catch (error) {
      console.error('❌ Error deleting employee:', error)
      showToast(error.message || 'Failed to delete employee', 'error')
    } finally {
      setLoading(false)
    }
  }

  // Timer operations
  const updateTimerConfig = (updates) => {
    const updated = storageService.updateTimerConfig(updates)
    setTimerConfig(updated)
    showToast('Timer settings updated!', 'success')
  }

  // Send task to WhatsApp via API
  const sendTaskToWhatsApp = async (taskId) => {
    try {
      console.log(`📱 Sending task ${taskId} to WhatsApp...`)
      await apiService.sendTaskToWhatsApp(taskId)
      
      // Reload tasks to get updated whatsapp_sent status
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      
      showToast('Task sent to WhatsApp! 📱', 'success')
      return true
    } catch (error) {
      console.error("❌ Failed to send task to WhatsApp:", error)
      showToast(error.message || 'Failed to send to WhatsApp', 'error')
      return false
    }
  }

  const value = {
    // State
    projects,
    tasks,
    employees,
    timerConfig,
    toast,
    loading,
    isOffline,
    modalOpen,
    setModalOpen,
    
    // Project methods
    addProject,
    updateProject,
    deleteProject,
    getProjectById,
    
    // Task methods
    addTask,
    updateTask,
    deleteTask,
    getTasksByProject,
    getTaskById,
    getTasks: () => tasks,
    
    // Employee methods
    getEmployeeById,
    getEmployeesByIds,
    addEmployee,
    updateEmployee,
    deleteEmployee,
    
    // Timer methods
    updateTimerConfig,
    
    // Utility methods
    showToast,
    sendTaskToWhatsApp,
    refreshData: loadData
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export { AppProvider }


