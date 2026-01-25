export const generateId = (prefix = 'id') => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

export const formatDateInput = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toISOString().split('T')[0]
}

export const isOverdue = (dueDate) => {
  if (!dueDate) return false
  return new Date(dueDate) < new Date()
}

export const calculateProgress = (total, completed) => {
  if (total === 0) return 0
  return Math.round((completed / total) * 100)
}

export const getInitials = (name) => {
  if (!name) return '?'
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export const getRandomColor = (colors) => {
  return colors[Math.floor(Math.random() * colors.length)]
}

export const sortByPriority = (tasks) => {
  const priorityOrder = { high: 1, medium: 2, low: 3 }
  return [...tasks].sort((a, b) => {
    return priorityOrder[a.priority] - priorityOrder[b.priority]
  })
}

export const groupTasksByStatus = (tasks) => {
  return tasks.reduce((acc, task) => {
    if (!acc[task.status]) {
      acc[task.status] = []
    }
    acc[task.status].push(task)
    return acc
  }, {})
}

export const getAvatarColor = (name) => {
  const colors = [
    'bg-blue-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-teal-500',
    'bg-orange-500',
    'bg-green-500',
    'bg-red-500',
    'bg-indigo-500'
  ]
  
  const index = name ? name.charCodeAt(0) % colors.length : 0
  return colors[index]
}

export const sortTasksByDueDate = (tasks, ascending = true) => {
  return [...tasks].sort((a, b) => {
    // Tasks without due dates go to the end
    const dateA = a.dueDate ? new Date(a.dueDate) : new Date('9999-12-31')
    const dateB = b.dueDate ? new Date(b.dueDate) : new Date('9999-12-31')
    return ascending ? dateA - dateB : dateB - dateA
  })
}


