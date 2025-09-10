import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Calendar as BigCalendar, momentLocalizer } from 'react-big-calendar'
import moment from 'moment'
import { ChevronLeftIcon, ChevronRightIcon, CalendarIcon } from '@heroicons/react/24/outline'
import { assignmentsAPI } from '../services/api'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/LoadingSpinner'

// Note: We'll use a simpler calendar implementation since react-big-calendar has moment.js dependency
// For now, let's create a custom calendar component

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

function Calendar() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [assignments, setAssignments] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState(null)

  useEffect(() => {
    fetchCalendarData()
  }, [currentDate])

  const fetchCalendarData = async () => {
    try {
      setLoading(true)
      const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1)
      const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0)
      
      const response = await assignmentsAPI.getCalendar({
        start_date: startOfMonth.toISOString().split('T')[0],
        end_date: endOfMonth.toISOString().split('T')[0],
        include_completed: false
      })

      setAssignments(response.data.assignments_by_date || {})
    } catch (error) {
      console.error('Error fetching calendar data:', error)
      toast.error('Failed to load calendar data')
    } finally {
      setLoading(false)
    }
  }

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    const days = []

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null)
    }

    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day))
    }

    return days
  }

  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate)
    newDate.setMonth(currentDate.getMonth() + direction)
    setCurrentDate(newDate)
  }

  const getAssignmentsForDate = (date) => {
    if (!date) return []
    const dateKey = date.toISOString().split('T')[0]
    return assignments[dateKey] || []
  }

  const isToday = (date) => {
    if (!date) return false
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  const isSelected = (date) => {
    if (!date || !selectedDate) return false
    return date.toDateString() === selectedDate.toDateString()
  }

  const updateAssignmentStatus = async (id, status) => {
    try {
      await assignmentsAPI.updateStatus(id, status)
      toast.success(`Assignment marked as ${status.replace('_', ' ')}`)
      fetchCalendarData() // Refresh calendar
    } catch (error) {
      console.error('Error updating assignment:', error)
      toast.error('Failed to update assignment status')
    }
  }

  if (loading) {
    return <LoadingSpinner message="Loading calendar..." />
  }

  const days = getDaysInMonth()
  const selectedAssignments = selectedDate ? getAssignmentsForDate(selectedDate) : []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">
          Let's stay on the grind.
        </h1>
        <p className="text-lg text-gray-300">
          View your assignments in calendar format
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Calendar */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 card"
        >
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => navigateMonth(-1)}
                className="p-2 text-gray-300 hover:text-white hover:bg-gray-900 rounded-lg transition-colors"
              >
                <ChevronLeftIcon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setCurrentDate(new Date())}
                className="px-3 py-2 text-sm font-medium text-primary-400 hover:text-primary-300 hover:bg-gray-900 rounded-lg transition-colors"
              >
                Today
              </button>
              <button
                onClick={() => navigateMonth(1)}
                className="p-2 text-gray-300 hover:text-white hover:bg-gray-900 rounded-lg transition-colors"
              >
                <ChevronRightIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {/* Day headers */}
            {DAYS.map(day => (
              <div key={day} className="p-3 text-center text-sm font-medium text-gray-500">
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {days.map((date, index) => {
              const dayAssignments = getAssignmentsForDate(date)
              const hasAssignments = dayAssignments.length > 0

              return (
                <motion.div
                  key={index}
                  whileHover={{ scale: 1.05 }}
                  onClick={() => date && setSelectedDate(date)}
                  className={`
                    min-h-[80px] p-2 border border-gray-800 cursor-pointer transition-all duration-200
                    ${date ? 'hover:bg-gray-900' : 'bg-gray-950 cursor-not-allowed'}
                    ${isToday(date) ? 'bg-primary-900/30 border-primary-500' : ''}
                    ${isSelected(date) ? 'bg-primary-800/30 border-primary-400' : ''}
                  `}
                >
                  {date && (
                    <>
                      <div className={`text-sm font-medium mb-1 ${
                        isToday(date) ? 'text-primary-400' : 'text-white'
                      }`}>
                        {date.getDate()}
                      </div>
                      
                      {hasAssignments && (
                        <div className="space-y-1">
                          {dayAssignments.slice(0, 2).map((assignment, idx) => (
                            <div
                              key={idx}
                              className={`text-xs p-1 rounded truncate ${
                                assignment.status === 'completed' ? 'bg-green-100 text-green-800' :
                                assignment.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}
                            >
                              {assignment.title}
                            </div>
                          ))}
                          {dayAssignments.length > 2 && (
                            <div className="text-xs text-gray-500">
                              +{dayAssignments.length - 2} more
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </motion.div>
              )
            })}
          </div>
        </motion.div>

        {/* Assignment Details Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center mb-6">
            <CalendarIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-bold text-white">
              {selectedDate ? (
                `${MONTHS[selectedDate.getMonth()]} ${selectedDate.getDate()}`
              ) : (
                'Select a date'
              )}
            </h3>
          </div>

          {selectedDate ? (
            <div className="space-y-4">
              {selectedAssignments.length === 0 ? (
                <div className="text-center py-8">
                  <CalendarIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No assignments on this date</p>
                </div>
              ) : (
                selectedAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="border border-gray-800 rounded-lg p-4 hover:shadow-lg transition-shadow bg-gray-950"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-white">{assignment.title}</h4>
                      <span className={`badge status-${assignment.status}`}>
                        {assignment.status.replace('_', ' ')}
                      </span>
                    </div>
                    
                    {assignment.description && (
                      <p className="text-sm text-gray-300 mb-3">
                        {assignment.description}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                      <span>Priority: {assignment.priority === 3 ? 'High' : assignment.priority === 2 ? 'Medium' : 'Low'}</span>
                      {assignment.estimated_hours && (
                        <span>~{assignment.estimated_hours}h</span>
                      )}
                    </div>

                    {assignment.status !== 'completed' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => updateAssignmentStatus(assignment.id, 'in_progress')}
                          className="btn-secondary text-xs py-1 px-2"
                          disabled={assignment.status === 'in_progress'}
                        >
                          {assignment.status === 'in_progress' ? 'In Progress' : 'Start'}
                        </button>
                        <button
                          onClick={() => updateAssignmentStatus(assignment.id, 'completed')}
                          className="btn-success text-xs py-1 px-2"
                        >
                          Complete
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <CalendarIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Click on a date to view assignments</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default Calendar
