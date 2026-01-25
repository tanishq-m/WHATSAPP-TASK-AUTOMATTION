import { formatDateInput } from '../../utils/helpers'

const DatePicker = ({ 
  label, 
  value, 
  onChange, 
  error = '',
  required = false,
  disabled = false,
  min,
  max,
  className = ''
}) => {
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="label">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type="date"
        value={formatDateInput(value)}
        onChange={onChange}
        required={required}
        disabled={disabled}
        min={min}
        max={max}
        className={`input ${error ? 'border-red-500 focus:ring-red-500' : ''} ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}

export default DatePicker


