import { useState } from 'react'
import { api, OAuthAuthorizeResponse, TestConnectionResponse } from '../api/client'
import './AddAccountModal.css'

interface AddAccountModalProps {
  isOpen: boolean
  onClose: () => void
  username: string
  onAccountAdded: () => void
}

export default function AddAccountModal({ isOpen, onClose, username, onAccountAdded }: AddAccountModalProps) {
  const [activeTab, setActiveTab] = useState<'gmail' | 'yahoo'>('gmail')
  const [gmailEmail, setGmailEmail] = useState('')
  const [yahooEmail, setYahooEmail] = useState('')
  const [yahooPassword, setYahooPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)

  if (!isOpen) return null

  const handleGmailConnect = async () => {
    if (!gmailEmail.trim()) {
      setError('Please enter your Gmail address')
      return
    }

    if (!username.trim()) {
      setError('Please enter a username first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await api.get<OAuthAuthorizeResponse>('/api/oauth/authorize', {
        params: {
          username,
          email: gmailEmail.trim()
        }
      })

      // Redirect to Google OAuth
      window.location.href = response.data.authorization_url
    } catch (err: any) {
      setLoading(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to start OAuth flow'
      setError(errorMessage)
    }
  }

  const handleYahooTest = async () => {
    if (!yahooEmail.trim() || !yahooPassword.trim()) {
      setError('Please enter both email and app password')
      return
    }

    setTesting(true)
    setError(null)

    try {
      const response = await api.post<TestConnectionResponse>('/api/emails/accounts/test-connection', {
        provider: 'yahoo',
        email: yahooEmail.trim(),
        credentials: yahooPassword.trim()
      })

      if (response.data.success) {
        // Test passed, now create account
        await handleYahooSubmit()
      } else {
        setError(response.data.message)
        setTesting(false)
      }
    } catch (err: any) {
      setTesting(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || err.response?.data?.message || 'Connection test failed'
      setError(errorMessage)
    }
  }

  const handleYahooSubmit = async () => {
    if (!yahooEmail.trim() || !yahooPassword.trim()) {
      setError('Please enter both email and app password')
      return
    }

    if (!username.trim()) {
      setError('Please enter a username first')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await api.post('/api/emails/accounts/yahoo', {
        email: yahooEmail.trim(),
        app_password: yahooPassword.trim(),
        username
      })

      // Success
      setYahooEmail('')
      setYahooPassword('')
      setError(null)
      onAccountAdded()
      onClose()
    } catch (err: any) {
      setLoading(false)
      const errorMessage = err.userMessage || err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to add Yahoo account'
      setError(errorMessage)
    }
  }

  const handleClose = () => {
    if (!loading && !testing) {
      setGmailEmail('')
      setYahooEmail('')
      setYahooPassword('')
      setError(null)
      onClose()
    }
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Email Account</h2>
          <button className="modal-close" onClick={handleClose} disabled={loading || testing}>
            ×
          </button>
        </div>

        <div className="modal-tabs">
          <button
            className={`tab ${activeTab === 'gmail' ? 'active' : ''}`}
            onClick={() => setActiveTab('gmail')}
            disabled={loading || testing}
          >
            Gmail
          </button>
          <button
            className={`tab ${activeTab === 'yahoo' ? 'active' : ''}`}
            onClick={() => setActiveTab('yahoo')}
            disabled={loading || testing}
          >
            Yahoo
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {activeTab === 'gmail' && (
          <div className="modal-body">
            <p className="help-text">
              Connect your Gmail account using OAuth. You'll be redirected to Google to authorize access.
            </p>
            <div className="form-group">
              <label>Gmail Address</label>
              <input
                type="email"
                value={gmailEmail}
                onChange={(e) => setGmailEmail(e.target.value)}
                placeholder="your.email@gmail.com"
                disabled={loading}
                className="input"
              />
            </div>
            <div className="modal-actions">
              <button
                onClick={handleGmailConnect}
                disabled={loading || !gmailEmail.trim()}
                className="btn btn-primary"
              >
                {loading ? 'Connecting...' : 'Connect Gmail'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'yahoo' && (
          <div className="modal-body">
            <p className="help-text">
              Add your Yahoo account using an app-specific password. You'll need to generate one from your Yahoo Account Security settings.
            </p>
            <div className="form-group">
              <label>Yahoo Email Address</label>
              <input
                type="email"
                value={yahooEmail}
                onChange={(e) => setYahooEmail(e.target.value)}
                placeholder="your.email@yahoo.com"
                disabled={loading || testing}
                className="input"
              />
            </div>
            <div className="form-group">
              <label>App-Specific Password</label>
              <input
                type="password"
                value={yahooPassword}
                onChange={(e) => setYahooPassword(e.target.value)}
                placeholder="Enter your app password"
                disabled={loading || testing}
                className="input"
              />
              <small className="help-text">
                <a
                  href="https://login.yahoo.com/account/security"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  How to generate an app password
                </a>
              </small>
            </div>
            <div className="modal-actions">
              <button
                onClick={handleYahooTest}
                disabled={loading || testing || !yahooEmail.trim() || !yahooPassword.trim()}
                className="btn btn-secondary"
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </button>
              <button
                onClick={handleYahooSubmit}
                disabled={loading || testing || !yahooEmail.trim() || !yahooPassword.trim()}
                className="btn btn-primary"
              >
                {loading ? 'Adding...' : 'Add Account'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

