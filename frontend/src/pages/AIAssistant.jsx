import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  SparklesIcon, 
  PaperAirplaneIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  ChartBarIcon,
  PlusIcon,
  UserIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { aiAPI, classesAPI, pendingAssignmentsAPI, assignmentsAPI } from '../services/api'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/LoadingSpinner'
import ApprovalInterface from '../components/ApprovalInterface'
import EditAssignmentModal from '../components/EditAssignmentModal'

function AIAssistant() {
  const [loading, setLoading] = useState(false)
  const [aiStatus, setAiStatus] = useState(null)
  const [classes, setClasses] = useState([])
  
  // Chat state
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm Alice, your AI assignment assistant. 👋\n\nI can help you with:\n• Query information about your assignments and classes\n• Create new assignments or parse syllabi\n• General conversation about your academic work\n\nWhat would you like to do today?",
      sender: 'ai',
      timestamp: new Date(),
      agent: 'general'
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const messagesEndRef = useRef(null)
  
  // Pending assignments and editing state
  const [pendingAssignments, setPendingAssignments] = useState([])
  const [editingAssignment, setEditingAssignment] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)

  useEffect(() => {
    checkAIStatus()
    fetchClasses()
    fetchPendingAssignments()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const checkAIStatus = async () => {
    try {
      const response = await aiAPI.getStatus()
      setAiStatus(response.data)
    } catch (error) {
      console.error('Error checking AI status:', error)
    }
  }

  const fetchClasses = async () => {
    try {
      const response = await classesAPI.getAll()
      setClasses(response.data)
    } catch (error) {
      console.error('Error fetching classes:', error)
    }
  }

  const fetchPendingAssignments = async () => {
    try {
      const response = await pendingAssignmentsAPI.getAll({ status: 'pending' })
      setPendingAssignments(response.data)
    } catch (error) {
      console.error('Error fetching pending assignments:', error)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentMessage = inputMessage
    setInputMessage('')
    setLoading(true)

    try {
      const response = await aiAPI.chat({
        message: currentMessage
      })

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.response,
        sender: 'ai',
        timestamp: new Date(),
        agent: response.data.agent_used,
        actionTaken: response.data.action_taken,
        data: response.data.data
      }

      setMessages(prev => [...prev, aiMessage])

      // Refresh data if actions were taken
      if (response.data.action_taken) {
        if (response.data.data.classes_created || response.data.data.classes) {
          fetchClasses()
        }
        if (response.data.data.pending_assignments_created || response.data.data.pending_assignments) {
          fetchPendingAssignments()
        }
      }

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: "I'm sorry, I'm having trouble processing that right now. Please try again.",
        sender: 'ai',
        timestamp: new Date(),
        agent: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    {
      text: "What assignments do I have due this week?",
      icon: ChartBarIcon,
      agent: "query"
    },
    {
      text: "Show me all my classes",
      icon: ChartBarIcon,
      agent: "query"
    },
    {
      text: "Create 3 programming assignments for my computer science class",
      icon: PlusIcon,
      agent: "create"
    },
    {
      text: "Parse this syllabus and create assignments",
      icon: PlusIcon,
      agent: "create"
    }
  ]

  const handleQuickAction = (actionText) => {
    setInputMessage(actionText)
  }

  // Approval and editing functions
  const handleApproveAssignment = async (assignmentId) => {
    try {
      await pendingAssignmentsAPI.approve(assignmentId)
      toast.success('Assignment approved successfully')
      fetchPendingAssignments()
    } catch (error) {
      console.error('Error approving assignment:', error)
      toast.error('Failed to approve assignment')
    }
  }

  const handleRejectAssignment = async (assignmentId) => {
    try {
      await pendingAssignmentsAPI.reject(assignmentId)
      toast.success('Assignment rejected')
      fetchPendingAssignments()
    } catch (error) {
      console.error('Error rejecting assignment:', error)
      toast.error('Failed to reject assignment')
    }
  }

  const handleApproveAll = async () => {
    try {
      await pendingAssignmentsAPI.approveAll()
      toast.success('All assignments approved successfully')
      fetchPendingAssignments()
    } catch (error) {
      console.error('Error approving all assignments:', error)
      toast.error('Failed to approve all assignments')
    }
  }

  const handleRejectAll = async () => {
    try {
      await pendingAssignmentsAPI.rejectAll()
      toast.success('All assignments rejected')
      fetchPendingAssignments()
    } catch (error) {
      console.error('Error rejecting all assignments:', error)
      toast.error('Failed to reject all assignments')
    }
  }

  const handleEditAssignment = (assignment) => {
    setEditingAssignment(assignment)
    setShowEditModal(true)
  }

  const handleSaveAssignment = async (assignmentId, updateData) => {
    try {
      await pendingAssignmentsAPI.update(assignmentId, updateData)
      toast.success('Assignment updated successfully')
      fetchPendingAssignments()
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

  const getAgentIcon = (agent) => {
    switch (agent) {
      case 'query':
        return ChartBarIcon
      case 'create':
        return PlusIcon
      case 'general':
        return SparklesIcon
      default:
        return SparklesIcon
    }
  }

  const getAgentBadge = (agent) => {
    switch (agent) {
      case 'query':
        return { text: 'Query Agent', color: 'bg-blue-500' }
      case 'create':
        return { text: 'Create Agent', color: 'bg-green-500' }
      case 'general':
        return { text: 'Alice AI', color: 'bg-purple-500' }
      default:
        return { text: 'Alice AI', color: 'bg-purple-500' }
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            >
              <SparklesIcon className="h-8 w-8 text-purple-400" />
            </motion.div>
            <h1 className="text-3xl font-bold text-white">
              Alice AI Assistant ✨
            </h1>
          </div>
          
          {/* AI Status */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                aiStatus?.groq_connected ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <span className="text-xs text-gray-300">
                {aiStatus?.groq_connected ? 'AI Connected' : 'AI Offline'}
              </span>
            </div>
            {aiStatus?.mock_mode && (
              <div className="flex items-center space-x-2">
                <ExclamationTriangleIcon className="h-4 w-4 text-yellow-400" />
                <span className="text-xs text-yellow-400">Mock Mode</span>
              </div>
            )}
          </div>
        </div>
        <p className="text-lg text-gray-300">
          Productivity Reimagined
        </p>
      </motion.div>

      {/* Chat Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Quick Actions Sidebar */}
        <div className="lg:col-span-1">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="card"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              {quickActions.map((action, index) => {
                const IconComponent = action.icon
                return (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action.text)}
                    className="w-full text-left p-3 rounded-lg border border-gray-700 hover:border-gray-600 hover:bg-gray-800 transition-colors group"
                  >
                    <div className="flex items-start space-x-3">
                      <IconComponent className={`h-5 w-5 mt-0.5 ${
                        action.agent === 'query' ? 'text-blue-400' : 
                        action.agent === 'create' ? 'text-green-400' : 'text-purple-400'
                      }`} />
                      <span className="text-sm text-gray-300 group-hover:text-white">
                        {action.text}
                      </span>
                    </div>
                  </button>
                )
              })}
            </div>
          </motion.div>
        </div>

        {/* Main Chat Area */}
        <div className="lg:col-span-3">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="card h-[600px] flex flex-col"
          >
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <AnimatePresence>
                {messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] ${message.sender === 'user' ? 'order-2' : 'order-1'}`}>
                      {message.sender === 'ai' && (
                        <div className="flex items-center space-x-2 mb-2">
                          <div className={`w-6 h-6 rounded-full ${getAgentBadge(message.agent).color} flex items-center justify-center`}>
                            <SparklesIcon className="h-3 w-3 text-white" />
                          </div>
                          <span className="text-xs text-gray-400">
                            {getAgentBadge(message.agent).text}
                          </span>
                          {message.actionTaken && (
                            <span className="text-xs bg-green-900 text-green-300 px-2 py-0.5 rounded">
                              Action Taken
                            </span>
                          )}
                        </div>
                      )}
                      <div
                        className={`p-4 rounded-lg ${
                          message.sender === 'user'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-800 text-gray-100'
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{message.text}</div>
                        <div className="text-xs opacity-70 mt-2">
                          {message.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.sender === 'user' ? 'bg-primary-600 order-1 mr-3' : 'bg-gray-700 order-2 ml-3'
                    }`}>
                      {message.sender === 'user' ? (
                        <UserIcon className="h-4 w-4 text-white" />
                      ) : (
                        <SparklesIcon className="h-4 w-4 text-purple-400" />
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {loading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <LoadingSpinner size="small" />
                      <span className="text-gray-300">Alice is thinking...</span>
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-700 p-4">
              <form onSubmit={handleSendMessage} className="flex space-x-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask Alice about assignments, classes, or anything else..."
                  className="flex-1 input-field"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !inputMessage.trim()}
                  className="btn-primary px-4 py-2 flex items-center space-x-2"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Pending Assignments Approval */}
      {pendingAssignments.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <ApprovalInterface
            pendingAssignments={pendingAssignments}
            onApprove={handleApproveAssignment}
            onReject={handleRejectAssignment}
            onApproveAll={handleApproveAll}
            onRejectAll={handleRejectAll}
            onEdit={handleEditAssignment}
          />
        </motion.div>
      )}

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

export default AIAssistant
