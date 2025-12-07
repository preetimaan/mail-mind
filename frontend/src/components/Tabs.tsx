import './Tabs.css'

export type TabType = 'analysis' | 'insights' | 'settings'

interface TabsProps {
  currentTab: TabType
  onTabChange: (tab: TabType) => void
  hasAccounts: boolean
}

export default function Tabs({ currentTab, onTabChange, hasAccounts }: TabsProps) {
  const tabs = [
    {
      id: 'analysis' as TabType,
      label: 'Analysis',
      icon: '🔍'
    },
    {
      id: 'insights' as TabType,
      label: 'Insights',
      icon: '📈',
      disabled: !hasAccounts
    },
    {
      id: 'settings' as TabType,
      label: 'Settings',
      icon: '⚙️'
    }
  ]

  return (
    <div className="tabs-container">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab ${currentTab === tab.id ? 'active' : ''} ${tab.disabled ? 'disabled' : ''}`}
          onClick={() => !tab.disabled && onTabChange(tab.id)}
          disabled={tab.disabled}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  )
}

