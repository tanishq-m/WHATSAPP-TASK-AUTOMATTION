/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        priority: {
          high: '#EF4444',
          medium: '#F59E0B',
          low: '#10B981'
        },
        status: {
          ready: '#6B7280',
          progress: '#3B82F6',
          pending: '#F59E0B',
          completed: '#10B981'
        },
        project: {
          blue: '#3B82F6',
          purple: '#8B5CF6',
          pink: '#EC4899',
          teal: '#14B8A6',
          orange: '#F59E0B'
        }
      }
    },
  },
  plugins: [],
}


