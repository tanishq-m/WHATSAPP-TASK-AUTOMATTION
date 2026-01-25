import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { STATUS_LABELS, STATUS_COLORS } from '../../utils/constants'
import SortableTaskCard from './SortableTaskCard'

const KanbanColumn = ({ status, tasks, onTaskClick }) => {
  const { setNodeRef, isOver } = useDroppable({
    id: status
  })

  // Use taskId (or fallback to id) to match SortableTaskCard's dragId
  const taskIds = tasks.map(t => t.taskId || t.id)

  return (
    <div className="kanban-column flex flex-col">
      {/* Column Header */}
      <div className="flex items-center justify-between mb-3 sticky top-0 bg-gray-50 z-10 py-1">
        <div className="flex items-center gap-2">
          <div 
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: STATUS_COLORS[status] }}
          />
          <h3 className="font-semibold text-gray-900 text-sm sm:text-base truncate">
            {STATUS_LABELS[status]}
          </h3>
        </div>
        <span className="text-xs sm:text-sm font-medium text-gray-500 bg-white px-2 py-0.5 rounded flex-shrink-0">
          {tasks.length}
        </span>
      </div>

      {/* Tasks List - with drop zone highlight */}
      <div 
        ref={setNodeRef}
        className={`flex-1 space-y-3 min-h-[200px] rounded-lg transition-all duration-200 ${
          isOver 
            ? 'bg-blue-100 ring-2 ring-blue-400 ring-inset' 
            : 'bg-transparent'
        }`}
      >
        <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <SortableTaskCard
              key={task.taskId || task.id}
              task={task}
              onClick={() => onTaskClick(task)}
            />
          ))}
        </SortableContext>
      </div>
    </div>
  )
}

export default KanbanColumn


