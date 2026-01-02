import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TeamView from './pages/TeamView'
import UserDetail from './pages/UserDetail'
import DevLogin from './components/DevLogin'
import { apiService } from './services/api'
import './styles/App.css'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('auth_token')
    if (!token) {
      setCheckingAuth(false)
      return
    }

    try {
      await apiService.getCurrentUser()
      setIsAuthenticated(true)
    } catch (err) {
      // Token invalid, clear it
      localStorage.removeItem('auth_token')
      setIsAuthenticated(false)
    } finally {
      setCheckingAuth(false)
    }
  }

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  if (checkingAuth) {
    return <div className="loading">Checking authentication...</div>
  }

  if (!isAuthenticated) {
    return (
      <Router>
        <div className="app">
          <header className="app-header">
            <h1>Engineer Productivity Analyzer</h1>
            <p className="subtitle">Insights for team leads — not for punishment</p>
          </header>
          <main className="app-main">
            <DevLogin onLogin={handleLogin} />
          </main>
        </div>
      </Router>
    )
  }

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Engineer Productivity Analyzer</h1>
          <p className="subtitle">Insights for team leads — not for punishment</p>
          <button 
            onClick={() => {
              localStorage.removeItem('auth_token')
              setIsAuthenticated(false)
            }}
            className="btn-logout"
          >
            Logout
          </button>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/teams/:teamId" element={<TeamView />} />
            <Route path="/users/:userId" element={<UserDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

