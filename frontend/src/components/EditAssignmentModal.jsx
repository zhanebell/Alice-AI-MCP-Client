import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  XMarkIcon,
  CalendarIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'

const priorityOptions = [
  { value: 1, label: 'Low', color: 'text-green-400' },
  { value: 2, label: 'Medium', color: 'text-yellow-400' },
  { value: 3, label: 'High', color: 'text-red-400' }
]

function EditAssignmentModal({ assignment, classes, isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 2,
    estimated_hours: '',
    class_id: ''
  })
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (assignment) {
      // Convert the assignment data to form format
      const dueDate = new Date(assignment.due_date)
      const formattedDate = format(dueDate, "yyyy-MM-dd'T'HH:mm")
      
      setFormData({
        title: assignment.title || '',
        description: assignment.description || '',
        due_date: formattedDate,
        priority: assignment.priority || 2,
        estimated_hours: assignment.estimated_hours || '',
        class_id: assignment.class_id || ''
      })
      setErrors({})
    }
  }, [assignment])

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required'
    }
    
    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required'
    }
    
    if (!formData.class_id) {
      newErrors.class_id = 'Class is required'
    }
    
    if (formData.estimated_hours && (isNaN(formData.estimated_hours) || formData.estimated_hours < 0)) {
      newErrors.estimated_hours = 'Estimated hours must be a positive number'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)
    
    try {
      const updateData = {
        ...formData,
        estimated_hours: formData.estimated_hours ? parseInt(formData.estimated_hours) : null,
        class_id: parseInt(formData.class_id)
      }
      
      await onSave(assignment.id, updateData)
      onClose()
    } catch (error) {
      console.error('Error updating assignment:', error)
      setErrors({ submit: 'Failed to update assignment. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    setFormData({
      title: '',
      description: '',
      due_date: '',
      priority: 2,
      estimated_hours: '',
      class_id: ''
    })
    setErrors({})
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50"
          onClick={handleCancel}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative bg-gray-950 rounded-lg shadow-xl w-full max-w-md mx-auto border border-gray-700"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">
              Edit Assignment
            </h2>
            <button
              onClick={handleCancel}
              className="text-gray-400 hover:text-gray-300 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-300 mb-1">
                Title *
              </label>
              <input
                type="text"
                id="title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-900 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white ${
                  errors.title ? 'border-red-400' : 'border-gray-600'
                }`}
                placeholder="Assignment title"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
                Description
              </label>
              <textarea
                id="description"
                rows={3}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white"
                placeholder="Assignment description (optional)"
              />
            </div>

            {/* Due Date */}
            <div>
              <label htmlFor="due_date" className="block text-sm font-medium text-gray-300 mb-1">
                Due Date *
              </label>
              <div className="relative">
                <input
                  type="datetime-local"
                  id="due_date"
                  value={formData.due_date}
                  onChange={(e) => handleInputChange('due_date', e.target.value)}
                  className={`w-full px-3 py-2 bg-gray-900 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white ${
                    errors.due_date ? 'border-red-400' : 'border-gray-600'
                  }`}
                />
                <CalendarIcon className="absolute right-3 top-2.5 h-5 w-5 text-gray-400 pointer-events-none" />
              </div>
              {errors.due_date && (
                <p className="mt-1 text-sm text-red-600">{errors.due_date}</p>
              )}
            </div>

            {/* Priority */}
            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-gray-300 mb-1">
                Priority
              </label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) => handleInputChange('priority', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white"
              >
                {priorityOptions.map(option => (
                  <option key={option.value} value={option.value} className="bg-gray-900 text-white">
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Estimated Hours */}
            <div>
              <label htmlFor="estimated_hours" className="block text-sm font-medium text-gray-300 mb-1">
                Estimated Hours
              </label>
              <div className="relative">
                <input
                  type="number"
                  id="estimated_hours"
                  min="0"
                  step="1"
                  value={formData.estimated_hours}
                  onChange={(e) => handleInputChange('estimated_hours', e.target.value)}
                  className={`w-full px-3 py-2 bg-gray-900 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white ${
                    errors.estimated_hours ? 'border-red-400' : 'border-gray-600'
                  }`}
                  placeholder="Hours"
                />
                <ClockIcon className="absolute right-3 top-2.5 h-5 w-5 text-gray-400 pointer-events-none" />
              </div>
              {errors.estimated_hours && (
                <p className="mt-1 text-sm text-red-600">{errors.estimated_hours}</p>
              )}
            </div>

            {/* Class */}
            <div>
              <label htmlFor="class_id" className="block text-sm font-medium text-gray-300 mb-1">
                Class *
              </label>
              <select
                id="class_id"
                value={formData.class_id}
                onChange={(e) => handleInputChange('class_id', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-900 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white ${
                  errors.class_id ? 'border-red-400' : 'border-gray-600'
                }`}
              >
                <option value="" className="bg-gray-900 text-white">Select a class</option>
                {classes.map(cls => (
                  <option key={cls.id} value={cls.id} className="bg-gray-900 text-white">
                    {cls.name} - {cls.full_name || cls.name}
                  </option>
                ))}
              </select>
              {errors.class_id && (
                <p className="mt-1 text-sm text-red-600">{errors.class_id}</p>
              )}
            </div>

            {/* Submit Error */}
            {errors.submit && (
              <div className="flex items-center space-x-2 text-red-600">
                <ExclamationTriangleIcon className="h-5 w-5" />
                <p className="text-sm">{errors.submit}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={handleCancel}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 border border-gray-600 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </div>
  )
}

export default EditAssignmentModal
