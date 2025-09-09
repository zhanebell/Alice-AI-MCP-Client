import axios from 'axios'

const API_BASE_URL = 'http://localhost:8001/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Classes API
export const classesAPI = {
  getAll: () => api.get('/classes'),
  get: (id) => api.get(`/classes/${id}`),
  create: (data) => api.post('/classes', data),
  update: (id, data) => api.put(`/classes/${id}`, data),
  delete: (id) => api.delete(`/classes/${id}`),
}

// Assignments API
export const assignmentsAPI = {
  getAll: (params = {}) => api.get('/assignments', { params }),
  get: (id) => api.get(`/assignments/${id}`),
  create: (data) => api.post('/assignments', data),
  update: (id, data) => api.put(`/assignments/${id}`, data),
  updateStatus: (id, status, actualHours = null) => 
    api.patch(`/assignments/${id}/status`, null, { 
      params: { status, actual_hours: actualHours } 
    }),
  delete: (id) => api.delete(`/assignments/${id}`),
  getCalendar: (params = {}) => api.get('/assignments/calendar', { params }),
}

// AI API
export const aiAPI = {
  parseSyllabus: (data) => api.post('/ai/parse-syllabus', data),
  generateAssignments: (data) => api.post('/ai/generate-assignments', data),
  getStatus: () => api.get('/ai/status'),
  chat: (data) => api.post('/ai/chat', data),
}

// Pending Assignments API
export const pendingAssignmentsAPI = {
  getAll: (params = {}) => api.get('/pending-assignments', { params }),
  get: (id) => api.get(`/pending-assignments/${id}`),
  create: (data) => api.post('/pending-assignments', data),
  update: (id, data) => api.put(`/pending-assignments/${id}`, data),
  approve: (id) => api.post(`/pending-assignments/${id}/approve`),
  reject: (id) => api.post(`/pending-assignments/${id}/reject`),
  approveAll: (classId = null) => api.post('/pending-assignments/approve-all', null, { 
    params: classId ? { class_id: classId } : {} 
  }),
  rejectAll: (classId = null) => api.post('/pending-assignments/reject-all', null, { 
    params: classId ? { class_id: classId } : {} 
  }),
  delete: (id) => api.delete(`/pending-assignments/${id}`),
}

// Health check
export const healthCheck = () => api.get('/health')

// App shutdown
export const shutdownApp = () => api.post('/shutdown')

export default api
