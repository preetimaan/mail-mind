import { useState } from 'react'
import { AnalysisRun } from '../api/client'
import EmptyState from './EmptyState'

interface AnalysisRunsListProps {
  runs: AnalysisRun[]
  loading: boolean
  onRetry: (runId: number) => void
}

export default function AnalysisRunsList({ runs, loading, onRetry }: AnalysisRunsListProps) {
  const [expandedFailedGroups, setExpandedFailedGroups] = useState<Set<number>>(new Set())

  if (runs.length === 0) {
    return (
      <EmptyState
        title="No analysis runs yet"
        message="Start your first analysis to see results here."
        icon="🔍"
      />
    )
  }

  // Group consecutive failed runs
  const grouped: Array<{ type: 'single' | 'failed-group', runs: AnalysisRun[], groupIndex?: number }> = []
  let currentFailedGroup: AnalysisRun[] = []
  let groupIndex = 0
  
  for (let i = 0; i < runs.length; i++) {
    const run = runs[i]
    if (run.status === 'failed') {
      currentFailedGroup.push(run)
    } else {
      if (currentFailedGroup.length > 0) {
        if (currentFailedGroup.length > 1) {
          grouped.push({ type: 'failed-group', runs: currentFailedGroup, groupIndex: groupIndex++ })
        } else {
          grouped.push({ type: 'single', runs: currentFailedGroup })
        }
        currentFailedGroup = []
      }
      grouped.push({ type: 'single', runs: [run] })
    }
  }
  
  if (currentFailedGroup.length > 0) {
    if (currentFailedGroup.length > 1) {
      grouped.push({ type: 'failed-group', runs: currentFailedGroup, groupIndex: groupIndex++ })
    } else {
      grouped.push({ type: 'single', runs: currentFailedGroup })
    }
  }

  return (
    <div className="runs-list">
      {grouped.map((group) => {
        if (group.type === 'failed-group' && group.groupIndex !== undefined) {
          const isExpanded = expandedFailedGroups.has(group.groupIndex)
          const firstRun = group.runs[0]
          const lastRun = group.runs[group.runs.length - 1]
          
          return (
            <div key={`group-${group.groupIndex}`}>
              <div 
                className="run-item" 
                style={{ 
                  cursor: 'pointer',
                  backgroundColor: '#fff5f5',
                  border: '1px solid #f8d7da'
                }}
                onClick={() => {
                  const newSet = new Set(expandedFailedGroups)
                  if (isExpanded) {
                    newSet.delete(group.groupIndex!)
                  } else {
                    newSet.add(group.groupIndex!)
                  }
                  setExpandedFailedGroups(newSet)
                }}
              >
                <div>
                  <strong>
                    {group.runs.length} consecutive failed {group.runs.length === 1 ? 'run' : 'runs'}
                  </strong>
                  <div style={{ marginTop: '0.25rem', fontSize: '0.85rem', color: '#666' }}>
                    {new Date(firstRun.start_date).toLocaleDateString()} - {new Date(lastRun.end_date).toLocaleDateString()}
                  </div>
                  {!isExpanded && firstRun.error_message && (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#c33' }}>
                      {firstRun.error_message}
                    </div>
                  )}
                </div>
                <div className="run-status">
                  <span className="status-badge status-failed">
                    {group.runs.length} failed
                  </span>
                  <span style={{ fontSize: '0.9rem', color: '#666' }}>
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </div>
              {isExpanded && (
                <div style={{ marginLeft: '1rem', marginTop: '0.5rem', borderLeft: '2px solid #f8d7da', paddingLeft: '1rem' }}>
                  {group.runs.map((run) => (
                    <div key={run.id} className="run-item" style={{ marginBottom: '0.5rem' }}>
                      <div>
                        <strong>{new Date(run.start_date).toLocaleDateString()}</strong> -{' '}
                        {new Date(run.end_date).toLocaleDateString()}
                        {run.error_message && (
                          <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#c33' }}>
                            {run.error_message}
                          </div>
                        )}
                      </div>
                      <div className="run-status">
                        <span className="status-badge status-failed">
                          failed
                        </span>
                        {run.emails_processed > 0 && (
                          <span>{run.emails_processed} emails</span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onRetry(run.id)
                          }}
                          className="button"
                          style={{ 
                            marginLeft: '1rem',
                            padding: '0.5rem 1rem',
                            fontSize: '0.9rem'
                          }}
                          disabled={loading}
                        >
                          Retry
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        } else {
          const run = group.runs[0]
          return (
            <div key={run.id} className="run-item">
              <div>
                <strong>{new Date(run.start_date).toLocaleDateString()}</strong> -{' '}
                {new Date(run.end_date).toLocaleDateString()}
                {run.status === 'failed' && run.error_message && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#c33' }}>
                    {run.error_message}
                  </div>
                )}
              </div>
              <div className="run-status">
                <span className={`status-badge status-${run.status}`}>
                  {run.status}
                </span>
                {run.emails_processed > 0 && (
                  <span>{run.emails_processed} emails</span>
                )}
                {run.status === 'failed' && (
                  <button
                    onClick={() => onRetry(run.id)}
                    className="button"
                    style={{ 
                      marginLeft: '1rem',
                      padding: '0.5rem 1rem',
                      fontSize: '0.9rem'
                    }}
                    disabled={loading}
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          )
        }
      })}
    </div>
  )
}

