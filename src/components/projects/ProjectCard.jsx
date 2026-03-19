import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, CheckCircle, ClipboardList, PlayCircle, Clock, Pencil, Trash2, Users } from 'lucide-react'
import { formatDate } from '../../utils/helpers'
import { useApp } from '../../context/useApp'
import ProgressBar from '../common/ProgressBar'
import EmployeeAvatar from '../employees/EmployeeAvatar'
import ConfirmDialog from '../common/ConfirmDialog'
import CreateProjectModal from './CreateProjectModal'

const ProjectCard = ({ project }) => {
  const navigate = useNavigate()
  const { getEmployeesByIds, deleteProject } = useApp()
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  
  const assignedEmployees = getEmployeesByIds(project.assignedEmployees || [])
  const displayEmployees = assignedEmployees.slice(0, 3)
  const remainingCount = assignedEmployees.length - 3

  const handleCardClick = () => {
    navigate(`/project/${project.id}`)
  }

  const handleDelete = async () => {
    try {
      await deleteProject(project.id)
      setShowDeleteConfirm(false)
      // No navigation needed - already on dashboard
      // The project list will auto-refresh via AppContext
    } catch (error) {
      console.error('Failed to delete project:', error)
    }
  }

  return (
    <>
      <div 
        className="card-hover p-4 md:p-5 cursor-pointer relative"
        style={{ borderLeftWidth: '4px', borderLeftColor: project.color }}
      >
        {/* Action Buttons */}
        <div className="absolute top-3 right-3 flex gap-2">
          <button
            onClick={(e) => { 
              e.stopPropagation()
              setShowEditModal(true)
            }}
            className="p-2 hover:bg-gray-100 rounded-lg transition-smooth tap-target"
            title="Edit project"
          >
            <Pencil className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={(e) => { 
              e.stopPropagation()
              setShowDeleteConfirm(true)
            }}
            className="p-2 hover:bg-red-50 rounded-lg transition-smooth tap-target"
            title="Delete project"
          >
            <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
          </button>
        </div>

        {/* Clickable Card Content */}
        <div onClick={handleCardClick}>
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

      {/* Team Members Count */}
      <div className="flex items-center gap-2 text-sm text-gray-700 mb-3 pb-3 border-b border-gray-100">
        <Users className="w-4 h-4" />
        <span className="font-medium">
          Team Members: {assignedEmployees.length}
        </span>
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
      </div>

      {/* Edit Project Modal */}
      <CreateProjectModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        project={project}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Project?"
        message={`Are you sure you want to delete "${project.name}"?\n\n⚠️ WARNING: This will also delete ${project.taskCount || 0} task${project.taskCount !== 1 ? 's' : ''} associated with this project.\n\nThis action cannot be undone.`}
        confirmText="Delete Project"
        variant="danger"
      />
    </>
  )
}

export default ProjectCard


