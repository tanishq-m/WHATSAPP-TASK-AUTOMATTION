import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import TaskSubmission from '../pages/TaskSubmission'
import SubmissionSuccess from '../pages/SubmissionSuccess'

// Mock fetch
global.fetch = vi.fn()

describe('Stage 1.3: Task Submission Form', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('TaskSubmission Page - Loading State', () => {
    it('should show loading spinner while fetching submission details', () => {
      fetch.mockImplementation(() => new Promise(() => {})) // Never resolves
      
      render(
        <MemoryRouter initialEntries={['/submit/test-token-123']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      expect(screen.getByText(/loading submission/i)).toBeInTheDocument()
    })
  })

  describe('TaskSubmission Page - Error States', () => {
    it('should display error when token is invalid', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => ({
          success: false,
          error: 'Invalid or expired token'
        })
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/invalid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/access denied/i)).toBeInTheDocument()
        expect(screen.getByText(/invalid or expired token/i)).toBeInTheDocument()
      })
    })

    it('should display error when token is already used', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => ({
          success: false,
          error: 'Token already used'
        })
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/used-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/access denied/i)).toBeInTheDocument()
        expect(screen.getByText(/already been used/i)).toBeInTheDocument()
      })
    })

    it('should handle network errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))
      
      render(
        <MemoryRouter initialEntries={['/submit/test-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
        expect(screen.getByText(/check your connection/i)).toBeInTheDocument()
      })
    })
  })

  describe('TaskSubmission Page - Success State', () => {
    const mockSubmission = {
      success: true,
      data: {
        task_id: 'task_001',
        task_title: 'Complete Project Report',
        task_description: 'Prepare and submit the quarterly report',
        task_priority: 'high',
        task_due_date: '2026-02-15',
        employee_id: 1,
        employee_name: 'John Doe',
        status: 'pending'
      }
    }

    it('should display task details correctly', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Complete Project Report')).toBeInTheDocument()
        expect(screen.getByText(/prepare and submit the quarterly report/i)).toBeInTheDocument()
        expect(screen.getByText('John Doe')).toBeInTheDocument()
        expect(screen.getByText(/high/i)).toBeInTheDocument()
      })
    })

    it('should display due date formatted correctly', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/due date/i)).toBeInTheDocument()
        expect(screen.getByText(/2\/15\/2026/)).toBeInTheDocument()
      })
    })

    it('should show priority badge with correct color', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        const priorityBadge = screen.getByText(/high/i)
        expect(priorityBadge).toHaveClass('text-red-600')
      })
    })
  })

  describe('TaskSubmission Form - Message Input', () => {
    const mockSubmission = {
      success: true,
      data: {
        task_id: 'task_001',
        task_title: 'Test Task',
        task_priority: 'medium',
        employee_name: 'John Doe',
        status: 'pending'
      }
    }

    it('should allow typing in message textarea', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/describe your progress/i)).toBeInTheDocument()
      })
      
      const textarea = screen.getByPlaceholderText(/describe your progress/i)
      fireEvent.change(textarea, { target: { value: 'Task completed successfully!' } })
      
      expect(textarea.value).toBe('Task completed successfully!')
    })

    it('should disable submit button when form is empty', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /submit task update/i })
        expect(submitButton).toBeDisabled()
      })
    })

    it('should enable submit button when message is entered', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/describe your progress/i)).toBeInTheDocument()
      })
      
      const textarea = screen.getByPlaceholderText(/describe your progress/i)
      fireEvent.change(textarea, { target: { value: 'Done!' } })
      
      const submitButton = screen.getByRole('button', { name: /submit task update/i })
      expect(submitButton).not.toBeDisabled()
    })
  })

  describe('TaskSubmission Form - File Upload', () => {
    const mockSubmission = {
      success: true,
      data: {
        task_id: 'task_001',
        task_title: 'Test Task',
        task_priority: 'medium',
        employee_name: 'John Doe',
        status: 'pending'
      }
    }

    it('should display file upload area', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/choose files/i)).toBeInTheDocument()
        expect(screen.getByText(/drag and drop/i)).toBeInTheDocument()
      })
    })

    it('should display selected files', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByLabelText(/choose files/i)).toBeInTheDocument()
      })
      
      const fileInput = screen.getByLabelText(/choose files/i)
      const file = new File(['test content'], 'test.jpg', { type: 'image/jpeg' })
      
      fireEvent.change(fileInput, { target: { files: [file] } })
      
      await waitFor(() => {
        expect(screen.getByText('test.jpg')).toBeInTheDocument()
      })
    })

    it('should allow removing selected files', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByLabelText(/choose files/i)).toBeInTheDocument()
      })
      
      const fileInput = screen.getByLabelText(/choose files/i)
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      
      fireEvent.change(fileInput, { target: { files: [file] } })
      
      await waitFor(() => {
        expect(screen.getByText('test.jpg')).toBeInTheDocument()
      })
      
      const removeButtons = screen.getAllByRole('button')
      const removeButton = removeButtons.find(btn => btn.querySelector('svg'))
      fireEvent.click(removeButton)
      
      await waitFor(() => {
        expect(screen.queryByText('test.jpg')).not.toBeInTheDocument()
      })
    })

    it('should show file size correctly', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByLabelText(/choose files/i)).toBeInTheDocument()
      })
      
      const fileInput = screen.getByLabelText(/choose files/i)
      const file = new File(['a'.repeat(2048)], 'large.pdf', { type: 'application/pdf' })
      Object.defineProperty(file, 'size', { value: 2048 })
      
      fireEvent.change(fileInput, { target: { files: [file] } })
      
      await waitFor(() => {
        expect(screen.getByText('large.pdf')).toBeInTheDocument()
        expect(screen.getByText(/2 KB/)).toBeInTheDocument()
      })
    })

    it('should enable submit button when files are selected', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByLabelText(/choose files/i)).toBeInTheDocument()
      })
      
      const fileInput = screen.getByLabelText(/choose files/i)
      const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
      
      fireEvent.change(fileInput, { target: { files: [file] } })
      
      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /submit task update/i })
        expect(submitButton).not.toBeDisabled()
      })
    })
  })

  describe('TaskSubmission Form - Validation', () => {
    const mockSubmission = {
      success: true,
      data: {
        task_id: 'task_001',
        task_title: 'Test Task',
        task_priority: 'medium',
        employee_name: 'John Doe',
        status: 'pending'
      }
    }

    it('should show error when submitting empty form', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /submit task update/i })).toBeInTheDocument()
      })
      
      // Button should be disabled for empty form
      const submitButton = screen.getByRole('button', { name: /submit task update/i })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('TaskSubmission Form - Submission', () => {
    const mockSubmission = {
      success: true,
      data: {
        task_id: 'task_001',
        task_title: 'Test Task',
        task_priority: 'medium',
        employee_name: 'John Doe',
        status: 'pending'
      }
    }

    it('should submit successfully with message only', async () => {
      let postCalled = false
      fetch
        .mockResolvedValueOnce({ json: async () => mockSubmission })
        .mockImplementationOnce(async (url, options) => {
          if (options?.method === 'POST') {
            postCalled = true
          }
          return {
            json: async () => ({
              success: true,
              data: {
                task_id: 'task_001',
                message_posted: true,
                files_uploaded: 0,
                uploaded_files: []
              }
            })
          }
        })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/describe your progress/i)).toBeInTheDocument()
      })
      
      const textarea = screen.getByPlaceholderText(/describe your progress/i)
      fireEvent.change(textarea, { target: { value: 'Completed!' } })
      
      const submitButton = screen.getByRole('button', { name: /submit task update/i })
      expect(submitButton).not.toBeDisabled()
      
      fireEvent.click(submitButton)
      
      // Wait for post to be called
      await waitFor(() => {
        expect(postCalled).toBe(true)
      }, { timeout: 2000 })
    })

    it('should show loading state during submission', async () => {
      fetch
        .mockResolvedValueOnce({ json: async () => mockSubmission })
        .mockImplementation(() => new Promise(() => {})) // Never resolves
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/describe your progress/i)).toBeInTheDocument()
      })
      
      const textarea = screen.getByPlaceholderText(/describe your progress/i)
      fireEvent.change(textarea, { target: { value: 'Done' } })
      
      const submitButton = screen.getByRole('button', { name: /submit task update/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/submitting/i)).toBeInTheDocument()
      })
    })

    it('should handle submission errors', async () => {
      fetch
        .mockResolvedValueOnce({ json: async () => mockSubmission })
        .mockResolvedValueOnce({
          json: async () => ({
            success: false,
            error: 'Submission failed'
          })
        })
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/describe your progress/i)).toBeInTheDocument()
      })
      
      const textarea = screen.getByPlaceholderText(/describe your progress/i)
      fireEvent.change(textarea, { target: { value: 'Done' } })
      
      const submitButton = screen.getByRole('button', { name: /submit task update/i })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/submission failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('SubmissionSuccess Page', () => {
    it('should render success message', () => {
      render(
        <BrowserRouter>
          <SubmissionSuccess />
        </BrowserRouter>
      )
      
      expect(screen.getByText(/submission successful/i)).toBeInTheDocument()
      expect(screen.getByText(/submitted successfully/i)).toBeInTheDocument()
    })

    it('should show expiration notice', () => {
      render(
        <BrowserRouter>
          <SubmissionSuccess />
        </BrowserRouter>
      )
      
      expect(screen.getByText(/expired and cannot be used again/i)).toBeInTheDocument()
    })

    it('should display success icon', () => {
      render(
        <BrowserRouter>
          <SubmissionSuccess />
        </BrowserRouter>
      )
      
      const successIcon = screen.getByText(/submission successful/i).parentElement.querySelector('svg')
      expect(successIcon).toBeInTheDocument()
    })
  })

  describe('Mobile Responsiveness', () => {
    const mockSubmission = {
      success: true,
      data: {
        task_id: 'task_001',
        task_title: 'Mobile Test Task',
        task_priority: 'low',
        employee_name: 'Jane Doe',
        status: 'pending'
      }
    }

    it('should render correctly on mobile viewport', async () => {
      fetch.mockResolvedValueOnce({
        json: async () => mockSubmission
      })
      
      // Set mobile viewport
      global.innerWidth = 375
      global.innerHeight = 667
      
      render(
        <MemoryRouter initialEntries={['/submit/valid-token']}>
          <TaskSubmission />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Mobile Test Task')).toBeInTheDocument()
      })
      
      // Should have mobile-friendly padding and spacing
      const mainContainer = screen.getByText('Mobile Test Task').closest('div')
      expect(mainContainer).toBeInTheDocument()
    })
  })
})
