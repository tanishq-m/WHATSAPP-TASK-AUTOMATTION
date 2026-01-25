import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { STATUS_LABELS, STATUS_COLORS } from '../../utils/constants'
import SortableTaskCard from './SortableTaskCard'

const KanbanColumn = ({ status, tasks, onTaskClick }) => {
  const { setNodeRef, isOver } = useDroppable({
    id: status
  })

  const taskIds = tasks.map(t => t.id)

  return (
    <div className="kanban-column flex flex-col">
      {/* Column Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div 
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: STATUS_COLORS[status] }}
          />
          <h3 className="font-semibold text-gray-900">
            {STATUS_LABELS[status]}
          </h3>
        </div>
        <span className="text-sm font-medium text-gray-500 bg-white px-2 py-0.5 rounded">
          {tasks.length}
        </span>
      </div>

      {/* Tasks List - with drop zone highlight */}
      <div 
        ref={setNodeRef}
        className={`flex-1 space-y-3 min-h-[200px] rounded-lg transition-colors ${
          isOver 
            ? 'bg-blue-50 ring-2 ring-blue-300 ring-inset' 
            : ''
        }`}
      >
        <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <SortableTaskCard
              key={task.id}
              task={task}
              onClick={() => onTaskClick(task)}
            />
          ))}
        </SortableContext>
        
        {tasks.length === 0 && (
          <div className="flex items-center justify-center h-32 text-sm text-gray-400">
            No tasks
          </div>
        )}
      </div>
    </div>
  )
}

export default KanbanColumn


