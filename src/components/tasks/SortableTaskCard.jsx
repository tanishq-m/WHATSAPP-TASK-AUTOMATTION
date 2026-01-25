import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import TaskCard from './TaskCard'

const SortableTaskCard = ({ task, onClick }) => {
  // Use taskId for drag-and-drop ID (matches backend API expectation)
  // taskId format: "task_001", "task_002", etc.
  const dragId = task.taskId || task.id
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
    isOver
  } = useSortable({ id: dragId })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    // Improve drag performance on mobile
    willChange: isDragging ? 'transform' : undefined,
    // Elevate dragging card
    zIndex: isDragging ? 50 : undefined
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`w-full touch-manipulation select-none ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
      {...attributes}
      {...listeners}
    >
      <TaskCard 
        task={task} 
        onClick={onClick}
        isDragging={isDragging}
      />
    </div>
  )
}

export default SortableTaskCard


