import { useState } from 'react'
import { User, X } from 'lucide-react'
import { useApp } from '../../context/useApp'
import Modal from '../common/Modal'
import Button from '../common/Button'

const FilterDropdown = ({ selectedEmployee, onSelect }) => {
  const { employees } = useApp()
  const [showModal, setShowModal] = useState(false)

  // Get selected employee name
  const selectedEmployeeName = selectedEmployee 
    ? employees.find(e => e.id === selectedEmployee)?.name 
    : 'All Members'

  const handleSelect = (employeeId) => {
    onSelect(employeeId)
    setShowModal(false)
  }

  return (
    <>
      {/* Mobile/Desktop Filter Button */}
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-smooth tap-target"
      >
        <User className="w-4 h-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">
          Filter by: {selectedEmployeeName}
        </span>
      </button>

      {/* Filter Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Filter by Team Member"
        size="sm"
      >
        <div className="space-y-2">
          {/* All Members Option */}
          <label
            className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-smooth tap-target ${
              !selectedEmployee 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <input
              type="radio"
              name="filter-employee"
              checked={!selectedEmployee}
              onChange={() => handleSelect(null)}
              className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
            />
            <div className="flex-1">
              <div className="font-medium text-gray-900">All Members</div>
              <div className="text-sm text-gray-500">Show all tasks</div>
            </div>
          </label>

          {/* Individual Employees */}
          {employees.map((employee) => (
            <label
              key={employee.id}
              className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-smooth tap-target ${
                selectedEmployee === employee.id 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="filter-employee"
                checked={selectedEmployee === employee.id}
                onChange={() => handleSelect(employee.id)}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">{employee.name}</div>
                <div className="text-sm text-gray-500">{employee.role}</div>
              </div>
            </label>
          ))}
        </div>

        <div className="mt-6">
          <Button
            variant="primary"
            fullWidth
            onClick={() => setShowModal(false)}
          >
            Apply Filter
          </Button>
        </div>
      </Modal>
    </>
  )
}

export default FilterDropdown
