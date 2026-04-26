import { useEffect } from 'react'

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

    if (oauthSuccess === '1' && oauthUsername) {
      onSuccess(oauthUsername)
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (oauthError) {
      onError(decodeURIComponent(oauthError))
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [onSuccess, onError])
}

