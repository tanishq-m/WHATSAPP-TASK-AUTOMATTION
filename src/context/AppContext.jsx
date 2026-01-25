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

  // Initialize data from localStorage
  useEffect(() => {
    storageService.init()
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    
    let loadedTasks = []
    
    try {
      // Try to fetch employees from backend API
      console.log("🔄 Loading employees from backend API...")
      const employeesData = await apiService.getEmployees()
      setEmployees(employeesData)
      console.log("✅ Employees loaded from API")
    } catch (error) {
      // Fallback to localStorage if API fails
      console.warn("⚠️ API failed, falling back to localStorage for employees")
      console.error("Error:", error)
      setEmployees(storageService.getEmployees())
      showToast("Using offline data - backend not connected", "warning")
    }

    // Try to fetch tasks from backend API first (needed for project stats)
    try {
      console.log("🔄 Loading tasks from backend API...")
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      loadedTasks = tasksData
      console.log("✅ Tasks loaded from API")
    } catch (error) {
      console.warn("⚠️ API failed, falling back to localStorage for tasks")
      console.error("Error:", error)
      const tasksData = storageService.getTasks()
      setTasks(tasksData)
      loadedTasks = tasksData
      if (!toast.show) {
        showToast("Using offline data for tasks", "warning")
      }
    }

    // Try to fetch projects from backend API
    try {
      console.log("🔄 Loading projects from backend API...")
      const projectsData = await apiService.getProjects()
      // Calculate stats for projects using loaded tasks
      const projectsWithStats = calculateProjectStats(projectsData, loadedTasks)
      setProjects(projectsWithStats)
      console.log("✅ Projects loaded from API")
    } catch (error) {
      console.warn("⚠️ API failed, falling back to localStorage for projects")
      console.error("Error:", error)
      setProjects(getProjectsWithStats())
      if (!toast.show) { // Only show toast if not already showing
        showToast("Using offline data for projects", "warning")
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
      
      return {
        ...project,
        taskCount,
        completedTasks,
        unassignedTasks,
        inProgressTasks,
        pendingTasks,
        progress
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
      
      return {
        ...project,
        taskCount,
        completedTasks,
        unassignedTasks,
        inProgressTasks,
        pendingTasks,
        progress
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
    try {
      console.log("🔄 Creating project via API...", project)
      const newProject = await apiService.createProject(project)
      await loadData() // Refresh all data
      showToast('Project created successfully!', 'success')
      return newProject
    } catch (error) {
      console.error("❌ Failed to create project via API:", error)
      // Fallback to localStorage
      const newProject = storageService.addProject(project)
      setProjects(getProjectsWithStats())
      showToast('Project created (offline mode)', 'warning')
      return newProject
    }
  }

  const updateProject = async (id, updates) => {
    try {
      console.log(`🔄 Updating project ${id} via API...`, updates)
      await apiService.updateProject(id, updates)
      await loadData() // Refresh all data
      showToast('Project updated successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to update project via API:", error)
      // Fallback to localStorage
      storageService.updateProject(id, updates)
      setProjects(getProjectsWithStats())
      showToast('Project updated (offline mode)', 'warning')
    }
  }

  const deleteProject = async (id) => {
    try {
      console.log(`🔄 Deleting project ${id} via API...`)
      await apiService.deleteProject(id)
      await loadData() // Refresh all data
      showToast('Project deleted successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to delete project via API:", error)
      // Fallback to localStorage
      storageService.deleteProject(id)
      setProjects(getProjectsWithStats())
      showToast('Project deleted (offline mode)', 'warning')
    }
  }

  const getProjectById = (id) => {
    return projects.find(p => p.id === id)
  }

  // Task operations
  const addTask = async (task) => {
    try {
      console.log("📡 Creating task via API...")
      const newTask = await apiService.createTask(task)
      // Refresh tasks from API
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      showToast('Task created successfully!', 'success')
      return newTask
    } catch (error) {
      console.error("❌ Failed to create task via API:", error)
      // Fallback to localStorage
      const newTask = storageService.addTask(task)
      setTasks(storageService.getTasks())
      showToast('Task created (offline mode)', 'warning')
      return newTask
    }
  }

  const updateTask = async (id, updates, source = 'admin') => {
    // Store previous state for potential rollback
    const previousTasks = [...tasks]
    
    // Optimistic update - update UI immediately for better UX
    setTasks(prev => prev.map(t => {
      const taskId = t.taskId || t.id
      if (taskId === id) {
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
      showToast('Task updated successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to update task via API:", error)
      // Revert optimistic update on error - restore previous state
      setTasks(previousTasks)
      // Try fallback to localStorage
      try {
        storageService.updateTask(id, updates)
        setTasks(storageService.getTasks())
        showToast('Task updated (offline mode)', 'warning')
      } catch (localError) {
        console.error("❌ LocalStorage fallback also failed:", localError)
        showToast('Failed to update task. Please try again.', 'error')
      }
    }
  }

  const deleteTask = async (id) => {
    try {
      console.log(`📡 Deleting task ${id} via API...`)
      await apiService.deleteTask(id)
      // Refresh tasks from API
      const tasksData = await apiService.getTasks()
      setTasks(tasksData)
      showToast('Task deleted successfully!', 'success')
    } catch (error) {
      console.error("❌ Failed to delete task via API:", error)
      // Fallback to localStorage
      storageService.deleteTask(id)
      setTasks(storageService.getTasks())
      showToast('Task deleted (offline mode)', 'warning')
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


