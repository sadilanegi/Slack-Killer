import React, { useState } from 'react'
import { apiService } from '../services/api'
import '../styles/DevLogin.css'

/**
 * Development login component
 * Allows quick login for development/testing
 */
function DevLogin({ onLogin }) {
  const [email, setEmail] = useState('admin@example.com')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      const response = await apiService.devLogin(email)
      console.log('Login response:', response.data)
      // Wait a moment to ensure token is stored
      await new Promise(resolve => setTimeout(resolve, 100))
      if (onLogin) {
        onLogin()
      }
      // Reload page to refresh auth state
      window.location.reload()
    } catch (err) {
      console.error('Login error:', err)
      setError(err.response?.data?.detail || err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dev-login">
      <div className="dev-login-card">
        <h2>Development Login</h2>
        <p className="dev-login-note">
          Quick login for development. Use any email from your database.
        </p>
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email:</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@example.com"
              required
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading} className="btn-login">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <div className="dev-login-hint">
          <p><strong>Quick start:</strong></p>
          <p>1. Run backend: <code>uvicorn app.main:app --reload</code></p>
          <p>2. Create dev users: <code>python scripts/create_dev_user.py</code></p>
          <p>3. Login with: admin@example.com, manager@example.com, or engineer@example.com</p>
        </div>
      </div>
    </div>
  )
}

export default DevLogin

