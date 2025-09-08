import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  SparklesIcon, 
  DocumentTextIcon, 
  PlusIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
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
  const [activeTab, setActiveTab] = useState('syllabus') // 'syllabus' or 'generate'
  
  // Syllabus parsing state
  const [syllabusText, setSyllabusText] = useState('')
  const [syllabusResults, setSyllabusResults] = useState(null)
  
  // Assignment generation state
  const [generatePrompt, setGeneratePrompt] = useState('')
  const [selectedClassId, setSelectedClassId] = useState('')
  const [generateResults, setGenerateResults] = useState(null)
  
  // Pending assignments and editing state
  const [pendingAssignments, setPendingAssignments] = useState([])
  const [editingAssignment, setEditingAssignment] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)

  useEffect(() => {
    checkAIStatus()
    fetchClasses()
    fetchPendingAssignments()
  }, [])

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

  const handleParseSyllabus = async (e) => {
    e.preventDefault()
    if (!syllabusText.trim()) {
      toast.error('Please enter syllabus text')
      return
    }

    try {
      setLoading(true)
      const response = await aiAPI.parseSyllabus({
        syllabus_text: syllabusText
      })
      
      setSyllabusResults(response.data)
      toast.success(response.data.message)
      
      // Refresh classes list if new classes were created
      if (response.data.classes_created.length > 0) {
        fetchClasses()
      }
      
      // Refresh pending assignments if any were created
      if (response.data.pending_assignments_created && response.data.pending_assignments_created.length > 0) {
        fetchPendingAssignments()
      }
    } catch (error) {
      console.error('Error parsing syllabus:', error)
      toast.error('Failed to parse syllabus')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateAssignments = async (e) => {
    e.preventDefault()
    if (!generatePrompt.trim()) {
      toast.error('Please enter a prompt')
      return
    }

    try {
      setLoading(true)
      const response = await aiAPI.generateAssignments({
        prompt: generatePrompt,
        class_id: selectedClassId ? parseInt(selectedClassId) : null
      })
      
      setGenerateResults(response.data)
      toast.success(response.data.message)
      
      // Refresh pending assignments if any were created
      if (response.data.pending_assignments_created && response.data.pending_assignments_created.length > 0) {
        fetchPendingAssignments()
      }
    } catch (error) {
      console.error('Error generating assignments:', error)
      toast.error('Failed to generate assignments')
    } finally {
      setLoading(false)
    }
  }

  const sampleSyllabus = `ICS 211 - Introduction to Computer Science II
Course Description: Advanced programming concepts including data structures, algorithms, and object-oriented programming.

Assignment Schedule:
- Programming Assignment 1: Basic OOP concepts (Due: September 15, 2024)
- Programming Assignment 2: Data Structures implementation (Due: October 1, 2024)
- Midterm Project: Binary Search Tree implementation (Due: October 20, 2024)
- Programming Assignment 3: Graph algorithms (Due: November 10, 2024)
- Final Project: Complete application with GUI (Due: December 5, 2024)

Exam Schedule:
- Midterm Exam: October 25, 2024
- Final Exam: December 15, 2024`

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

  const samplePrompts = [
    "Create 3 progressive programming assignments for learning React.js",
    "Generate study tasks for preparing for a calculus midterm exam",
    "Design weekly lab assignments for an organic chemistry course",
    "Create project milestones for building a mobile app in 8 weeks"
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
              AI Assignment Assistant ✨
            </h1>
          </div>
          
          {/* Subtle AI Status */}
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
          Parse syllabi and generate assignments automatically using Alice AI
        </p>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <div className="border-b border-gray-800">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('syllabus')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'syllabus'
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-gray-300 hover:text-white hover:border-gray-600'
              }`}
            >
              <DocumentTextIcon className="h-5 w-5 inline mr-2" />
              Parse Syllabus
            </button>
            <button
              onClick={() => setActiveTab('generate')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'generate'
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-gray-300 hover:text-white hover:border-gray-600'
              }`}
            >
              <SparklesIcon className="h-5 w-5 inline mr-2" />
              Generate Assignments
            </button>
          </nav>
        </div>
      </motion.div>

      {activeTab === 'syllabus' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* Syllabus Input */}
          <div className="card">
            <h2 className="text-xl font-bold text-white mb-4">
              📄 Syllabus Parser
            </h2>
            <p className="text-gray-300 mb-6">
              Paste your syllabus text below and AI will automatically extract classes and assignments.
            </p>
            
            <form onSubmit={handleParseSyllabus}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Syllabus Text
                </label>
                <textarea
                  value={syllabusText}
                  onChange={(e) => setSyllabusText(e.target.value)}
                  rows={12}
                  className="input-field font-mono text-sm"
                  placeholder="Paste your syllabus here..."
                />
              </div>
              
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setSyllabusText(sampleSyllabus)}
                  className="btn-secondary flex-1"
                >
                  Use Sample
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary flex-1 flex items-center justify-center"
                >
                  {loading ? (
                    <LoadingSpinner size="small" />
                  ) : (
                    <>
                      <SparklesIcon className="h-5 w-5 mr-2" />
                      Parse with AI
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Syllabus Results */}
          <div className="card">
            <h2 className="text-xl font-bold text-white mb-4">
              📊 Parsing Results
            </h2>
            
            {syllabusResults ? (
              <div className="space-y-6">
                {/* Classes Created */}
                {syllabusResults.classes_created.length > 0 && (
                  <div>
                    <h3 className="font-medium text-white mb-3 flex items-center">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Classes Created ({syllabusResults.classes_created.length})
                    </h3>
                    <div className="space-y-2">
                      {syllabusResults.classes_created.map((classItem, index) => (
                        <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <h4 className="font-medium text-green-900">{classItem.name}</h4>
                          {classItem.full_name && (
                            <p className="text-green-700 text-sm">{classItem.full_name}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Assignments Created */}
                {syllabusResults.assignments_created.length > 0 && (
                  <div>
                    <h3 className="font-medium text-white mb-3 flex items-center">
                      <CheckCircleIcon className="h-5 w-5 text-blue-500 mr-2" />
                      Assignments Created ({syllabusResults.assignments_created.length})
                    </h3>
                    <div className="space-y-2">
                      {syllabusResults.assignments_created.map((assignment, index) => (
                        <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-blue-900">{assignment.title}</h4>
                            <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded">
                              Priority: {assignment.priority === 3 ? 'High' : assignment.priority === 2 ? 'Medium' : 'Low'}
                            </span>
                          </div>
                          <p className="text-blue-700 text-sm">
                            Due: {new Date(assignment.due_date).toLocaleDateString()}
                          </p>
                          {assignment.estimated_hours && (
                            <p className="text-blue-600 text-xs">
                              ~{assignment.estimated_hours} hours
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                  <p className="text-gray-300 text-sm">
                    ✅ {syllabusResults.message}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <DocumentTextIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">
                  Results will appear here after parsing
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {activeTab === 'generate' && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* Generation Input */}
          <div className="card">
            <h2 className="text-xl font-bold text-white mb-4">
              🤖 Assignment Generator
            </h2>
            <p className="text-gray-300 mb-6">
              Describe what kind of assignments you need and AI will generate them for you.
            </p>
            
            <form onSubmit={handleGenerateAssignments}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Assignment Prompt
                </label>
                <textarea
                  value={generatePrompt}
                  onChange={(e) => setGeneratePrompt(e.target.value)}
                  rows={6}
                  className="input-field"
                  placeholder="Describe the assignments you want to generate..."
                />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Class (Optional)
                </label>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                  className="input-field"
                >
                  <option value="">Select a class or create new</option>
                  {classes.map((classItem) => (
                    <option key={classItem.id} value={classItem.id}>
                      {classItem.name} - {classItem.full_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Sample Prompts
                </label>
                <div className="grid grid-cols-1 gap-2">
                  {samplePrompts.map((prompt, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setGeneratePrompt(prompt)}
                      className="text-left p-2 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded border border-gray-700 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center"
              >
                {loading ? (
                  <LoadingSpinner size="small" />
                ) : (
                  <>
                    <SparklesIcon className="h-5 w-5 mr-2" />
                    Generate Assignments
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Generation Results */}
          <div className="card">
            <h2 className="text-xl font-bold text-white mb-4">
              🎯 Generated Assignments
            </h2>
            
            {generateResults ? (
              <div className="space-y-6">
                {generateResults.assignments_created.length > 0 && (
                  <div>
                    <h3 className="font-medium text-white mb-3 flex items-center">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                      Assignments Generated ({generateResults.assignments_created.length})
                    </h3>
                    <div className="space-y-3">
                      {generateResults.assignments_created.map((assignment, index) => (
                        <div key={index} className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-medium text-purple-900">{assignment.title}</h4>
                            <span className="text-xs text-purple-700 bg-purple-100 px-2 py-1 rounded">
                              Priority: {assignment.priority === 3 ? 'High' : assignment.priority === 2 ? 'Medium' : 'Low'}
                            </span>
                          </div>
                          {assignment.description && (
                            <p className="text-purple-700 text-sm mb-2">
                              {assignment.description}
                            </p>
                          )}
                          <div className="flex items-center justify-between text-xs text-purple-600">
                            <span>Due: {new Date(assignment.due_date).toLocaleDateString()}</span>
                            {assignment.estimated_hours && (
                              <span>~{assignment.estimated_hours} hours</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                  <p className="text-gray-300 text-sm">
                    ✅ {generateResults.message}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <SparklesIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">
                  Generated assignments will appear here
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Pending Assignments Approval */}
      {pendingAssignments.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
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
