import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Calendar from './pages/Calendar'
import Classes from './pages/Classes'
import AIAssistant from './pages/AIAssistant'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-black">
        <Navbar />
        <main className="pb-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/classes" element={<Classes />} />
            <Route path="/ai" element={<AIAssistant />} />
          </Routes>
        </main>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#000000',
              color: '#ffffff',
              border: '1px solid #1f1f1f',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#22c55e',
                secondary: '#000000',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#000000',
              },
            },
          }}
        />
      </div>
    </Router>
  )
}

export default App
