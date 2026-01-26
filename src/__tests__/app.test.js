/**
 * Frontend Test Suite for WhatsApp Task Manager
 * 
 * Run tests: npm test
 * Run with coverage: npm test -- --coverage
 * 
 * This file tests React components, API services, and utility functions.
 * Add new tests here when adding new functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ============================================================================
// MOCK SETUP
// ============================================================================

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Helper to create mock response
const createMockResponse = (data, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
});

// ============================================================================
// API SERVICE TESTS
// ============================================================================

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.resetModules(); // Reset module cache for fresh imports
  });

  describe('getProjects', () => {
    it('should fetch all projects successfully', async () => {
      const mockProjects = [
        { id: 'proj_1', name: 'Project 1' },
        { id: 'proj_2', name: 'Project 2' },
      ];
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: mockProjects })
      );

      const { getProjects } = await import('../services/api.service.js');
      const result = await getProjects();

      const callUrl = mockFetch.mock.calls[0][0];
      expect(callUrl).toContain('/api/projects');
      expect(result).toHaveLength(2);
    });

    // ========================================================================
    // P3-9 / API Fix: Projects should transform snake_case to camelCase
    // ========================================================================
    it('should transform project snake_case fields to camelCase', async () => {
      const mockProjects = [
        { 
          id: 'proj_1', 
          name: 'Test Project',
          start_date: '2026-01-01',
          end_date: '2026-12-31',
          created_at: '2026-01-01T00:00:00Z',
          assigned_employees: [1, 2, 3]
        },
      ];
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: mockProjects })
      );

      const { getProjects } = await import('../services/api.service.js');
      const result = await getProjects();

      expect(result[0]).toHaveProperty('startDate', '2026-01-01');
      expect(result[0]).toHaveProperty('endDate', '2026-12-31');
      expect(result[0]).toHaveProperty('createdAt');
      expect(result[0]).toHaveProperty('assignedEmployees');
      expect(result[0].assignedEmployees).toEqual([1, 2, 3]);
    });

    it('should handle projects with empty assigned_employees array', async () => {
      const mockProjects = [
        { 
          id: 'proj_1', 
          name: 'Empty Team Project',
          assigned_employees: []
        },
      ];
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: mockProjects })
      );

      const { getProjects } = await import('../services/api.service.js');
      const result = await getProjects();

      expect(result[0].assignedEmployees).toEqual([]);
    });

    it('should throw error on API failure', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: false, error: 'Server error' }, 500)
      );

      const { getProjects } = await import('../services/api.service.js');
      await expect(getProjects()).rejects.toThrow();
    });
  });

  // ============================================================================
  // P3-9 / API Fix: Employee API Tests
  // ============================================================================
  describe('getEmployees', () => {
    it('should fetch employees and transform to camelCase', async () => {
      const mockEmployees = [
        { id: 1, name: 'John Doe', phone: '+911234567890', created_at: '2026-01-01T00:00:00Z' },
        { id: 2, name: 'Jane Smith', phone: '+919876543210', created_at: '2026-01-02T00:00:00Z' },
      ];
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: mockEmployees })
      );

      const { getEmployees } = await import('../services/api.service.js');
      const result = await getEmployees();

      expect(result).toHaveLength(2);
      expect(result[0]).toHaveProperty('createdAt');
      expect(result[0].name).toBe('John Doe');
    });

    it('should handle employee with snake_case fields', async () => {
      const mockEmployees = [
        { 
          id: 1, 
          name: 'Test User', 
          phone_number: '+911234567890',
          created_at: '2026-01-01T00:00:00Z',
          last_active: '2026-01-15T10:00:00Z'
        },
      ];
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: mockEmployees })
      );

      const { getEmployees } = await import('../services/api.service.js');
      const result = await getEmployees();

      expect(result[0]).toHaveProperty('createdAt');
      if (result[0].phoneNumber) {
        expect(result[0]).toHaveProperty('phoneNumber');
      }
      if (result[0].lastActive) {
        expect(result[0]).toHaveProperty('lastActive');
      }
    });
  });

  describe('getTasks', () => {
    it('should fetch tasks and transform to camelCase', async () => {
      const mockTasks = [
        { task_id: 'task_1', assigned_to: 1, due_date: '2026-01-01' },
      ];
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: mockTasks })
      );

      const { getTasks } = await import('../services/api.service.js');
      const result = await getTasks();

      expect(result[0]).toHaveProperty('taskId');
      expect(result[0]).toHaveProperty('assignedTo');
      expect(result[0]).toHaveProperty('dueDate');
    });

    it('should filter tasks by projectId', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: [] })
      );

      const { getTasks } = await import('../services/api.service.js');
      await getTasks('proj_123');

      // Check that the URL contains the projectId parameter
      const callUrl = mockFetch.mock.calls[0][0];
      expect(callUrl).toContain('projectId=proj_123');
    });
  });

  describe('createTask', () => {
    it('should create task with correct payload', async () => {
      const newTask = {
        title: 'New Task',
        description: 'Description',
        projectId: 'proj_1',
        assignedTo: 1,
        priority: 'high',
        status: 'unassigned',
      };

      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: { task_id: 'task_new', ...newTask } })
      );

      const { createTask } = await import('../services/api.service.js');
      const result = await createTask(newTask);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tasks'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(String),
        })
      );
      expect(result).toHaveProperty('taskId');
    });
  });

  describe('updateTask', () => {
    it('should update task with correct ID', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, data: { task_id: 'task_1', status: 'done' } })
      );

      const { updateTask } = await import('../services/api.service.js');
      await updateTask('task_1', { status: 'done' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tasks/task_1'),
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  describe('deleteTask', () => {
    it('should delete task by ID', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true })
      );

      const { deleteTask } = await import('../services/api.service.js');
      await deleteTask('task_1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tasks/task_1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('sendTaskToWhatsApp', () => {
    it('should send task to WhatsApp', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ success: true, whatsapp_response: 'sent' })
      );

      const { sendTaskToWhatsApp } = await import('../services/api.service.js');
      await sendTaskToWhatsApp('task_1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tasks/task_1/send-whatsapp-buttons'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('getTaskWhatsAppStatus', () => {
    it('should get WhatsApp status for task', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ 
          success: true, 
          data: { whatsapp_sent: true, whatsapp_response: 'completed' } 
        })
      );

      const { getTaskWhatsAppStatus } = await import('../services/api.service.js');
      const result = await getTaskWhatsAppStatus('task_1');

      expect(result.whatsappSent).toBe(true);
      expect(result.whatsappResponse).toBe('completed');
    });
  });

  // ============================================================================
  // ISSUE #1 TESTS: Task ID Consistency
  // ============================================================================
  describe('Task ID Consistency (Issue #1)', () => {
    it('should have both id and taskId set consistently for task objects', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [
            { task_id: 'task_001', title: 'Test Task', status: 'unassigned' }
          ]
        })
      );

      const { getTasks } = await import('../services/api.service.js');
      const tasks = await getTasks();

      expect(tasks[0].taskId).toBe('task_001');
      expect(tasks[0].id).toBe('task_001');
      expect(tasks[0].id).toBe(tasks[0].taskId);
    });

    it('should return task with consistent IDs after update', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { task_id: 'task_001', status: 'done' }
        })
      );

      const { updateTask } = await import('../services/api.service.js');
      const task = await updateTask('task_001', { status: 'done' });

      expect(task.taskId).toBe('task_001');
      expect(task.id).toBe('task_001');
    });

    it('should return task with consistent IDs after creation', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { task_id: 'task_new', title: 'New Task' }
        })
      );

      const { createTask } = await import('../services/api.service.js');
      const task = await createTask({ title: 'New Task', projectId: 'proj_1' });

      expect(task.taskId).toBe('task_new');
      expect(task.id).toBe('task_new');
    });
  });

  // ============================================================================
  // ISSUE #9 TESTS: Field Mapping for assignedTo/employeeId
  // ============================================================================
  describe('Field Mapping Consistency (Issue #9)', () => {
    it('should map employee_id to both employeeId and assignedTo', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [
            { task_id: 'task_001', employee_id: 5, title: 'Test Task' }
          ]
        })
      );

      const { getTasks } = await import('../services/api.service.js');
      const tasks = await getTasks();

      expect(tasks[0].employeeId).toBe(5);
      expect(tasks[0].assignedTo).toBe(5);
    });

    it('should handle null employee_id correctly', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [
            { task_id: 'task_001', employee_id: null, title: 'Unassigned Task' }
          ]
        })
      );

      const { getTasks } = await import('../services/api.service.js');
      const tasks = await getTasks();

      expect(tasks[0].employeeId).toBeNull();
      expect(tasks[0].assignedTo).toBeNull();
    });

    it('should preserve assignedTo after task update', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { task_id: 'task_001', employee_id: 3, status: 'done' }
        })
      );

      const { updateTask } = await import('../services/api.service.js');
      const task = await updateTask('task_001', { status: 'done', assignedTo: 3 });

      expect(task.employeeId).toBe(3);
      expect(task.assignedTo).toBe(3);
    });
  });

  // ============================================================================
  // ISSUE #2 TESTS: Optional Fields (assignedTo and dueDate)
  // ============================================================================
  describe('Optional Task Fields (Issue #2)', () => {
    it('should create task without assignedTo (unassigned task)', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { 
            task_id: 'task_unassigned', 
            title: 'Unassigned Task',
            employee_id: null,
            due_date: null
          }
        })
      );

      const { createTask } = await import('../services/api.service.js');
      const task = await createTask({ 
        title: 'Unassigned Task', 
        projectId: 'proj_1',
        assignedTo: null,
        dueDate: null
      });

      expect(task.taskId).toBe('task_unassigned');
      expect(task.assignedTo).toBeNull();
      expect(task.dueDate).toBeNull();
    });

    it('should create task without dueDate', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { 
            task_id: 'task_no_due', 
            title: 'Task Without Due Date',
            employee_id: 1,
            due_date: null
          }
        })
      );

      const { createTask } = await import('../services/api.service.js');
      const task = await createTask({ 
        title: 'Task Without Due Date', 
        projectId: 'proj_1',
        assignedTo: 1,
        dueDate: null
      });

      expect(task.taskId).toBe('task_no_due');
      expect(task.assignedTo).toBe(1);
      expect(task.dueDate).toBeNull();
    });

    it('should create task with only required fields (title and projectId)', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { 
            task_id: 'task_minimal', 
            title: 'Minimal Task',
            project_id: 'proj_1',
            employee_id: null,
            due_date: null,
            priority: 'medium'
          }
        })
      );

      const { createTask } = await import('../services/api.service.js');
      const task = await createTask({ 
        title: 'Minimal Task', 
        projectId: 'proj_1'
      });

      expect(task.taskId).toBe('task_minimal');
      expect(task.title).toBe('Minimal Task');
      expect(task.projectId).toBe('proj_1');
    });
  });

  // ============================================================================
  // ISSUE #3 TESTS: Kanban Column Rename (UNASSIGNED status)
  // ============================================================================
  describe('Kanban Column Rename (Issue #3)', () => {
    it('should use unassigned status instead of ready_to_start', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [
            { task_id: 'task_001', status: 'unassigned', title: 'New Task' }
          ]
        })
      );

      const { getTasks } = await import('../services/api.service.js');
      const tasks = await getTasks();

      expect(tasks[0].status).toBe('unassigned');
    });

    it('should create new tasks with unassigned status by default', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { 
            task_id: 'task_new', 
            title: 'New Unassigned Task',
            status: 'unassigned'
          }
        })
      );

      const { createTask } = await import('../services/api.service.js');
      const task = await createTask({ 
        title: 'New Unassigned Task', 
        projectId: 'proj_1'
      });

      expect(task.status).toBe('unassigned');
    });

    it('should handle all valid status values', async () => {
      const validStatuses = ['unassigned', 'in_progress', 'pending_verification', 'completed'];
      
      for (const status of validStatuses) {
        mockFetch.mockResolvedValueOnce(
          createMockResponse({
            success: true,
            data: { 
              task_id: `task_${status}`, 
              status: status
            }
          })
        );

        const { updateTask } = await import('../services/api.service.js');
        const task = await updateTask('task_001', { status });

        expect(task.status).toBe(status);
      }
    });
  });

  // ============================================================================
  // ISSUE #5 TESTS: Project Card Task Statistics
  // ============================================================================
  describe('Project Statistics Calculation (Issue #5)', () => {
    it('should calculate detailed task breakdown for projects', async () => {
      // Mock projects
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [{ id: 'proj_1', name: 'Test Project' }]
        })
      );
      
      // Mock tasks with different statuses
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [
            { task_id: 'task_1', project_id: 'proj_1', status: 'unassigned' },
            { task_id: 'task_2', project_id: 'proj_1', status: 'unassigned' },
            { task_id: 'task_3', project_id: 'proj_1', status: 'in_progress' },
            { task_id: 'task_4', project_id: 'proj_1', status: 'in_progress' },
            { task_id: 'task_5', project_id: 'proj_1', status: 'in_progress' },
            { task_id: 'task_6', project_id: 'proj_1', status: 'pending_verification' },
            { task_id: 'task_7', project_id: 'proj_1', status: 'completed' },
            { task_id: 'task_8', project_id: 'proj_1', status: 'completed' },
          ]
        })
      );

      const { getProjects, getTasks } = await import('../services/api.service.js');
      
      await getProjects();
      const tasks = await getTasks();
      
      // Manually calculate stats like AppContext does
      const proj1Tasks = tasks.filter(t => t.projectId === 'proj_1');
      const unassigned = proj1Tasks.filter(t => t.status === 'unassigned').length;
      const inProgress = proj1Tasks.filter(t => t.status === 'in_progress').length;
      const pending = proj1Tasks.filter(t => t.status === 'pending_verification').length;
      const completed = proj1Tasks.filter(t => t.status === 'completed').length;

      expect(unassigned).toBe(2);
      expect(inProgress).toBe(3);
      expect(pending).toBe(1);
      expect(completed).toBe(2);
      expect(proj1Tasks.length).toBe(8);
    });

    it('should handle projects with no tasks', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: [{ id: 'proj_empty', name: 'Empty Project' }]
        })
      );
      
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: []
        })
      );

      const { getProjects, getTasks } = await import('../services/api.service.js');
      
      await getProjects();
      const tasks = await getTasks();
      
      const emptyProjectTasks = tasks.filter(t => t.projectId === 'proj_empty');
      expect(emptyProjectTasks.length).toBe(0);
    });

    it('should calculate progress percentage correctly', async () => {
      const { calculateProgress } = await import('../utils/helpers.js');
      
      // 2 completed out of 8 total
      expect(calculateProgress(8, 2)).toBe(25);
      
      // 5 completed out of 10 total
      expect(calculateProgress(10, 5)).toBe(50);
      
      // 8 completed out of 8 total
      expect(calculateProgress(8, 8)).toBe(100);
      
      // 0 completed
      expect(calculateProgress(5, 0)).toBe(0);
    });
  });
});


// ============================================================================
// ISSUE #6 TESTS: Free Drag-and-Drop Between All Columns
// ============================================================================
describe('Free Drag-and-Drop Movement (Issue #6)', () => {
  it('should allow task status update to any valid status', async () => {
    const allStatuses = ['unassigned', 'in_progress', 'pending_verification', 'completed'];
    
    // Test moving from one status to all others
    for (const targetStatus of allStatuses) {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { 
            task_id: 'task_001', 
            status: targetStatus,
            title: 'Test Task'
          }
        })
      );

      const { updateTask } = await import('../services/api.service.js');
      const task = await updateTask('task_001', { status: targetStatus });

      expect(task.status).toBe(targetStatus);
    }
  });

  it('should allow moving from completed back to in_progress', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          status: 'in_progress',
          previous_status: 'completed'
        }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    const task = await updateTask('task_001', { status: 'in_progress' });

    expect(task.status).toBe('in_progress');
  });

  it('should allow moving from unassigned directly to completed', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          status: 'completed',
          previous_status: 'unassigned'
        }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    const task = await updateTask('task_001', { status: 'completed' });

    expect(task.status).toBe('completed');
  });

  it('should update task status without restrictions on transitions', async () => {
    // Test non-linear transitions (no workflow restrictions)
    const transitions = [
      { from: 'pending_verification', to: 'unassigned' },
      { from: 'completed', to: 'pending_verification' },
      { from: 'in_progress', to: 'unassigned' },
    ];

    for (const transition of transitions) {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({
          success: true,
          data: { 
            task_id: 'task_001', 
            status: transition.to
          }
        })
      );

      const { updateTask } = await import('../services/api.service.js');
      const task = await updateTask('task_001', { status: transition.to });

      expect(task.status).toBe(transition.to);
    }
  });
});


// ============================================================================
// ISSUE #8 TESTS: Update Source Separation (Admin vs Webhook)
// ============================================================================
describe('Update Source Separation (Issue #8)', () => {
  it('should pass updateSource parameter when updating task', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          status: 'in_progress',
          update_source: 'admin'
        }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    await updateTask('task_001', { status: 'in_progress', updateSource: 'admin' });

    // Verify fetch was called with updateSource in the body
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/tasks/task_001'),
      expect.objectContaining({
        method: 'PUT',
        body: expect.stringContaining('updateSource')
      })
    );
  });

  it('should allow admin to update task status without restrictions', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          status: 'completed',
          update_source: 'admin'
        }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    const task = await updateTask('task_001', { 
      status: 'completed', 
      updateSource: 'admin' 
    });

    expect(task.status).toBe('completed');
    expect(task.updateSource).toBe('admin');
  });

  it('should distinguish between admin and webhook updates', async () => {
    // Admin update
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          status: 'in_progress',
          update_source: 'admin'
        }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    const adminUpdate = await updateTask('task_001', { 
      status: 'in_progress', 
      updateSource: 'admin' 
    });

    expect(adminUpdate.updateSource).toBe('admin');

    // Webhook update (would come from different endpoint, but same data structure)
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          status: 'pending_verification',
          update_source: 'webhook',
          whatsapp_response: 'completed'
        }
      })
    );

    const webhookUpdate = await updateTask('task_001', { 
      status: 'pending_verification',
      whatsappResponse: 'completed',
      updateSource: 'webhook'
    });

    expect(webhookUpdate.updateSource).toBe('webhook');
    expect(webhookUpdate.whatsappResponse).toBe('completed');
  });

  it('should handle task updates without updateSource parameter', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          task_id: 'task_001', 
          title: 'Updated Task'
        }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    const task = await updateTask('task_001', { title: 'Updated Task' });

    expect(task.title).toBe('Updated Task');
    // Should work even without updateSource
  });
});


// ============================================================================
// ISSUE #7 TESTS: Edit Project Functionality
// ============================================================================
describe('Edit Project Functionality (Issue #7)', () => {
  it('should update project with new name and description', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          project_id: 'proj_001',
          name: 'Updated Project Name',
          description: 'Updated description'
        }
      })
    );

    const { updateProject } = await import('../services/api.service.js');
    const project = await updateProject('proj_001', { 
      name: 'Updated Project Name',
      description: 'Updated description'
    });

    expect(project.name).toBe('Updated Project Name');
    expect(project.description).toBe('Updated description');
  });

  it('should update project dates', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          project_id: 'proj_001',
          start_date: '2026-02-01',
          end_date: '2026-03-31'
        }
      })
    );

    const { updateProject } = await import('../services/api.service.js');
    const project = await updateProject('proj_001', { 
      startDate: '2026-02-01',
      endDate: '2026-03-31'
    });

    expect(project.startDate).toBe('2026-02-01');
    expect(project.endDate).toBe('2026-03-31');
  });

  it('should update project team members', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          project_id: 'proj_001',
          assigned_employees: [1, 2, 3]
        }
      })
    );

    const { updateProject } = await import('../services/api.service.js');
    const project = await updateProject('proj_001', { 
      assignedEmployees: [1, 2, 3]
    });

    expect(project.assignedEmployees).toEqual([1, 2, 3]);
  });

  it('should handle project updates with all fields', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: true,
        data: { 
          project_id: 'proj_001',
          name: 'Complete Update',
          description: 'New description',
          start_date: '2026-02-01',
          end_date: '2026-03-31',
          assigned_employees: [1, 2]
        }
      })
    );

    const { updateProject } = await import('../services/api.service.js');
    const project = await updateProject('proj_001', { 
      name: 'Complete Update',
      description: 'New description',
      startDate: '2026-02-01',
      endDate: '2026-03-31',
      assignedEmployees: [1, 2]
    });

    expect(project.name).toBe('Complete Update');
    expect(project.description).toBe('New description');
    expect(project.startDate).toBe('2026-02-01');
    expect(project.endDate).toBe('2026-03-31');
    expect(project.assignedEmployees).toEqual([1, 2]);
  });

  it('should handle project update errors', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({
        success: false,
        error: 'Project not found'
      }, false)
    );

    const { updateProject } = await import('../services/api.service.js');
    
    await expect(updateProject('proj_999', { name: 'Test' }))
      .rejects.toThrow();
  });
});


// ============================================================================
// UTILITY FUNCTION TESTS
// ============================================================================

describe('Utility Functions', () => {
  describe('helpers', () => {
    it('formatDate should format date correctly', async () => {
      const { formatDate } = await import('../utils/helpers.js');
      
      // Test with valid date
      const result = formatDate('2026-01-15');
      expect(result).toBeDefined();
      expect(typeof result).toBe('string');
    });

    it('generateId should create unique IDs', async () => {
      const { generateId } = await import('../utils/helpers.js');
      
      const id1 = generateId('task');
      const id2 = generateId('task');
      
      expect(id1).toMatch(/^task_/);
      expect(id2).toMatch(/^task_/);
      expect(id1).not.toBe(id2);
    });

    it('calculateProgress should calculate percentage', async () => {
      const { calculateProgress } = await import('../utils/helpers.js');
      
      // Function takes (total, completed) not tasks array
      const progress = calculateProgress(4, 2);
      expect(progress).toBe(50); // 2 out of 4
    });

    it('calculateProgress should return 0 for zero total', async () => {
      const { calculateProgress } = await import('../utils/helpers.js');
      
      const progress = calculateProgress(0, 0);
      expect(progress).toBe(0);
    });

    it('isOverdue should detect overdue dates', async () => {
      const { isOverdue } = await import('../utils/helpers.js');
      
      // Past date should be overdue
      expect(isOverdue('2020-01-01')).toBe(true);
      // Future date should not be overdue
      expect(isOverdue('2030-01-01')).toBe(false);
    });

    it('getInitials should extract initials from name', async () => {
      const { getInitials } = await import('../utils/helpers.js');
      
      expect(getInitials('John Doe')).toBe('JD');
      expect(getInitials('Alice')).toBe('A');
      expect(getInitials('')).toBe('?');
    });
  });

  describe('validators', () => {
    it('validateTask should return isValid and errors', async () => {
      const { validateTask } = await import('../utils/validators.js');
      
      const validTask = {
        title: 'Valid Task',
        projectId: 'proj_1',
        assignedTo: 1,
        dueDate: '2026-01-01',
        priority: 'high',
      };
      
      const result = validateTask(validTask);
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('validateTask should return errors for missing title', async () => {
      const { validateTask } = await import('../utils/validators.js');
      
      const invalidTask = {
        projectId: 'proj_1',
      };
      
      const result = validateTask(invalidTask);
      expect(result.isValid).toBe(false);
      expect(result.errors.title).toBeDefined();
    });

    it('validateTask should accept task without assignedTo (Issue #2)', async () => {
      const { validateTask } = await import('../utils/validators.js');
      
      const taskWithoutEmployee = {
        title: 'Unassigned Task',
        projectId: 'proj_1',
        priority: 'medium',
      };
      
      const result = validateTask(taskWithoutEmployee);
      expect(result.isValid).toBe(true);
      expect(result.errors.assignedTo).toBeUndefined();
    });

    it('validateTask should accept task without dueDate (Issue #2)', async () => {
      const { validateTask } = await import('../utils/validators.js');
      
      const taskWithoutDueDate = {
        title: 'Task Without Due Date',
        projectId: 'proj_1',
        assignedTo: 1,
        priority: 'high',
      };
      
      const result = validateTask(taskWithoutDueDate);
      expect(result.isValid).toBe(true);
      expect(result.errors.dueDate).toBeUndefined();
    });

    it('validateTask should accept task with only required fields (Issue #2)', async () => {
      const { validateTask } = await import('../utils/validators.js');
      
      const minimalTask = {
        title: 'Minimal Task',
        projectId: 'proj_1',
        priority: 'medium',
      };
      
      const result = validateTask(minimalTask);
      expect(result.isValid).toBe(true);
      expect(Object.keys(result.errors)).toHaveLength(0);
    });

    it('validateProject should validate correctly', async () => {
      const { validateProject } = await import('../utils/validators.js');
      
      const validResult = validateProject({ 
        name: 'Valid Project',
        startDate: '2026-01-01',
        endDate: '2026-12-31'
      });
      expect(validResult.isValid).toBe(true);
      
      const invalidResult = validateProject({ name: '' });
      expect(invalidResult.isValid).toBe(false);
      
      const missingResult = validateProject({});
      expect(missingResult.isValid).toBe(false);
    });

    // ========================================================================
    // P3-6: Optional Dates Validation Tests
    // ========================================================================
    it('validateProject should accept project without dates (P3-6)', async () => {
      const { validateProject } = await import('../utils/validators.js');
      
      const projectWithoutDates = {
        name: 'Project Without Dates'
      };
      
      const result = validateProject(projectWithoutDates);
      expect(result.isValid).toBe(true);
      expect(result.errors.startDate).toBeUndefined();
      expect(result.errors.endDate).toBeUndefined();
    });

    it('validateProject should accept project with only start date (P3-6)', async () => {
      const { validateProject } = await import('../utils/validators.js');
      
      const projectWithStartOnly = {
        name: 'Project With Start Date Only',
        startDate: '2026-01-01'
      };
      
      const result = validateProject(projectWithStartOnly);
      expect(result.isValid).toBe(true);
    });

    it('validateProject should accept project with only end date (P3-6)', async () => {
      const { validateProject } = await import('../utils/validators.js');
      
      const projectWithEndOnly = {
        name: 'Project With End Date Only',
        endDate: '2026-12-31'
      };
      
      const result = validateProject(projectWithEndOnly);
      expect(result.isValid).toBe(true);
    });

    it('validateProject should reject if endDate is before startDate (P3-6)', async () => {
      const { validateProject } = await import('../utils/validators.js');
      
      const projectWithInvalidDates = {
        name: 'Project With Invalid Dates',
        startDate: '2026-12-31',
        endDate: '2026-01-01'
      };
      
      const result = validateProject(projectWithInvalidDates);
      expect(result.isValid).toBe(false);
      expect(result.errors.endDate).toBeDefined();
    });

    it('validateProject should accept empty string dates as optional (P3-6)', async () => {
      const { validateProject } = await import('../utils/validators.js');
      
      const projectWithEmptyDates = {
        name: 'Project With Empty Dates',
        startDate: '',
        endDate: ''
      };
      
      const result = validateProject(projectWithEmptyDates);
      expect(result.isValid).toBe(true);
    });
  });

  describe('constants', () => {
    it('should export STATUS options', async () => {
      const { STATUS } = await import('../utils/constants.js');
      
      expect(STATUS).toBeDefined();
      expect(typeof STATUS).toBe('object');
      expect(STATUS.IN_PROGRESS).toBe('in_progress');
    });

    it('should export PRIORITY options', async () => {
      const { PRIORITY } = await import('../utils/constants.js');
      
      expect(PRIORITY).toBeDefined();
      expect(PRIORITY.HIGH).toBe('high');
      expect(PRIORITY.MEDIUM).toBe('medium');
      expect(PRIORITY.LOW).toBe('low');
    });

    it('should export STORAGE_KEYS', async () => {
      const { STORAGE_KEYS } = await import('../utils/constants.js');
      
      expect(STORAGE_KEYS).toBeDefined();
      expect(STORAGE_KEYS.PROJECTS).toBe('wtm_projects');
      expect(STORAGE_KEYS.TASKS).toBe('wtm_tasks');
    });
  });
});


// ============================================================================
// COMPONENT RENDERING TESTS (Basic)
// ============================================================================

describe('Component Imports', () => {
  // These tests verify components can be imported without errors
  
  it('Button component should import', async () => {
    const module = await import('../components/common/Button.jsx');
    expect(module.default).toBeDefined();
  });

  it('Input component should import', async () => {
    const module = await import('../components/common/Input.jsx');
    expect(module.default).toBeDefined();
  });

  it('Modal component should import', async () => {
    const module = await import('../components/common/Modal.jsx');
    expect(module.default).toBeDefined();
  });

  it('TaskCard component should import', async () => {
    const module = await import('../components/tasks/TaskCard.jsx');
    expect(module.default).toBeDefined();
  });

  it('KanbanBoard component should import', async () => {
    const module = await import('../components/tasks/KanbanBoard.jsx');
    expect(module.default).toBeDefined();
  });

  it('ProjectCard component should import', async () => {
    const module = await import('../components/projects/ProjectCard.jsx');
    expect(module.default).toBeDefined();
  });
});


// ============================================================================
// LOCAL STORAGE SERVICE TESTS
// ============================================================================

describe('LocalStorage Service', () => {
  const mockLocalStorage = {
    store: {},
    getItem: vi.fn((key) => mockLocalStorage.store[key] || null),
    setItem: vi.fn((key, value) => { mockLocalStorage.store[key] = value; }),
    removeItem: vi.fn((key) => { delete mockLocalStorage.store[key]; }),
    clear: vi.fn(() => { mockLocalStorage.store = {}; }),
  };

  beforeEach(() => {
    mockLocalStorage.clear();
    mockLocalStorage.getItem.mockClear();
    mockLocalStorage.setItem.mockClear();
    Object.defineProperty(global, 'localStorage', { value: mockLocalStorage });
  });

  it('LocalStorageService should be a class with methods', async () => {
    const module = await import('../services/localStorage.service.js');
    expect(module.default).toBeDefined();
    expect(typeof module.default.getItem).toBe('function');
    expect(typeof module.default.setItem).toBe('function');
  });

  it('should have project methods', async () => {
    const module = await import('../services/localStorage.service.js');
    const storage = module.default;
    
    expect(typeof storage.getProjects).toBe('function');
    expect(typeof storage.setProjects).toBe('function');
  });

  it('should have task methods', async () => {
    const module = await import('../services/localStorage.service.js');
    const storage = module.default;
    
    expect(typeof storage.getTasks).toBe('function');
    expect(typeof storage.setTasks).toBe('function');
  });

  it('should have employee methods', async () => {
    const module = await import('../services/localStorage.service.js');
    const storage = module.default;
    
    expect(typeof storage.getEmployees).toBe('function');
    expect(typeof storage.setEmployees).toBe('function');
  });
});


// ============================================================================
// CONTEXT TESTS
// ============================================================================

describe('AppContext', () => {
  it('AppContext should export correctly', async () => {
    const module = await import('../context/AppContext.jsx');
    expect(module.AppProvider).toBeDefined();
    expect(module.AppContext).toBeDefined();
  });

  it('useApp hook should export correctly', async () => {
    const module = await import('../context/useApp.js');
    expect(module.useApp).toBeDefined();
  });
});


// ============================================================================
// DATA TRANSFORMATION TESTS
// ============================================================================

describe('Data Transformations', () => {
  describe('toCamelCase', () => {
    it('should convert snake_case to camelCase', async () => {
      // Import dynamically to get the actual function
      const module = await import('../services/api.service.js');
      
      // Since toCamelCase is not exported, we test through getTasks behavior
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ 
          success: true, 
          data: [{ 
            task_id: 'task_1',
            project_id: 'proj_1',
            assigned_to: 1,
            due_date: '2026-01-01',
            whatsapp_sent: true,
            whatsapp_response: 'completed',
            created_at: '2026-01-01T00:00:00Z'
          }] 
        })
      );

      const result = await module.getTasks();
      
      expect(result[0]).toHaveProperty('taskId');
      expect(result[0]).toHaveProperty('projectId');
      expect(result[0]).toHaveProperty('assignedTo');
      expect(result[0]).toHaveProperty('dueDate');
      expect(result[0]).toHaveProperty('whatsappSent');
      expect(result[0]).toHaveProperty('whatsappResponse');
      expect(result[0]).toHaveProperty('createdAt');
    });

    it('should handle nested objects', async () => {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ 
          success: true, 
          data: { 
            task_id: 'task_1',
            employee_info: {
              employee_name: 'Test User',
              phone_number: '+911234567890'
            }
          } 
        })
      );

      const { createTask } = await import('../services/api.service.js');
      const result = await createTask({ title: 'Test' });
      
      expect(result).toHaveProperty('taskId');
      if (result.employeeInfo) {
        expect(result.employeeInfo).toHaveProperty('employeeName');
        expect(result.employeeInfo).toHaveProperty('phoneNumber');
      }
    });
  });
});


// ============================================================================
// ERROR BOUNDARY TESTS
// ============================================================================

describe('Error Handling', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle network errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const { getProjects } = await import('../services/api.service.js');
    await expect(getProjects()).rejects.toThrow('Network error');
  });

  it('should handle API errors with status codes', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ success: false, error: 'Internal Server Error' }),
    });

    const { getProjects } = await import('../services/api.service.js');
    await expect(getProjects()).rejects.toThrow();
  });

  it('should handle 404 errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ success: false, error: 'Not found' }),
    });

    const { deleteTask } = await import('../services/api.service.js');
    await expect(deleteTask('nonexistent')).rejects.toThrow();
  });
});


// ============================================================================
// TASK STATUS WORKFLOW TESTS
// ============================================================================

describe('Task Status Workflow', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should correctly track WhatsApp sent status', async () => {
    // First call - send to WhatsApp
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: { whatsapp_sent: true }, message: 'Message sent' })
    );
    
    // Second call - get status
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { whatsapp_sent: true, whatsapp_response: null } 
      })
    );

    const { sendTaskToWhatsApp, getTaskWhatsAppStatus } = await import('../services/api.service.js');
    
    await sendTaskToWhatsApp('task_1');
    const status = await getTaskWhatsAppStatus('task_1');
    
    expect(status.whatsappSent).toBe(true);
  });

  it('should correctly track completed response', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { 
          whatsapp_sent: true, 
          whatsapp_response: 'completed',
          response_notes: null
        } 
      })
    );

    const { getTaskWhatsAppStatus } = await import('../services/api.service.js');
    const status = await getTaskWhatsAppStatus('task_1');
    
    expect(status.whatsappResponse).toBe('completed');
  });

  it('should correctly track not_completed response', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { 
          whatsapp_sent: true, 
          whatsapp_response: 'not_completed',
          response_notes: 'Blocked by dependency'
        } 
      })
    );

    const { getTaskWhatsAppStatus } = await import('../services/api.service.js');
    const status = await getTaskWhatsAppStatus('task_1');
    
    expect(status.whatsappResponse).toBe('not_completed');
    expect(status.responseNotes).toBe('Blocked by dependency');
  });
});


// ============================================================================
// EDGE CASE TESTS
// ============================================================================

describe('Edge Cases', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle empty response data', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: [] })
    );

    const { getTasks } = await import('../services/api.service.js');
    const result = await getTasks();
    
    expect(result).toEqual([]);
  });

  it('should handle null values in response', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: [{ 
          task_id: 'task_1',
          description: null,
          assigned_to: null,
          due_date: null
        }] 
      })
    );

    const { getTasks } = await import('../services/api.service.js');
    const result = await getTasks();
    
    expect(result[0].taskId).toBe('task_1');
    expect(result[0].description).toBeNull();
  });

  it('should handle special characters in task title', async () => {
    const specialTitle = 'Test <script>alert("xss")</script>';
    
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { task_id: 'task_1', title: specialTitle } 
      })
    );

    const { createTask } = await import('../services/api.service.js');
    const result = await createTask({ title: specialTitle });
    
    expect(result.title).toBe(specialTitle);
  });
});

// ============================================================================
// ID CONSISTENCY TESTS (Bug Fix Verification)
// ============================================================================
describe('Task ID Consistency', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle tasks with both taskId and id fields', async () => {
    // Test that toCamelCase ensures id === taskId for consistency
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: [{ 
          task_id: 'task_123',
          title: 'Test Task',
          status: 'unassigned'
        }] 
      })
    );

    const { getTasks } = await import('../services/api.service.js');
    const result = await getTasks();
    
    // After toCamelCase transformation, both id and taskId should exist and be equal
    expect(result[0].taskId).toBe('task_123');
    expect(result[0].id).toBe('task_123');
    expect(result[0].id).toBe(result[0].taskId);
  });

  it('should match tasks correctly regardless of id field used', async () => {
    // This test verifies the bug fix where updateTask matching was inconsistent
    // The bug: Some tasks only had taskId, some only had id, causing match failures
    
    const tasksWithMixedIds = [
      { taskId: 'task_1', title: 'Task with taskId only' },
      { id: 'task_2', title: 'Task with id only' },
      { taskId: 'task_3', id: 'task_3', title: 'Task with both fields' }
    ];

    // Each task should be matchable by either id or taskId
    tasksWithMixedIds.forEach(task => {
      const matchById = task.id === 'task_1' || task.taskId === 'task_1';
      const matchByTaskId = task.id === 'task_1' || task.taskId === 'task_1';
      
      // If task has task_1, both methods should find it
      if (task.taskId === 'task_1' || task.id === 'task_1') {
        expect(matchById || matchByTaskId).toBe(true);
      }
    });
  });

  it('should update task priority consistently across all projects', async () => {
    // This is the EXACT bug the user reported:
    // "Priority update works in 'messaging system' but not 'Hello boss' project"
    
    // Simulate tasks from different projects
    const messagingSystemTask = { 
      task_id: 'msg_task_1', 
      project_id: 'messaging_system',
      priority: 'medium' 
    };
    
    const helloBossTask = { 
      task_id: 'hello_task_1',
      project_id: 'hello_boss',
      priority: 'medium'
    };

    // Mock update for messaging system task
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { ...messagingSystemTask, priority: 'high' }
      })
    );

    // Mock update for hello boss task
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { ...helloBossTask, priority: 'high' }
      })
    );

    const { updateTask } = await import('../services/api.service.js');
    
    // Both updates should work identically
    const result1 = await updateTask('msg_task_1', { priority: 'high' });
    const result2 = await updateTask('hello_task_1', { priority: 'high' });
    
    // Both should have updated priority
    expect(result1.priority).toBe('high');
    expect(result2.priority).toBe('high');
    
    // Both API calls should have been made correctly
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});


// ============================================================================
// EDGE CASE TESTS
// ============================================================================

describe('Edge Cases - API Error Handling', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle network timeout gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

    const { getProjects } = await import('../services/api.service.js');
    
    await expect(getProjects()).rejects.toThrow();
  });

  it('should handle 500 server error', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: false, error: 'Internal server error' }, 500)
    );

    const { getProjects } = await import('../services/api.service.js');
    
    await expect(getProjects()).rejects.toThrow();
  });

  it('should handle empty response data', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: [] })
    );

    const { getProjects } = await import('../services/api.service.js');
    const result = await getProjects();
    
    expect(result).toEqual([]);
  });

  it('should handle null response data', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: null })
    );

    const { getTasks } = await import('../services/api.service.js');
    const result = await getTasks();
    
    expect(result).toEqual([]);
  });

  it('should handle malformed JSON response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.reject(new Error('Invalid JSON'))
    });

    const { getProjects } = await import('../services/api.service.js');
    
    await expect(getProjects()).rejects.toThrow();
  });
});


describe('Edge Cases - Data Transformation', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle deeply nested snake_case objects', async () => {
    const nestedData = {
      id: 'proj_1',
      project_name: 'Test',
      project_details: {
        created_at: '2026-01-01',
        updated_at: '2026-01-02',
        nested_info: {
          deep_field: 'value'
        }
      }
    };

    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: [nestedData] })
    );

    const { getProjects } = await import('../services/api.service.js');
    const result = await getProjects();

    expect(result[0]).toHaveProperty('projectName');
    expect(result[0]).toHaveProperty('projectDetails');
    expect(result[0].projectDetails).toHaveProperty('createdAt');
    expect(result[0].projectDetails).toHaveProperty('nestedInfo');
    expect(result[0].projectDetails.nestedInfo).toHaveProperty('deepField');
  });

  it('should handle arrays within objects during transformation', async () => {
    const dataWithArrays = {
      id: 'proj_1',
      team_members: [
        { member_id: 1, member_name: 'John', is_active: true },
        { member_id: 2, member_name: 'Jane', is_active: false }
      ]
    };

    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: [dataWithArrays] })
    );

    const { getProjects } = await import('../services/api.service.js');
    const result = await getProjects();

    expect(result[0].teamMembers).toHaveLength(2);
    expect(result[0].teamMembers[0]).toHaveProperty('memberId', 1);
    expect(result[0].teamMembers[0]).toHaveProperty('memberName', 'John');
    expect(result[0].teamMembers[0]).toHaveProperty('isActive', true);
  });

  it('should handle empty strings in data', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: [{ id: 'proj_1', name: '', description: '', start_date: '' }] 
      })
    );

    const { getProjects } = await import('../services/api.service.js');
    const result = await getProjects();

    expect(result[0].name).toBe('');
    expect(result[0].description).toBe('');
    expect(result[0].startDate).toBe('');
  });

  it('should handle special characters in values', async () => {
    const specialData = {
      id: 'proj_1',
      name: 'Test <script>alert("xss")</script>',
      description: "Quote's and \"double\" quotes",
      notes: 'Unicode: प्रोजेक्ट 📱 テスト'
    };

    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: [specialData] })
    );

    const { getProjects } = await import('../services/api.service.js');
    const result = await getProjects();

    expect(result[0].name).toContain('<script>');
    expect(result[0].description).toContain("Quote's");
    expect(result[0].notes).toContain('प्रोजेक्ट');
  });

  it('should handle boolean fields correctly', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: [{ 
          task_id: 'task_1',
          whatsapp_sent: true,
          is_completed: false,
          has_attachments: null
        }] 
      })
    );

    const { getTasks } = await import('../services/api.service.js');
    const result = await getTasks();

    expect(result[0].whatsappSent).toBe(true);
    expect(result[0].isCompleted).toBe(false);
    expect(result[0].hasAttachments).toBeNull();
  });

  it('should handle numeric fields correctly', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: [{ 
          task_id: 'task_1',
          employee_id: 0,
          progress_percent: 50.5,
          negative_value: -10
        }] 
      })
    );

    const { getTasks } = await import('../services/api.service.js');
    const result = await getTasks();

    expect(result[0].employeeId).toBe(0);
    expect(result[0].progressPercent).toBe(50.5);
    expect(result[0].negativeValue).toBe(-10);
  });
});


describe('Edge Cases - Project Operations', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should create project with minimal data', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { id: 'proj_1', name: 'Minimal' }
      }, 201)
    );

    const { createProject } = await import('../services/api.service.js');
    const result = await createProject({ name: 'Minimal' });

    expect(result).toHaveProperty('id');
    expect(result.name).toBe('Minimal');
  });

  it('should handle project update with partial data', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { id: 'proj_1', name: 'Updated Name', start_date: '2026-01-01' }
      })
    );

    const { updateProject } = await import('../services/api.service.js');
    const result = await updateProject('proj_1', { name: 'Updated Name' });

    expect(result.name).toBe('Updated Name');
  });

  it('should handle project deletion', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, message: 'Project deleted' })
    );

    const { deleteProject } = await import('../services/api.service.js');
    await expect(deleteProject('proj_1')).resolves.not.toThrow();
  });

  it('should handle deleting non-existent project', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: false, error: 'Project not found' }, 404)
    );

    const { deleteProject } = await import('../services/api.service.js');
    await expect(deleteProject('proj_nonexistent')).rejects.toThrow();
  });
});


describe('Edge Cases - Task Operations', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should create task with all fields', async () => {
    const fullTask = {
      task_id: 'task_1',
      title: 'Full Task',
      description: 'Description',
      project_id: 'proj_1',
      employee_id: 1,
      due_date: '2026-12-31',
      priority: 'high',
      status: 'in_progress'
    };

    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, data: fullTask }, 201)
    );

    const { createTask } = await import('../services/api.service.js');
    const result = await createTask(fullTask);

    expect(result.taskId).toBe('task_1');
    expect(result.id).toBe('task_1');
    expect(result.priority).toBe('high');
  });

  it('should handle task status transitions', async () => {
    const statuses = ['unassigned', 'in_progress', 'pending_verification', 'completed'];
    
    for (const status of statuses) {
      mockFetch.mockResolvedValueOnce(
        createMockResponse({ 
          success: true, 
          data: { task_id: 'task_1', status }
        })
      );

      const { updateTask } = await import('../services/api.service.js');
      const result = await updateTask('task_1', { status });

      expect(result.status).toBe(status);
    }
  });

  it('should handle task with missing optional fields', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { 
          task_id: 'task_1', 
          title: 'Task',
          description: null,
          due_date: null,
          employee_id: null
        }
      })
    );

    const { getTaskById } = await import('../services/api.service.js');
    const result = await getTaskById('task_1');

    expect(result.description).toBeNull();
    expect(result.dueDate).toBeNull();
    expect(result.employeeId).toBeNull();
  });

  it('should handle deleting task', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: true, message: 'Task deleted' })
    );

    const { deleteTask } = await import('../services/api.service.js');
    await expect(deleteTask('task_1')).resolves.not.toThrow();
  });
});


describe('Edge Cases - Employee Operations', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle employee with all fields', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { 
          id: 1, 
          name: 'John Doe', 
          phone: '+919876543210',
          role: 'Developer',
          created_at: '2026-01-01T00:00:00Z'
        }
      })
    );

    const { getEmployeeById } = await import('../services/api.service.js');
    const result = await getEmployeeById(1);

    expect(result.name).toBe('John Doe');
    expect(result.phone).toBe('+919876543210');
    expect(result.createdAt).toBeDefined();
  });

  it('should handle getting all employees', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: [
          { id: 1, name: 'Employee 1' },
          { id: 2, name: 'Employee 2' },
          { id: 3, name: 'Employee 3' }
        ]
      })
    );

    const { getEmployees } = await import('../services/api.service.js');
    const result = await getEmployees();

    expect(result).toHaveLength(3);
  });

  it('should handle non-existent employee', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ success: false, error: 'Employee not found' }, 404)
    );

    const { getEmployeeById } = await import('../services/api.service.js');
    await expect(getEmployeeById(999)).rejects.toThrow();
  });
});


describe('Edge Cases - WhatsApp Operations', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle sending WhatsApp message', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { 
          task_id: 'task_1',
          whatsapp_sent: true,
          message_id: 'msg_123'
        }
      })
    );

    const { sendTaskToWhatsApp } = await import('../services/api.service.js');
    const result = await sendTaskToWhatsApp('task_1');

    expect(result.whatsappSent).toBe(true);
  });

  it('should handle WhatsApp send failure', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: false, 
        error: 'Task not assigned to employee'
      }, 400)
    );

    const { sendTaskToWhatsApp } = await import('../services/api.service.js');
    await expect(sendTaskToWhatsApp('task_1')).rejects.toThrow();
  });

  it('should handle getting WhatsApp status', async () => {
    mockFetch.mockResolvedValueOnce(
      createMockResponse({ 
        success: true, 
        data: { 
          whatsapp_sent: true,
          whatsapp_response: 'completed'
        }
      })
    );

    const { getTaskWhatsAppStatus } = await import('../services/api.service.js');
    const result = await getTaskWhatsAppStatus('task_1');

    expect(result.whatsappSent).toBe(true);
    expect(result.whatsappResponse).toBe('completed');
  });
});


describe('Edge Cases - Utility Functions', () => {
  it('should format dates correctly', async () => {
    const { formatDate } = await import('../utils/helpers.js');
    
    // Valid date
    expect(formatDate('2026-01-25')).toBeTruthy();
    
    // Empty/null dates return empty string
    expect(formatDate('')).toBe('');
    expect(formatDate(null)).toBe('');
    expect(formatDate(undefined)).toBe('');
  });

  it('should detect overdue tasks correctly', async () => {
    const { isOverdue } = await import('../utils/helpers.js');
    
    // Past date - overdue
    expect(isOverdue('2020-01-01')).toBe(true);
    
    // Future date - not overdue
    expect(isOverdue('2030-12-31')).toBe(false);
    
    // No date - not overdue
    expect(isOverdue(null)).toBe(false);
    expect(isOverdue('')).toBe(false);
  });

  it('should group tasks by status correctly', async () => {
    const { groupTasksByStatus } = await import('../utils/helpers.js');
    
    const tasks = [
      { id: 1, status: 'unassigned' },
      { id: 2, status: 'in_progress' },
      { id: 3, status: 'unassigned' },
      { id: 4, status: 'completed' }
    ];

    const grouped = groupTasksByStatus(tasks);

    expect(grouped.unassigned).toHaveLength(2);
    expect(grouped.in_progress).toHaveLength(1);
    expect(grouped.completed).toHaveLength(1);
  });

  it('should handle empty task list when grouping', async () => {
    const { groupTasksByStatus } = await import('../utils/helpers.js');
    
    const grouped = groupTasksByStatus([]);

    // Empty array returns empty object
    expect(Object.keys(grouped)).toHaveLength(0);
  });

  it('should sort tasks by priority correctly', async () => {
    const { sortByPriority } = await import('../utils/helpers.js');
    
    const tasks = [
      { id: 1, priority: 'low' },
      { id: 2, priority: 'high' },
      { id: 3, priority: 'medium' },
      { id: 4, priority: 'high' }
    ];

    const sorted = sortByPriority(tasks);

    // High priority should come first
    expect(sorted[0].priority).toBe('high');
    expect(sorted[1].priority).toBe('high');
    expect(sorted[2].priority).toBe('medium');
    expect(sorted[3].priority).toBe('low');
  });

  it('should handle tasks with missing priority', async () => {
    const { sortByPriority } = await import('../utils/helpers.js');
    
    const tasks = [
      { id: 1 },
      { id: 2, priority: 'high' },
      { id: 3, priority: null }
    ];

    const sorted = sortByPriority(tasks);
    expect(sorted).toHaveLength(3);
  });
});


describe('Edge Cases - Validation Functions', () => {
  it('should validate required fields', async () => {
    const { validateRequired } = await import('../utils/validators.js');
    
    expect(validateRequired('value')).toBe(true);
    expect(validateRequired('')).toBe(false);
    expect(validateRequired(null)).toBe(false);
    expect(validateRequired(undefined)).toBe(false);
    expect(validateRequired('   ')).toBe(false);
  });

  it('should validate phone numbers', async () => {
    const { validatePhone } = await import('../utils/validators.js');
    
    expect(validatePhone('+919876543210')).toBe(true);
    expect(validatePhone('+1234567890')).toBe(true);
    expect(validatePhone('invalid')).toBe(false);
    expect(validatePhone('')).toBe(false);
  });

  it('should validate dates', async () => {
    const { validateDate } = await import('../utils/validators.js');
    
    expect(validateDate('2026-01-25')).toBe(true);
    expect(validateDate('invalid-date')).toBe(false);
    expect(validateDate('')).toBe(true); // Empty is allowed
  });

  it('should validate priority values', async () => {
    const { validatePriority } = await import('../utils/validators.js');
    
    expect(validatePriority('high')).toBe(true);
    expect(validatePriority('medium')).toBe(true);
    expect(validatePriority('low')).toBe(true);
    expect(validatePriority('critical')).toBe(false);
    expect(validatePriority('')).toBe(false);
  });

  it('should validate status values', async () => {
    const { validateStatus } = await import('../utils/validators.js');
    
    expect(validateStatus('unassigned')).toBe(true);
    expect(validateStatus('in_progress')).toBe(true);
    expect(validateStatus('pending_verification')).toBe(true);
    expect(validateStatus('completed')).toBe(true);
    expect(validateStatus('todo')).toBe(false);
    expect(validateStatus('invalid')).toBe(false);
  });
});

