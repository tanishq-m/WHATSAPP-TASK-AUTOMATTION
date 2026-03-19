import { useNavigate } from 'react-router-dom'
import { Calendar, CheckCircle, AlertTriangle } from 'lucide-react'
import ProgressBar from '../common/ProgressBar'
import { formatDate } from '../../utils/helpers'

const ProjectSummaryCard = ({ project }) => {
  const navigate = useNavigate()
  
  const handleClick = () => {
    navigate(`/project/${project.projectId}`)
  }
  
  return (
    <div
      onClick={handleClick}
      className="card-hover p-4 cursor-pointer"
      style={{ borderLeftWidth: '4px', borderLeftColor: project.projectColor }}
    >
      {/* Project name */}
      <h3 className="font-semibold text-gray-900 mb-2 truncate">
        {project.projectName}
      </h3>
      
      {/* Stats row */}
      <div className="flex items-center gap-4 mb-3 text-sm">
        <div className="flex items-center gap-1 text-gray-600">
          <CheckCircle className="w-4 h-4" />
          <span>{project.completedTasks}/{project.totalTasks}</span>
        </div>
        
        {project.overdueTasks > 0 && (
          <div className="flex items-center gap-1 text-red-600 font-medium">
            <AlertTriangle className="w-4 h-4" />
            <span>{project.overdueTasks} overdue</span>
          </div>
        )}
      </div>
      
      {/* Progress bar */}
      <ProgressBar 
        progress={project.completionRate} 
        size="sm"
        showLabel={false}
      />
      
      {/* Date range */}
      {project.startDate && project.endDate && (
        <div className="flex items-center gap-1 text-xs text-gray-500 mt-2">
          <Calendar className="w-3 h-3" />
          <span>{formatDate(project.startDate)} - {formatDate(project.endDate)}</span>
        </div>
      )}
    </div>
  )
}

export default ProjectSummaryCard
