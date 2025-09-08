import React from 'react'
import { motion } from 'framer-motion'
import { 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  ArrowTopRightOnSquareIcon,
  TrashIcon,
  PencilIcon
} from '@heroicons/react/24/outline'
import { format, isToday, isTomorrow, isPast } from 'date-fns'

const statusConfig = {
  not_started: {
    label: 'Not Started',
    color: 'text-red-400 bg-red-900/30 border-red-700',
    icon: ClockIcon
  },
  in_progress: {
    label: 'In Progress',
    color: 'text-yellow-400 bg-yellow-900/30 border-yellow-700',
    icon: ClockIcon
  },
  completed: {
    label: 'Completed',
    color: 'text-green-400 bg-green-900/30 border-green-700',
    icon: CheckCircleIcon
  }
}

const priorityConfig = {
  1: { label: 'Low', color: 'text-green-400' },
  2: { label: 'Medium', color: 'text-yellow-400' },
  3: { label: 'High', color: 'text-red-400' }
}

function AssignmentCard({ assignment, onStatusUpdate, onDelete, onEdit, compact = false }) {
  const dueDate = new Date(assignment.due_date)
  const config = statusConfig[assignment.status]
  const priority = priorityConfig[assignment.priority]
  const IconComponent = config.icon

  const getDueDateText = () => {
    if (isToday(dueDate)) return 'Due today'
    if (isTomorrow(dueDate)) return 'Due tomorrow'
    if (isPast(dueDate) && assignment.status !== 'completed') return 'Overdue'
    return `Due ${format(dueDate, 'MMM d, yyyy')}`
  }

  const getDueDateColor = () => {
    if (isPast(dueDate) && assignment.status !== 'completed') return 'text-red-600'
    if (isToday(dueDate)) return 'text-orange-600'
    if (isTomorrow(dueDate)) return 'text-yellow-600'
    return 'text-gray-400'
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ scale: 1.02 }}
      className={`bg-gray-950 rounded-lg border border-gray-700 shadow-sm hover:shadow-md transition-all duration-200 ${
        compact ? 'p-4' : 'p-6'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className={`font-semibold text-white truncate ${
              compact ? 'text-sm' : 'text-lg'
            }`}>
              {assignment.title}
            </h3>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${priority.color}`}>
              {priority.label}
            </span>
          </div>

          {assignment.description && !compact && (
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
              <span className="text-primary-600 font-medium">
                {assignment.class_ref.name}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2 ml-4">
          {/* Status Badge */}
          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${config.color}`}>
            <IconComponent className="h-3 w-3 mr-1" />
            {config.label}
          </div>
        </div>
      </div>

      {/* Actions */}
      {!compact && (
        <div className="mt-4 flex items-center justify-between">
          <div className="flex space-x-2">
            {assignment.status !== 'completed' && (
              <>
                <button
                  onClick={() => onStatusUpdate(assignment.id, 'in_progress')}
                  className="btn-secondary text-xs py-1 px-2"
                  disabled={assignment.status === 'in_progress'}
                >
                  Start
                </button>
                <button
                  onClick={() => onStatusUpdate(assignment.id, 'completed')}
                  className="btn-success text-xs py-1 px-2"
                >
                  Complete
                </button>
              </>
            )}
            {assignment.status === 'completed' && (
              <button
                onClick={() => onStatusUpdate(assignment.id, 'not_started')}
                className="btn-secondary text-xs py-1 px-2"
              >
                Reopen
              </button>
            )}
          </div>

          <div className="flex space-x-1">
            {onEdit && (
              <button
                onClick={() => onEdit(assignment)}
                className="text-gray-400 hover:text-blue-600 transition-colors"
                title="Edit assignment"
              >
                <PencilIcon className="h-4 w-4" />
              </button>
            )}
            <button
              className="text-gray-400 hover:text-white transition-colors"
              title="View details"
            >
              <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            </button>
            {onDelete && (
              <button
                onClick={() => onDelete(assignment.id)}
                className="text-gray-400 hover:text-red-600 transition-colors"
                title="Delete assignment"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Progress indicator for completed assignments */}
      {assignment.status === 'completed' && assignment.actual_hours && assignment.estimated_hours && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="flex justify-between text-xs text-gray-400">
            <span>Time spent: {assignment.actual_hours}h</span>
            <span>Estimated: {assignment.estimated_hours}h</span>
          </div>
          <div className="mt-1 h-1 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all duration-300"
              style={{ 
                width: `${Math.min((assignment.actual_hours / assignment.estimated_hours) * 100, 100)}%` 
              }}
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default AssignmentCard
