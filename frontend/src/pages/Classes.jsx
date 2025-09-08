import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  PlusIcon, 
  AcademicCapIcon, 
  TrashIcon, 
  PencilIcon,
  BookOpenIcon 
} from '@heroicons/react/24/outline'
import { classesAPI, assignmentsAPI } from '../services/api'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/LoadingSpinner'
import AssignmentCard from '../components/AssignmentCard'
import EditClassModal from '../components/EditClassModal'
import EditAssignmentModal from '../components/EditAssignmentModal'

function Classes() {
  const [classes, setClasses] = useState([])
  const [assignments, setAssignments] = useState([])
  const [selectedClass, setSelectedClass] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showClassForm, setShowClassForm] = useState(false)
  const [showAssignmentForm, setShowAssignmentForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    full_name: '',
    description: '',
    color: '#3B82F6'
  })
  const [assignmentForm, setAssignmentForm] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 2,
    estimated_hours: ''
  })

  // Edit modal states
  const [editingClass, setEditingClass] = useState(null)
  const [showEditClassModal, setShowEditClassModal] = useState(false)
  const [editingAssignment, setEditingAssignment] = useState(null)
  const [showEditAssignmentModal, setShowEditAssignmentModal] = useState(false)

  const colors = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
    '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
  ]

  useEffect(() => {
    fetchClasses()
  }, [])

  useEffect(() => {
    if (selectedClass) {
      fetchAssignments(selectedClass.id)
    }
  }, [selectedClass])

  const fetchClasses = async () => {
    try {
      setLoading(true)
      const response = await classesAPI.getAll()
      setClasses(response.data)
      if (response.data.length > 0 && !selectedClass) {
        setSelectedClass(response.data[0])
      }
    } catch (error) {
      console.error('Error fetching classes:', error)
      toast.error('Failed to load classes')
    } finally {
      setLoading(false)
    }
  }

  const fetchAssignments = async (classId) => {
    try {
      const response = await assignmentsAPI.getAll({ 
        class_id: classId,
        include_completed: true 
      })
      setAssignments(response.data)
    } catch (error) {
      console.error('Error fetching assignments:', error)
      toast.error('Failed to load assignments')
    }
  }

  const handleCreateClass = async (e) => {
    e.preventDefault()
    try {
      const response = await classesAPI.create(formData)
      setClasses([...classes, response.data])
      setShowClassForm(false)
      setFormData({ name: '', full_name: '', description: '', color: '#3B82F6' })
      toast.success('Class created successfully!')
    } catch (error) {
      console.error('Error creating class:', error)
      toast.error('Failed to create class')
    }
  }

  const handleCreateAssignment = async (e) => {
    e.preventDefault()
    if (!selectedClass) {
      toast.error('Please select a class first')
      return
    }

    try {
      const assignmentData = {
        ...assignmentForm,
        class_id: selectedClass.id,
        estimated_hours: assignmentForm.estimated_hours ? parseInt(assignmentForm.estimated_hours) : null
      }
      
      const response = await assignmentsAPI.create(assignmentData)
      setAssignments([...assignments, response.data])
      setShowAssignmentForm(false)
      setAssignmentForm({
        title: '',
        description: '',
        due_date: '',
        priority: 2,
        estimated_hours: ''
      })
      toast.success('Assignment created successfully!')
    } catch (error) {
      console.error('Error creating assignment:', error)
      toast.error('Failed to create assignment')
    }
  }

  const handleDeleteClass = async (classId) => {
    if (!confirm('Are you sure? This will delete all assignments in this class.')) {
      return
    }

    try {
      await classesAPI.delete(classId)
      const updatedClasses = classes.filter(c => c.id !== classId)
      setClasses(updatedClasses)
      
      if (selectedClass?.id === classId) {
        setSelectedClass(updatedClasses[0] || null)
        setAssignments([])
      }
      
      toast.success('Class deleted successfully!')
    } catch (error) {
      console.error('Error deleting class:', error)
      toast.error('Failed to delete class')
    }
  }

  // Edit functions
  const handleEditClass = (classData) => {
    setEditingClass(classData)
    setShowEditClassModal(true)
  }

  const handleSaveClass = async (classId, updateData) => {
    try {
      const response = await classesAPI.update(classId, updateData)
      const updatedClasses = classes.map(c => 
        c.id === classId ? response.data : c
      )
      setClasses(updatedClasses)
      
      if (selectedClass?.id === classId) {
        setSelectedClass(response.data)
      }
      
      toast.success('Class updated successfully!')
      setShowEditClassModal(false)
      setEditingClass(null)
    } catch (error) {
      console.error('Error updating class:', error)
      toast.error('Failed to update class')
    }
  }

  const handleCloseEditClassModal = () => {
    setShowEditClassModal(false)
    setEditingClass(null)
  }

  const handleEditAssignment = (assignment) => {
    setEditingAssignment(assignment)
    setShowEditAssignmentModal(true)
  }

  const handleSaveAssignment = async (assignmentId, updateData) => {
    try {
      await assignmentsAPI.update(assignmentId, updateData)
      toast.success('Assignment updated successfully!')
      if (selectedClass) {
        fetchAssignments(selectedClass.id)
      }
      setShowEditAssignmentModal(false)
      setEditingAssignment(null)
    } catch (error) {
      console.error('Error updating assignment:', error)
      toast.error('Failed to update assignment')
    }
  }

  const handleCloseEditAssignmentModal = () => {
    setShowEditAssignmentModal(false)
    setEditingAssignment(null)
  }

  const updateAssignmentStatus = async (id, status) => {
    try {
      await assignmentsAPI.updateStatus(id, status)
      toast.success(`Assignment marked as ${status.replace('_', ' ')}`)
      if (selectedClass) {
        fetchAssignments(selectedClass.id)
      }
    } catch (error) {
      console.error('Error updating assignment:', error)
      toast.error('Failed to update assignment status')
    }
  }

  const deleteAssignment = async (id) => {
    if (!confirm('Are you sure you want to delete this assignment?')) {
      return
    }

    try {
      await assignmentsAPI.delete(id)
      setAssignments(assignments.filter(a => a.id !== id))
      toast.success('Assignment deleted successfully!')
    } catch (error) {
      console.error('Error deleting assignment:', error)
      toast.error('Failed to delete assignment')
    }
  }

  if (loading) {
    return <LoadingSpinner message="Loading classes..." />
  }

  const activeAssignments = assignments.filter(a => a.status !== 'completed')
  const completedAssignments = assignments.filter(a => a.status === 'completed')

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Classes & Subjects 📚
            </h1>
            <p className="text-lg text-gray-300">
              Organize your assignments by class or subject
            </p>
          </div>
          <button
            onClick={() => setShowClassForm(true)}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Class
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Classes Sidebar */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <div className="card">
            <h2 className="text-lg font-bold text-white mb-4">Your Classes</h2>
            
            {classes.length === 0 ? (
              <div className="text-center py-8">
                <BookOpenIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500 mb-4">No classes yet</p>
                <button
                  onClick={() => setShowClassForm(true)}
                  className="btn-primary text-sm"
                >
                  Create Your First Class
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {classes.map((classItem) => (
                  <motion.div
                    key={classItem.id}
                    whileHover={{ scale: 1.02 }}
                    onClick={() => setSelectedClass(classItem)}
                    className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedClass?.id === classItem.id
                        ? 'bg-primary-900/30 border-2 border-primary-400'
                        : 'bg-gray-900 hover:bg-gray-800 border-2 border-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: classItem.color }}
                        />
                        <div>
                          <h3 className="font-medium text-white">{classItem.name}</h3>
                          {classItem.full_name && (
                            <p className="text-xs text-gray-400 truncate">
                              {classItem.full_name}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex space-x-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleEditClass(classItem)
                          }}
                          className="text-gray-400 hover:text-blue-600 transition-colors"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteClass(classItem.id)
                          }}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </motion.div>

        {/* Assignments Content */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-3"
        >
          {selectedClass ? (
            <div>
              {/* Class Header */}
              <div className="card mb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: selectedClass.color + '20' }}
                    >
                      <AcademicCapIcon 
                        className="h-6 w-6"
                        style={{ color: selectedClass.color }}
                      />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-white">
                        {selectedClass.name}
                      </h2>
                      {selectedClass.full_name && (
                        <p className="text-gray-300">{selectedClass.full_name}</p>
                      )}
                      {selectedClass.description && (
                        <p className="text-sm text-gray-500 mt-1">
                          {selectedClass.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setShowAssignmentForm(true)}
                    className="btn-primary flex items-center"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Add Assignment
                  </button>
                </div>
              </div>

              {/* Active Assignments */}
              <div className="mb-8">
                <h3 className="text-lg font-bold text-white mb-4">
                  Active Assignments ({activeAssignments.length})
                </h3>
                {activeAssignments.length === 0 ? (
                  <div className="card text-center py-8">
                    <AcademicCapIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 mb-4">No active assignments</p>
                    <button
                      onClick={() => setShowAssignmentForm(true)}
                      className="btn-primary"
                    >
                      Add Your First Assignment
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {activeAssignments.map((assignment) => (
                      <AssignmentCard
                        key={assignment.id}
                        assignment={assignment}
                        onStatusUpdate={updateAssignmentStatus}
                        onDelete={deleteAssignment}
                        onEdit={handleEditAssignment}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Completed Assignments */}
              {completedAssignments.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">
                    Completed ({completedAssignments.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {completedAssignments.map((assignment) => (
                      <AssignmentCard
                        key={assignment.id}
                        assignment={assignment}
                        onStatusUpdate={updateAssignmentStatus}
                        onDelete={deleteAssignment}
                        onEdit={handleEditAssignment}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <BookOpenIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">
                No class selected
              </h3>
              <p className="text-gray-300 mb-6">
                Create a class or select one from the sidebar to get started
              </p>
              <button
                onClick={() => setShowClassForm(true)}
                className="btn-primary"
              >
                Create Your First Class
              </button>
            </div>
          )}
        </motion.div>
      </div>

      {/* Class Form Modal */}
      {showClassForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gray-950 rounded-lg p-6 w-full max-w-md mx-4"
          >
            <h3 className="text-lg font-bold text-white mb-4">Add New Class</h3>
            <form onSubmit={handleCreateClass}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Class Code *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    placeholder="e.g., ICS 211"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="input-field"
                    placeholder="e.g., Introduction to Computer Science II"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input-field"
                    rows={3}
                    placeholder="Brief description of the class"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Color
                  </label>
                  <div className="flex space-x-2">
                    {colors.map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setFormData({ ...formData, color })}
                        className={`w-8 h-8 rounded-full border-2 ${
                          formData.color === color ? 'border-gray-900' : 'border-gray-300'
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowClassForm(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  Create Class
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Assignment Form Modal */}
      {showAssignmentForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gray-950 rounded-lg p-6 w-full max-w-md mx-4"
          >
            <h3 className="text-lg font-bold text-white mb-4">Add New Assignment</h3>
            <form onSubmit={handleCreateAssignment}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={assignmentForm.title}
                    onChange={(e) => setAssignmentForm({ ...assignmentForm, title: e.target.value })}
                    className="input-field"
                    placeholder="Assignment title"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={assignmentForm.description}
                    onChange={(e) => setAssignmentForm({ ...assignmentForm, description: e.target.value })}
                    className="input-field"
                    rows={3}
                    placeholder="Assignment details"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Due Date *
                  </label>
                  <input
                    type="datetime-local"
                    value={assignmentForm.due_date}
                    onChange={(e) => setAssignmentForm({ ...assignmentForm, due_date: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={assignmentForm.priority}
                    onChange={(e) => setAssignmentForm({ ...assignmentForm, priority: parseInt(e.target.value) })}
                    className="input-field"
                  >
                    <option value={1}>Low</option>
                    <option value={2}>Medium</option>
                    <option value={3}>High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Estimated Hours
                  </label>
                  <input
                    type="number"
                    value={assignmentForm.estimated_hours}
                    onChange={(e) => setAssignmentForm({ ...assignmentForm, estimated_hours: e.target.value })}
                    className="input-field"
                    placeholder="How many hours do you estimate?"
                    min="1"
                  />
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAssignmentForm(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1">
                  Create Assignment
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Edit Class Modal */}
      <EditClassModal
        classData={editingClass}
        isOpen={showEditClassModal}
        onClose={handleCloseEditClassModal}
        onSave={handleSaveClass}
      />

      {/* Edit Assignment Modal */}
      <EditAssignmentModal
        assignment={editingAssignment}
        classes={classes}
        isOpen={showEditAssignmentModal}
        onClose={handleCloseEditAssignmentModal}
        onSave={handleSaveAssignment}
      />
    </div>
  )
}

export default Classes
