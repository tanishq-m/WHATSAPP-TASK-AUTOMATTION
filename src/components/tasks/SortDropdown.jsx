import { useState } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown, Star, User } from 'lucide-react'
import Modal from '../common/Modal'
import Button from '../common/Button'

const SortDropdown = ({ sortBy, onSortChange }) => {
  const [showModal, setShowModal] = useState(false)

  const sortOptions = [
    { id: 'priority', label: 'Priority (High → Low)', icon: Star },
    { id: 'dueDate-asc', label: 'Due Date (Earliest)', icon: ArrowUp },
    { id: 'dueDate-desc', label: 'Due Date (Latest)', icon: ArrowDown },
    { id: 'assignedTo', label: 'Assigned To (A-Z)', icon: User },
  ]

  const selectedOption = sortOptions.find(opt => opt.id === sortBy)
  const Icon = selectedOption?.icon || ArrowUpDown

  const handleSelect = (sortId) => {
    onSortChange(sortId)
    setShowModal(false)
  }

  return (
    <>
      {/* Mobile/Desktop Sort Button */}
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-smooth tap-target"
      >
        <Icon className="w-4 h-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">
          Sort: {selectedOption?.label || 'Select'}
        </span>
      </button>

      {/* Sort Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Sort Tasks By"
        size="sm"
      >
        <div className="space-y-2">
          {sortOptions.map((option) => {
            const OptionIcon = option.icon
            return (
              <label
                key={option.id}
                className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-smooth tap-target ${
                  sortBy === option.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="sort-option"
                  checked={sortBy === option.id}
                  onChange={() => handleSelect(option.id)}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <OptionIcon className="w-5 h-5 text-gray-500" />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{option.label}</div>
                </div>
              </label>
            )
          })}
        </div>

        <div className="mt-6">
          <Button
            variant="primary"
            fullWidth
            onClick={() => setShowModal(false)}
          >
            Apply Sorting
          </Button>
        </div>
      </Modal>
    </>
  )
}

export default SortDropdown
