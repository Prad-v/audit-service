import React from 'react'
import { Plus } from 'lucide-react'

interface NodePaletteProps {
  onNodeAdd: (nodeType: string) => void
}

const nodeTypes = [
  {
    type: 'pubsub_publisher',
    name: 'Pub/Sub Publisher',
    description: 'Publish messages to a Pub/Sub topic',
    icon: '📤',
    color: 'bg-blue-500'
  },
  {
    type: 'pubsub_subscriber',
    name: 'Pub/Sub Subscriber',
    description: 'Subscribe to messages from a Pub/Sub topic',
    icon: '📥',
    color: 'bg-blue-600'
  },
  {
    type: 'rest_client',
    name: 'REST Client',
    description: 'Make HTTP requests to webhooks or APIs',
    icon: '🌐',
    color: 'bg-green-500'
  },
  {
    type: 'webhook_receiver',
    name: 'Webhook Receiver',
    description: 'Receive and validate webhook calls',
    icon: '🔗',
    color: 'bg-green-600'
  },
  {
    type: 'attribute_comparator',
    name: 'Attribute Comparator',
    description: 'Compare attributes between messages',
    icon: '⚖️',
    color: 'bg-yellow-500'
  },
  {
    type: 'incident_creator',
    name: 'Incident Creator',
    description: 'Create incidents when tests fail',
    icon: '🚨',
    color: 'bg-red-500'
  },
  {
    type: 'delay',
    name: 'Delay',
    description: 'Add delays between operations',
    icon: '⏱️',
    color: 'bg-gray-500'
  },
  {
    type: 'condition',
    name: 'Condition',
    description: 'Conditional branching based on data',
    icon: '❓',
    color: 'bg-purple-500'
  }
]

export function NodePalette({ onNodeAdd }: NodePaletteProps) {
  return (
    <div className="p-4 space-y-3">
      <div className="text-sm font-medium text-gray-700 mb-3">Available Nodes</div>
      
      {nodeTypes.map((nodeType) => (
        <div
          key={nodeType.type}
          className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 cursor-pointer transition-colors"
          onClick={() => onNodeAdd(nodeType.type)}
        >
          <div className="flex items-start space-x-3">
            <div className={`w-8 h-8 rounded-lg ${nodeType.color} flex items-center justify-center text-white text-sm flex-shrink-0`}>
              {nodeType.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm text-gray-900">
                {nodeType.name}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {nodeType.description}
              </div>
            </div>
            <div className="flex-shrink-0">
              <Plus className="w-4 h-4 text-gray-400" />
            </div>
          </div>
        </div>
      ))}
      
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <div className="font-medium mb-2">Usage Tips:</div>
          <ul className="space-y-1">
            <li>• Drag nodes to position them</li>
            <li>• Click connection points to link nodes</li>
            <li>• Select nodes to configure properties</li>
            <li>• Use conditions for branching logic</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
