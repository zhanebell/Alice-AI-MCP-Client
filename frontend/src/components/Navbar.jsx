import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  CalendarIcon, 
  AcademicCapIcon, 
  SparklesIcon,
  PowerIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import { shutdownApp } from '../services/api'
import toast from 'react-hot-toast'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Calendar', href: '/calendar', icon: CalendarIcon },
  { name: 'Classes', href: '/classes', icon: AcademicCapIcon },
  { name: 'AI Assistant', href: '/ai', icon: SparklesIcon },
]

function Navbar() {
  const location = useLocation()
  const [isShuttingDown, setIsShuttingDown] = useState(false)

  const handleShutdown = async () => {
    if (isShuttingDown) return
    
    const confirmed = window.confirm(
      'Are you sure you want to shutdown the Alice AI application? This will close both the backend and frontend servers.'
    )
    
    if (!confirmed) return

    setIsShuttingDown(true)
    
    try {
      toast.loading('Shutting down application...', { duration: 2000 })
      await shutdownApp()
      
      // Give a moment for the toast to show, then close the window
      setTimeout(() => {
        window.close()
      }, 2000)
    } catch (error) {
      console.error('Error shutting down app:', error)
      toast.error('Error shutting down application')
      setIsShuttingDown(false)
    }
  }

  return (
    <nav className="bg-black shadow-lg border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center space-x-3"
              >
                <img 
                  src="/alice-ai-bot.png" 
                  alt="Alice AI" 
                  className="h-8 w-8 rounded-lg"
                />
                <span className="text-xl font-bold text-white">
                  Alice AI
                </span>
              </motion.div>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors duration-200 ${
                      isActive
                        ? 'border-b-2 border-primary-500 text-primary-400'
                        : 'text-gray-300 hover:text-white hover:border-gray-600'
                    }`}
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="hidden md:block"
            >
              <div className="text-sm text-gray-300">
                Your intelligent assignment assistant
              </div>
            </motion.div>
            
            {/* Shutdown Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleShutdown}
              disabled={isShuttingDown}
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                isShuttingDown
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
              title="Shutdown Application"
            >
              <PowerIcon className="w-4 h-4 mr-2" />
              {isShuttingDown ? 'Shutting Down...' : 'Shutdown'}
            </motion.button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className="sm:hidden">
        <div className="pt-2 pb-3 space-y-1 bg-black border-t border-gray-800">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`block px-3 py-2 text-base font-medium transition-colors duration-200 ${
                  isActive
                    ? 'bg-gray-950 border-l-4 border-primary-500 text-primary-400'
                    : 'text-gray-300 hover:text-white hover:bg-gray-950'
                }`}
              >
                <div className="flex items-center">
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </div>
              </Link>
            )
          })}
          
          {/* Mobile Shutdown Button */}
          <button
            onClick={handleShutdown}
            disabled={isShuttingDown}
            className={`block w-full text-left px-3 py-2 text-base font-medium transition-colors duration-200 ${
              isShuttingDown
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'text-red-400 hover:text-red-300 hover:bg-gray-950'
            }`}
          >
            <div className="flex items-center">
              <PowerIcon className="w-5 h-5 mr-3" />
              {isShuttingDown ? 'Shutting Down...' : 'Shutdown App'}
            </div>
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
