import React from 'react'
import { motion } from 'framer-motion'

function LoadingSpinner({ size = 'default', message = 'Loading...' }) {
  const sizeClasses = {
    small: 'h-4 w-4',
    default: 'h-8 w-8',
    large: 'h-12 w-12'
  }

  return (
    <div className="flex flex-col items-center justify-center py-12">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className={`${sizeClasses[size]} border-2 border-primary-200 border-t-primary-600 rounded-full`}
      />
      {message && (
        <p className="mt-4 text-gray-300 text-sm">{message}</p>
      )}
    </div>
  )
}

export default LoadingSpinner
