const ProgressBar = ({ 
  progress = 0, 
  showLabel = true, 
  size = 'md',
  color = 'blue',
  className = ''
}) => {
  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }
  
  const colors = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    orange: 'bg-orange-600',
    red: 'bg-red-600',
    purple: 'bg-purple-600'
  }

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>Progress</span>
          <span className="font-medium">{progress}%</span>
        </div>
      )}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizes[size]}`}>
        <div 
          className={`${sizes[size]} ${colors[color]} rounded-full transition-all duration-300`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>
    </div>
  )
}

export default ProgressBar


