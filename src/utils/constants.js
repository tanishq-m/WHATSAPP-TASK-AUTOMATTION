export const PRIORITY = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
}

export const PRIORITY_COLORS = {
  [PRIORITY.HIGH]: '#EF4444',
  [PRIORITY.MEDIUM]: '#F59E0B',
  [PRIORITY.LOW]: '#10B981'
}

export const PRIORITY_LABELS = {
  [PRIORITY.HIGH]: 'High',
  [PRIORITY.MEDIUM]: 'Medium',
  [PRIORITY.LOW]: 'Low'
}

export const STATUS = {
  UNASSIGNED: 'unassigned',        // Renamed from READY_TO_START
  IN_PROGRESS: 'in_progress',
  PENDING_VERIFICATION: 'pending_verification',
  COMPLETED: 'completed'
}

export const STATUS_COLORS = {
  [STATUS.UNASSIGNED]: '#6B7280',
  [STATUS.IN_PROGRESS]: '#3B82F6',
  [STATUS.PENDING_VERIFICATION]: '#F59E0B',
  [STATUS.COMPLETED]: '#10B981'
}

export const STATUS_LABELS = {
  [STATUS.UNASSIGNED]: 'Unassigned Tasks',  // Updated label
  [STATUS.IN_PROGRESS]: 'In Progress',
  [STATUS.PENDING_VERIFICATION]: 'Pending Verification',
  [STATUS.COMPLETED]: 'Completed'
}

export const PROJECT_COLORS = [
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#14B8A6', // Teal
  '#F59E0B'  // Orange
]

export const STORAGE_KEYS = {
  PROJECTS: 'wtm_projects',
  TASKS: 'wtm_tasks',
  EMPLOYEES: 'wtm_employees',
  TIMER_CONFIG: 'wtm_timer_config'
}


