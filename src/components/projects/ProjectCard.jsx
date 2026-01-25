import { useNavigate } from 'react-router-dom'
import { Calendar, CheckCircle, ClipboardList, PlayCircle, Clock } from 'lucide-react'
import { formatDate } from '../../utils/helpers'
import { useApp } from '../../context/useApp'
import ProgressBar from '../common/ProgressBar'
import EmployeeAvatar from '../employees/EmployeeAvatar'

const ProjectCard = ({ project }) => {
  const navigate = useNavigate()
  const { getEmployeesByIds } = useApp()
  
  const assignedEmployees = getEmployeesByIds(project.assignedEmployees || [])
  const displayEmployees = assignedEmployees.slice(0, 3)
  const remainingCount = assignedEmployees.length - 3

  return (
    <div 
      onClick={() => navigate(`/project/${project.id}`)}
      className="card-hover p-4 md:p-5 cursor-pointer"
      style={{ borderLeftWidth: '4px', borderLeftColor: project.color }}
    >
      {/* Project Name */}
      <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate">
        {project.name}
      </h3>

      {/* Date Range */}
      <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
        <Calendar className="w-4 h-4" />
        <span>
          {formatDate(project.startDate)} - {formatDate(project.endDate)}
        </span>
      </div>

      {/* Progress */}
      <div className="mb-4">
        <ProgressBar progress={project.progress} size="md" />
      </div>

      {/* Task Status Breakdown */}
      <div className="grid grid-cols-2 gap-2 text-sm mb-4">
        <div className="flex items-center gap-1 text-gray-500">
          <ClipboardList className="w-4 h-4" />
          <span>Unassigned: {project.unassignedTasks || 0}</span>
        </div>
        <div className="flex items-center gap-1 text-blue-600">
          <PlayCircle className="w-4 h-4" />
          <span>In Progress: {project.inProgressTasks || 0}</span>
        </div>
        <div className="flex items-center gap-1 text-amber-600">
          <Clock className="w-4 h-4" />
          <span>Pending: {project.pendingTasks || 0}</span>
        </div>
        <div className="flex items-center gap-1 text-green-600">
          <CheckCircle className="w-4 h-4" />
          <span>Done: {project.completedTasks || 0}/{project.taskCount || 0}</span>
        </div>
      </div>

      {/* Assigned Employees */}
      {assignedEmployees.length > 0 && (
        <div className="flex items-center gap-2">
          <div className="flex -space-x-2">
            {displayEmployees.map((employee) => (
              <div key={employee.id} className="ring-2 ring-white rounded-full">
                <EmployeeAvatar employee={employee} size="sm" />
              </div>
            ))}
          </div>
          {remainingCount > 0 && (
            <span className="text-xs font-medium text-gray-500">
              +{remainingCount} more
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default ProjectCard


