import Modal from './Modal'
import Button from './Button'
import { AlertTriangle } from 'lucide-react'

const ConfirmDialog = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = 'Confirm Action', 
  message = 'Are you sure you want to proceed?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger' // 'danger', 'primary', 'secondary'
}) => {
  const handleConfirm = () => {
    onConfirm()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div onClick={(e) => e.stopPropagation()}>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={title}
        size="sm"
      >
      <div className="space-y-4">
        {/* Warning Icon */}
        <div className="flex items-center justify-center">
          <div className={`p-3 rounded-full ${
            variant === 'danger' ? 'bg-red-100' : 'bg-yellow-100'
          }`}>
            <AlertTriangle className={`w-8 h-8 ${
              variant === 'danger' ? 'text-red-600' : 'text-yellow-600'
            }`} />
          </div>
        </div>

        {/* Message */}
        <div className="text-center">
          <p className="text-gray-700 whitespace-pre-line">
            {message}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
          <Button 
            type="button" 
            variant="secondary" 
            onClick={onClose}
            fullWidth
          >
            {cancelText}
          </Button>
          <Button 
            type="button" 
            variant={variant}
            onClick={handleConfirm}
            fullWidth
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
    </div>
  )
}

export default ConfirmDialog
