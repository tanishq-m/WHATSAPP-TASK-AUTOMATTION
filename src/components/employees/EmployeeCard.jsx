import { Phone, Briefcase, Edit2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import EmployeeAvatar from './EmployeeAvatar'

const EmployeeCard = ({ employee, onEdit, onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleEdit = (e) => {
    e.stopPropagation();
    onEdit(employee);
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    onDelete(employee);
  };

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
            
            {/* Action Buttons */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={handleEdit}
                className="p-2 hover:bg-gray-100 rounded-lg tap-target transition-colors"
                title="Edit employee"
              >
                <Edit2 className="w-4 h-4 text-gray-500 hover:text-blue-600" />
              </button>
              <button
                onClick={handleDelete}
                className="p-2 hover:bg-red-50 rounded-lg tap-target transition-colors"
                title="Delete employee"
              >
                <Trash2 className="w-4 h-4 text-gray-500 hover:text-red-600" />
              </button>
            </div>
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


