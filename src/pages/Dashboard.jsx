import { useState } from 'react'
import { Plus, FolderKanban } from 'lucide-react'
import { useApp } from '../context/useApp'
import ProjectCard from '../components/projects/ProjectCard'
import CreateProjectModal from '../components/projects/CreateProjectModal'
import Button from '../components/common/Button'

const Dashboard = () => {
  const { projects } = useApp()
  const [showCreateModal, setShowCreateModal] = useState(false)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            My Projects
          </h1>
          <p className="text-gray-600 mt-1">
            Manage your projects and track progress
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          variant="primary"
          className="flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          <span>New Project</span>
        </Button>
      </div>

      {/* Projects Grid */}
      {projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-16 md:py-24">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <FolderKanban className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No projects yet
          </h3>
          <p className="text-gray-600 mb-6 text-center max-w-sm">
            Get started by creating your first project and adding tasks to it
          </p>
          <Button
            onClick={() => setShowCreateModal(true)}
            variant="primary"
            className="flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>Create Your First Project</span>
          </Button>
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  )
}

export default Dashboard


