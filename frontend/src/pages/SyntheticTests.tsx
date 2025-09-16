import React, { useState, useEffect, useCallback } from 'react'
import { Plus, Play, Save, Trash2, Settings, Eye, EyeOff } from 'lucide-react'
import { SyntheticTestBuilder } from '../components/SyntheticTestBuilder'
import { TestExecutionHistory } from '../components/TestExecutionHistory'

interface SyntheticTest {
  test_id: string
  name: string
  description?: string
  nodes: any[]
  edges: any[]
  created_at: string
  updated_at: string
  enabled: boolean
  tags: string[]
}

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

export default function SyntheticTests() {
  const [activeTab, setActiveTab] = useState<'builder' | 'tests' | 'executions'>('builder')
  const [tests, setTests] = useState<SyntheticTest[]>([])
  const [executions, setExecutions] = useState<TestExecution[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTest, setSelectedTest] = useState<SyntheticTest | null>(null)

  const loadTests = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/synthetic-tests/tests/')
      if (response.ok) {
        const data = await response.json()
        setTests(data)
      }
    } catch (error) {
      console.error('Failed to load tests:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadExecutions = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/synthetic-tests/executions/')
      if (response.ok) {
        const data = await response.json()
        setExecutions(data)
      }
    } catch (error) {
      console.error('Failed to load executions:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const executeTest = async (testId: string) => {
    try {
      const response = await fetch(`/api/v1/synthetic-tests/tests/${testId}/execute`, {
        method: 'POST'
      })
      if (response.ok) {
        await loadExecutions()
      }
    } catch (error) {
      console.error('Failed to execute test:', error)
    }
  }

  const deleteTest = async (testId: string) => {
    if (!confirm('Are you sure you want to delete this test?')) return
    
    try {
      const response = await fetch(`/api/v1/synthetic-tests/tests/${testId}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        await loadTests()
      }
    } catch (error) {
      console.error('Failed to delete test:', error)
    }
  }

  useEffect(() => {
    if (activeTab === 'tests') {
      loadTests()
    } else if (activeTab === 'executions') {
      loadExecutions()
    }
  }, [activeTab, loadTests, loadExecutions])

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Synthetic Test Framework</h1>
            <p className="text-sm text-gray-600 mt-1">
              Create and manage synthetic tests with DAG-based workflows
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setActiveTab('builder')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center text-sm font-medium"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Test
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab('builder')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'builder'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Test Builder
          </button>
          <button
            onClick={() => setActiveTab('tests')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tests'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tests
          </button>
          <button
            onClick={() => setActiveTab('executions')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'executions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Executions
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="px-6 py-6">
        {activeTab === 'builder' && (
          <SyntheticTestBuilder
            test={selectedTest}
            onSave={loadTests}
            onTestSelect={setSelectedTest}
          />
        )}

        {activeTab === 'tests' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Synthetic Tests</h2>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {tests.length} test{tests.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading tests...</p>
                </div>
              ) : tests.length === 0 ? (
                <div className="text-center py-8 text-gray-600">
                  <p className="text-lg">No tests found</p>
                  <p className="text-sm mt-1">Create your first synthetic test using the Test Builder</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {tests.map((test) => (
                    <div key={test.test_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="font-medium text-gray-900">{test.name}</h3>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              test.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {test.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                          </div>
                          {test.description && (
                            <p className="text-sm text-gray-600 mb-2">{test.description}</p>
                          )}
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>{test.nodes.length} nodes</span>
                            <span>{test.edges.length} connections</span>
                            <span>Created {new Date(test.created_at).toLocaleDateString()}</span>
                          </div>
                          {test.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {test.tags.map((tag) => (
                                <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setSelectedTest(test)}
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium px-3 py-1 rounded-md hover:bg-blue-50"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => executeTest(test.test_id)}
                            className="text-green-600 hover:text-green-700 text-sm font-medium px-3 py-1 rounded-md hover:bg-green-50 flex items-center"
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Run
                          </button>
                          <button
                            onClick={() => deleteTest(test.test_id)}
                            className="text-red-600 hover:text-red-700 text-sm font-medium px-3 py-1 rounded-md hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'executions' && (
          <TestExecutionHistory executions={executions} loading={loading} />
        )}
      </div>
    </div>
  )
}
