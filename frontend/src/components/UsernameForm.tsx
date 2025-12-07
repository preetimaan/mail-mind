interface UsernameFormProps {
  usernameInput: string
  onUsernameInputChange: (value: string) => void
  onUsernameSubmit: () => void
  onUsernameKeyPress: (e: React.KeyboardEvent<HTMLInputElement>) => void
}

export default function UsernameForm({
  usernameInput,
  onUsernameInputChange,
  onUsernameSubmit,
  onUsernameKeyPress,
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
        />
        <button
          onClick={onUsernameSubmit}
          className="submit-button"
          disabled={!usernameInput.trim()}
        >
          Load
        </button>
      </div>
    </div>
  )
}

