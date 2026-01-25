import { Phone, Briefcase, Eye } from 'lucide-react'
import EmployeeAvatar from './EmployeeAvatar'

const EmployeeCard = ({ employee }) => {
  return (
    <div className="card-hover p-4">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <EmployeeAvatar employee={employee} size="lg" />
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-semibold text-gray-900 truncate">
              {employee.name}
            </h3>
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 flex-shrink-0">
              <Eye className="w-3 h-3" />
              View Only
            </span>
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Phone className="w-4 h-4" />
              <span>{employee.phone}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Briefcase className="w-4 h-4" />
              <span>{employee.role}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmployeeCard


