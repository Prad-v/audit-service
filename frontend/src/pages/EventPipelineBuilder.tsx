import React, { useState, useCallback, useRef, useEffect } from 'react'
import { 
  Plus, 
  Settings, 
  Save, 
  Trash2,
  Eye,
  EyeOff,
  ChevronLeft,
  Zap,
  Filter,
  Route,
  ArrowRight,
  Play,
  Pause,
  RotateCcw,
  Webhook,
  RefreshCw,
  X
} from 'lucide-react'
import PipelineNodeConfig from '../components/PipelineNodeConfig'

// Event Management Node Types (using our existing system)
interface EventNode {
  id: string
  type: 'event_subscription' | 'event_processor' | 'event_sink'
  name: string
  config: any
  position: { x: number; y: number }
  status: 'idle' | 'running' | 'error' | 'success'
  metrics?: {
    eventsPerSecond?: number
    totalEvents?: number
    lastProcessed?: string
    errorCount?: number
  }
  validationErrors?: string[]
  // Event management specific fields
  eventSubscriptionId?: string
  eventProcessorId?: string
  eventSinkId?: string
  resourceName?: string // The actual resource name from Event Management
}

// Event Management Connection Types
interface EventConnection {
  id: string
  sourceId: string
  targetId: string
  type: 'event_flow' | 'control' | 'error'
  label?: string
  status: 'active' | 'inactive' | 'error'
  // Event routing configuration
  routingRules?: {
    conditions: any[]
    transformations: any[]
  }
}

// Event Pipeline Configuration
interface EventPipelineConfig {
  id: string
  name: string
  description?: string
  nodes: EventNode[]
  connections: EventConnection[]
  status: 'draft' | 'active' | 'paused' | 'error'
  createdAt: string
  updatedAt: string
  executionMode: 'streaming' | 'batch'
  parallelism: number
}

// DAG State
interface DAGState {
  nodes: EventNode[]
  connections: EventConnection[]
  selectedNode: string | null
  selectedConnection: string | null
  isConnecting: boolean
  connectionStart: string | null
  dragState: {
    isDragging: boolean
    nodeId: string | null
    offset: { x: number; y: number }
  }
  canvasTransform: {
    scale: number
    offset: { x: number; y: number }
  }
}

// Event Management Resources
interface EventManagementResources {
  eventSubscriptions: Array<{ id: string; name: string; type: string; config: any }>
  eventProcessors: Array<{ id: string; name: string; type: string; config: any }>
  eventSinks: Array<{ id: string; name: string; type: string; config: any }>
}

const EventPipelineBuilder: React.FC = () => {
  // State
  const [pipelines, setPipelines] = useState<EventPipelineConfig[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<EventPipelineConfig | null>(null)
  const [dagState, setDagState] = useState<DAGState>({
    nodes: [],
    connections: [],
    selectedNode: null,
    selectedConnection: null,
    isConnecting: false,
    connectionStart: null,
    dragState: {
      isDragging: false,
      nodeId: null,
      offset: { x: 0, y: 0 }
    },
    canvasTransform: {
      scale: 1,
      offset: { x: 0, y: 0 }
    }
  })
  
  const [configPanelOpen, setConfigPanelOpen] = useState(false)
  const [configNode, setConfigNode] = useState<EventNode | null>(null)
  const [pipelineStatus, setPipelineStatus] = useState<'stopped' | 'running' | 'paused'>('stopped')
  const [showMetrics, setShowMetrics] = useState(true)
  const [validationMode, setValidationMode] = useState<'realtime' | 'manual'>('realtime')
  
  // Event Management Resources
  const [eventResources, setEventResources] = useState<EventManagementResources>({
    eventSubscriptions: [],
    eventProcessors: [],
    eventSinks: []
  })
  const [isLoadingResources, setIsLoadingResources] = useState(false)

  // Refs
  const canvasRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  // Load Event Management Resources
  const loadEventResources = useCallback(async () => {
    setIsLoadingResources(true)
    try {
      // Load Event Subscriptions - using subscriptions endpoint
      const subscriptionsResponse = await fetch('/api/v1/subscriptions/subscriptions')
      if (subscriptionsResponse.ok) {
        const subscriptions = await subscriptionsResponse.json()
        setEventResources(prev => ({ ...prev, eventSubscriptions: subscriptions.subscriptions || [] }))
      }
      
      // Load Event Processors
      const processorsResponse = await fetch('/api/v1/processors')
      if (processorsResponse.ok) {
        const processors = await processorsResponse.json()
        setEventResources(prev => ({ ...prev, eventProcessors: processors.processors || [] }))
      }
      
      // Load Event Sinks - using alerts as sinks for now
      const sinksResponse = await fetch('/api/v1/alerts/providers')
      if (sinksResponse.ok) {
        const sinks = await sinksResponse.json()
        setEventResources(prev => ({ ...prev, eventSinks: sinks.data || [] }))
      }
    } catch (error) {
      console.error('Failed to load event resources:', error)
    } finally {
      setIsLoadingResources(false)
    }
  }, [])

  // Load resources on component mount
  useEffect(() => {
    loadEventResources()
  }, [loadEventResources])

  // Sample pipeline templates using our event management system
  const pipelineTemplates = [
    {
      name: 'Webhook to Event Processor Pipeline',
      description: 'Receive webhook events, process through event processor, and route to multiple sinks',
      template: {
        nodes: [
          { 
            id: 'webhook-subscription-1', 
            type: 'event_subscription', 
            name: 'Webhook Events', 
            config: { 
              type: 'webhook', 
              endpoint: '/api/webhook/audit', 
              method: 'POST',
              headers: { 'Content-Type': 'application/json' }
            }, 
            position: { x: 100, y: 100 }, 
            status: 'idle',
            eventSubscriptionId: 'webhook-001',
            resourceName: 'webhook-001'
          },
          { 
            id: 'event-processor-1', 
            type: 'event_processor', 
            name: 'Audit Event Processor', 
            config: { 
              type: 'transformer',
              rules: [
                {
                  type: 'field_mapping',
                  source: 'message',
                  target: 'processed_message'
                },
                {
                  type: 'field_transformation',
                  field: 'level',
                  operation: 'uppercase'
                }
              ]
            }, 
            position: { x: 350, y: 100 }, 
            status: 'idle',
            eventProcessorId: 'processor-001',
            resourceName: 'processor-001'
          },
          { 
            id: 'event-sink-1', 
            type: 'event_sink', 
            name: 'Elasticsearch Sink', 
            config: { 
              type: 'elasticsearch', 
              endpoint: 'http://es:9200', 
              index: 'audit-events',
              batchSize: 1000
            }, 
            position: { x: 600, y: 100 }, 
            status: 'idle',
            eventSinkId: 'sink-001',
            resourceName: 'sink-001'
          },
          { 
            id: 'event-sink-2', 
            type: 'event_sink', 
            name: 'Kafka Sink', 
            config: { 
              type: 'kafka', 
              bootstrapServers: 'kafka:9092', 
              topic: 'audit-events',
              batchSize: 500
            }, 
            position: { x: 600, y: 250 }, 
            status: 'idle',
            eventSinkId: 'sink-002',
            resourceName: 'sink-002'
          }
        ],
        connections: [
          { 
            id: 'conn-1', 
            sourceId: 'webhook-subscription-1', 
            targetId: 'event-processor-1', 
            type: 'event_flow', 
            status: 'active',
            routingRules: {
              conditions: [],
              transformations: []
            }
          },
          { 
            id: 'conn-2', 
            sourceId: 'event-processor-1', 
            targetId: 'event-sink-1', 
            type: 'event_flow', 
            status: 'active',
            routingRules: {
              conditions: [{ field: 'level', operator: 'equals', value: 'error' }],
              transformations: []
            }
          },
          { 
            id: 'conn-3', 
            sourceId: 'event-processor-1', 
            targetId: 'event-sink-2', 
            type: 'event_flow', 
            status: 'active',
            routingRules: {
              conditions: [{ field: 'level', operator: 'equals', value: 'info' }],
              transformations: []
            }
          }
        ]
      }
    }
  ]

  // DAG Validation Functions
  const validateDAG = useCallback((nodes: EventNode[], connections: EventConnection[]): { isValid: boolean; errors: string[] } => {
    const errors: string[] = []
    
    // Check for cycles (DFS)
    const visited = new Set<string>()
    const recStack = new Set<string>()
    
    const hasCycle = (nodeId: string): boolean => {
      if (recStack.has(nodeId)) return true
      if (visited.has(nodeId)) return false
      
      visited.add(nodeId)
      recStack.add(nodeId)
      
      const outgoingConnections = connections.filter(c => c.sourceId === nodeId)
      for (const conn of outgoingConnections) {
        if (hasCycle(conn.targetId)) return true
      }
      
      recStack.delete(nodeId)
      return false
    }
    
    // Check each node for cycles
    for (const node of nodes) {
      if (hasCycle(node.id)) {
        errors.push(`Cycle detected involving node: ${node.name}`)
        break
      }
    }
    
    // Check for orphaned nodes
    const connectedNodes = new Set<string>()
    connections.forEach(conn => {
      connectedNodes.add(conn.sourceId)
      connectedNodes.add(conn.targetId)
    })
    
    const orphanedNodes = nodes.filter(node => !connectedNodes.has(node.id))
    if (orphanedNodes.length > 0) {
      errors.push(`Orphaned nodes found: ${orphanedNodes.map(n => n.name).join(', ')}`)
    }
    
    // Check for sources and sinks
    const sources = nodes.filter(n => n.type === 'event_subscription')
    const sinks = nodes.filter(n => n.type === 'event_sink')
    
    if (sources.length === 0) {
      errors.push('Pipeline must have at least one event subscription (source)')
    }
    
    if (sinks.length === 0) {
      errors.push('Pipeline must have at least one event sink (destination)')
    }
    
    return { isValid: errors.length === 0, errors }
  }, [])

  // Real-time validation
  useEffect(() => {
    if (validationMode === 'realtime' && dagState.nodes.length > 0) {
      const { errors } = validateDAG(dagState.nodes, dagState.connections)
      
      // Update node validation errors
      setDagState(prev => ({
        ...prev,
        nodes: prev.nodes.map(node => ({
          ...node,
          validationErrors: errors.filter(err => err.includes(node.name))
        }))
      }))
    }
  }, [dagState.nodes, dagState.connections, validationMode, validateDAG])

  // Node Management
  const addNode = useCallback((type: EventNode['type'], position: { x: number; y: number }, resourceId?: string, resourceName?: string) => {
    const newNode: EventNode = {
      id: `node-${Date.now()}`,
      type,
      name: resourceName || `${type.replace('_', ' ')}-${dagState.nodes.length + 1}`,
      config: {},
      position,
      status: 'idle',
      resourceName: resourceName || undefined
    }
    
    // Set the appropriate ID based on type
    if (type === 'event_subscription' && resourceId) {
      newNode.eventSubscriptionId = resourceId
    } else if (type === 'event_processor' && resourceId) {
      newNode.eventProcessorId = resourceId
    } else if (type === 'event_sink' && resourceId) {
      newNode.eventSinkId = resourceId
    }
    
    setDagState(prev => ({
      ...prev,
      nodes: [...prev.nodes, newNode]
    }))
  }, [dagState.nodes.length])

  const updateNode = useCallback((nodeId: string, updates: Partial<EventNode>) => {
    setDagState(prev => ({
      ...prev,
      nodes: prev.nodes.map(node => 
        node.id === nodeId ? { ...node, ...updates } : node
      )
    }))
  }, [])

  const deleteNode = useCallback((nodeId: string) => {
    setDagState(prev => ({
      ...prev,
      nodes: prev.nodes.filter(node => node.id !== nodeId),
      connections: prev.connections.filter(conn => 
        conn.sourceId !== nodeId && conn.targetId !== nodeId
      )
    }))
  }, [])

  // Connection Management
  const addConnection = useCallback((sourceId: string, targetId: string) => {
    // Prevent self-connections
    if (sourceId === targetId) return
    
    // Check if connection already exists
    const exists = dagState.connections.some(conn => 
      conn.sourceId === sourceId && conn.targetId === targetId
    )
    
    if (exists) return
    
    const newConnection: EventConnection = {
      id: `conn-${Date.now()}`,
      sourceId,
      targetId,
      type: 'event_flow',
      status: 'active',
      routingRules: {
        conditions: [],
        transformations: []
      }
    }
    
    setDagState(prev => ({
      ...prev,
      connections: [...prev.connections, newConnection]
    }))
  }, [dagState.connections])

  const deleteConnection = useCallback((connectionId: string) => {
    setDagState(prev => ({
      ...prev,
      connections: prev.connections.filter(conn => conn.id !== connectionId)
    }))
  }, [])

  // Canvas Interactions
  const handleCanvasMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target === canvasRef.current) {
      setDagState(prev => ({
        ...prev,
        selectedNode: null,
        selectedConnection: null
      }))
    }
  }, [])

  const handleNodeMouseDown = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    
    const node = dagState.nodes.find(n => n.id === nodeId)
    if (!node) return
    
    setDagState(prev => ({
      ...prev,
      selectedNode: nodeId,
      selectedConnection: null,
      dragState: {
        isDragging: true,
        nodeId,
        offset: {
          x: e.clientX - node.position.x,
          y: e.clientY - node.position.y
        }
      }
    }))
  }, [dagState.nodes])

  const handleNodeMouseMove = useCallback((e: React.MouseEvent) => {
    if (dagState.dragState.isDragging && dagState.dragState.nodeId) {
      const nodeId = dagState.dragState.nodeId
      const newPosition = {
        x: e.clientX - dagState.dragState.offset.x,
        y: e.clientY - dagState.dragState.offset.y
      }
      
      updateNode(nodeId, { position: newPosition })
    }
  }, [dagState.dragState, updateNode])

  const handleNodeMouseUp = useCallback(() => {
    setDagState(prev => ({
      ...prev,
      dragState: {
        isDragging: false,
        nodeId: null,
        offset: { x: 0, y: 0 }
      }
    }))
  }, [])

  // Connection Creation - FIXED
  const startConnection = useCallback((nodeId: string) => {
    console.log('Starting connection from node:', nodeId)
    setDagState(prev => ({
      ...prev,
      isConnecting: true,
      connectionStart: nodeId
    }))
  }, [])

  const completeConnection = useCallback((targetNodeId: string) => {
    console.log('Completing connection to node:', targetNodeId, 'from:', dagState.connectionStart)
    if (dagState.connectionStart && dagState.connectionStart !== targetNodeId) {
      addConnection(dagState.connectionStart, targetNodeId)
      console.log('Connection created successfully')
    } else {
      console.log('Invalid connection attempt')
    }
    
    setDagState(prev => ({
      ...prev,
      isConnecting: false,
      connectionStart: null
    }))
  }, [dagState.connectionStart, addConnection])

  // Handle canvas click for connection completion
  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    if (dagState.isConnecting && dagState.connectionStart) {
      console.log('Canvas clicked while connecting, canceling connection')
      // If clicking on canvas (not on a node), cancel the connection
      if (e.target === canvasRef.current) {
        setDagState(prev => ({
          ...prev,
          isConnecting: false,
          connectionStart: null
        }))
      }
    }
  }, [dagState.isConnecting, dagState.connectionStart])

  // Pipeline Operations
  const createNewPipeline = useCallback(() => {
    const newPipeline: EventPipelineConfig = {
      id: `pipeline-${Date.now()}`,
      name: 'New Event Pipeline',
      description: 'Event processing pipeline using our event management system',
      nodes: [],
      connections: [],
      status: 'draft',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      executionMode: 'streaming',
      parallelism: 1
    }
    
    setPipelines(prev => [...prev, newPipeline])
    setSelectedPipeline(newPipeline)
    setDagState({
      nodes: [],
      connections: [],
      selectedNode: null,
      selectedConnection: null,
      isConnecting: false,
      connectionStart: null,
      dragState: { isDragging: false, nodeId: null, offset: { x: 0, y: 0 } },
      canvasTransform: { scale: 1, offset: { x: 0, y: 0 } }
    })
  }, [])

  const loadPipelineTemplate = useCallback((template: any) => {
    if (selectedPipeline) {
      setDagState(prev => ({
        ...prev,
        nodes: template.template.nodes,
        connections: template.template.connections
      }))
    }
  }, [selectedPipeline])

  const savePipeline = useCallback(() => {
    if (selectedPipeline) {
      const updatedPipeline = {
        ...selectedPipeline,
        nodes: dagState.nodes,
        connections: dagState.connections,
        updatedAt: new Date().toISOString()
      }
      
      setPipelines(prev => 
        prev.map(p => p.id === selectedPipeline.id ? updatedPipeline : p)
      )
      setSelectedPipeline(updatedPipeline)
    }
  }, [selectedPipeline, dagState.nodes, dagState.connections])

  // Pipeline Execution
  const startPipeline = useCallback(() => {
    const { isValid, errors } = validateDAG(dagState.nodes, dagState.connections)
    
    if (!isValid) {
      alert(`Pipeline validation failed:\n${errors.join('\n')}`)
      return
    }
    
    setPipelineStatus('running')
    // Here you would call the backend to start the pipeline
  }, [dagState.nodes, dagState.connections, validateDAG])

  const stopPipeline = useCallback(() => {
    setPipelineStatus('stopped')
    // Here you would call the backend to stop the pipeline
  }, [])

  const pausePipeline = useCallback(() => {
    setPipelineStatus('paused')
    // Here you would call the backend to pause the pipeline
  }, [])

  // Node Configuration
  const openNodeConfig = useCallback((node: EventNode) => {
    setConfigNode(node)
    setConfigPanelOpen(true)
  }, [])

  const closeNodeConfig = useCallback(() => {
    setConfigPanelOpen(false)
    setConfigNode(null)
  }, [])

  const saveNodeConfig = useCallback((nodeId: string, config: any) => {
    updateNode(nodeId, { config })
    closeNodeConfig()
  }, [updateNode, closeNodeConfig])

  // Utility Functions
  const getNodeIcon = (type: EventNode['type']) => {
    switch (type) {
      case 'event_subscription': return <Webhook className="w-5 h-5" />
      case 'event_processor': return <Filter className="w-5 h-5" />
      case 'event_sink': return <Route className="w-5 h-5" />
      default: return <Zap className="w-5 h-5" />
    }
  }

  const getNodeColor = (type: EventNode['type']) => {
    switch (type) {
      case 'event_subscription': return 'bg-blue-100 text-blue-700 border-blue-300'
      case 'event_processor': return 'bg-green-100 text-green-700 border-green-300'
      case 'event_sink': return 'bg-purple-100 text-purple-700 border-purple-300'
      default: return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  const getStatusColor = (status: EventNode['status']) => {
    switch (status) {
      case 'running': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      case 'success': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  // Render DAG Canvas
  const renderDAGCanvas = () => (
    <div 
      ref={canvasRef}
      className="flex-1 relative overflow-hidden bg-gray-50 border border-gray-200 rounded-lg"
      onMouseDown={handleCanvasMouseDown}
      onMouseMove={handleNodeMouseMove}
      onMouseUp={handleNodeMouseUp}
      onClick={handleCanvasClick}
    >
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{
          transform: `scale(${dagState.canvasTransform.scale}) translate(${dagState.canvasTransform.offset.x}px, ${dagState.canvasTransform.offset.y}px)`
        }}
      >
        {/* Render connections */}
        {dagState.connections.map(connection => {
          const sourceNode = dagState.nodes.find(n => n.id === connection.sourceId)
          const targetNode = dagState.nodes.find(n => n.id === connection.targetId)
          
          if (!sourceNode || !targetNode) return null
          
          const fromX = sourceNode.position.x + 200
          const fromY = sourceNode.position.y + 50
          const toX = targetNode.position.x
          const toY = targetNode.position.y + 50
          
          return (
            <g key={connection.id}>
              <path
                d={`M ${fromX} ${fromY} L ${toX} ${toY}`}
                stroke={connection.status === 'error' ? '#ef4444' : '#6b7280'}
                strokeWidth="2"
                fill="none"
                markerEnd="url(#arrowhead)"
                className="cursor-pointer hover:stroke-blue-500"
                onClick={() => deleteConnection(connection.id)}
              />
              {/* Connection label */}
              <text
                x={(fromX + toX) / 2}
                y={(fromY + toY) / 2 - 10}
                textAnchor="middle"
                className="text-xs fill-gray-600 pointer-events-none"
              >
                {connection.label || 'Event Flow'}
              </text>
            </g>
          )
        })}
        
        {/* Arrow marker definition */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#6B7280" />
          </marker>
        </defs>
      </svg>

      {/* Render nodes */}
      {dagState.nodes.map(node => (
        <div
          key={node.id}
          className={`absolute border-2 rounded-lg p-4 bg-white shadow-md cursor-move ${
            dagState.selectedNode === node.id ? 'ring-2 ring-blue-500' : ''
          } ${node.validationErrors && node.validationErrors.length > 0 ? 'border-red-500' : 'border-gray-300'}`}
          style={{
            left: node.position.x,
            top: node.position.y,
            width: 200
          }}
          onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
        >
          {/* Node header */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className={`p-2 rounded-md ${getNodeColor(node.type)}`}>
                {getNodeIcon(node.type)}
              </div>
              <span className="font-medium text-gray-900">{node.name}</span>
            </div>
            
            {/* Node actions */}
            <div className="flex items-center space-x-1">
              <button
                onClick={() => openNodeConfig(node)}
                className="p-1 text-blue-600 hover:text-blue-700"
                title="Configure node"
              >
                <Settings className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => startConnection(node.id)}
                className={`p-1 ${dagState.isConnecting && dagState.connectionStart === node.id ? 'text-red-600' : 'text-green-600 hover:text-green-700'}`}
                title={dagState.isConnecting && dagState.connectionStart === node.id ? 'Click target node to complete connection' : 'Start connection'}
              >
                <ArrowRight className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => deleteNode(node.id)}
                className="p-1 text-red-600 hover:text-red-700"
                title="Delete node"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Node info */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Type:</span>
              <span className="text-xs font-medium text-gray-700 capitalize">{node.type.replace('_', ' ')}</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Status:</span>
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(node.status)} text-white`}>
                {node.status}
              </span>
            </div>

            {/* Event management specific info */}
            {node.eventSubscriptionId && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Subscription ID:</span>
                <span className="text-xs font-medium text-gray-700">{node.eventSubscriptionId}</span>
              </div>
            )}

            {node.eventProcessorId && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Processor ID:</span>
                <span className="text-xs font-medium text-gray-700">{node.eventProcessorId}</span>
              </div>
            )}

            {node.eventSinkId && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Sink ID:</span>
                <span className="text-xs font-medium text-gray-700">{node.eventSinkId}</span>
              </div>
            )}

            {/* Validation errors */}
            {node.validationErrors && node.validationErrors.length > 0 && (
              <div className="pt-2 border-t border-red-200">
                <div className="text-xs text-red-600 font-medium">Validation Errors:</div>
                {node.validationErrors.map((error, idx) => (
                  <div key={idx} className="text-xs text-red-500">• {error}</div>
                ))}
              </div>
            )}

            {/* Metrics */}
            {showMetrics && node.metrics && (
              <div className="pt-2 border-t border-gray-200">
                <div className="text-xs text-gray-500 mb-1">Metrics:</div>
                {node.metrics.eventsPerSecond && (
                  <div className="text-xs text-gray-700">
                    Events/sec: {node.metrics.eventsPerSecond}
                  </div>
                )}
                {node.metrics.totalEvents && (
                  <div className="text-xs text-gray-700">
                    Total: {node.metrics.totalEvents}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Connection points */}
          <div 
            className="absolute -right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-300 rounded-full cursor-crosshair hover:border-blue-500 hover:scale-110 transition-transform"
            onMouseDown={(e) => {
              e.stopPropagation()
              console.log('Output connection point clicked for node:', node.id)
              startConnection(node.id)
            }}
            title="Click to start connection from this node"
          />
          <div 
            className={`absolute -left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 rounded-full cursor-crosshair transition-all ${
              dagState.isConnecting && dagState.connectionStart && dagState.connectionStart !== node.id
                ? 'bg-blue-500 border-2 border-blue-600 scale-125'
                : 'bg-white border-2 border-gray-300 hover:border-green-500 hover:scale-110'
            }`}
            onMouseDown={(e) => {
              e.stopPropagation()
              if (dagState.isConnecting && dagState.connectionStart && dagState.connectionStart !== node.id) {
                console.log('Input connection point clicked, completing connection to:', node.id)
                completeConnection(node.id)
              } else {
                console.log('Input connection point clicked but no connection in progress')
              }
            }}
            title={
              dagState.isConnecting && dagState.connectionStart && dagState.connectionStart !== node.id
                ? "Click to complete connection to this node"
                : "Input connection point"
            }
          />
        </div>
      ))}

      {/* Connection preview */}
      {dagState.isConnecting && dagState.connectionStart && (
        <div className="absolute inset-0 pointer-events-none">
          <svg className="w-full h-full">
            {(() => {
              const sourceNode = dagState.nodes.find(n => n.id === dagState.connectionStart)
              if (!sourceNode) return null
              
              const fromX = sourceNode.position.x + 200
              const fromY = sourceNode.position.y + 50
              
              return (
                <g>
                  {/* Connection line */}
                  <path
                    d={`M ${fromX} ${fromY} L ${dagState.dragState.offset.x || fromX} ${dagState.dragState.offset.y || fromY}`}
                    stroke="#3b82f6"
                    strokeWidth="3"
                    strokeDasharray="8,4"
                    fill="none"
                    opacity="0.8"
                  />
                  
                  {/* Arrow head */}
                  <polygon
                    points={`${dagState.dragState.offset.x || fromX},${dagState.dragState.offset.y || fromY} ${(dagState.dragState.offset.x || fromX) - 10},${(dagState.dragState.offset.y || fromY) - 5} ${(dagState.dragState.offset.x || fromX) - 10},${(dagState.dragState.offset.y || fromY) + 5}`}
                    fill="#3b82f6"
                    opacity="0.8"
                  />
                  
                  {/* Connection instruction text */}
                  <text
                    x={(fromX + (dagState.dragState.offset.x || fromX)) / 2}
                    y={(fromY + (dagState.dragState.offset.y || fromY)) / 2 - 20}
                    textAnchor="middle"
                    className="text-sm font-medium fill-blue-600"
                    style={{ fontSize: '14px', fontWeight: '600' }}
                  >
                    Click target node to complete connection
                  </text>
                </g>
              )
            })()}
          </svg>
        </div>
      )}
    </div>
  )

  // Main render
  if (!selectedPipeline) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Event Pipeline Builder</h1>
            <p className="text-gray-600 mt-2">
              Build Directed Acyclic Graph (DAG) pipelines for event processing using our Event Management System
            </p>
          </div>
          
          <button
            onClick={createNewPipeline}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create New Pipeline
          </button>
        </div>

        {/* Pipeline templates */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pipelineTemplates.map((template, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h3>
              <p className="text-gray-600 text-sm mb-4">{template.description}</p>
              <button
                onClick={() => loadPipelineTemplate(template)}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                Load Template
              </button>
            </div>
          ))}
        </div>

        {/* Recent pipelines */}
        {pipelines.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Recent Pipelines</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {pipelines.map(pipeline => (
                <div
                  key={pipeline.id}
                  onClick={() => setSelectedPipeline(pipeline)}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <h3 className="font-semibold text-gray-900">{pipeline.name}</h3>
                  <p className="text-sm text-gray-600">{pipeline.description}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${pipeline.status === 'active' ? 'bg-green-500' : pipeline.status === 'error' ? 'bg-red-500' : 'bg-gray-500'} text-white`}>
                      {pipeline.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(pipeline.updatedAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Pipeline header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSelectedPipeline(null)}
              className="text-gray-600 hover:text-gray-900"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{selectedPipeline.name}</h1>
              <p className="text-sm text-gray-600">{selectedPipeline.description}</p>
            </div>
          </div>
          
          {/* Pipeline controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowMetrics(!showMetrics)}
              className={`p-2 rounded-md ${showMetrics ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'}`}
            >
              {showMetrics ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>
            
            {pipelineStatus === 'stopped' && (
              <button
                onClick={startPipeline}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Pipeline
              </button>
            )}
            
            {pipelineStatus === 'running' && (
              <>
                <button
                  onClick={pausePipeline}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
                >
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </button>
                
                <button
                  onClick={stopPipeline}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Stop
                </button>
              </>
            )}
            
            {pipelineStatus === 'paused' && (
              <button
                onClick={startPipeline}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Resume
              </button>
            )}
            
            <button
              onClick={savePipeline}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Save className="w-4 h-4 mr-2" />
              Save
            </button>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-3">
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700">Add Node:</span>
          
          {/* Event Subscription Nodes */}
          <div className="relative">
            <button
              onClick={() => addNode('event_subscription', { x: 100, y: 100 })}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-sm"
            >
              <Webhook className="w-4 h-4 inline mr-1" />
              Event Subscription
            </button>
            
            {/* Dropdown for existing subscriptions */}
            {eventResources.eventSubscriptions.length > 0 && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <div className="p-2 border-b border-gray-200">
                  <span className="text-xs font-medium text-gray-700">Select Existing:</span>
                </div>
                {eventResources.eventSubscriptions.map(sub => (
                  <button
                    key={sub.id}
                    onClick={() => addNode('event_subscription', { x: 100, y: 100 }, sub.id, sub.name)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                  >
                    <div className="font-medium">{sub.name}</div>
                    <div className="text-xs text-gray-500">{sub.type}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* Event Processor Nodes */}
          <div className="relative">
            <button
              onClick={() => addNode('event_processor', { x: 300, y: 150 })}
              className="px-3 py-1 bg-green-100 text-green-700 rounded-md hover:bg-green-200 text-sm"
            >
              <Filter className="w-4 h-4 inline mr-1" />
              Event Processor
            </button>
            
            {/* Dropdown for existing processors */}
            {eventResources.eventProcessors.length > 0 && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <div className="p-2 border-b border-gray-200">
                  <span className="text-xs font-medium text-gray-700">Select Existing:</span>
                </div>
                {eventResources.eventProcessors.map(proc => (
                  <button
                    key={proc.id}
                    onClick={() => addNode('event_processor', { x: 300, y: 150 }, proc.id, proc.name)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                  >
                    <div className="font-medium">{proc.name}</div>
                    <div className="text-xs text-gray-500">{proc.type}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* Event Sink Nodes */}
          <div className="relative">
            <button
              onClick={() => addNode('event_sink', { x: 500, y: 200 })}
              className="px-3 py-1 bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 text-sm"
            >
              <Route className="w-4 h-4 inline mr-1" />
              Event Sink
            </button>
            
            {/* Dropdown for existing sinks */}
            {eventResources.eventSinks.length > 0 && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <div className="p-2 border-b border-gray-200">
                  <span className="text-xs font-medium text-gray-700">Select Existing:</span>
                </div>
                {eventResources.eventSinks.map(sink => (
                  <button
                    key={sink.id}
                    onClick={() => addNode('event_sink', { x: 500, y: 200 }, sink.id, sink.name)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                  >
                    <div className="font-medium">{sink.name}</div>
                    <div className="text-xs text-gray-500">{sink.type}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <div className="border-l border-gray-300 h-6 mx-2" />
          
          {/* Connection Status */}
          {dagState.isConnecting && (
            <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-md">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">
                Connecting from: {dagState.nodes.find(n => n.id === dagState.connectionStart)?.name || 'Unknown'}
              </span>
              <button
                onClick={() => setDagState(prev => ({ ...prev, isConnecting: false, connectionStart: null }))}
                className="text-blue-600 hover:text-blue-800"
                title="Cancel connection"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          
          <button
            onClick={loadEventResources}
            disabled={isLoadingResources}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 inline mr-1 ${isLoadingResources ? 'animate-spin' : ''}`} />
            Refresh Resources
          </button>
          
          <span className="text-sm font-medium text-gray-700">Validation:</span>
          <select
            value={validationMode}
            onChange={(e) => setValidationMode(e.target.value as 'realtime' | 'manual')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="realtime">Real-time</option>
            <option value="manual">Manual</option>
          </select>
          
          <button
            onClick={() => {
              const { errors } = validateDAG(dagState.nodes, dagState.connections)
              if (errors.length === 0) {
                alert('Pipeline is valid!')
              } else {
                alert(`Pipeline validation failed:\n${errors.join('\n')}`)
              }
            }}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
          >
            Validate
          </button>
        </div>
      </div>

      {/* DAG Canvas */}
      {renderDAGCanvas()}

      {/* Node Configuration Panel */}
      <PipelineNodeConfig
        node={configNode}
        isOpen={configPanelOpen}
        onClose={closeNodeConfig}
        onSave={saveNodeConfig}
        onTest={() => {}}
      />
    </div>
  )
}

export default EventPipelineBuilder
