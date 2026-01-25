import { generateId } from '../utils/helpers'
import { PRIORITY, STATUS, PROJECT_COLORS } from '../utils/constants'

// Hardcoded employees for MVP
export const MOCK_EMPLOYEES = [
  {
    id: 'emp_001',
    name: 'Rajesh Kumar',
    phone: '+919876543210',
    role: 'Developer',
    createdAt: new Date('2025-01-01').toISOString()
  },
  {
    id: 'emp_002',
    name: 'Priya Singh',
    phone: '+919876543211',
    role: 'Designer',
    createdAt: new Date('2025-01-01').toISOString()
  },
  {
    id: 'emp_003',
    name: 'Amit Patel',
    phone: '+919876543212',
    role: 'Tester',
    createdAt: new Date('2025-01-01').toISOString()
  }
]

export const MOCK_PROJECTS = [
  {
    id: 'proj_001',
    name: 'Website Redesign',
    startDate: '2025-01-05',
    endDate: '2025-03-31',
    color: PROJECT_COLORS[0],
    assignedEmployees: ['emp_001', 'emp_002'],
    createdAt: new Date().toISOString()
  },
  {
    id: 'proj_002',
    name: 'Mobile App Development',
    startDate: '2025-01-10',
    endDate: '2025-04-30',
    color: PROJECT_COLORS[1],
    assignedEmployees: ['emp_001', 'emp_003'],
    createdAt: new Date().toISOString()
  }
]

export const MOCK_TASKS = [
  {
    id: 'task_001',
    title: 'Design homepage mockup',
    description: 'Create Figma mockup for new homepage with modern design',
    projectId: 'proj_001',
    assignedTo: 'emp_002',
    dueDate: '2025-01-15',
    priority: PRIORITY.HIGH,
    status: STATUS.UNASSIGNED,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    comments: [],
    whatsappSent: false,
    lastWhatsappSent: null
  },
  {
    id: 'task_002',
    title: 'Setup development environment',
    description: 'Install Node.js, React, and configure development tools',
    projectId: 'proj_001',
    assignedTo: 'emp_001',
    dueDate: '2025-01-10',
    priority: PRIORITY.HIGH,
    status: STATUS.IN_PROGRESS,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    comments: [],
    whatsappSent: true,
    lastWhatsappSent: new Date().toISOString()
  },
  {
    id: 'task_003',
    title: 'Create color palette',
    description: 'Define primary, secondary colors and create style guide',
    projectId: 'proj_001',
    assignedTo: 'emp_002',
    dueDate: '2025-01-12',
    priority: PRIORITY.MEDIUM,
    status: STATUS.PENDING_VERIFICATION,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    comments: [],
    whatsappSent: true,
    lastWhatsappSent: new Date().toISOString()
  },
  {
    id: 'task_004',
    title: 'Write test cases',
    description: 'Create comprehensive test cases for all components',
    projectId: 'proj_001',
    assignedTo: 'emp_003',
    dueDate: '2025-01-20',
    priority: PRIORITY.LOW,
    status: STATUS.COMPLETED,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    comments: [],
    whatsappSent: true,
    lastWhatsappSent: new Date().toISOString()
  },
  {
    id: 'task_005',
    title: 'API Integration',
    description: 'Connect frontend with backend APIs',
    projectId: 'proj_002',
    assignedTo: 'emp_001',
    dueDate: '2025-01-25',
    priority: PRIORITY.HIGH,
    status: STATUS.UNASSIGNED,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    comments: [],
    whatsappSent: false,
    lastWhatsappSent: null
  }
]

export const MOCK_TIMER_CONFIG = {
  morningTaskTime: '09:00',
  eodFormTime: '18:00',
  enabled: true,
  lastRun: null
}


