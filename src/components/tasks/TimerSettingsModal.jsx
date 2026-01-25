import { useState, useEffect } from 'react'
import { Clock, Bell, AlertCircle } from 'lucide-react'
import Modal from '../common/Modal'
import Button from '../common/Button'
import { useApp } from '../../context/useApp'

const TimerSettingsModal = ({ isOpen, onClose }) => {
  const { timerConfig, updateTimerConfig } = useApp()
  
  const [formData, setFormData] = useState({
    morningTaskTime: '09:00',
    eodFormTime: '18:00',
    enabled: true
  })

  useEffect(() => {
    if (timerConfig) {
      setFormData({
        morningTaskTime: timerConfig.morningTaskTime || '09:00',
        eodFormTime: timerConfig.eodFormTime || '18:00',
        enabled: timerConfig.enabled !== undefined ? timerConfig.enabled : true
      })
    }
  }, [timerConfig])

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    updateTimerConfig(formData)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Timer Settings" size="md">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Info Alert */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">WhatsApp Integration (Phase 2)</p>
            <p>Configure when tasks should be automatically sent to employees via WhatsApp.</p>
          </div>
        </div>

        {/* Enable/Disable Toggle */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <Bell className="w-5 h-5 text-gray-600" />
            <div>
              <p className="font-medium text-gray-900">Enable Automatic Sending</p>
              <p className="text-sm text-gray-600">Send tasks and forms automatically</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.enabled}
              onChange={(e) => handleChange('enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Morning Task Time */}
        <div>
          <label className="label flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Morning Task List Time
          </label>
          <input
            type="time"
            value={formData.morningTaskTime}
            onChange={(e) => handleChange('morningTaskTime', e.target.value)}
            disabled={!formData.enabled}
            className="input"
          />
          <p className="mt-1 text-sm text-gray-500">
            Employees will receive their daily task list at this time
          </p>
        </div>

        {/* EOD Form Time */}
        <div>
          <label className="label flex items-center gap-2">
            <Clock className="w-4 h-4" />
            End of Day Form Time
          </label>
          <input
            type="time"
            value={formData.eodFormTime}
            onChange={(e) => handleChange('eodFormTime', e.target.value)}
            disabled={!formData.enabled}
            className="input"
          />
          <p className="mt-1 text-sm text-gray-500">
            Employees will receive a form to update task status at this time
          </p>
        </div>

        {/* Example Preview */}
        {formData.enabled && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm font-medium text-green-800 mb-2">Example Schedule:</p>
            <ul className="text-sm text-green-700 space-y-1">
              <li>• {formData.morningTaskTime} - Send task list to all employees</li>
              <li>• {formData.eodFormTime} - Send status update form</li>
            </ul>
          </div>
        )}

        <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
          <Button 
            type="button" 
            variant="secondary" 
            onClick={onClose}
            fullWidth
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="primary"
            fullWidth
          >
            Save Settings
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default TimerSettingsModal


