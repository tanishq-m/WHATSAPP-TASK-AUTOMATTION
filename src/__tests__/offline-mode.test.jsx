import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AppProvider, AppContext } from '../context/AppContext'
import { useContext } from 'react'
import apiService from '../services/api.service'

// Mock the services
vi.mock('../services/api.service')
vi.mock('../services/localStorage.service', () => ({
  default: {
    init: vi.fn(),
    getProjects: vi.fn(() => []),
    getTasks: vi.fn(() => []),
    getEmployees: vi.fn(() => []),
    getTimerConfig: vi.fn(() => ({ workMinutes: 25, breakMinutes: 5, longBreakMinutes: 15 })),
    setProjects: vi.fn(),
    setTasks: vi.fn(),
    setEmployees: vi.fn(),
    updateTimerConfig: vi.fn((updates) => ({ workMinutes: 25, breakMinutes: 5, longBreakMinutes: 15, ...updates }))
  }
}))

// Test component that uses AppContext
const TestComponent = ({ testFn }) => {
  const context = useContext(AppContext)
  
  // Call test function with context when component mounts
  if (testFn) {
    testFn(context)
  }
  
  return (
    <div>
      <div data-testid="offline-status">{context.isOffline ? 'offline' : 'online'}</div>
      <div data-testid="projects-count">{context.projects.length}</div>
      <div data-testid="tasks-count">{context.tasks.length}</div>
    </div>
  )
}

describe('Offline Mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial Load', () => {
    it('should set isOffline to false when API loads successfully', async () => {
      // Mock successful API calls
      apiService.getProjects.mockResolvedValue([
        { id: 'proj_1', name: 'Project 1', assigned_employees: [] }
      ])
      apiService.getTasks.mockResolvedValue([
        { id: 'task_1', title: 'Task 1', projectId: 'proj_1', status: 'unassigned' }
      ])
      apiService.getEmployees.mockResolvedValue([
        { id: 1, name: 'John Doe', phone: '+911234567890' }
      ])

      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('online')
      })
    })

    it('should set isOffline to true when API fails', async () => {
      // Mock failed API calls
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      render(
        <AppProvider>
          <TestComponent />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })
    })
  })

  describe('Write Operations When Offline', () => {
    it('should prevent addProject when offline', async () => {
      // Mock failed API to trigger offline mode
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      // Wait for offline state to be set
      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      // Try to add project while offline
      const result = await contextRef.addProject({ name: 'New Project' })

      // Should return null and not call API
      expect(result).toBeNull()
      expect(apiService.createProject).not.toHaveBeenCalled()
    })

    it('should prevent updateProject when offline', async () => {
      // Mock failed API to trigger offline mode
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      // Try to update project while offline
      await contextRef.updateProject('proj_1', { name: 'Updated' })

      // Should not call API
      expect(apiService.updateProject).not.toHaveBeenCalled()
    })

    it('should prevent deleteProject when offline', async () => {
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      await contextRef.deleteProject('proj_1')

      expect(apiService.deleteProject).not.toHaveBeenCalled()
    })

    it('should prevent addTask when offline', async () => {
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      const result = await contextRef.addTask({ title: 'New Task', projectId: 'proj_1' })

      expect(result).toBeNull()
      expect(apiService.createTask).not.toHaveBeenCalled()
    })

    it('should prevent updateTask when offline', async () => {
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      await contextRef.updateTask('task_1', { status: 'in_progress' })

      expect(apiService.updateTask).not.toHaveBeenCalled()
    })

    it('should prevent deleteTask when offline', async () => {
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      await contextRef.deleteTask('task_1')

      expect(apiService.deleteTask).not.toHaveBeenCalled()
    })
  })

  describe('Recovery from Offline Mode', () => {
    it('should transition from offline to online when API becomes available', async () => {
      // Start offline
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      // Mock API recovery
      apiService.getProjects.mockResolvedValue([
        { id: 'proj_1', name: 'Project 1', assigned_employees: [] }
      ])
      apiService.getTasks.mockResolvedValue([
        { id: 'task_1', title: 'Task 1', projectId: 'proj_1', status: 'unassigned' }
      ])
      apiService.getEmployees.mockResolvedValue([
        { id: 1, name: 'John Doe', phone: '+911234567890' }
      ])

      // Trigger refresh
      await contextRef.refreshData()

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('online')
      })
    })

    it('should allow write operations after recovering from offline mode', async () => {
      // Start offline
      apiService.getProjects.mockRejectedValue(new Error('Network error'))
      apiService.getTasks.mockRejectedValue(new Error('Network error'))
      apiService.getEmployees.mockRejectedValue(new Error('Network error'))

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })

      // Mock API recovery
      apiService.getProjects.mockResolvedValue([])
      apiService.getTasks.mockResolvedValue([])
      apiService.getEmployees.mockResolvedValue([])
      apiService.createProject.mockResolvedValue({ id: 'proj_new', name: 'New Project' })

      // Refresh to go online
      await contextRef.refreshData()

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('online')
      })

      // Now write operations should work
      const result = await contextRef.addProject({ name: 'New Project' })

      expect(result).not.toBeNull()
      expect(apiService.createProject).toHaveBeenCalled()
    })
  })

  describe('Error Handling During Operations', () => {
    it('should set isOffline when write operation fails', async () => {
      // Start online
      apiService.getProjects.mockResolvedValue([])
      apiService.getTasks.mockResolvedValue([])
      apiService.getEmployees.mockResolvedValue([])

      let contextRef = null

      render(
        <AppProvider>
          <TestComponent testFn={(ctx) => { contextRef = ctx }} />
        </AppProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('online')
      })

      // Mock API failure during operation
      apiService.createProject.mockRejectedValue(new Error('Connection lost'))

      // Try to create project
      await contextRef.addProject({ name: 'Test Project' })

      // Should now be offline
      await waitFor(() => {
        expect(screen.getByTestId('offline-status').textContent).toBe('offline')
      })
    })
  })
})
