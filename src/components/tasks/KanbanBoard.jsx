import { useState } from 'react'
import { DndContext, DragOverlay, closestCorners, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import { STATUS } from '../../utils/constants'
import { groupTasksByStatus } from '../../utils/helpers'
import { useApp } from '../../context/useApp'
import KanbanColumn from './KanbanColumn'
import TaskCard from './TaskCard'
import TaskModal from './TaskModal'

const KanbanBoard = ({ tasks, projectId }) => {
  const { updateTask } = useApp()
  const [selectedTask, setSelectedTask] = useState(null)
  const [activeTask, setActiveTask] = useState(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8
      }
    })
  )

  const groupedTasks = groupTasksByStatus(tasks)

  const columns = [
    { id: STATUS.UNASSIGNED, tasks: groupedTasks[STATUS.UNASSIGNED] || [] },
    { id: STATUS.IN_PROGRESS, tasks: groupedTasks[STATUS.IN_PROGRESS] || [] },
    { id: STATUS.PENDING_VERIFICATION, tasks: groupedTasks[STATUS.PENDING_VERIFICATION] || [] },
    { id: STATUS.COMPLETED, tasks: groupedTasks[STATUS.COMPLETED] || [] }
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

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
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


