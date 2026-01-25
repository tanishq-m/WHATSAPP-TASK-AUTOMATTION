import { PRIORITY_COLORS, PRIORITY_LABELS } from '../../utils/constants'

const TaskPriorityBadge = ({ priority }) => {
  const styles = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-orange-100 text-orange-800',
    low: 'bg-green-100 text-green-800'
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${styles[priority]}`}>
      <span 
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: PRIORITY_COLORS[priority] }}
      />
      {PRIORITY_LABELS[priority]}
    </span>
  )
}

export default TaskPriorityBadge


