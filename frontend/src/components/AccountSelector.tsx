import { useState } from 'react'
import { EmailAccount } from '../api/client'
import DeleteAccountModal from './DeleteAccountModal'

interface AccountSelectorProps {
  accounts: EmailAccount[]
  selectedAccount: number | null
  onSelect: (accountId: number) => void
  onAddAccount: () => void
  onDeleteAccount: (accountId: number) => void
  onReconnectAccount?: (accountId: number, email: string, provider: string) => void
}

export default function AccountSelector({ 
  accounts, 
  selectedAccount, 
  onSelect, 
  onAddAccount,
  onDeleteAccount,
  onReconnectAccount
}: AccountSelectorProps) {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  if (accounts.length === 0) {
    return (
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0 }}>Email Accounts</h2>
          <button 
            onClick={onAddAccount} 
            className="btn btn-primary"
            style={{ 
              fontSize: '1rem',
              fontWeight: '600',
              gap: '0.5rem',
              minWidth: '140px'
            }}
            type="button"
          >
            <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>+</span> Add Account
          </button>
        </div>
        <p>No email accounts configured for this username.</p>
        <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
          Click "Add Account" to connect your Gmail or Yahoo account.
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <h2 style={{ margin: 0 }}>Email Accounts</h2>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            onClick={onAddAccount}
            className="btn btn-primary"
            style={{
              fontSize: "1rem",
              fontWeight: "600",
              gap: "0.5rem",
              minWidth: "140px",
            }}
            type="button"
          >
            <span style={{ fontSize: "1.2rem", lineHeight: 1 }}>+</span> Add Account
          </button>
          <button
            onClick={() => setDeleteModalOpen(true)}
            type="button"
            className="btn"
            style={{
              background: "none",
              border: "1px solid #ddd",
              color: "#333",
              borderRadius: "4px",
              fontSize: "1rem",
              fontWeight: "500",
              gap: "0.5rem",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#f8f9fa";
              e.currentTarget.style.borderColor = "#bbb";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
              e.currentTarget.style.borderColor = "#ddd";
            }}
          >
            Delete Account
          </button>
        </div>
      </div>
      <div className="form-group">
        <label className="label">Select Account</label>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "stretch" }}>
          <select
            className="input"
            value={selectedAccount || ""}
            onChange={(e) => onSelect(Number(e.target.value))}
            style={{ flex: 1, minWidth: "200px" }}
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.email} ({account.provider})
                {!account.is_active ? " - ⚠️ Needs Reconnection" : ""}
              </option>
            ))}
          </select>
          {selectedAccount &&
            (() => {
              const account = accounts.find((a) => a.id === selectedAccount);
              if (!account) return null;

              return (
                <>
                  {!account.is_active && onReconnectAccount && (
                    <button
                      onClick={() =>
                        onReconnectAccount(
                          account.id,
                          account.email,
                          account.provider
                        )
                      }
                      className="btn btn-primary"
                      style={{
                        fontSize: "0.9rem",
                        fontWeight: "500",
                        whiteSpace: "nowrap",
                        minWidth: "120px",
                      }}
                      title="Reconnect this account (token expired)"
                      type="button"
                    >
                      🔄 Reconnect
                    </button>
                  )}
                </>
              );
            })()}
        </div>
      </div>
      {accounts.length > 0 && (
        <div
          style={{
            marginTop: "1rem",
            paddingTop: "1rem",
            borderTop: "1px solid #eee",
            fontSize: "0.9rem",
            color: "#666",
          }}
        >
          <strong>{accounts.length}</strong> account
          {accounts.length !== 1 ? "s" : ""} configured
          {accounts.some((a) => !a.is_active) && (
            <span
              style={{
                marginLeft: "1rem",
                color: "#dc3545",
                fontWeight: "500",
              }}
            >
              ⚠️ {accounts.filter((a) => !a.is_active).length} account
              {accounts.filter((a) => !a.is_active).length !== 1
                ? "s"
                : ""}{" "}
              need reconnection
            </span>
          )}
        </div>
      )}

      <DeleteAccountModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        accounts={accounts}
        onDelete={onDeleteAccount}
      />
    </div>
  );
}

