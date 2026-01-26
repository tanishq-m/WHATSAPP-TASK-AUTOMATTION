import { Users, Plus, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { useApp } from '../context/useApp'
import EmployeeCard from '../components/employees/EmployeeCard'
import EmployeeModal from '../components/employees/EmployeeModal'
import ConfirmDialog from '../components/common/ConfirmDialog'
import Button from '../components/common/Button'

const Employees = () => {
  const { employees, deleteEmployee, getTasks } = useApp()
  const [showEmployeeModal, setShowEmployeeModal] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [employeeToDelete, setEmployeeToDelete] = useState(null)

  const handleAddEmployee = () => {
    setSelectedEmployee(null)
    setShowEmployeeModal(true)
  }

  const handleEditEmployee = (employee) => {
    setSelectedEmployee(employee)
    setShowEmployeeModal(true)
  }

  const handleDeleteEmployee = (employee) => {
    setEmployeeToDelete(employee)
    setShowDeleteConfirm(true)
  }

  const confirmDelete = async () => {
    if (employeeToDelete) {
      await deleteEmployee(employeeToDelete.id)
      setShowDeleteConfirm(false)
      setEmployeeToDelete(null)
    }
  }

  const getTaskCountForEmployee = (employeeId) => {
    const tasks = getTasks()
    return tasks.filter(task => task.assignedTo === employeeId).length
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
            Manage your team members and their roles
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

      {/* Employee Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Total Members</p>
          <p className="text-2xl font-bold text-gray-900">{employees.filter(e => e != null).length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Developers</p>
          <p className="text-2xl font-bold text-blue-600">
            {employees.filter(e => e?.role === 'Developer').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Designers</p>
          <p className="text-2xl font-bold text-purple-600">
            {employees.filter(e => e?.role === 'Designer').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-600 mb-1">Testers</p>
          <p className="text-2xl font-bold text-green-600">
            {employees.filter(e => e?.role === 'Tester').length}
          </p>
        </div>
      </div>

      {/* Employees List */}
      {employees.filter(e => e != null).length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.filter(e => e != null).map((employee) => (
            <EmployeeCard 
              key={employee.id} 
              employee={employee}
              onEdit={handleEditEmployee}
              onDelete={handleDeleteEmployee}
            />
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
            Add your first team member to get started with task assignments
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

      {/* Employee Modal */}
      <EmployeeModal
        isOpen={showEmployeeModal}
        onClose={() => setShowEmployeeModal(false)}
        employee={selectedEmployee}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={confirmDelete}
        title="Delete Employee"
        message={
          employeeToDelete 
            ? `Are you sure you want to delete "${employeeToDelete.name}"? ${
                getTaskCountForEmployee(employeeToDelete.id) > 0
                  ? `This employee has ${getTaskCountForEmployee(employeeToDelete.id)} active tasks that will be marked as unassigned.`
                  : ''
              }`
            : ''
        }
        confirmText="Delete Employee"
        variant="danger"
      />
    </div>
  )
}

export default Employees


