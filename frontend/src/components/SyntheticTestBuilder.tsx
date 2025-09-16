import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Save, Play, Settings, Plus, Trash2, Copy, Eye } from 'lucide-react'
import { DAGCanvas } from './DAGCanvas'
import { NodePalette } from './NodePalette'
import { NodeProperties } from './NodeProperties'
import { TestConfiguration } from './TestConfiguration'

interface SyntheticTest {
  test_id: string
  name: string
  description?: string
  nodes: any[]
  edges: any[]
  enabled: boolean
  tags: string[]
}

interface SyntheticTestBuilderProps {
  test?: SyntheticTest | null
  onSave: () => void
  onTestSelect: (test: SyntheticTest | null) => void
}

export function SyntheticTestBuilder({ test, onSave, onTestSelect }: SyntheticTestBuilderProps) {
  const [currentTest, setCurrentTest] = useState<SyntheticTest>(
    test || {
      test_id: '',
      name: '',
      description: '',
      nodes: [],
      edges: [],
      enabled: true,
      tags: []
    }
  )
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [showNodePalette, setShowNodePalette] = useState(false)
  const [showTestConfig, setShowTestConfig] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<any>(null)

  const canvasRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (test) {
      setCurrentTest(test)
    }
  }, [test])

  const handleNodeAdd = useCallback((nodeType: string) => {
    const newNode = {
      id: `node_${Date.now()}`,
      type: nodeType,
      name: `New ${nodeType}`,
      position: { x: 100, y: 100 },
      config: {}
    }
    
    setCurrentTest(prev => ({
      ...prev,
      nodes: [...prev.nodes, newNode]
    }))
    setShowNodePalette(false)
  }, [])

  const handleNodeUpdate = useCallback((nodeId: string, updates: any) => {
    setCurrentTest(prev => ({
      ...prev,
      nodes: prev.nodes.map(node => 
        node.id === nodeId ? { ...node, ...updates } : node
      )
    }))
  }, [])

  const handleNodeDelete = useCallback((nodeId: string) => {
    setCurrentTest(prev => ({
      ...prev,
      nodes: prev.nodes.filter(node => node.id !== nodeId),
      edges: prev.edges.filter(edge => 
        edge.source !== nodeId && edge.target !== nodeId
      )
    }))
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null)
    }
  }, [selectedNode])

  const handleEdgeAdd = useCallback((sourceId: string, targetId: string) => {
    const newEdge = {
      id: `edge_${Date.now()}`,
      source: sourceId,
      target: targetId
    }
    
    setCurrentTest(prev => ({
      ...prev,
      edges: [...prev.edges, newEdge]
    }))
  }, [])

  const handleEdgeDelete = useCallback((edgeId: string) => {
    setCurrentTest(prev => ({
      ...prev,
      edges: prev.edges.filter(edge => edge.id !== edgeId)
    }))
  }, [])

  const handleSave = async () => {
    try {
      const url = currentTest.test_id 
        ? `/api/v1/synthetic-tests/tests/${currentTest.test_id}`
        : '/api/v1/synthetic-tests/tests/'
      
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

  const handleExecute = async () => {
    if (!currentTest.test_id) {
      alert('Please save the test before executing')
      return
    }
    
    setIsExecuting(true)
    setExecutionResult(null)
    
    try {
      const response = await fetch(`/api/v1/synthetic-tests/tests/${currentTest.test_id}/execute`, {
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

  const handleTestConfigUpdate = (config: Partial<SyntheticTest>) => {
    setCurrentTest(prev => ({ ...prev, ...config }))
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Node Palette */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Node Palette</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          <NodePalette onNodeAdd={handleNodeAdd} />
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {currentTest.name || 'Untitled Test'}
              </h2>
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

        {/* Canvas */}
        <div className="flex-1 relative" ref={canvasRef}>
          <DAGCanvas
            nodes={currentTest.nodes}
            edges={currentTest.edges}
            selectedNode={selectedNode}
            onNodeSelect={setSelectedNode}
            onNodeUpdate={handleNodeUpdate}
            onNodeDelete={handleNodeDelete}
            onEdgeAdd={handleEdgeAdd}
            onEdgeDelete={handleEdgeDelete}
          />
        </div>
      </div>

      {/* Right Sidebar - Node Properties */}
      {selectedNode && (
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Node Properties</h2>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-600 hover:text-gray-900"
              >
                ×
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            <NodeProperties
              node={selectedNode}
              onUpdate={(updates) => handleNodeUpdate(selectedNode.id, updates)}
            />
          </div>
        </div>
      )}

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
                <span className="font-medium">Node Results:</span>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-sm overflow-x-auto">
                  {JSON.stringify(executionResult.node_results, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
