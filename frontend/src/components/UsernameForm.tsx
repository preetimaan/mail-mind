interface UsernameFormProps {
  usernameInput: string
  onUsernameInputChange: (value: string) => void
  onUsernameSubmit: () => void
  onUsernameKeyPress: (e: React.KeyboardEvent<HTMLInputElement>) => void
  disabled?: boolean
}

export default function UsernameForm({
  usernameInput,
  onUsernameInputChange,
  onUsernameSubmit,
  onUsernameKeyPress,
  disabled = false,
}: UsernameFormProps) {
  return (
    <div className="form-group">
      <label className="label">Username</label>
      <div className="username-form">
        <input
          type="text"
          className="input username-input"
          value={usernameInput}
          onChange={(e) => onUsernameInputChange(e.target.value)}
          onKeyPress={onUsernameKeyPress}
          placeholder="Enter your username"
          disabled={disabled}
        />
        <button
          onClick={onUsernameSubmit}
          className="submit-button"
          disabled={disabled || !usernameInput.trim()}
        >
          {disabled ? 'Signing in…' : 'Load'}
        </button>
      </div>
    </div>
  )
}

