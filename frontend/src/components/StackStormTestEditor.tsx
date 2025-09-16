import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Save, Play, Settings, Code, FileText, Zap, Shield, Clock } from 'lucide-react'
import { TestConfiguration } from './TestConfiguration'

interface StackStormTest {
  test_id: string
  name: string
  description?: string
  test_type: 'action' | 'workflow' | 'rule' | 'sensor'
  stackstorm_pack: string
  test_code: string
  test_parameters: Record<string, any>
  expected_result?: Record<string, any>
  timeout: number
  retry_count: number
  retry_delay: number
  enabled: boolean
  tags: string[]
  deployed: boolean
}

interface StackStormTestEditorProps {
  test?: StackStormTest | null
  onSave: () => void
  onTestSelect: (test: StackStormTest | null) => void
}

export function StackStormTestEditor({ test, onSave, onTestSelect }: StackStormTestEditorProps) {
  const [currentTest, setCurrentTest] = useState<StackStormTest>(
    test || {
      test_id: '',
      name: '',
      description: '',
      test_type: 'action',
      stackstorm_pack: 'synthetic_tests',
      test_code: `#!/usr/bin/env python3
"""
Synthetic test action
"""

import json
import sys
from datetime import datetime, timezone

def main():
    """
    Main function for synthetic test
    """
    try:
        # Your test logic here
        # Example: Check if a service is responding
        
        # Simulate test logic
        result = {
            "status": "success",
            "message": "Test passed successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "response_time": 0.5,
                "status_code": 200
            }
        }
        
        print(json.dumps(result))
        return result
        
    except Exception as e:
        # Test failed
        result = {
            "status": "failed",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(json.dumps(result))
        return result

if __name__ == "__main__":
    main()`,
      test_parameters: {},
      expected_result: {},
      timeout: 300,
      retry_count: 0,
      retry_delay: 5,
      enabled: true,
      tags: [],
      deployed: false
    }
  )
  const [showTestConfig, setShowTestConfig] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<any>(null)

  const editorRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (test) {
      setCurrentTest(test)
    }
  }, [test])

  const handleSave = async () => {
    try {
      const url = currentTest.test_id 
        ? `/api/v1/stackstorm-tests/tests/${currentTest.test_id}`
        : '/api/v1/stackstorm-tests/tests/'
      
      const method = currentTest.test_id ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(currentTest)
      })
      
      if (response.ok) {
        const savedTest = await response.json()
        setCurrentTest(savedTest)
        onSave()
        alert('Test saved successfully!')
      } else {
        throw new Error('Failed to save test')
      }
    } catch (error) {
      console.error('Failed to save test:', error)
      alert('Failed to save test')
    }
  }

  const handleDeploy = async () => {
    if (!currentTest.test_id) {
      alert('Please save the test before deploying')
      return
    }
    
    try {
      const response = await fetch(`/api/v1/stackstorm-tests/tests/${currentTest.test_id}/deploy`, {
        method: 'POST'
      })
      
      if (response.ok) {
        setCurrentTest(prev => ({ ...prev, deployed: true }))
        alert('Test deployed successfully to StackStorm!')
      } else {
        throw new Error('Failed to deploy test')
      }
    } catch (error) {
      console.error('Failed to deploy test:', error)
      alert('Failed to deploy test to StackStorm')
    }
  }

  const handleExecute = async () => {
    if (!currentTest.test_id) {
      alert('Please save the test before executing')
      return
    }
    
    setIsExecuting(true)
    setExecutionResult(null)
    
    try {
      const response = await fetch(`/api/v1/stackstorm-tests/tests/${currentTest.test_id}/execute`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const result = await response.json()
        setExecutionResult(result)
      } else {
        throw new Error('Failed to execute test')
      }
    } catch (error) {
      console.error('Failed to execute test:', error)
      alert('Failed to execute test')
    } finally {
      setIsExecuting(false)
    }
  }

  const handleTestConfigUpdate = (config: Partial<StackStormTest>) => {
    setCurrentTest(prev => ({ ...prev, ...config }))
  }

  const getTestTypeIcon = (type: string) => {
    switch (type) {
      case 'action': return <Zap className="w-4 h-4" />
      case 'workflow': return <FileText className="w-4 h-4" />
      case 'rule': return <Shield className="w-4 h-4" />
      case 'sensor': return <Clock className="w-4 h-4" />
      default: return <Code className="w-4 h-4" />
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                {getTestTypeIcon(currentTest.test_type)}
                {currentTest.name || 'Untitled Test'}
              </h2>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                {currentTest.test_type}
              </span>
              {currentTest.deployed && (
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                  Deployed
                </span>
              )}
              <button
                onClick={() => setShowTestConfig(true)}
                className="text-gray-600 hover:text-gray-900 p-1 rounded"
                title="Test Configuration"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSave}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center text-sm font-medium"
              >
                <Save className="w-4 h-4 mr-2" />
                Save
              </button>
              {currentTest.test_id && !currentTest.deployed && (
                <button
                  onClick={handleDeploy}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center text-sm font-medium"
                >
                  <Code className="w-4 h-4 mr-2" />
                  Deploy to StackStorm
                </button>
              )}
              <button
                onClick={handleExecute}
                disabled={isExecuting || !currentTest.test_id}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center text-sm font-medium"
              >
                <Play className="w-4 h-4 mr-2" />
                {isExecuting ? 'Executing...' : 'Execute'}
              </button>
            </div>
          </div>
        </div>

        {/* Code Editor */}
        <div className="flex-1 flex">
          <div className="flex-1 p-4">
            <div className="bg-white rounded-lg border border-gray-200 h-full flex flex-col">
              <div className="border-b border-gray-200 px-4 py-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-900">Test Code</h3>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <span>Python</span>
                    <span>•</span>
                    <span>{currentTest.test_code.length} characters</span>
                  </div>
                </div>
              </div>
              <div className="flex-1 p-4">
                <textarea
                  ref={editorRef}
                  value={currentTest.test_code}
                  onChange={(e) => setCurrentTest(prev => ({ ...prev, test_code: e.target.value }))}
                  className="w-full h-full font-mono text-sm border-0 resize-none focus:outline-none focus:ring-0"
                  placeholder="Enter your StackStorm test code here..."
                  spellCheck={false}
                />
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="border-b border-gray-200 px-4 py-3">
              <h3 className="text-sm font-medium text-gray-900">Test Parameters</h3>
            </div>
            <div className="flex-1 p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Test Type
                </label>
                <select
                  value={currentTest.test_type}
                  onChange={(e) => setCurrentTest(prev => ({ ...prev, test_type: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="action">Action</option>
                  <option value="workflow">Workflow</option>
                  <option value="rule">Rule</option>
                  <option value="sensor">Sensor</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  StackStorm Pack
                </label>
                <input
                  type="text"
                  value={currentTest.stackstorm_pack}
                  onChange={(e) => setCurrentTest(prev => ({ ...prev, stackstorm_pack: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="synthetic_tests"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={currentTest.timeout}
                  onChange={(e) => setCurrentTest(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="3600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Retry Count
                </label>
                <input
                  type="number"
                  value={currentTest.retry_count}
                  onChange={(e) => setCurrentTest(prev => ({ ...prev, retry_count: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Retry Delay (seconds)
                </label>
                <input
                  type="number"
                  value={currentTest.retry_delay}
                  onChange={(e) => setCurrentTest(prev => ({ ...prev, retry_delay: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="300"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Test Parameters (JSON)
                </label>
                <textarea
                  value={JSON.stringify(currentTest.test_parameters, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value)
                      setCurrentTest(prev => ({ ...prev, test_parameters: parsed }))
                    } catch {
                      // Invalid JSON, keep the text for editing
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={4}
                  placeholder='{"param1": "value1"}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expected Result (JSON)
                </label>
                <textarea
                  value={JSON.stringify(currentTest.expected_result, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value)
                      setCurrentTest(prev => ({ ...prev, expected_result: parsed }))
                    } catch {
                      // Invalid JSON, keep the text for editing
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={4}
                  placeholder='{"status": "success"}'
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Test Configuration Modal */}
      {showTestConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Test Configuration</h3>
              <button
                onClick={() => setShowTestConfig(false)}
                className="text-gray-600 hover:text-gray-900"
              >
                ×
              </button>
            </div>
            <TestConfiguration
              test={currentTest}
              onUpdate={handleTestConfigUpdate}
              onClose={() => setShowTestConfig(false)}
            />
          </div>
        </div>
      )}

      {/* Execution Result Modal */}
      {executionResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Execution Result</h3>
              <button
                onClick={() => setExecutionResult(null)}
                className="text-gray-600 hover:text-gray-900"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <span className="font-medium">Status: </span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  executionResult.status === 'passed' 
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {executionResult.status}
                </span>
              </div>
              {executionResult.error_message && (
                <div>
                  <span className="font-medium">Error: </span>
                  <span className="text-red-600">{executionResult.error_message}</span>
                </div>
              )}
              {executionResult.created_incident_id && (
                <div>
                  <span className="font-medium">Incident Created: </span>
                  <span className="text-blue-600">{executionResult.created_incident_id}</span>
                </div>
              )}
              <div>
                <span className="font-medium">Output Data:</span>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-sm overflow-x-auto">
                  {JSON.stringify(executionResult.output_data, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
