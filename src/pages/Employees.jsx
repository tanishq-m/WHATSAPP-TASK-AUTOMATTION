import { Users, Plus, UserPlus } from 'lucide-react'
import { useApp } from '../context/useApp'
import EmployeeCard from '../components/employees/EmployeeCard'
import Button from '../components/common/Button'

const Employees = () => {
  const { employees, showToast } = useApp()

  const handleAddEmployee = () => {
    showToast('Add employee feature coming in Phase 2!', 'info')
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
            Team Members
          </h1>
          <p className="text-gray-600 mt-1">
            View and manage your team
          </p>
        </div>
        <Button
          onClick={handleAddEmployee}
          variant="primary"
          className="flex items-center gap-2"
        >
          <UserPlus className="w-5 h-5" />
          <span>Add Employee</span>
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex gap-3">
        <Users className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">MVP Mode - View Only</p>
          <p>
            These employees are hardcoded for the MVP. In Phase 2, you'll be able to add, 
            edit, and manage employees directly.
          </p>
        </div>
      </div>

      {/* Employee Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Total Members</p>
          <p className="text-2xl font-bold text-gray-900">{employees.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Developers</p>
          <p className="text-2xl font-bold text-blue-600">
            {employees.filter(e => e.role === 'Developer').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Designers</p>
          <p className="text-2xl font-bold text-purple-600">
            {employees.filter(e => e.role === 'Designer').length}
          </p>
        </div>
      </div>

      {/* Employees List */}
      {employees.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.map((employee) => (
            <EmployeeCard key={employee.id} employee={employee} />
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-16 md:py-24">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Users className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No employees yet
          </h3>
          <p className="text-gray-600 mb-6 text-center max-w-sm">
            Add your first team member to get started
          </p>
          <Button
            onClick={handleAddEmployee}
            variant="primary"
            className="flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>Add First Employee</span>
          </Button>
        </div>
      )}
    </div>
  )
}

export default Employees


