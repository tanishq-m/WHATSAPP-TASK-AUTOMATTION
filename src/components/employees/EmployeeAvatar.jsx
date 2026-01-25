import { getInitials, getAvatarColor } from '../../utils/helpers'

const EmployeeAvatar = ({ employee, size = 'md', showName = false }) => {
  if (!employee) {
    return (
      <div className={`${getSizeClass(size)} bg-gray-300 rounded-full flex items-center justify-center`}>
        <span className={`${getTextSizeClass(size)} text-gray-600 font-medium`}>?</span>
      </div>
    )
  }

  const initials = getInitials(employee.name)
  const colorClass = getAvatarColor(employee.name)

  return (
    <div className={`flex items-center gap-2 ${showName ? '' : 'inline-flex'}`}>
      <div 
        className={`${getSizeClass(size)} ${colorClass} rounded-full flex items-center justify-center flex-shrink-0`}
        title={employee.name}
      >
        <span className={`${getTextSizeClass(size)} text-white font-medium`}>
          {initials}
        </span>
      </div>
      {showName && (
        <span className="text-sm font-medium text-gray-900 truncate">
          {employee.name}
        </span>
      )}
    </div>
  )
}

const getSizeClass = (size) => {
  const sizes = {
    xs: 'w-6 h-6',
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  }
  return sizes[size] || sizes.md
}

const getTextSizeClass = (size) => {
  const textSizes = {
    xs: 'text-xs',
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
    xl: 'text-xl'
  }
  return textSizes[size] || textSizes.md
}

export default EmployeeAvatar


