import storageService from './localStorage.service'

class TimerService {
  constructor() {
    this.intervalId = null
  }

  // Check if it's time to send morning tasks
  checkMorningTaskTime() {
    const config = storageService.getTimerConfig()
    if (!config || !config.enabled) return false

    const now = new Date()
    const [hours, minutes] = config.morningTaskTime.split(':')
    const targetTime = new Date()
    targetTime.setHours(parseInt(hours), parseInt(minutes), 0, 0)

    // Check if current time matches (within 1 minute)
    const diff = Math.abs(now - targetTime)
    return diff < 60000 // Within 1 minute
  }

  // Check if it's time to send EOD form
  checkEODFormTime() {
    const config = storageService.getTimerConfig()
    if (!config || !config.enabled) return false

    const now = new Date()
    const [hours, minutes] = config.eodFormTime.split(':')
    const targetTime = new Date()
    targetTime.setHours(parseInt(hours), parseInt(minutes), 0, 0)

    // Check if current time matches (within 1 minute)
    const diff = Math.abs(now - targetTime)
    return diff < 60000 // Within 1 minute
  }

  // Mock function to send morning tasks
  sendMorningTasks() {
    console.log('🔔 Sending morning task list to employees...')
    const tasks = storageService.getTasks()
    const employees = storageService.getEmployees()

    employees.forEach(employee => {
      const employeeTasks = tasks.filter(t => t.assignedTo === employee.id && t.status !== 'completed')
      if (employeeTasks.length > 0) {
        console.log(`📱 WhatsApp message to ${employee.name}:`)
        console.log(`Good morning! Here are your tasks for today:`)
        employeeTasks.forEach((task, index) => {
          console.log(`${index + 1}. [${task.priority.toUpperCase()}] ${task.title}`)
        })
      }
    })

    // Update last run time
    storageService.updateTimerConfig({ lastRun: new Date().toISOString() })
    
    return {
      success: true,
      message: 'Morning tasks sent to all employees',
      timestamp: new Date().toISOString()
    }
  }

  // Mock function to send EOD form
  sendEODForm() {
    console.log('🔔 Sending EOD form to employees...')
    const employees = storageService.getEmployees()

    employees.forEach(employee => {
      console.log(`📱 WhatsApp form to ${employee.name}:`)
      console.log(`Please update your task status. Reply with task number and YES/NO:`)
    })

    return {
      success: true,
      message: 'EOD form sent to all employees',
      timestamp: new Date().toISOString()
    }
  }

  // Start monitoring
  startMonitoring(onMorningTask, onEODForm) {
    // Check every minute
    this.intervalId = setInterval(() => {
      if (this.checkMorningTaskTime()) {
        const result = this.sendMorningTasks()
        if (onMorningTask) onMorningTask(result)
      }

      if (this.checkEODFormTime()) {
        const result = this.sendEODForm()
        if (onEODForm) onEODForm(result)
      }
    }, 60000) // Check every minute

    console.log('⏰ Timer service started')
  }

  // Stop monitoring
  stopMonitoring() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
      console.log('⏰ Timer service stopped')
    }
  }

  // Get next scheduled time
  getNextScheduledTime() {
    const config = storageService.getTimerConfig()
    if (!config || !config.enabled) return null

    const now = new Date()
    const [morningHours, morningMinutes] = config.morningTaskTime.split(':')
    const [eodHours, eodMinutes] = config.eodFormTime.split(':')

    const morningTime = new Date()
    morningTime.setHours(parseInt(morningHours), parseInt(morningMinutes), 0, 0)

    const eodTime = new Date()
    eodTime.setHours(parseInt(eodHours), parseInt(eodMinutes), 0, 0)

    // Find next upcoming time
    if (now < morningTime) {
      return { type: 'morning', time: morningTime }
    } else if (now < eodTime) {
      return { type: 'eod', time: eodTime }
    } else {
      // Next day morning
      morningTime.setDate(morningTime.getDate() + 1)
      return { type: 'morning', time: morningTime }
    }
  }
}

export default new TimerService()


