import { useApp } from '../../context/useApp'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'

const Toast = () => {
  const { toast, showToast } = useApp()

  if (!toast.show) return null

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />
  }

  const styles = {
    success: 'toast-success',
    error: 'toast-error',
    info: 'toast-info'
  }

  return (
    <div className={`${styles[toast.type]} flex items-center gap-3`}>
      {icons[toast.type]}
      <span className="flex-1">{toast.message}</span>
      <button 
        onClick={() => showToast('', 'info')}
        className="hover:opacity-80 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

export default Toast


