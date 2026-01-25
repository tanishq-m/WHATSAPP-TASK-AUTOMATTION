import { useState } from 'react'
import { DndContext, DragOverlay, closestCenter, PointerSensor, TouchSensor, useSensor, useSensors, rectIntersection } from '@dnd-kit/core'
import { STATUS } from '../../utils/constants'
import { groupTasksByStatus, sortByPriority, sortTasksByDueDate } from '../../utils/helpers'
import { useApp } from '../../context/useApp'
import KanbanColumn from './KanbanColumn'
import TaskCard from './TaskCard'
import TaskModal from './TaskModal'
import FilterDropdown from './FilterDropdown'
import SortDropdown from './SortDropdown'

const KanbanBoard = ({ tasks, projectId }) => {
  const { updateTask, getEmployeeById } = useApp()
  const [selectedTask, setSelectedTask] = useState(null)
  const [activeTask, setActiveTask] = useState(null)
  const [filterEmployee, setFilterEmployee] = useState(null)
  const [sortBy, setSortBy] = useState('priority')

  // Configure sensors for both pointer (mouse) and touch (mobile/tablet)
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8 // Minimum drag distance before activation
      }
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200, // Hold for 200ms before drag starts (prevents accidental drags while scrolling)
        tolerance: 8 // Allow 8px movement during delay
      }
    })
  )

  // Apply filter before grouping
  const filteredTasks = filterEmployee 
    ? tasks.filter(t => t.assignedTo === filterEmployee)
    : tasks

  // Sort tasks function
  const sortTasks = (tasksArray) => {
    switch (sortBy) {
      case 'dueDate-asc':
        return sortTasksByDueDate(tasksArray, true)
      case 'dueDate-desc':
        return sortTasksByDueDate(tasksArray, false)
      case 'priority':
        return sortByPriority(tasksArray)
      case 'assignedTo':
        return [...tasksArray].sort((a, b) => {
          const nameA = getEmployeeById(a.assignedTo)?.name || ''
          const nameB = getEmployeeById(b.assignedTo)?.name || ''
          return nameA.localeCompare(nameB)
        })
      default:
        return tasksArray
    }
  }

  const groupedTasks = groupTasksByStatus(filteredTasks)

  // Apply sorting to each column
  const columns = [
    { id: STATUS.UNASSIGNED, tasks: sortTasks(groupedTasks[STATUS.UNASSIGNED] || []) },
    { id: STATUS.IN_PROGRESS, tasks: sortTasks(groupedTasks[STATUS.IN_PROGRESS] || []) },
    { id: STATUS.PENDING_VERIFICATION, tasks: sortTasks(groupedTasks[STATUS.PENDING_VERIFICATION] || []) },
    { id: STATUS.COMPLETED, tasks: sortTasks(groupedTasks[STATUS.COMPLETED] || []) }
  ]

  const handleDragStart = (event) => {
    // Find task by taskId (API format: "task_001") or fall back to id
    const task = tasks.find(t => (t.taskId || t.id) === event.active.id)
    setActiveTask(task)
  }

  const handleDragEnd = (event) => {
    const { active, over } = event
    
    if (!over) {
      setActiveTask(null)
      return
    }

    const dragId = active.id
    const newStatus = over.id

    // Check if dropped on a column (status)
    if (Object.values(STATUS).includes(newStatus)) {
      // Find task by taskId (matches the drag ID we set in SortableTaskCard)
      const task = tasks.find(t => (t.taskId || t.id) === dragId)
      if (task && task.status !== newStatus) {
        // Use taskId for API call (backend expects "task_001" format)
        const apiTaskId = task.taskId || task.id
        console.log(`📦 Dragging task ${apiTaskId} to ${newStatus}`)
        // Explicitly pass 'admin' source to distinguish from webhook updates
        updateTask(apiTaskId, { status: newStatus }, 'admin')
      }
    }

    setActiveTask(null)
  }

  const handleDragCancel = () => {
    setActiveTask(null)
  }

  const handleTaskClick = (task) => {
    setSelectedTask(task)
  }

  const handleCloseModal = () => {
    setSelectedTask(null)
  }

  // Custom collision detection: prioritize column drops over task sorting
  const customCollisionDetection = (args) => {
    // First check if we're over a column (status zone)
    const columnCollisions = rectIntersection({
      ...args,
      droppableContainers: args.droppableContainers.filter(
        container => Object.values(STATUS).includes(container.id)
      )
    })
    
    if (columnCollisions.length > 0) {
      return columnCollisions
    }
    
    // Fall back to closest center for task-to-task sorting
    return closestCenter(args)
  }

  return (
    <>
      {/* Filter and Sort Controls */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 px-1">
        <FilterDropdown 
          selectedEmployee={filterEmployee}
          onSelect={setFilterEmployee}
        />
        <SortDropdown 
          sortBy={sortBy}
          onSortChange={setSortBy}
        />
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={customCollisionDetection}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        {/* Kanban columns container - horizontal scroll on mobile */}
        <div className="flex gap-3 sm:gap-4 overflow-x-auto pb-4 px-1 -mx-1 snap-x snap-mandatory sm:snap-none custom-scrollbar touch-pan-x">
          {columns.map((column) => (
            <KanbanColumn
              key={column.id}
              status={column.id}
              tasks={column.tasks}
              onTaskClick={handleTaskClick}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask ? <TaskCard task={activeTask} isDragging /> : null}
        </DragOverlay>
      </DndContext>

      {/* Task Edit Modal */}
      {selectedTask && (
        <TaskModal
          isOpen={!!selectedTask}
          onClose={handleCloseModal}
          task={selectedTask}
          projectId={projectId}
        />
      )}
    </>
  )
}

export default KanbanBoard


