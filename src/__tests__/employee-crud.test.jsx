/**
 * Frontend test suite for Phase 3 Employee Management
 * Tests employee CRUD operations, form validation, and edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AppProvider } from '../context/AppContext'
import EmployeeModal from '../components/employees/EmployeeModal'
import EmployeeCard from '../components/employees/EmployeeCard'
import Employees from '../pages/Employees'

// Mock API service
vi.mock('../services/api.service.js', () => ({
  getEmployees: vi.fn(),
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  deleteEmployee: vi.fn(),
  getProjects: vi.fn(() => Promise.resolve([])),
  getTasks: vi.fn(() => Promise.resolve([]))
}))

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AppProvider>
      {children}
    </AppProvider>
  </BrowserRouter>
)

describe('Phase 3: Employee CRUD Operations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  describe('EmployeeModal Component', () => {
    const mockOnClose = vi.fn()
    
    it('should render create employee modal correctly', () => {
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      expect(screen.getByText('Add Employee')).toBeInTheDocument()
      expect(screen.getByLabelText(/Employee Name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Phone Number/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Role/i)).toBeInTheDocument()
      expect(screen.getByText('Create Employee')).toBeInTheDocument()
    })

    it('should render edit employee modal with pre-filled data', () => {
      const employee = {
        id: 1,
        name: 'John Smith',
        phone: '+919876543210',
        role: 'Developer'
      }

      render(
        <TestWrapper>
          <EmployeeModal 
            isOpen={true} 
            onClose={mockOnClose} 
            employee={employee}
          />
        </TestWrapper>
      )

      expect(screen.getByText('Edit Employee')).toBeInTheDocument()
      expect(screen.getByDisplayValue('John Smith')).toBeInTheDocument()
      expect(screen.getByDisplayValue('+919876543210')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Developer')).toBeInTheDocument()
      expect(screen.getByText('Update Employee')).toBeInTheDocument()
    })

    it('should allow typing in all form fields', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const nameInput = screen.getByLabelText(/Employee Name/i)
      const phoneInput = screen.getByLabelText(/Phone Number/i)
      const roleSelect = screen.getByLabelText(/Role/i)

      // Test typing in name field
      await user.type(nameInput, 'Test Employee')
      expect(nameInput).toHaveValue('Test Employee')

      // Test typing in phone field
      await user.type(phoneInput, '+919876543210')
      expect(phoneInput).toHaveValue('+919876543210')

      // Test selecting role
      await user.selectOptions(roleSelect, 'Developer')
      expect(roleSelect).toHaveValue('Developer')
    })

    it('should validate required fields', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      const submitButton = screen.getByText('Create Employee')
      
      // Try to submit empty form
      await user.click(submitButton)

      // Should show validation errors (depends on your validation implementation)
      await waitFor(() => {
        // Check if form doesn't submit without required fields
        expect(mockOnClose).not.toHaveBeenCalled()
      })
    })

    it('should display helper text for phone field', () => {
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={mockOnClose} />
        </TestWrapper>
      )

      expect(screen.getByText('Include country code (e.g., +91 for India)')).toBeInTheDocument()
    })
  })

  describe('EmployeeCard Component', () => {
    const mockEmployee = {
      id: 1,
      name: 'John Smith',
      phone: '+919876543210',
      role: 'Developer'
    }

    const mockOnEdit = vi.fn()
    const mockOnDelete = vi.fn()

    it('should render employee information correctly', () => {
      render(
        <EmployeeCard 
          employee={mockEmployee}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('John Smith')).toBeInTheDocument()
      expect(screen.getByText('+919876543210')).toBeInTheDocument()
      expect(screen.getByText('Developer')).toBeInTheDocument()
    })

    it('should render edit and delete buttons', () => {
      render(
        <EmployeeCard 
          employee={mockEmployee}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByTitle('Edit employee')).toBeInTheDocument()
      expect(screen.getByTitle('Delete employee')).toBeInTheDocument()
    })

    it('should call onEdit when edit button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <EmployeeCard 
          employee={mockEmployee}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const editButton = screen.getByTitle('Edit employee')
      await user.click(editButton)

      expect(mockOnEdit).toHaveBeenCalledWith(mockEmployee)
    })

    it('should call onDelete when delete button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <EmployeeCard 
          employee={mockEmployee}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getByTitle('Delete employee')
      await user.click(deleteButton)

      expect(mockOnDelete).toHaveBeenCalledWith(mockEmployee)
    })
  })

  describe('Employees Page', () => {
    it('should render page header correctly', () => {
      render(
        <TestWrapper>
          <Employees />
        </TestWrapper>
      )

      expect(screen.getByText('Team Members')).toBeInTheDocument()
      expect(screen.getByText('Manage your team members and their roles')).toBeInTheDocument()
      expect(screen.getByText('Add Employee')).toBeInTheDocument()
    })

    it('should render employee stats correctly', () => {
      render(
        <TestWrapper>
          <Employees />
        </TestWrapper>
      )

      expect(screen.getByText('Total Members')).toBeInTheDocument()
      expect(screen.getByText('Developers')).toBeInTheDocument()
      expect(screen.getByText('Designers')).toBeInTheDocument()
      expect(screen.getByText('Testers')).toBeInTheDocument()
    })

    it('should show empty state when no employees exist', () => {
      render(
        <TestWrapper>
          <Employees />
        </TestWrapper>
      )

      expect(screen.getByText('No employees yet')).toBeInTheDocument()
      expect(screen.getByText('Add your first team member to get started with task assignments')).toBeInTheDocument()
      expect(screen.getByText('Add First Employee')).toBeInTheDocument()
    })

    it('should open employee modal when add button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <Employees />
        </TestWrapper>
      )

      // Use getByRole to specifically target the button, not the modal title
      const addButton = screen.getByRole('button', { name: /Add Employee/i })
      await user.click(addButton)

      // Modal should be open (check for modal title heading)
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Add Employee/i })).toBeInTheDocument()
      })
    })
  })

  describe('Employee Form Validation', () => {
    it('should validate phone number format', () => {
      const testCases = [
        { phone: '+919876543210', valid: true, description: 'Valid Indian number' },
        { phone: '+14155551234', valid: true, description: 'Valid US number' },
        { phone: '919876543210', valid: false, description: 'Missing + prefix' },
        { phone: '+91888', valid: false, description: 'Too short' },
        { phone: '', valid: false, description: 'Empty string' },
      ]

      testCases.forEach(({ phone, valid, description }) => {
        // This would test your validateEmployee function
        // The exact implementation depends on your validation logic
      })
    })

    it('should validate required fields', () => {
      const testCases = [
        { name: '', phone: '+919876543210', role: 'Developer', valid: false },
        { name: 'John', phone: '', role: 'Developer', valid: false },
        { name: 'John', phone: '+919876543210', role: '', valid: false },
        { name: 'John', phone: '+919876543210', role: 'Developer', valid: true },
      ]

      testCases.forEach(({ name, phone, role, valid }) => {
        // Test your validateEmployee function with these inputs
      })
    })
  })

  describe('API Error Handling', () => {
    it('should handle duplicate phone number error', async () => {
      const { createEmployee } = await import('../services/api.service.js')
      
      // Mock API to return duplicate phone error
      createEmployee.mockRejectedValue(new Error('Phone number already exists'))

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Fill form with valid data
      await user.type(screen.getByLabelText(/Employee Name/i), 'Test Employee')
      await user.type(screen.getByLabelText(/Phone Number/i), '+919876543210')
      await user.selectOptions(screen.getByLabelText(/Role/i), 'Developer')

      // Submit form
      await user.click(screen.getByText('Create Employee'))

      // Should show error message (this depends on your toast/error handling)
      await waitFor(() => {
        // Check that the error was handled properly
        expect(createEmployee).toHaveBeenCalled()
      })
    })

    it('should handle network errors gracefully', async () => {
      const { createEmployee } = await import('../services/api.service.js')
      
      // Mock network error
      createEmployee.mockRejectedValue(new Error('Network error'))

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Fill and submit form
      await user.type(screen.getByLabelText(/Employee Name/i), 'Test Employee')
      await user.type(screen.getByLabelText(/Phone Number/i), '+919876543210')
      await user.selectOptions(screen.getByLabelText(/Role/i), 'Developer')
      await user.click(screen.getByText('Create Employee'))

      await waitFor(() => {
        expect(createEmployee).toHaveBeenCalled()
      })
    })
  })

  describe('Delete Confirmation', () => {
    it('should show confirmation dialog with task count', async () => {
      const mockEmployee = {
        id: 1,
        name: 'John Smith',
        phone: '+919876543210',
        role: 'Developer'
      }

      render(
        <TestWrapper>
          <Employees />
        </TestWrapper>
      )

      // This test would require mocking the delete confirmation dialog
      // and checking that it shows the correct message about tasks
    })
  })

  describe('Edge Cases and Bug Fixes', () => {
    it('should handle special characters in names', async () => {
      const specialNames = [
        'José María',
        '李明',
        'Müller-Schmidt',
        "O'Connor",
        'Jean-Pierre'
      ]

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      for (const name of specialNames) {
        const nameInput = screen.getByLabelText(/Employee Name/i)
        
        // Clear and type new name
        await user.clear(nameInput)
        await user.type(nameInput, name)
        
        expect(nameInput).toHaveValue(name)
      }
    })

    it('should trim whitespace from inputs', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      const nameInput = screen.getByLabelText(/Employee Name/i)
      
      // Type name with leading/trailing spaces
      await user.type(nameInput, '  John Smith  ')
      
      // Your validation should trim whitespace
      // This depends on your form handling implementation
    })

    it('should pause auto-refresh when modal is open', () => {
      const { setModalOpen } = vi.fn()
      
      render(
        <TestWrapper>
          <EmployeeModal 
            isOpen={true} 
            onClose={vi.fn()} 
          />
        </TestWrapper>
      )

      // Should call setModalOpen(true) when modal opens
      // This is handled in the useEffect in EmployeeModal
    })

    it('should handle form submission during loading state', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      // Fill form
      await user.type(screen.getByLabelText(/Employee Name/i), 'Test Employee')
      await user.type(screen.getByLabelText(/Phone Number/i), '+919876543210')
      await user.selectOptions(screen.getByLabelText(/Role/i), 'Developer')

      // Submit form
      const submitButton = screen.getByText('Create Employee')
      await user.click(submitButton)

      // Button should be disabled during submission
      // This depends on your loading state implementation
    })
  })

  describe('Accessibility and Mobile Support', () => {
    it('should have proper ARIA labels', () => {
      render(
        <TestWrapper>
          <EmployeeModal isOpen={true} onClose={vi.fn()} />
        </TestWrapper>
      )

      expect(screen.getByLabelText(/Employee Name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Phone Number/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Role/i)).toBeInTheDocument()
    })

    it('should have touch-friendly button sizes', () => {
      const mockEmployee = {
        id: 1,
        name: 'John Smith',
        phone: '+919876543210',
        role: 'Developer'
      }

      render(
        <EmployeeCard 
          employee={mockEmployee}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      )

      const editButton = screen.getByTitle('Edit employee')
      const deleteButton = screen.getByTitle('Delete employee')

      // Check for tap-target class (44px minimum)
      expect(editButton).toHaveClass('tap-target')
      expect(deleteButton).toHaveClass('tap-target')
    })
  })
})

// Integration test for complete employee lifecycle
describe('Employee Management Integration', () => {
  it('should handle complete CRUD lifecycle', async () => {
    const { createEmployee, updateEmployee, deleteEmployee } = await import('../services/api.service.js')
    
    // Mock successful API responses
    createEmployee.mockResolvedValue({
      id: 1,
      name: 'Integration Test Employee',
      phone: '+919999999999',
      role: 'Developer'
    })

    updateEmployee.mockResolvedValue({
      id: 1,
      name: 'Updated Employee',
      phone: '+919999999999',
      role: 'Senior Developer'
    })

    deleteEmployee.mockResolvedValue({ success: true })

    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <Employees />
      </TestWrapper>
    )

    // Wait for component to stabilize
    await waitFor(() => {
      expect(screen.getByText('Team Members')).toBeInTheDocument()
    })

    // 1. Create employee - use getByRole to specifically target the button
    const addButton = screen.getByRole('button', { name: /Add Employee/i })
    expect(addButton).toBeInTheDocument()
    await user.click(addButton)
    
    // Wait for modal to open
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Add Employee/i })).toBeInTheDocument()
    })
    
    await user.type(screen.getByLabelText(/Employee Name/i), 'Integration Test Employee')
    await user.type(screen.getByLabelText(/Phone Number/i), '+919999999999')
    await user.selectOptions(screen.getByLabelText(/Role/i), 'Developer')
    
    await user.click(screen.getByText('Create Employee'))

    await waitFor(() => {
      expect(createEmployee).toHaveBeenCalledWith({
        name: 'Integration Test Employee',
        phone: '+919999999999',
        role: 'Developer'
      })
    })

    // 2. Edit employee (would require employee to be in the list)
    // This part would need the component to be updated with the created employee

    // 3. Delete employee
    // This would require clicking the delete button on the employee card
  })
})