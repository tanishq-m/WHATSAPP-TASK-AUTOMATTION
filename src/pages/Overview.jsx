import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/useApp'
import * as apiService from '../services/api.service'
import { Home, FolderKanban, CheckCircle, Clock, AlertCircle, TrendingUp } from 'lucide-react'
import AttentionCard from '../components/dashboard/AttentionCard'
import ProjectSummaryCard from '../components/dashboard/ProjectSummaryCard'

const Overview = () => {
  const { showToast } = useApp()
  const navigate = useNavigate()
  
  const [summary, setSummary] = useState(null)
  const [projects, setProjects] = useState([])
  const [attentionItems, setAttentionItems] = useState([])
  const [loading, setLoading] = useState(true)
  
  // Fetch data on mount
  useEffect(() => {
    loadDashboardData()
  }, [])
  
  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch all dashboard data
      const [summaryData, projectsData, attentionData] = await Promise.all([
        apiService.getDashboardSummary(),
        apiService.getProjectsOverview(),
        apiService.getAttentionItems()
      ])
      
      setSummary(summaryData)
      setProjects(projectsData)
      setAttentionItems(attentionData)
    } catch (error) {
      console.error('Error loading dashboard:', error)
      showToast('Failed to load dashboard data', 'error')
      
      // Set empty state on error
      setSummary({
        totalProjects: 0,
        totalTasks: 0,
        tasksByStatus: {},
        completionRate: 0
      })
      setProjects([])
      setAttentionItems([])
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          Dashboard Overview
        </h1>
        <p className="text-gray-600 mt-1">
          Bird's eye view of all your projects
        </p>
      </div>
      
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading dashboard...</p>
        </div>
      ) : (
        <>
          {/* Summary Stats - 4 cards in grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {/* Total Projects */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <FolderKanban className="w-5 h-5 text-blue-600" />
                <span className="text-2xl font-bold text-gray-900">
                  {summary?.totalProjects || 0}
                </span>
              </div>
              <p className="text-sm text-gray-600">Projects</p>
            </div>
            
            {/* Total Tasks */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-2xl font-bold text-gray-900">
                  {summary?.totalTasks || 0}
                </span>
              </div>
              <p className="text-sm text-gray-600">Tasks</p>
            </div>
            
            {/* Completion Rate */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                <span className="text-2xl font-bold text-gray-900">
                  {summary?.completionRate || 0}%
                </span>
              </div>
              <p className="text-sm text-gray-600">Complete</p>
            </div>
            
            {/* Team Size */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-5 h-5 text-orange-600" />
                <span className="text-2xl font-bold text-gray-900">
                  {summary?.totalEmployees || 0}
                </span>
              </div>
              <p className="text-sm text-gray-600">Team Members</p>
            </div>
          </div>
          
          {/* Needs Attention Section */}
          {attentionItems.length > 0 && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Needs Attention ({attentionItems.length})
              </h2>
              <div className="space-y-3">
                {attentionItems.map((item) => (
                  <AttentionCard
                    key={item.taskId}
                    item={item}
                    onActionComplete={loadDashboardData}
                  />
                ))}
              </div>
            </div>
          )}
          
          {attentionItems.length === 0 && (
            <div className="mb-8 card p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
              <p className="text-gray-600">All caught up! 🎉 No tasks need attention right now.</p>
            </div>
          )}
          
          {/* All Projects Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                All Projects ({projects.length})
              </h2>
              <button
                onClick={() => navigate('/projects')}
                className="btn-secondary text-sm"
              >
                Manage Projects
              </button>
            </div>
            
            {projects.length === 0 ? (
              <div className="card p-8 text-center">
                <FolderKanban className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 mb-4">No projects yet</p>
                <button
                  onClick={() => navigate('/projects')}
                  className="btn-primary"
                >
                  Create Your First Project
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <ProjectSummaryCard
                    key={project.projectId}
                    project={project}
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Overview
