import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  XMarkIcon,
  SwatchIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

const colorOptions = [
  { value: '#3B82F6', name: 'Blue', class: 'bg-blue-500' },
  { value: '#10B981', name: 'Green', class: 'bg-green-500' },
  { value: '#F59E0B', name: 'Yellow', class: 'bg-yellow-500' },
  { value: '#EF4444', name: 'Red', class: 'bg-red-500' },
  { value: '#8B5CF6', name: 'Purple', class: 'bg-purple-500' },
  { value: '#06B6D4', name: 'Cyan', class: 'bg-cyan-500' },
  { value: '#F97316', name: 'Orange', class: 'bg-orange-500' },
  { value: '#84CC16', name: 'Lime', class: 'bg-lime-500' },
  { value: '#EC4899', name: 'Pink', class: 'bg-pink-500' },
  { value: '#6B7280', name: 'Gray', class: 'bg-gray-500' }
]

function EditClassModal({ classData, isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    full_name: '',
    description: '',
    color: '#3B82F6'
  })
  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (classData) {
      setFormData({
        name: classData.name || '',
        full_name: classData.full_name || '',
        description: classData.description || '',
        color: classData.color || '#3B82F6'
      })
      setErrors({})
    }
  }, [classData])

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
    
    if (!formData.name.trim()) {
      newErrors.name = 'Class name is required'
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
      await onSave(classData.id, formData)
      onClose()
    } catch (error) {
      console.error('Error updating class:', error)
      setErrors({ submit: 'Failed to update class. Please try again.' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    setFormData({
      name: '',
      full_name: '',
      description: '',
      color: '#3B82F6'
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
              Edit Class
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
            {/* Class Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
                Class Code *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-900 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white ${
                  errors.name ? 'border-red-400' : 'border-gray-600'
                }`}
                placeholder="e.g., ICS 211, MATH 101"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            {/* Full Name */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                id="full_name"
                value={formData.full_name}
                onChange={(e) => handleInputChange('full_name', e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-white"
                placeholder="e.g., Introduction to Computer Science II"
              />
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
                placeholder="Class description (optional)"
              />
            </div>

            {/* Color */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Class Color
              </label>
              <div className="grid grid-cols-5 gap-2">
                {colorOptions.map(color => (
                  <button
                    key={color.value}
                    type="button"
                    onClick={() => handleInputChange('color', color.value)}
                    className={`relative w-10 h-10 rounded-lg ${color.class} hover:scale-110 transition-transform ${
                      formData.color === color.value ? 'ring-2 ring-primary-400 ring-offset-2 ring-offset-gray-950' : ''
                    }`}
                    title={color.name}
                  >
                    {formData.color === color.value && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
              <div className="mt-2 flex items-center space-x-2">
                <SwatchIcon className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-400">Current: {formData.color}</span>
              </div>
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

export default EditClassModal
