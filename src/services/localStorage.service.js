import { STORAGE_KEYS } from '../utils/constants'
import { MOCK_EMPLOYEES, MOCK_PROJECTS, MOCK_TASKS, MOCK_TIMER_CONFIG } from './mockData'

class LocalStorageService {
  // Initialize with mock data if not exists
  init() {
    if (!this.getProjects().length) {
      this.setProjects(MOCK_PROJECTS)
    }
    if (!this.getTasks().length) {
      this.setTasks(MOCK_TASKS)
    }
    if (!this.getEmployees().length) {
      this.setEmployees(MOCK_EMPLOYEES)
    }
    if (!this.getTimerConfig()) {
      this.setTimerConfig(MOCK_TIMER_CONFIG)
    }
  }

  // Generic methods
  getItem(key) {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error(`Error getting ${key} from localStorage:`, error)
      return null
    }
  }

  setItem(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error setting ${key} in localStorage:`, error)
    }
  }

  // Projects
  getProjects() {
    return this.getItem(STORAGE_KEYS.PROJECTS) || []
  }

  setProjects(projects) {
    this.setItem(STORAGE_KEYS.PROJECTS, projects)
  }

  getProjectById(id) {
    const projects = this.getProjects()
    return projects.find(p => p.id === id)
  }

  addProject(project) {
    const projects = this.getProjects()
    projects.push(project)
    this.setProjects(projects)
    return project
  }

  updateProject(id, updates) {
    const projects = this.getProjects()
    const index = projects.findIndex(p => p.id === id)
    if (index !== -1) {
      projects[index] = { ...projects[index], ...updates }
      this.setProjects(projects)
      return projects[index]
    }
    return null
  }

  deleteProject(id) {
    const projects = this.getProjects()
    const filtered = projects.filter(p => p.id !== id)
    this.setProjects(filtered)
    // Also delete all tasks in this project
    const tasks = this.getTasks()
    const filteredTasks = tasks.filter(t => t.projectId !== id)
    this.setTasks(filteredTasks)
  }

  // Tasks
  getTasks() {
    return this.getItem(STORAGE_KEYS.TASKS) || []
  }

  setTasks(tasks) {
    this.setItem(STORAGE_KEYS.TASKS, tasks)
  }

  getTaskById(id) {
    const tasks = this.getTasks()
    return tasks.find(t => t.id === id)
  }

  getTasksByProject(projectId) {
    const tasks = this.getTasks()
    return tasks.filter(t => t.projectId === projectId)
  }

  getTasksByEmployee(employeeId) {
    const tasks = this.getTasks()
    return tasks.filter(t => t.assignedTo === employeeId)
  }

  addTask(task) {
    const tasks = this.getTasks()
    tasks.push(task)
    this.setTasks(tasks)
    return task
  }

  updateTask(id, updates) {
    const tasks = this.getTasks()
    const index = tasks.findIndex(t => t.id === id)
    if (index !== -1) {
      tasks[index] = { ...tasks[index], ...updates, updatedAt: new Date().toISOString() }
      this.setTasks(tasks)
      return tasks[index]
    }
    return null
  }

  deleteTask(id) {
    const tasks = this.getTasks()
    const filtered = tasks.filter(t => t.id !== id)
    this.setTasks(filtered)
  }

  // Employees
  getEmployees() {
    return this.getItem(STORAGE_KEYS.EMPLOYEES) || []
  }

  setEmployees(employees) {
    this.setItem(STORAGE_KEYS.EMPLOYEES, employees)
  }

  getEmployeeById(id) {
    const employees = this.getEmployees()
    return employees.find(e => e.id === id)
  }

  addEmployee(employee) {
    const employees = this.getEmployees()
    employees.push(employee)
    this.setEmployees(employees)
    return employee
  }

  updateEmployee(id, updates) {
    const employees = this.getEmployees()
    const index = employees.findIndex(e => e.id === id)
    if (index !== -1) {
      employees[index] = { ...employees[index], ...updates }
      this.setEmployees(employees)
      return employees[index]
    }
    return null
  }

  deleteEmployee(id) {
    const employees = this.getEmployees()
    const filtered = employees.filter(e => e.id !== id)
    this.setEmployees(filtered)
  }

  // Timer Config
  getTimerConfig() {
    return this.getItem(STORAGE_KEYS.TIMER_CONFIG)
  }

  setTimerConfig(config) {
    this.setItem(STORAGE_KEYS.TIMER_CONFIG, config)
  }

  updateTimerConfig(updates) {
    const config = this.getTimerConfig() || {}
    const updated = { ...config, ...updates }
    this.setTimerConfig(updated)
    return updated
  }

  // Clear all data
  clearAll() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key)
    })
  }
}

export default new LocalStorageService()


