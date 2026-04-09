import { useEffect } from 'react'
import { ACCESS_TOKEN_KEY } from '../api/client'

interface UseOAuthCallbackOptions {
  onSuccess: (username: string) => void
  onError: (error: string) => void
}

export function useOAuthCallback({ onSuccess, onError }: UseOAuthCallbackOptions) {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const oauthSuccess = params.get('oauth_success')
    const oauthError = params.get('oauth_error')
    const oauthUsername = params.get('username')
    const accessToken = params.get('access_token')

    if (oauthSuccess === '1' && oauthUsername) {
      if (accessToken) {
        localStorage.setItem(ACCESS_TOKEN_KEY, decodeURIComponent(accessToken))
      }
      onSuccess(oauthUsername)
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (oauthError) {
      onError(decodeURIComponent(oauthError))
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [onSuccess, onError])
}
