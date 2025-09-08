import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  CheckIcon,
  XMarkIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  PencilIcon
} from '@heroicons/react/24/outline'
import { format, isToday, isTomorrow, isPast } from 'date-fns'

const priorityConfig = {
  1: { label: 'Low', color: 'text-green-400' },
  2: { label: 'Medium', color: 'text-yellow-400' },
  3: { label: 'High', color: 'text-red-400' }
}

function PendingAssignmentCard({ assignment, onApprove, onReject, onEdit }) {
  const [isLoading, setIsLoading] = useState(false)
  const dueDate = new Date(assignment.due_date)
  const priority = priorityConfig[assignment.priority]

  const getDueDateText = () => {
    if (isToday(dueDate)) return 'Due today'
    if (isTomorrow(dueDate)) return 'Due tomorrow'
    if (isPast(dueDate)) return 'Overdue'
    return `Due ${format(dueDate, 'MMM d, yyyy')}`
  }

  const getDueDateColor = () => {
    if (isPast(dueDate)) return 'text-red-600'
    if (isToday(dueDate)) return 'text-orange-600'
    if (isTomorrow(dueDate)) return 'text-yellow-600'
    return 'text-gray-400'
  }

  const handleApprove = async () => {
    setIsLoading(true)
    try {
      await onApprove(assignment.id)
    } catch (error) {
      console.error('Error approving assignment:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReject = async () => {
    setIsLoading(true)
    try {
      await onReject(assignment.id)
    } catch (error) {
      console.error('Error rejecting assignment:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-gray-950 border border-gray-700 rounded-lg p-4 hover:shadow-md transition-all duration-200"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="font-semibold text-white truncate">
              {assignment.title}
            </h3>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${priority.color}`}>
              {priority.label}
            </span>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-900/30 text-yellow-400 border border-yellow-700">
              <ClockIcon className="h-3 w-3 mr-1" />
              Pending
            </span>
          </div>

          {assignment.description && (
            <p className="text-gray-300 text-sm mb-3 line-clamp-2">
              {assignment.description}
            </p>
          )}

          <div className="flex items-center space-x-4 text-sm">
            <span className={`font-medium ${getDueDateColor()}`}>
              {getDueDateText()}
            </span>
            {assignment.estimated_hours && (
              <span className="text-gray-400">
                ~{assignment.estimated_hours}h
              </span>
            )}
            {assignment.class_ref && (
              <span className="text-primary-400 font-medium">
                {assignment.class_ref.name}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex space-x-2">
          <button
            onClick={handleApprove}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckIcon className="h-3 w-3 mr-1" />
            Approve
          </button>
          <button
            onClick={handleReject}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XMarkIcon className="h-3 w-3 mr-1" />
            Reject
          </button>
        </div>

        <div className="flex space-x-1">
          {onEdit && (
            <button
              onClick={() => onEdit(assignment)}
              className="text-gray-400 hover:text-blue-600 transition-colors"
              title="Edit assignment before approving"
            >
              <PencilIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function ApprovalInterface({ pendingAssignments, onApprove, onReject, onApproveAll, onRejectAll, onEdit }) {
  const [isLoading, setIsLoading] = useState(false)

  const handleApproveAll = async () => {
    setIsLoading(true)
    try {
      await onApproveAll()
    } catch (error) {
      console.error('Error approving all assignments:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRejectAll = async () => {
    setIsLoading(true)
    try {
      await onRejectAll()
    } catch (error) {
      console.error('Error rejecting all assignments:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (!pendingAssignments || pendingAssignments.length === 0) {
    return null
  }

  return (
    <div className="bg-gray-950 rounded-lg border border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">
            Review Assignments
          </h3>
          <p className="text-sm text-gray-300">
            {pendingAssignments.length} assignment{pendingAssignments.length !== 1 ? 's' : ''} pending approval
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={handleApproveAll}
            disabled={isLoading}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckIcon className="h-4 w-4 mr-1" />
            Approve All
          </button>
          <button
            onClick={handleRejectAll}
            disabled={isLoading}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <XMarkIcon className="h-4 w-4 mr-1" />
            Reject All
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {pendingAssignments.map(assignment => (
          <PendingAssignmentCard
            key={assignment.id}
            assignment={assignment}
            onApprove={onApprove}
            onReject={onReject}
            onEdit={onEdit}
          />
        ))}
      </div>

      <div className="mt-4 p-3 bg-gray-900 border border-gray-700 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-gray-300">
              Review each assignment carefully before approving. You can edit assignments before approving them to make any necessary changes.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ApprovalInterface
