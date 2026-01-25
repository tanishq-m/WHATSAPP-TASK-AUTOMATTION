import { Calendar, Users, CheckCircle, Clock } from 'lucide-react'
import { formatDate } from '../../utils/helpers'
import { STATUS } from '../../utils/constants'

const ProjectStats = ({ project, tasks }) => {
  // Calculate unique team members with assigned tasks
  const uniqueAssignedMembers = new Set(
    tasks
      .filter(t => t.assignedTo) // Only tasks with assigned members
      .map(t => t.assignedTo)
  )
  const activeTeamMembers = uniqueAssignedMembers.size
  const totalTeamMembers = project.assignedEmployees?.length || 0

  const stats = [
    {
      label: 'Date Range',
      value: `${formatDate(project.startDate)} - ${formatDate(project.endDate)}`,
      icon: Calendar,
      color: 'text-blue-600'
    },
    {
      label: 'Team Members',
      value: `${activeTeamMembers}/${totalTeamMembers}`,
      icon: Users,
      color: 'text-purple-600'
    },
    {
      label: 'Total Tasks',
      value: tasks.length,
      icon: CheckCircle,
      color: 'text-green-600'
    },
    {
      label: 'In Progress',
      value: tasks.filter(t => 
        t.status === STATUS.IN_PROGRESS || t.status === STATUS.PENDING_VERIFICATION
      ).length,
      icon: Clock,
      color: 'text-orange-600'
    }
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon
        return (
          <div key={index} className="card p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-gray-50 ${stat.color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
                <p className={`text-lg font-semibold ${stat.color} truncate`}>
                  {stat.value}
                </p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ProjectStats


