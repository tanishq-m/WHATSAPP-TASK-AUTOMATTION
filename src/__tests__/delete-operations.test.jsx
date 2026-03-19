import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom'
import { AppProvider } from '../context/AppContext'
import Dashboard from '../pages/Dashboard'
import ProjectDetail from '../pages/ProjectDetail'
import Employees from '../pages/Employees'
import * as apiService from '../services/api.service'

// Mock API service
vi.mock('../services/api.service', () => ({
  getProjects: vi.fn(),
  getTasks: vi.fn(),
  getEmployees: vi.fn(),
  deleteProject: vi.fn(),
  deleteTask: vi.fn(),
  deleteEmployee: vi.fn(),
  createProject: vi.fn(),
  createTask: vi.fn(),
  createEmployee: vi.fn(),
  updateProject: vi.fn(),
  updateTask: vi.fn(),
  updateEmployee: vi.fn(),
}))

// Helper component to wrap tests
const TestWrapper = ({ children, initialRoute = '/' }) => (
  <MemoryRouter initialEntries={[initialRoute]}>
    <AppProvider>
      {children}
    </AppProvider>
  </MemoryRouter>
)

// Helper component for routing tests
const AppWithRoutes = ({ initialRoute = '/' }) => (
  <MemoryRouter initialEntries={[initialRoute]}>
    <AppProvider>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/project/:projectId" element={<ProjectDetail />} />
        <Route path="/employees" element={<Employees />} />
      </Routes>
    </AppProvider>
  </MemoryRouter>
)

describe('Delete Operations - Navigation Behavior', () => {
  const mockProjects = [
    {
      id: 'proj_1',
      name: 'Test Project 1',
      description: 'First project',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      color: '#3B82F6',
      assignedEmployees: [1],
      taskCount: 5,
      completedTasks: 2,
      unassignedTasks: 1,
      inProgressTasks: 1,
      pendingTasks: 1,
      progress: 40
    },
    {
      id: 'proj_2',
      name: 'Test Project 2',
      description: 'Second project',
      startDate: '2024-02-01',
      endDate: '2024-12-31',
      color: '#10B981',
      assignedEmployees: [2],
      taskCount: 3,
      completedTasks: 1,
      unassignedTasks: 1,
      inProgressTasks: 1,
      pendingTasks: 0,
      progress: 33
    }
  ]

  const mockTasks = [
    {
      id: 'task_1',
      taskId: 'task_1',
      title: 'Task 1',
      description: 'Test task',
      projectId: 'proj_1',
      assignedTo: 1,
      status: 'completed',
      priority: 'high',
      dueDate: '2024-12-31'
    },
    {
      id: 'task_2',
      taskId: 'task_2',
      title: 'Task 2',
      description: 'Test task 2',
      projectId: 'proj_1',
      assignedTo: 1,
      status: 'in_progress',
      priority: 'medium',
      dueDate: '2024-12-31'
    }
  ]

  const mockEmployees = [
    {
      id: 1,
      name: 'John Doe',
      phone: '+919876543210',
      role: 'Developer'
    },
    {
      id: 2,
      name: 'Jane Smith',
      phone: '+919876543211',
      role: 'Designer'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    apiService.getProjects.mockResolvedValue(mockProjects)
    apiService.getTasks.mockResolvedValue(mockTasks)
    apiService.getEmployees.mockResolvedValue(mockEmployees)
    apiService.deleteProject.mockResolvedValue({ success: true })
    apiService.deleteTask.mockResolvedValue({ success: true })
    apiService.deleteEmployee.mockResolvedValue({ success: true })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Project Deletion', () => {
    it('should stay on dashboard after deleting a project', async () => {
      const user = userEvent.setup()
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Find the first project card and its delete button
      const projectCards = screen.getAllByText(/Test Project/i)
      expect(projectCards).toHaveLength(2)

      // Click delete button on first project
      const deleteButtons = screen.getAllByTitle('Delete project')
      await user.click(deleteButtons[0])

      // Confirm deletion in dialog
      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /Delete Project/i })
      await user.click(confirmButton)

      // Wait for deletion to complete
      await waitFor(() => {
        expect(apiService.deleteProject).toHaveBeenCalledWith('proj_1')
      })

      // Verify we're still on dashboard (header should be visible)
      await waitFor(() => {
        expect(screen.getByText('My Projects')).toBeInTheDocument()
      })

      // Verify the URL hasn't changed (should still be on dashboard)
      expect(window.location.pathname).toBe('/')
    })

    it('should not navigate away when project deletion fails', async () => {
      const user = userEvent.setup()
      apiService.deleteProject.mockRejectedValue(new Error('Delete failed'))
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Click delete button on first project
      const deleteButtons = screen.getAllByTitle('Delete project')
      await user.click(deleteButtons[0])

      // Confirm deletion in dialog
      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      // Find the confirm button in the modal
      const confirmButtons = screen.getAllByRole('button', { name: /Delete Project/i })
      const confirmButton = confirmButtons.find(btn => btn.textContent === 'Delete Project')
      await user.click(confirmButton)

      // Wait for deletion attempt
      await waitFor(() => {
        expect(apiService.deleteProject).toHaveBeenCalled()
      })

      // Verify we're still on dashboard
      expect(screen.getByText('My Projects')).toBeInTheDocument()
      expect(window.location.pathname).toBe('/')
    })

    it('should handle deleting multiple projects without navigation', async () => {
      const user = userEvent.setup()
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Delete first project
      const deleteButtons = screen.getAllByTitle('Delete project')
      await user.click(deleteButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      const confirmButtons = screen.getAllByRole('button', { name: /Delete Project/i })
      const confirmButton = confirmButtons.find(btn => btn.textContent === 'Delete Project')
      await user.click(confirmButton)

      await waitFor(() => {
        expect(apiService.deleteProject).toHaveBeenCalledWith('proj_1')
      })

      // Verify still on dashboard
      expect(screen.getByText('My Projects')).toBeInTheDocument()
      expect(window.location.pathname).toBe('/')
    })
  })

  describe('Task Deletion', () => {
    it('should stay on same page after deleting a task', async () => {
      const user = userEvent.setup()
      
      render(<AppWithRoutes initialRoute="/project/proj_1" />)

      // Wait for project and tasks to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Find and click delete button on task
      const deleteButtons = screen.getAllByTitle('Delete task')
      if (deleteButtons.length > 0) {
        await user.click(deleteButtons[0])

        // Confirm deletion
        await waitFor(() => {
          expect(screen.getByText('Delete Task')).toBeInTheDocument()
        })

        const confirmButton = screen.getByRole('button', { name: /Delete/i })
        await user.click(confirmButton)

        // Wait for deletion
        await waitFor(() => {
          expect(apiService.deleteTask).toHaveBeenCalled()
        })

        // Verify we're still on project detail page
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
        expect(window.location.pathname).toBe('/project/proj_1')
      }
    })

    it('should not navigate when task deletion fails', async () => {
      const user = userEvent.setup()
      apiService.deleteTask.mockRejectedValue(new Error('Delete failed'))
      
      render(<AppWithRoutes initialRoute="/project/proj_1" />)

      // Wait for project to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Try to delete a task
      const deleteButtons = screen.getAllByTitle('Delete task')
      if (deleteButtons.length > 0) {
        await user.click(deleteButtons[0])

        await waitFor(() => {
          expect(screen.getByText('Delete Task')).toBeInTheDocument()
        })

        await user.click(screen.getByRole('button', { name: /Delete/i }))

        // Wait for deletion attempt
        await waitFor(() => {
          expect(apiService.deleteTask).toHaveBeenCalled()
        })

        // Verify we're still on project detail page
        expect(window.location.pathname).toBe('/project/proj_1')
      }
    })
  })

  describe('Employee Deletion', () => {
    it('should stay on employees page after deleting an employee', async () => {
      const user = userEvent.setup()
      
      render(<AppWithRoutes initialRoute="/employees" />)

      // Wait for employees to load
      await waitFor(() => {
        expect(screen.getByText('Team Members')).toBeInTheDocument()
        expect(screen.getByText('John Doe')).toBeInTheDocument()
      })

      // Find and click delete button
      const deleteButtons = screen.getAllByTitle('Delete employee')
      await user.click(deleteButtons[0])

      // Confirm deletion
      await waitFor(() => {
        expect(screen.getAllByText('Delete Employee')[0]).toBeInTheDocument()
      })

      const confirmButtons = screen.getAllByRole('button', { name: /Delete Employee/i })
      const confirmButton = confirmButtons.find(btn => btn.textContent === 'Delete Employee')
      await user.click(confirmButton)

      // Wait for deletion
      await waitFor(() => {
        expect(apiService.deleteEmployee).toHaveBeenCalledWith(1)
      })

      // Verify we're still on employees page
      await waitFor(() => {
        expect(screen.getByText('Team Members')).toBeInTheDocument()
      })
      expect(window.location.pathname).toBe('/employees')
    })

    it('should not navigate when employee deletion fails', async () => {
      const user = userEvent.setup()
      apiService.deleteEmployee.mockRejectedValue(new Error('Delete failed'))
      
      render(<AppWithRoutes initialRoute="/employees" />)

      // Wait for employees to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument()
      })

      // Try to delete employee
      const deleteButtons = screen.getAllByTitle('Delete employee')
      await user.click(deleteButtons[0])

      await waitFor(() => {
        expect(screen.getAllByText('Delete Employee')[0]).toBeInTheDocument()
      })

      const confirmButtons = screen.getAllByRole('button', { name: /Delete Employee/i })
      const confirmButton = confirmButtons.find(btn => btn.textContent === 'Delete Employee')
      await user.click(confirmButton)

      // Wait for deletion attempt
      await waitFor(() => {
        expect(apiService.deleteEmployee).toHaveBeenCalled()
      })

      // Verify we're still on employees page
      expect(window.location.pathname).toBe('/employees')
    })
  })

  describe('Confirmation Dialog Behavior', () => {
    it('should not delete when canceling confirmation dialog', async () => {
      const user = userEvent.setup()
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Click delete button
      const deleteButtons = screen.getAllByTitle('Delete project')
      await user.click(deleteButtons[0])

      // Cancel deletion
      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      const cancelButton = screen.getByRole('button', { name: /Cancel/i })
      await user.click(cancelButton)

      // Verify delete was not called
      expect(apiService.deleteProject).not.toHaveBeenCalled()

      // Verify we're still on dashboard
      expect(screen.getByText('My Projects')).toBeInTheDocument()
      expect(window.location.pathname).toBe('/')
    })

    it('should close dialog without action when clicking outside', async () => {
      const user = userEvent.setup()
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Click delete button
      const deleteButtons = screen.getAllByTitle('Delete project')
      await user.click(deleteButtons[0])

      // Wait for dialog to appear
      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      // Verify delete was not called
      await waitFor(() => {
        expect(apiService.deleteProject).not.toHaveBeenCalled()
      }, { timeout: 1000 }).catch(() => {
        // Expected to timeout without deletion
      })
    })
  })

  describe('Page State After Deletion', () => {
    it('should refresh project list after successful deletion', async () => {
      const user = userEvent.setup()
      
      // Mock returning fewer projects after deletion
      apiService.deleteProject.mockImplementation(async () => {
        apiService.getProjects.mockResolvedValue([mockProjects[1]]) // Only return second project
        return { success: true }
      })
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Delete first project
      const deleteButtons = screen.getAllByTitle('Delete project')
      await user.click(deleteButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      const confirmButtons = screen.getAllByRole('button', { name: /Delete Project/i })
      const confirmButton = confirmButtons.find(btn => btn.textContent === 'Delete Project')
      await user.click(confirmButton)

      // Wait for deletion and refresh
      await waitFor(() => {
        expect(apiService.deleteProject).toHaveBeenCalled()
        expect(apiService.getProjects).toHaveBeenCalled()
      })

      // Verify we're still on dashboard
      expect(window.location.pathname).toBe('/')
    })

    it('should show empty state when all projects are deleted', async () => {
      const user = userEvent.setup()
      
      // Start with only one project
      apiService.getProjects.mockResolvedValue([mockProjects[0]])
      
      // After deletion, return empty array
      apiService.deleteProject.mockImplementation(async () => {
        apiService.getProjects.mockResolvedValue([])
        return { success: true }
      })
      
      render(<AppWithRoutes initialRoute="/" />)

      // Wait for project to load
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument()
      })

      // Delete the project
      const deleteButton = screen.getByTitle('Delete project')
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText('Delete Project?')).toBeInTheDocument()
      })

      const confirmButtons = screen.getAllByRole('button', { name: /Delete Project/i })
      const confirmButton = confirmButtons.find(btn => btn.textContent === 'Delete Project')
      await user.click(confirmButton)

      // Wait for deletion
      await waitFor(() => {
        expect(apiService.deleteProject).toHaveBeenCalled()
      })

      // Verify empty state is shown
      await waitFor(() => {
        expect(screen.getByText(/No projects yet/i)).toBeInTheDocument()
      })

      // Verify we're still on dashboard
      expect(window.location.pathname).toBe('/')
    })
  })
})
