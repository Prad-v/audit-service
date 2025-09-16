import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Trash2, Copy, Settings } from 'lucide-react'

interface Node {
  id: string
  type: string
  name: string
  position: { x: number; y: number }
  config: any
}

interface Edge {
  id: string
  source: string
  target: string
}

interface DAGCanvasProps {
  nodes: Node[]
  edges: Edge[]
  selectedNode: Node | null
  onNodeSelect: (node: Node | null) => void
  onNodeUpdate: (nodeId: string, updates: any) => void
  onNodeDelete: (nodeId: string) => void
  onEdgeAdd: (sourceId: string, targetId: string) => void
  onEdgeDelete: (edgeId: string) => void
}

export function DAGCanvas({
  nodes,
  edges,
  selectedNode,
  onNodeSelect,
  onNodeUpdate,
  onNodeDelete,
  onEdgeAdd,
  onEdgeDelete
}: DAGCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionStart, setConnectionStart] = useState<string | null>(null)
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 })

  const getNodeTypeColor = (type: string) => {
    switch (type) {
      case 'pubsub_publisher': return 'bg-blue-500'
      case 'pubsub_subscriber': return 'bg-blue-600'
      case 'rest_client': return 'bg-green-500'
      case 'webhook_receiver': return 'bg-green-600'
      case 'attribute_comparator': return 'bg-yellow-500'
      case 'incident_creator': return 'bg-red-500'
      case 'delay': return 'bg-gray-500'
      case 'condition': return 'bg-purple-500'
      default: return 'bg-gray-400'
    }
  }

  const getNodeTypeIcon = (type: string) => {
    switch (type) {
      case 'pubsub_publisher': return '📤'
      case 'pubsub_subscriber': return '📥'
      case 'rest_client': return '🌐'
      case 'webhook_receiver': return '🔗'
      case 'attribute_comparator': return '⚖️'
      case 'incident_creator': return '🚨'
      case 'delay': return '⏱️'
      case 'condition': return '❓'
      default: return '📦'
    }
  }

  const handleMouseDown = useCallback((e: React.MouseEvent, nodeId: string) => {
    if (e.button === 0) { // Left click
      setIsDragging(true)
      setDragStart({ x: e.clientX, y: e.clientY })
      onNodeSelect(nodes.find(n => n.id === nodeId) || null)
    }
  }, [nodes, onNodeSelect])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && selectedNode) {
      const deltaX = e.clientX - dragStart.x
      const deltaY = e.clientY - dragStart.y
      
      onNodeUpdate(selectedNode.id, {
        position: {
          x: selectedNode.position.x + deltaX,
          y: selectedNode.position.y + deltaY
        }
      })
      
      setDragStart({ x: e.clientX, y: e.clientY })
    }
  }, [isDragging, selectedNode, dragStart, onNodeUpdate])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleNodeClick = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    const node = nodes.find(n => n.id === nodeId)
    onNodeSelect(node || null)
  }, [nodes, onNodeSelect])

  const handleCanvasClick = useCallback(() => {
    onNodeSelect(null)
  }, [onNodeSelect])

  const handleConnectionStart = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    setIsConnecting(true)
    setConnectionStart(nodeId)
  }, [])

  const handleConnectionEnd = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    if (isConnecting && connectionStart && connectionStart !== nodeId) {
      onEdgeAdd(connectionStart, nodeId)
    }
    setIsConnecting(false)
    setConnectionStart(null)
  }, [isConnecting, connectionStart, onEdgeAdd])

  const handleEdgeClick = useCallback((e: React.MouseEvent, edgeId: string) => {
    e.stopPropagation()
    onEdgeDelete(edgeId)
  }, [onEdgeDelete])

  // Calculate edge path
  const getEdgePath = (edge: Edge) => {
    const sourceNode = nodes.find(n => n.id === edge.source)
    const targetNode = nodes.find(n => n.id === edge.target)
    
    if (!sourceNode || !targetNode) return ''
    
    const startX = sourceNode.position.x + 100 // Node width / 2
    const startY = sourceNode.position.y + 30  // Node height / 2
    const endX = targetNode.position.x + 100
    const endY = targetNode.position.y + 30
    
    const midX = (startX + endX) / 2
    
    return `M ${startX} ${startY} Q ${midX} ${startY} ${midX} ${(startY + endY) / 2} Q ${midX} ${endY} ${endX} ${endY}`
  }

  return (
    <div
      ref={canvasRef}
      className="w-full h-full bg-gray-50 relative overflow-hidden cursor-default"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onClick={handleCanvasClick}
    >
      {/* Grid Background */}
      <div className="absolute inset-0 opacity-20">
        <svg width="100%" height="100%">
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Edges */}
      <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
        {edges.map(edge => (
          <g key={edge.id}>
            <path
              d={getEdgePath(edge)}
              stroke="#6b7280"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrowhead)"
              className="pointer-events-auto cursor-pointer hover:stroke-blue-500"
              onClick={(e) => handleEdgeClick(e, edge.id)}
            />
            <circle
              cx={(nodes.find(n => n.id === edge.source)?.position.x || 0) + 100}
              cy={(nodes.find(n => n.id === edge.source)?.position.y || 0) + 30}
              r="4"
              fill="#6b7280"
              className="pointer-events-auto cursor-pointer hover:fill-blue-500"
              onClick={(e) => handleConnectionStart(e, edge.source)}
            />
          </g>
        ))}
        
        {/* Arrow marker */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#6b7280"
            />
          </marker>
        </defs>
      </svg>

      {/* Nodes */}
      {nodes.map(node => (
        <div
          key={node.id}
          className={`absolute w-48 h-16 rounded-lg border-2 shadow-lg cursor-move ${
            selectedNode?.id === node.id
              ? 'border-blue-500 shadow-blue-200'
              : 'border-gray-300 hover:border-gray-400'
          } ${getNodeTypeColor(node.type)}`}
          style={{
            left: node.position.x,
            top: node.position.y,
            zIndex: selectedNode?.id === node.id ? 10 : 2
          }}
          onMouseDown={(e) => handleMouseDown(e, node.id)}
          onClick={(e) => handleNodeClick(e, node.id)}
        >
          <div className="flex items-center h-full px-3">
            <div className="flex-shrink-0 text-white text-lg mr-2">
              {getNodeTypeIcon(node.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white font-medium text-sm truncate">
                {node.name}
              </div>
              <div className="text-white text-xs opacity-75 truncate">
                {node.type.replace('_', ' ')}
              </div>
            </div>
          </div>
          
          {/* Connection points */}
          <div
            className="absolute -right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-400 rounded-full cursor-crosshair hover:border-blue-500"
            onMouseDown={(e) => handleConnectionStart(e, node.id)}
            onMouseUp={(e) => handleConnectionEnd(e, node.id)}
          />
        </div>
      ))}

      {/* Connection line preview */}
      {isConnecting && connectionStart && (
        <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 5 }}>
          <line
            x1={nodes.find(n => n.id === connectionStart)?.position.x + 100 || 0}
            y1={nodes.find(n => n.id === connectionStart)?.position.y + 30 || 0}
            x2={0} // Will be updated with mouse position
            y2={0} // Will be updated with mouse position
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="5,5"
          />
        </svg>
      )}

      {/* Empty state */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-4xl mb-4">🔧</div>
            <h3 className="text-lg font-medium mb-2">No nodes yet</h3>
            <p className="text-sm">Add nodes from the palette to start building your test</p>
          </div>
        </div>
      )}
    </div>
  )
}
