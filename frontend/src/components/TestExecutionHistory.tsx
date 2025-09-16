import React from 'react'
import { Clock, CheckCircle, XCircle, AlertCircle, Play, Pause } from 'lucide-react'

interface TestExecution {
  execution_id: string
  test_id: string
  status: 'pending' | 'running' | 'passed' | 'failed' | 'timeout' | 'cancelled'
  started_at?: string
  completed_at?: string
  error_message?: string
  node_results: Record<string, any>
  created_incident_id?: string
}

interface TestExecutionHistoryProps {
  executions: TestExecution[]
  loading: boolean
}

export function TestExecutionHistory({ executions, loading }: TestExecutionHistoryProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'running':
        return <Play className="w-5 h-5 text-blue-600" />
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-600" />
      case 'timeout':
        return <AlertCircle className="w-5 h-5 text-orange-600" />
      case 'cancelled':
        return <Pause className="w-5 h-5 text-gray-600" />
      default:
        return <Clock className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-600 bg-green-100'
      case 'failed': return 'text-red-600 bg-red-100'
      case 'running': return 'text-blue-600 bg-blue-100'
      case 'pending': return 'text-yellow-600 bg-yellow-100'
      case 'timeout': return 'text-orange-600 bg-orange-100'
      case 'cancelled': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatDuration = (startedAt?: string, completedAt?: string) => {
    if (!startedAt) return 'N/A'
    
    const start = new Date(startedAt)
    const end = completedAt ? new Date(completedAt) : new Date()
    const duration = end.getTime() - start.getTime()
    
    if (duration < 1000) return `${duration}ms`
    if (duration < 60000) return `${Math.round(duration / 1000)}s`
    return `${Math.round(duration / 60000)}m`
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading execution history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Test Execution History</h2>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {executions.length} execution{executions.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {executions.length === 0 ? (
          <div className="text-center py-8 text-gray-600">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg">No executions found</p>
            <p className="text-sm mt-1">Execute a test to see results here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {executions.map((execution) => (
              <div key={execution.execution_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getStatusIcon(execution.status)}
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="font-medium text-gray-900">
                          Test Execution {execution.execution_id.slice(0, 8)}
                        </h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(execution.status)}`}>
                          {execution.status}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">Started:</span>
                          <span className="ml-1">{formatDateTime(execution.started_at)}</span>
                        </div>
                        <div>
                          <span className="font-medium">Duration:</span>
                          <span className="ml-1">{formatDuration(execution.started_at, execution.completed_at)}</span>
                        </div>
                        <div>
                          <span className="font-medium">Nodes:</span>
                          <span className="ml-1">{execution.node_results ? Object.keys(execution.node_results).length : 0}</span>
                        </div>
                      </div>

                      {execution.error_message && (
                        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                          <div className="flex items-start">
                            <XCircle className="w-4 h-4 text-red-600 mt-0.5 mr-2 flex-shrink-0" />
                            <div>
                              <div className="text-sm font-medium text-red-800">Error</div>
                              <div className="text-sm text-red-700 mt-1">{execution.error_message}</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {execution.created_incident_id && (
                        <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-md">
                          <div className="flex items-start">
                            <AlertCircle className="w-4 h-4 text-orange-600 mt-0.5 mr-2 flex-shrink-0" />
                            <div>
                              <div className="text-sm font-medium text-orange-800">Incident Created</div>
                              <div className="text-sm text-orange-700 mt-1">
                                Incident ID: {execution.created_incident_id}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Node Results Summary */}
                      {execution.node_results && Object.keys(execution.node_results).length > 0 && (
                        <div className="mt-3">
                          <div className="text-sm font-medium text-gray-700 mb-2">Node Results:</div>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                            {Object.entries(execution.node_results).map(([nodeId, result]) => (
                              <div key={nodeId} className="flex items-center space-x-2 text-xs">
                                <span className={`w-2 h-2 rounded-full ${
                                  result.status === 'passed' ? 'bg-green-500' : 'bg-red-500'
                                }`}></span>
                                <span className="text-gray-600 truncate">{nodeId}</span>
                                <span className={`px-1 py-0.5 rounded text-xs ${
                                  result.status === 'passed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                }`}>
                                  {result.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        // Show detailed results modal
                        console.log('Show detailed results for:', execution.execution_id)
                      }}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium px-3 py-1 rounded-md hover:bg-blue-50"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
