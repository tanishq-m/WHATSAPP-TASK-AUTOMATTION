import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, FolderX, Pencil } from 'lucide-react'
import { useApp } from '../context/useApp'
import Button from '../components/common/Button'
import ProjectStats from '../components/projects/ProjectStats'
import KanbanBoard from '../components/tasks/KanbanBoard'
import TaskModal from '../components/tasks/TaskModal'
import CreateProjectModal from '../components/projects/CreateProjectModal'

const ProjectDetail = () => {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const { getProjectById, getTasksByProject, tasks: allTasks } = useApp()
  
  const [project, setProject] = useState(null)
  const [tasks, setTasks] = useState([])
  const [showCreateTask, setShowCreateTask] = useState(false)
  const [showEditProject, setShowEditProject] = useState(false)

  // Update tasks whenever allTasks changes (e.g., after API calls)
  useEffect(() => {
    const proj = getProjectById(projectId)
    if (proj) {
      setProject(proj)
    }
  }, [projectId, getProjectById])

  // Update tasks whenever the global tasks state changes
  useEffect(() => {
    setTasks(getTasksByProject(projectId))
  }, [projectId, getTasksByProject, allTasks])

  if (!project) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <FolderX className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Project not found
          </h3>
          <p className="text-gray-600 mb-6">
            This project may have been deleted or doesn't exist
          </p>
          <Button onClick={() => navigate('/')} variant="primary">
            Back to Projects
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-smooth self-start tap-target"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 truncate">
              {project.name}
            </h1>
            <div 
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: project.color }}
            />
            <button
              onClick={() => setShowEditProject(true)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-smooth tap-target"
              title="Edit project"
            >
              <Pencil className="w-4 h-4 text-gray-600" />
            </button>
          </div>
          {project.description && (
            <p className="text-gray-600 text-sm mt-1">{project.description}</p>
          )}
        </div>

        <Button
          onClick={() => setShowCreateTask(true)}
          variant="primary"
          className="flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-5 h-5" />
          <span>New Task</span>
        </Button>
      </div>

      {/* Project Stats */}
      <div className="mb-6">
        <ProjectStats project={project} tasks={tasks} />
      </div>

      {/* Kanban Board */}
      <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 md:p-6 overflow-hidden">
        <h2 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">
          Task Board
        </h2>
        {tasks.length > 0 ? (
          <KanbanBoard tasks={tasks} projectId={projectId} />
        ) : (
          <div className="flex flex-col items-center justify-center py-8 sm:py-12">
            <p className="text-gray-500 mb-4 text-sm sm:text-base text-center px-4">No tasks yet. Create your first task!</p>
            <Button
              onClick={() => setShowCreateTask(true)}
              variant="secondary"
              className="flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              <span>Create Task</span>
            </Button>
          </div>
        )}
      </div>

      {/* Create Task Modal */}
      <TaskModal
        isOpen={showCreateTask}
        onClose={() => setShowCreateTask(false)}
        projectId={projectId}
      />

      {/* Edit Project Modal */}
      <CreateProjectModal
        isOpen={showEditProject}
        onClose={() => setShowEditProject(false)}
        project={project}
      />
    </div>
  )
}

export default ProjectDetail


