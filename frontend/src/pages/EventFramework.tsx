import { useState, useEffect } from 'react'
import { Database, Filter, Zap, Route, Bell, Plus, Edit, Trash2, TestTube, Play, Download, RotateCcw } from 'lucide-react'
import { EventSubscriptions } from './EventSubscriptions'
import { CloudEvents } from './CloudEvents'
import { processorsApi } from '@/lib/api'

// Simple toast notification function
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  const toast = document.createElement('div')
  toast.className = `fixed top-4 right-4 px-4 py-2 rounded-md text-white z-50 ${
    type === 'success' ? 'bg-green-600' : 'bg-red-600'
  }`
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => {
    document.body.removeChild(toast)
  }, 3000)
}

export function EventFramework() {
  const [activeTab, setActiveTab] = useState('subscriptions')

  const tabs = [
    { id: 'subscriptions', label: 'Event Subscriptions', icon: Database },
    { id: 'events', label: 'Cloud Events', icon: Bell },
    { id: 'processors', label: 'Event Processors', icon: Zap },
    { id: 'playground', label: 'Processor Playground', icon: Play },
    { id: 'rules', label: 'Event Rules', icon: Filter },
    { id: 'schemas', label: 'Event Schemas', icon: Database },
    { id: 'routing', label: 'Event Routing', icon: Route }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Event Framework</h1>
          <p className="mt-2 text-gray-600">
            Manage event subscriptions, processors, and transformation pipelines
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow">
          {activeTab === 'subscriptions' && <EventSubscriptions />}
          {activeTab === 'events' && <CloudEvents />}
          {activeTab === 'processors' && <EventProcessorsTab />}
          {activeTab === 'playground' && <EventProcessorPlaygroundTab />}
          {activeTab === 'rules' && <EventRulesTab />}
          {activeTab === 'schemas' && <EventSchemasTab />}
          {activeTab === 'routing' && <EventRoutingTab />}
        </div>
      </div>
    </div>
  )
}

// Event Rules Tab Component
function EventRulesTab() {
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center">
          <Plus className="w-4 h-4 mr-2" />
          Create Event Rule
        </button>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <Filter className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Event Rules</h3>
          <p className="mt-1 text-sm text-gray-500">
            Configure event processing rules and triggers for automated event handling.
          </p>
          <div className="mt-6">
            <button className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Create Event Rule
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Event Processors Tab Component
function EventProcessorsTab() {
  const [processors, setProcessors] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedProcessor, setSelectedProcessor] = useState<any>(null)
  const [testingProcessor, setTestingProcessor] = useState<string | null>(null)

  // State for transformation rules
  const [transformations, setTransformations] = useState<any[]>([])
  
  // State for enrichment fields
  const [enrichments, setEnrichments] = useState<any[]>([])
  
  // State for filter conditions
  const [filters, setFilters] = useState<any[]>([])
  
  // State for routing rules
  const [routes, setRoutes] = useState<any[]>([])

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    processor_type: 'transformer',
    config: {},
    order: 0,
    depends_on: [],
    event_types: [],
    severity_levels: [],
    cloud_providers: [],
    conditions: {},
    transformations: {
      rules: [],
      enrichments: [],
      filters: [],
      routes: []
    } as any,
    enabled: true,
    tenant_id: 'default',
    created_by: 'admin'
  })

  useEffect(() => {
    loadProcessors()
  }, [])

  // Update local state when formData changes
  useEffect(() => {
    setTransformations(formData.transformations?.rules || [])
    setEnrichments(formData.transformations?.enrichments || [])
    setFilters(formData.transformations?.filters || [])
    setRoutes(formData.transformations?.routes || [])
  }, [formData.transformations])

  const loadProcessors = async () => {
    try {
      setLoading(true)
      const response = await processorsApi.getEventProcessors()
      setProcessors(response.processors || [])
    } catch (error) {
      console.error('Failed to load processors:', error)
      showToast('Failed to load event processors', 'error')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      processor_type: 'transformer',
      config: {},
      order: 0,
      depends_on: [],
      event_types: [],
      severity_levels: [],
      cloud_providers: [],
      conditions: {},
      transformations: {
        rules: [],
        enrichments: [],
        filters: [],
        routes: []
      } as any,
      enabled: true,
      tenant_id: 'default',
      created_by: 'admin'
    })
    setTransformations([])
    setEnrichments([])
    setFilters([])
    setRoutes([])
  }

  const handleCreate = () => {
    resetForm()
    setIsCreateDialogOpen(true)
  }

  const handleEdit = (processor: any) => {
    setFormData({
      name: processor.name,
      description: processor.description || '',
      processor_type: processor.processor_type,
      config: processor.config || {},
      order: processor.order || 0,
      depends_on: processor.depends_on || [],
      event_types: processor.event_types || [],
      severity_levels: processor.severity_levels || [],
      cloud_providers: processor.cloud_providers || [],
      conditions: processor.conditions || {},
      transformations: processor.transformations || {},
      enabled: processor.enabled,
      tenant_id: processor.tenant_id,
      created_by: processor.created_by
    })
    setSelectedProcessor(processor)
    setIsEditDialogOpen(true)
  }

  const handleDelete = async (processorId: string) => {
    if (!confirm('Are you sure you want to delete this event processor?')) return

    try {
      await processorsApi.deleteEventProcessor(processorId)
      showToast('Event processor deleted successfully')
      loadProcessors()
    } catch (error) {
      console.error('Failed to delete processor:', error)
      showToast('Failed to delete event processor', 'error')
    }
  }

  const handleTestProcessor = async (processorId: string) => {
    try {
      setTestingProcessor(processorId)
      const testData = {
        event_type: 'test_event',
        severity: 'info',
        message: 'Test event for processor validation',
        timestamp: new Date().toISOString(),
        source: 'test_source',
        metadata: {
          user_id: 'test_user',
          session_id: 'test_session'
        }
      }
      await processorsApi.testEventProcessor(processorId, testData)
      showToast('Processor test completed successfully')
    } catch (error) {
      console.error('Failed to test processor:', error)
      showToast('Failed to test event processor', 'error')
    } finally {
      setTestingProcessor(null)
    }
  }

  const handleSubmit = async () => {
    try {
      if (isEditDialogOpen && selectedProcessor) {
        await processorsApi.updateEventProcessor(selectedProcessor.processor_id, formData)
        showToast('Event processor updated successfully')
      } else {
        await processorsApi.createEventProcessor(formData)
        showToast('Event processor created successfully')
      }

      setIsCreateDialogOpen(false)
      setIsEditDialogOpen(false)
      setSelectedProcessor(null)
      resetForm()
      loadProcessors()
    } catch (error) {
      console.error('Failed to save processor:', error)
      showToast('Failed to save event processor', 'error')
    }
  }

  const getProcessorTypeLabel = (type: string) => {
    const types = {
      transformer: 'Transformer',
      enricher: 'Enricher',
      filter: 'Filter',
      router: 'Router'
    }
    return types[type as keyof typeof types] || type
  }

  const getProcessorTypeColor = (type: string) => {
    const colors = {
      transformer: 'bg-blue-100 text-blue-800',
      enricher: 'bg-green-100 text-green-800',
      filter: 'bg-yellow-100 text-yellow-800',
      router: 'bg-purple-100 text-purple-800'
    }
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  // Transformation functions
  const addTransformation = () => {
    const newTransformation = {
      id: `transform_${Date.now()}`,
      type: 'field_mapping',
      source_field: '',
      target_field: '',
      function: 'copy',
      parameters: {}
    }
    const updated = [...transformations, newTransformation]
    setTransformations(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, rules: updated }
    }))
  }

  const updateTransformation = (index: number, field: string, value: any) => {
    const updated = transformations.map((t, i) => 
      i === index ? { ...t, [field]: value } : t
    )
    setTransformations(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, rules: updated }
    }))
  }

  const removeTransformation = (index: number) => {
    const updated = transformations.filter((_, i) => i !== index)
    setTransformations(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, rules: updated }
    }))
  }

  // Enrichment functions
  const addEnrichment = () => {
    const newEnrichment = {
      id: `enrich_${Date.now()}`,
      field: '',
      value: '',
      type: 'static'
    }
    const updated = [...enrichments, newEnrichment]
    setEnrichments(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, enrichments: updated }
    }))
  }

  const updateEnrichment = (index: number, field: string, value: any) => {
    const updated = enrichments.map((e, i) => 
      i === index ? { ...e, [field]: value } : e
    )
    setEnrichments(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, enrichments: updated }
    }))
  }

  const removeEnrichment = (index: number) => {
    const updated = enrichments.filter((_, i) => i !== index)
    setEnrichments(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, enrichments: updated }
    }))
  }

  // Filter functions
  const addFilter = () => {
    const newFilter = {
      id: `filter_${Date.now()}`,
      field: '',
      operator: 'equals',
      value: '',
      condition: 'and'
    }
    const updated = [...filters, newFilter]
    setFilters(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, filters: updated }
    }))
  }

  const updateFilter = (index: number, field: string, value: any) => {
    const updated = filters.map((f, i) => 
      i === index ? { ...f, [field]: value } : f
    )
    setFilters(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, filters: updated }
    }))
  }

  const removeFilter = (index: number) => {
    const updated = filters.filter((_, i) => i !== index)
    setFilters(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, filters: updated }
    }))
  }

  // Route functions
  const addRoute = () => {
    const newRoute = {
      id: `route_${Date.now()}`,
      name: '',
      condition: '',
      destination: '',
      priority: 1
    }
    const updated = [...routes, newRoute]
    setRoutes(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, routes: updated }
    }))
  }

  const updateRoute = (index: number, field: string, value: any) => {
    const updated = routes.map((r, i) => 
      i === index ? { ...r, [field]: value } : r
    )
    setRoutes(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, routes: updated }
    }))
  }

  const removeRoute = (index: number) => {
    const updated = routes.filter((_, i) => i !== index)
    setRoutes(updated)
    setFormData(prev => ({
      ...prev,
      transformations: { ...prev.transformations, routes: updated }
    }))
  }

  const renderTransformationConfig = () => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-medium text-gray-900">Transformation Rules</h4>
          <button
            type="button"
            onClick={addTransformation}
            className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
          >
            Add Rule
          </button>
        </div>
        
        {transformations.map((transform, index) => (
          <div key={transform.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Rule {index + 1}</span>
              <button
                type="button"
                onClick={() => removeTransformation(index)}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Source Field</label>
                <input
                  type="text"
                  value={transform.source_field}
                  onChange={(e) => updateTransformation(index, 'source_field', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., message, severity"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Target Field</label>
                <input
                  type="text"
                  value={transform.target_field}
                  onChange={(e) => updateTransformation(index, 'target_field', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., processed_message, level"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Transformation Function</label>
              <select
                value={transform.function}
                onChange={(e) => updateTransformation(index, 'function', e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="copy">Copy (no change)</option>
                <option value="upcase">Uppercase</option>
                <option value="downcase">Lowercase</option>
                <option value="trim">Trim whitespace</option>
                <option value="replace">Replace text</option>
                <option value="parse_json">Parse JSON</option>
                <option value="to_string">Convert to string</option>
                <option value="to_number">Convert to number</option>
                <option value="round">Round number</option>
                <option value="format_timestamp">Format timestamp</option>
                <option value="extract_regex">Extract with regex</option>
              </select>
            </div>
            
            {transform.function === 'replace' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Find</label>
                  <input
                    type="text"
                    value={transform.parameters?.find || ''}
                    onChange={(e) => updateTransformation(index, 'parameters', { ...transform.parameters, find: e.target.value })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Text to find"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Replace With</label>
                  <input
                    type="text"
                    value={transform.parameters?.replace || ''}
                    onChange={(e) => updateTransformation(index, 'parameters', { ...transform.parameters, replace: e.target.value })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Replacement text"
                  />
                </div>
              </div>
            )}
            
            {transform.function === 'extract_regex' && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Regex Pattern</label>
                <input
                  type="text"
                  value={transform.parameters?.pattern || ''}
                  onChange={(e) => updateTransformation(index, 'parameters', { ...transform.parameters, pattern: e.target.value })}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., ([A-Z]+)"
                />
              </div>
            )}
            
            {transform.function === 'format_timestamp' && (
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Format</label>
                <input
                  type="text"
                  value={transform.parameters?.format || ''}
                  onChange={(e) => updateTransformation(index, 'parameters', { ...transform.parameters, format: e.target.value })}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., %Y-%m-%d %H:%M:%S"
                />
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderEnrichmentConfig = () => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-medium text-gray-900">Enrichment Fields</h4>
          <button
            type="button"
            onClick={addEnrichment}
            className="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
          >
            Add Field
          </button>
        </div>
        
        {enrichments.map((enrichment, index) => (
          <div key={enrichment.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Enrichment {index + 1}</span>
              <button
                type="button"
                onClick={() => removeEnrichment(index)}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Field Name</label>
                <input
                  type="text"
                  value={enrichment.field}
                  onChange={(e) => updateEnrichment(index, 'field', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., environment, region"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Value Type</label>
                <select
                  value={enrichment.type}
                  onChange={(e) => updateEnrichment(index, 'type', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="static">Static Value</option>
                  <option value="timestamp">Current Timestamp</option>
                  <option value="uuid">Generate UUID</option>
                  <option value="hostname">Hostname</option>
                  <option value="environment">Environment Variable</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Value</label>
                <input
                  type="text"
                  value={enrichment.value}
                  onChange={(e) => updateEnrichment(index, 'value', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder={enrichment.type === 'static' ? 'Static value' : 'Parameter'}
                  disabled={enrichment.type !== 'static'}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderFilterConfig = () => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-medium text-gray-900">Filter Conditions</h4>
          <button
            type="button"
            onClick={addFilter}
            className="text-sm bg-yellow-600 text-white px-3 py-1 rounded hover:bg-yellow-700"
          >
            Add Filter
          </button>
        </div>
        
        {filters.map((filter, index) => (
          <div key={filter.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Filter {index + 1}</span>
              <button
                type="button"
                onClick={() => removeFilter(index)}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
            
            <div className="grid grid-cols-4 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Field</label>
                <input
                  type="text"
                  value={filter.field}
                  onChange={(e) => updateFilter(index, 'field', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., severity, event_type"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Operator</label>
                <select
                  value={filter.operator}
                  onChange={(e) => updateFilter(index, 'operator', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="equals">Equals</option>
                  <option value="not_equals">Not Equals</option>
                  <option value="contains">Contains</option>
                  <option value="not_contains">Not Contains</option>
                  <option value="starts_with">Starts With</option>
                  <option value="ends_with">Ends With</option>
                  <option value="regex">Regex Match</option>
                  <option value="greater_than">Greater Than</option>
                  <option value="less_than">Less Than</option>
                  <option value="exists">Exists</option>
                  <option value="not_exists">Not Exists</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Value</label>
                <input
                  type="text"
                  value={filter.value}
                  onChange={(e) => updateFilter(index, 'value', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Filter value"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Condition</label>
                <select
                  value={filter.condition}
                  onChange={(e) => updateFilter(index, 'condition', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="and">AND</option>
                  <option value="or">OR</option>
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderRouterConfig = () => {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-medium text-gray-900">Routing Rules</h4>
          <button
            type="button"
            onClick={addRoute}
            className="text-sm bg-purple-600 text-white px-3 py-1 rounded hover:bg-purple-700"
          >
            Add Route
          </button>
        </div>
        
        {routes.map((route, index) => (
          <div key={route.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Route {index + 1}</span>
              <button
                type="button"
                onClick={() => removeRoute(index)}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Route Name</label>
                <input
                  type="text"
                  value={route.name}
                  onChange={(e) => updateRoute(index, 'name', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g., high_severity, error_events"
                />
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Priority</label>
                <input
                  type="number"
                  value={route.priority}
                  onChange={(e) => updateRoute(index, 'priority', parseInt(e.target.value))}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  min="1"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Condition (VRL Expression)</label>
              <input
                type="text"
                value={route.condition}
                onChange={(e) => updateRoute(index, 'condition', e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="e.g., .severity == 'error' || .event_type == 'alert'"
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Destination</label>
              <input
                type="text"
                value={route.destination}
                onChange={(e) => updateRoute(index, 'destination', e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="e.g., error_topic, alert_queue, webhook_url"
              />
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderProcessorSpecificConfig = () => {
    switch (formData.processor_type) {
      case 'transformer':
        return renderTransformationConfig()
      case 'enricher':
        return renderEnrichmentConfig()
      case 'filter':
        return renderFilterConfig()
      case 'router':
        return renderRouterConfig()
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading event processors...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Event Processor
        </button>
      </div>
      
      {/* Processors List */}
      <div className="grid gap-6">
        {processors.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-6">
            <div className="text-center py-12">
              <Zap className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Event Processors</h3>
              <p className="mt-1 text-sm text-gray-500">
                Configure event processors, transformers, and enrichment pipelines.
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Event Processor
                </button>
              </div>
            </div>
          </div>
        ) : (
          processors.map((processor) => (
            <div key={processor.processor_id} className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-3">
                  <Zap className="w-6 h-6 text-blue-600" />
                  <div>
                    <h3 className="text-lg font-semibold">{processor.name}</h3>
                    <p className="text-gray-600">{processor.description}</p>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getProcessorTypeColor(processor.processor_type)}`}>
                      {getProcessorTypeLabel(processor.processor_type)}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-1">
                  <button
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                    onClick={() => handleTestProcessor(processor.processor_id)}
                    disabled={testingProcessor === processor.processor_id}
                    title="Test Processor"
                  >
                    <TestTube className="w-4 h-4" />
                  </button>
                  <button
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                    onClick={() => handleEdit(processor)}
                    title="Edit Processor"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                    onClick={() => handleDelete(processor.processor_id)}
                    title="Delete Processor"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Status:</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    processor.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {processor.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Order:</span>
                  <span className="text-sm font-medium">{processor.order}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Processed:</span>
                  <span className="text-sm font-medium">{processor.processed_count || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Errors:</span>
                  <span className="text-sm font-medium">{processor.error_count || 0}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create/Edit Dialog */}
      {(isCreateDialogOpen || isEditDialogOpen) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">
                {isEditDialogOpen ? 'Edit Event Processor' : 'Create Event Processor'}
              </h2>
            </div>
            <div className="space-y-6">
              {/* Basic Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter processor name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Processor Type</label>
                  <select
                    value={formData.processor_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, processor_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="transformer">Transformer</option>
                    <option value="enricher">Enricher</option>
                    <option value="filter">Filter</option>
                    <option value="router">Router</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Enter description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Order</label>
                  <input
                    type="number"
                    value={formData.order}
                    onChange={(e) => setFormData(prev => ({ ...prev, order: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Enabled</label>
                  <label className="flex items-center mt-2">
                    <input
                      type="checkbox"
                      checked={formData.enabled}
                      onChange={(e) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                      className="mr-2"
                    />
                    Enable this processor
                  </label>
                </div>
              </div>

              {/* Processor-Specific Configuration */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {formData.processor_type === 'transformer' && 'Transformation Rules'}
                  {formData.processor_type === 'enricher' && 'Enrichment Configuration'}
                  {formData.processor_type === 'filter' && 'Filter Conditions'}
                  {formData.processor_type === 'router' && 'Routing Rules'}
                </h3>
                {renderProcessorSpecificConfig()}
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => {
                  setIsCreateDialogOpen(false)
                  setIsEditDialogOpen(false)
                  setSelectedProcessor(null)
                  resetForm()
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {isEditDialogOpen ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Event Schemas Tab Component
function EventSchemasTab() {
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center">
          <Plus className="w-4 h-4 mr-2" />
          Create Event Schema
        </button>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <Database className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Event Schemas</h3>
          <p className="mt-1 text-sm text-gray-500">
            Manage event type definitions, validation rules, and schema evolution.
          </p>
          <div className="mt-6">
            <button className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Create Event Schema
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Event Routing Tab Component
function EventRoutingTab() {
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center">
          <Plus className="w-4 h-4 mr-2" />
          Add Routing Rule
        </button>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <Route className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Event Routing</h3>
          <p className="mt-1 text-sm text-gray-500">
            Configure event flow, routing rules, and destination mappings.
          </p>
          <div className="mt-6">
            <button className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Routing Rule
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Event Processor Playground Tab Component
function EventProcessorPlaygroundTab() {
  const [processors, setProcessors] = useState<any[]>([])
  const [selectedProcessor, setSelectedProcessor] = useState<any>(null)
  const [testEvent, setTestEvent] = useState(`{
  "event_type": "log",
  "severity": "error",
  "message": "database connection failed",
  "source": "app-server-01",
  "user_id": "user123",
  "session_id": "sess456",
  "timestamp": "2024-01-15T10:30:45Z",
  "metadata": {
    "service": "auth-service",
    "region": "us-west-1",
    "environment": "production"
  }
}`)
  const [output, setOutput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState('')
  const [testResults, setTestResults] = useState<any[]>([])

  // Sample test events
  const sampleEvents = {
    log_event: {
      name: 'Log Event',
      data: `{
  "event_type": "log",
  "severity": "error",
  "message": "database connection failed",
  "source": "app-server-01",
  "user_id": "user123",
  "session_id": "sess456",
  "timestamp": "2024-01-15T10:30:45Z",
  "metadata": {
    "service": "auth-service",
    "region": "us-west-1",
    "environment": "production"
  }
}`
    },
    alert_event: {
      name: 'Alert Event',
      data: `{
  "event_type": "alert",
  "severity": "warning",
  "message": "High CPU usage detected",
  "source": "monitoring-system",
  "component": "web-server",
  "value": 85.5,
  "threshold": 80.0,
  "timestamp": "2024-01-15T10:30:45Z"
}`
    },
    security_event: {
      name: 'Security Event',
      data: `{
  "event_type": "security",
  "severity": "critical",
  "message": "Failed login attempt",
  "source": "auth-service",
  "user_id": "unknown",
  "ip_address": "192.168.1.100",
  "attempt_count": 5,
  "timestamp": "2024-01-15T10:30:45Z"
}`
    },
    audit_event: {
      name: 'Audit Event',
      data: `{
  "event_type": "audit",
  "severity": "info",
  "message": "User login successful",
  "source": "auth-service",
  "user_id": "admin",
  "action": "login",
  "ip_address": "192.168.1.50",
  "timestamp": "2024-01-15T10:30:45Z"
}`
    }
  }

  useEffect(() => {
    loadProcessors()
  }, [])

  const loadProcessors = async () => {
    try {
      const response = await processorsApi.getEventProcessors()
      setProcessors(response.processors || [])
    } catch (error) {
      console.error('Failed to load processors:', error)
      showToast('Failed to load event processors', 'error')
    }
  }

  const runProcessorTest = async () => {
    if (!selectedProcessor) {
      showToast('Please select an event processor first', 'error')
      return
    }

    setIsRunning(true)
    setError('')
    setOutput('')

    try {
      // Parse the test event
      let parsedEvent
      try {
        parsedEvent = JSON.parse(testEvent)
      } catch (e) {
        throw new Error('Invalid JSON in test event')
      }

      // Test the processor
      const response = await processorsApi.testEventProcessor(selectedProcessor.processor_id, parsedEvent)
      
      // Format the output
      const result = {
        processor: selectedProcessor.name,
        processor_type: selectedProcessor.processor_type,
        input_event: parsedEvent,
        output_event: response.result,
        timestamp: new Date().toISOString(),
        success: true
      }

      setOutput(JSON.stringify(result.output_event, null, 2))
      setTestResults(prev => [result, ...prev.slice(0, 9)]) // Keep last 10 results
      
      showToast('Processor test completed successfully!')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      showToast('Processor test failed', 'error')
    } finally {
      setIsRunning(false)
    }
  }

  const loadSampleEvent = (eventKey: string) => {
    const sample = sampleEvents[eventKey as keyof typeof sampleEvents]
    if (sample) {
      setTestEvent(sample.data)
      showToast(`Loaded ${sample.name} sample`)
    }
  }

  const clearResults = () => {
    setTestResults([])
    setOutput('')
    setError('')
  }

  const exportTestResult = () => {
    if (!output) {
      showToast('No test result to export', 'error')
      return
    }

    const exportData = {
      processor: selectedProcessor?.name,
      test_event: JSON.parse(testEvent),
      result: JSON.parse(output),
      timestamp: new Date().toISOString()
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `processor-test-${selectedProcessor?.name || 'result'}-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    showToast('Test result exported successfully!')
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Event Processor Playground</h2>
          <p className="text-gray-600 mt-1">
            Test your configured event processors with sample data and see real-time results
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={clearResults}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Clear Results
          </button>
          <button
            onClick={exportTestResult}
            disabled={!output}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Result
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Processor Selection */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Select Processor</h3>
          <div className="space-y-3">
            {processors.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Zap className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p>No event processors found</p>
                <p className="text-sm">Create processors in the Event Processors tab first</p>
              </div>
            ) : (
              processors.map((processor) => (
                <div
                  key={processor.processor_id}
                  onClick={() => setSelectedProcessor(processor)}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedProcessor?.processor_id === processor.processor_id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{processor.name}</h4>
                      <p className="text-sm text-gray-600">{processor.description}</p>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-2 ${
                        processor.processor_type === 'transformer' ? 'bg-blue-100 text-blue-800' :
                        processor.processor_type === 'enricher' ? 'bg-green-100 text-green-800' :
                        processor.processor_type === 'filter' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-purple-100 text-purple-800'
                      }`}>
                        {processor.processor_type}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className={`w-3 h-3 rounded-full ${
                        processor.enabled ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Test Event Input */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">Test Event</h3>
            <div className="flex space-x-1">
              {Object.entries(sampleEvents).map(([key, sample]) => (
                <button
                  key={key}
                  onClick={() => loadSampleEvent(key)}
                  className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  {sample.name}
                </button>
              ))}
            </div>
          </div>
          <div className="border border-gray-300 rounded-md">
            <div className="bg-gray-50 px-3 py-2 border-b border-gray-300">
              <span className="text-sm font-medium text-gray-700">Event Data (JSON)</span>
            </div>
            <textarea
              value={testEvent}
              onChange={(e) => setTestEvent(e.target.value)}
              className="w-full h-64 p-4 font-mono text-sm border-0 focus:ring-0 resize-none"
              placeholder="Enter JSON event data..."
            />
          </div>
          <button
            onClick={runProcessorTest}
            disabled={!selectedProcessor || isRunning}
            className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <Play className="w-4 h-4 mr-2" />
            {isRunning ? 'Testing...' : 'Test Processor'}
          </button>
        </div>

        {/* Output */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Output</h3>
          <div className="border border-gray-300 rounded-md">
            <div className="bg-gray-50 px-3 py-2 border-b border-gray-300">
              <span className="text-sm font-medium text-gray-700">Transformed Event</span>
            </div>
            <div className="p-4">
              {error ? (
                <div className="text-red-600 font-mono text-sm">
                  <div className="font-semibold mb-2">Error:</div>
                  <pre className="whitespace-pre-wrap">{error}</pre>
                </div>
              ) : output ? (
                <pre className="font-mono text-sm text-gray-900 whitespace-pre-wrap">{output}</pre>
              ) : (
                <div className="text-gray-500 text-sm">
                  Select a processor and click "Test Processor" to see results
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Test History */}
      {testResults.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Test History</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="space-y-3">
              {testResults.map((result, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{result.processor}</h4>
                      <p className="text-sm text-gray-600">
                        Type: {result.processor_type} • {new Date(result.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-gray-600">Success</span>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Input Fields:</span>
                      <div className="text-gray-600">
                        {Object.keys(result.input_event).length} fields
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Output Fields:</span>
                      <div className="text-gray-600">
                        {result.output_event ? Object.keys(result.output_event).length : 0} fields
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Processor Information */}
      {selectedProcessor && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Processor Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-blue-800 mb-1">Configuration</h4>
              <ul className="text-blue-700 space-y-1">
                <li><strong>Type:</strong> {selectedProcessor.processor_type}</li>
                <li><strong>Order:</strong> {selectedProcessor.order}</li>
                <li><strong>Status:</strong> {selectedProcessor.enabled ? 'Enabled' : 'Disabled'}</li>
                <li><strong>Processed:</strong> {selectedProcessor.processed_count || 0} events</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-800 mb-1">Transformation Details</h4>
              <ul className="text-blue-700 space-y-1">
                {selectedProcessor.processor_type === 'transformer' && (
                  <li><strong>Rules:</strong> {selectedProcessor.transformations?.rules?.length || 0}</li>
                )}
                {selectedProcessor.processor_type === 'enricher' && (
                  <li><strong>Enrichments:</strong> {selectedProcessor.transformations?.enrichments?.length || 0}</li>
                )}
                {selectedProcessor.processor_type === 'filter' && (
                  <li><strong>Filters:</strong> {selectedProcessor.transformations?.filters?.length || 0}</li>
                )}
                {selectedProcessor.processor_type === 'router' && (
                  <li><strong>Routes:</strong> {selectedProcessor.transformations?.routes?.length || 0}</li>
                )}
                <li><strong>Event Types:</strong> {selectedProcessor.event_types?.length || 0}</li>
                <li><strong>Cloud Providers:</strong> {selectedProcessor.cloud_providers?.length || 0}</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
