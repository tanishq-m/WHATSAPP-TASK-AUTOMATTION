import { createContext, useState, useEffect, useCallback } from 'react'
import storageService from '../services/localStorage.service'
import apiService from '../services/api.service'
import timerService from '../services/timer.service'
import { calculateProgress } from '../utils/helpers'
import { STATUS } from '../utils/constants'

export const AppContext = createContext()

export const AppProvider = ({ children }) => {
  const [projects, setProjects] = useState([])
  const [tasks, setTasks] = useState([])
  const [employees, setEmployees] = useState([])
  const [timerConfig, setTimerConfig] = useState(null)
  const [toast, setToast] = useState({ show: false, message: '', type: 'info' })
  const [loading, setLoading] = useState(false)
  const [isOffline, setIsOffline] = useState(false)

  // Initialize data from localStorage
  useEffect(() => {
    storageService.init()
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    
    let loadedTasks = []
    let loadedProjects = []
    let loadedEmployees = []
    let apiSuccess = false
    
    try {
      // Try to fetch employees from backend API
      console.log("🔄 Loading employees from backend API...")
      const employeesData = await apiService.getEmployees()
      loadedEmployees = employeesData
      setEmployees(employeesData)
      console.log("✅ Employees loaded from API:", employeesData.length)
      
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
      loadedTasks = tasksData
      setTasks(tasksData)
      console.log("✅ Tasks loaded from API:", tasksData.length)
      
      // Sync to localStorage
      storageService.setTasks(tasksData)
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
      loadedProjects = projectsData
      // Calculate stats for projects using loaded tasks
      const projectsWithStats = calculateProjectStats(projectsData, loadedTasks)
      setProjects(projectsWithStats)
      console.log("✅ Projects loaded from API:", projectsData.length)
      apiSuccess = true
      
      // Sync to localStorage
      storageService.setProjects(projectsData)
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
      setIsOffline(false)
    } else {
      setIsOffline(true)
      if (!toast.show) {
        showToast("⚠️ Offline Mode - Cannot save changes until reconnected", "warning")
      }
    }

    setTimerConfig(storageService.getTimerConfig())
    setLoading(false)
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
    
    // Employee methods
    getEmployeeById,
    getEmployeesByIds,
    
    // Timer methods
    updateTimerConfig,
    
    // Utility methods
    showToast,
    sendTaskToWhatsApp,
    refreshData: loadData
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}


