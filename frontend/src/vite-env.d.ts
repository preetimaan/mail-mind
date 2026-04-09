/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_AUTH_LOGIN_SECRET?: string
  readonly DEV?: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

