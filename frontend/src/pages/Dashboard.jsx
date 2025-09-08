import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  PlusIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  CalendarDaysIcon,
  AcademicCapIcon 
} from '@heroicons/react/24/outline'
import { format, isToday, isTomorrow, isThisWeek } from 'date-fns'
import toast from 'react-hot-toast'
import { assignmentsAPI, classesAPI } from '../services/api'
import AssignmentCard from '../components/AssignmentCard'
import LoadingSpinner from '../components/LoadingSpinner'
import EditAssignmentModal from '../components/EditAssignmentModal'

const statusColors = {
  not_started: 'text-red-400 bg-red-900/30',
  in_progress: 'text-yellow-400 bg-yellow-900/30',
  completed: 'text-green-400 bg-green-900/30',
}

const priorityIcons = {
  1: ClockIcon,
  2: ExclamationTriangleIcon,
  3: ExclamationTriangleIcon,
}

function Dashboard() {
  const [assignments, setAssignments] = useState([])
  const [classes, setClasses] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingAssignment, setEditingAssignment] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [stats, setStats] = useState({
    total: 0,
    notStarted: 0,
    inProgress: 0,
    completed: 0,
    dueToday: 0,
    dueTomorrow: 0,
    dueThisWeek: 0,
  })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [assignmentsRes, classesRes] = await Promise.all([
        assignmentsAPI.getAll({ include_completed: false }),
        classesAPI.getAll()
      ])

      setAssignments(assignmentsRes.data)
      setClasses(classesRes.data)
      calculateStats(assignmentsRes.data)
    } catch (error) {
      console.error('Error fetching data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const calculateStats = (assignmentList) => {
    const now = new Date()
    const stats = {
      total: assignmentList.length,
      notStarted: assignmentList.filter(a => a.status === 'not_started').length,
      inProgress: assignmentList.filter(a => a.status === 'in_progress').length,
      completed: assignmentList.filter(a => a.status === 'completed').length,
      dueToday: assignmentList.filter(a => isToday(new Date(a.due_date))).length,
      dueTomorrow: assignmentList.filter(a => isTomorrow(new Date(a.due_date))).length,
      dueThisWeek: assignmentList.filter(a => isThisWeek(new Date(a.due_date))).length,
    }
    setStats(stats)
  }

  const updateAssignmentStatus = async (id, status) => {
    try {
      await assignmentsAPI.updateStatus(id, status)
      toast.success(`Assignment marked as ${status.replace('_', ' ')}`)
      fetchData() // Refresh data
    } catch (error) {
      console.error('Error updating assignment:', error)
      toast.error('Failed to update assignment status')
    }
  }

  const handleEditAssignment = (assignment) => {
    setEditingAssignment(assignment)
    setShowEditModal(true)
  }

  const handleSaveAssignment = async (assignmentId, updateData) => {
    try {
      await assignmentsAPI.update(assignmentId, updateData)
      toast.success('Assignment updated successfully!')
      fetchData() // Refresh data
      setShowEditModal(false)
      setEditingAssignment(null)
    } catch (error) {
      console.error('Error updating assignment:', error)
      toast.error('Failed to update assignment')
    }
  }

  const handleCloseEditModal = () => {
    setShowEditModal(false)
    setEditingAssignment(null)
  }

  const upcomingAssignments = assignments
    .filter(a => a.status !== 'completed')
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
    .slice(0, 5)

  const recentAssignments = assignments
    .filter(a => isThisWeek(new Date(a.due_date)))
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome back! 📚
        </h1>
        <p className="text-lg text-gray-300">
          Here's what's on your plate today
        </p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
      >
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-primary-100 rounded-lg">
              <AcademicCapIcon className="h-6 w-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Total Assignments</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <ClockIcon className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">In Progress</p>
              <p className="text-2xl font-bold text-white">{stats.inProgress}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Completed</p>
              <p className="text-2xl font-bold text-white">{stats.completed}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <CalendarDaysIcon className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Due Today</p>
              <p className="text-2xl font-bold text-white">{stats.dueToday}</p>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Assignments */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">Upcoming Assignments</h2>
            <PlusIcon className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            {upcomingAssignments.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-3" />
                <p className="text-gray-500">All caught up! 🎉</p>
              </div>
            ) : (
              upcomingAssignments.map((assignment) => (
                <AssignmentCard
                  key={assignment.id}
                  assignment={assignment}
                  onStatusUpdate={updateAssignmentStatus}
                  onEdit={handleEditAssignment}
                  compact
                />
              ))
            )}
          </div>
        </motion.div>

        {/* This Week's Assignments */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">This Week</h2>
            <CalendarDaysIcon className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            {recentAssignments.length === 0 ? (
              <div className="text-center py-8">
                <CalendarDaysIcon className="h-12 w-12 text-blue-500 mx-auto mb-3" />
                <p className="text-gray-500">No assignments this week</p>
              </div>
            ) : (
              recentAssignments.map((assignment) => (
                <div key={assignment.id} className="border-l-4 border-primary-400 pl-4 py-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-white">{assignment.title}</h3>
                      <p className="text-sm text-gray-500">
                        Due {format(new Date(assignment.due_date), 'EEE, MMM d')}
                      </p>
                    </div>
                    <span className={`badge status-${assignment.status}`}>
                      {assignment.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="mt-8 card"
      >
        <h2 className="text-xl font-bold text-white mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn-primary flex items-center justify-center py-3">
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Assignment
          </button>
          <button className="btn-secondary flex items-center justify-center py-3">
            <AcademicCapIcon className="h-5 w-5 mr-2" />
            Create Class
          </button>
          <button className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-medium py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              ✨
            </motion.div>
            <span className="ml-2">AI Assistant</span>
          </button>
        </div>
      </motion.div>

      {/* Edit Assignment Modal */}
      <EditAssignmentModal
        assignment={editingAssignment}
        classes={classes}
        isOpen={showEditModal}
        onClose={handleCloseEditModal}
        onSave={handleSaveAssignment}
      />
    </div>
  )
}

export default Dashboard
