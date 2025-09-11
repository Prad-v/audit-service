import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Filter, ChevronLeft, ChevronRight, Eye, Plus, Save, ArrowLeft } from 'lucide-react'
import { auditApi, type AuditEvent } from '@/lib/api'
import { formatDate, getStatusColor } from '@/lib/utils'
import { DynamicFilter, type DynamicFilterItem } from '@/components/DynamicFilter'

export function AuditLogs() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'logs' | 'create'>('logs')
  
  const [filters, setFilters] = useState({
    page: 1,
    size: 20,
    event_type: '',
    user_id: '',
    resource_type: '',
    action: '',
    status: '',
    sort_by: 'timestamp',
    sort_order: 'desc' as 'asc' | 'desc',
  })

  const [dynamicFilters, setDynamicFilters] = useState<DynamicFilterItem[]>([])
  const [filterInfo, setFilterInfo] = useState<{
    available_fields: string[]
    supported_operators: string[]
  }>({ available_fields: [], supported_operators: [] })

  // Create Event form state
  const [formData, setFormData] = useState({
    event_type: '',
    user_id: '',
    session_id: '',
    ip_address: '',
    user_agent: '',
    resource_type: '',
    resource_id: '',
    action: '',
    status: 'success',
    request_data: '',
    response_data: '',
    metadata: '',
    tenant_id: 'default',
    service_name: 'audit-service',
    correlation_id: '',
    retention_period_days: 90,
  })

  // Create Event mutation
  const createEventMutation = useMutation({
    mutationFn: auditApi.createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
      setActiveTab('logs')
      setFormData({
        event_type: '',
        user_id: '',
        session_id: '',
        ip_address: '',
        user_agent: '',
        resource_type: '',
        resource_id: '',
        action: '',
        status: 'success',
        request_data: '',
        response_data: '',
        metadata: '',
        tenant_id: 'default',
        service_name: 'audit-service',
        correlation_id: '',
        retention_period_days: 90,
      })
    },
  })

  // Fetch filter information
  const { data: filterInfoData } = useQuery({
    queryKey: ['filter-info'],
    queryFn: () => auditApi.getFilterInfo(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  useEffect(() => {
    if (filterInfoData) {
      setFilterInfo({
        available_fields: filterInfoData.available_fields || [],
        supported_operators: filterInfoData.supported_operators || []
      })
    }
  }, [filterInfoData])

  // Prepare API parameters including dynamic filters
  const apiParams = {
    ...filters,
    dynamic_filters: dynamicFilters.length > 0 ? JSON.stringify(dynamicFilters.map(f => ({
      field: f.field,
      operator: f.operator,
      value: f.value,
      case_sensitive: f.case_sensitive
    }))) : undefined
  }

  const { data, isLoading, error } = useQuery({
    queryKey: ['events', apiParams],
    queryFn: () => auditApi.getEvents(apiParams),
  })

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }))
  }

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }))
  }

  const handleDynamicFiltersChange = (newFilters: DynamicFilterItem[]) => {
    setDynamicFilters(newFilters)
    setFilters(prev => ({ ...prev, page: 1 }))
  }

  const handleCreateEvent = (e: React.FormEvent) => {
    e.preventDefault()
    
    const eventData = {
      ...formData,
      request_data: formData.request_data ? JSON.parse(formData.request_data) : undefined,
      response_data: formData.response_data ? JSON.parse(formData.response_data) : undefined,
      metadata: formData.metadata ? JSON.parse(formData.metadata) : undefined,
    }

    createEventMutation.mutate(eventData)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading audit logs...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-center text-red-600">
          Error loading audit logs. Please try again.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600">Browse and search through audit events</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('logs')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'logs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Eye className="w-4 h-4 inline mr-2" />
            View Logs
          </button>
          <button
            onClick={() => setActiveTab('create')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'create'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Create Event
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'logs' && (
        <>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center space-x-4 mb-4">
          <Filter className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        </div>
        
        {/* Basic Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Event Type
            </label>
            <input
              type="text"
              value={filters.event_type}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="input-field"
              placeholder="e.g., user_login"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User ID
            </label>
            <input
              type="text"
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              className="input-field"
              placeholder="e.g., user123"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resource Type
            </label>
            <input
              type="text"
              value={filters.resource_type}
              onChange={(e) => handleFilterChange('resource_type', e.target.value)}
              className="input-field"
              placeholder="e.g., file"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Action
            </label>
            <input
              type="text"
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="input-field"
              placeholder="e.g., read"
            />
          </div>
        </div>
        <div className="mt-4 flex items-center space-x-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="input-field"
            >
              <option value="">All</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort Order
            </label>
            <select
              value={filters.sort_order}
              onChange={(e) => handleFilterChange('sort_order', e.target.value)}
              className="input-field"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>

        {/* Dynamic Filters */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <DynamicFilter
            filters={dynamicFilters}
            onFiltersChange={handleDynamicFiltersChange}
            availableFields={filterInfo.available_fields}
            supportedOperators={filterInfo.supported_operators}
          />
        </div>
      </div>

      {/* Results */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Results ({data?.total_count || 0} events)
          </h2>
          <div className="text-sm text-gray-600">
            Page {filters.page} of {data?.total_pages || 1}
          </div>
        </div>

        {data?.items && data.items.length > 0 ? (
          <div className="space-y-4">
            {data.items.map((event: AuditEvent) => (
              <div key={event.audit_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(event.status)}`}>
                      {event.status}
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{event.event_type}</h3>
                      <p className="text-sm text-gray-600">{event.action}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-600">{formatDate(event.timestamp)}</p>
                      <p className="text-xs text-gray-500">{event.user_id || 'System'}</p>
                    </div>
                    <Link
                      to={`/events/${event.audit_id}`}
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <Eye className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
                {event.resource_type && (
                  <div className="mt-2 text-sm text-gray-600">
                    Resource: {event.resource_type} {event.resource_id && `(${event.resource_id})`}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-600">
            No audit events found matching your criteria.
          </div>
        )}

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <button
              onClick={() => handlePageChange(filters.page - 1)}
              disabled={filters.page <= 1}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </button>
            <div className="flex items-center space-x-2">
              {Array.from({ length: Math.min(5, data.total_pages) }, (_, i) => {
                const page = i + 1
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-3 py-2 text-sm font-medium rounded-md ${
                      page === filters.page
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => handlePageChange(filters.page + 1)}
              disabled={filters.page >= data.total_pages}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </button>
          </div>
        )}
      </div>
        </>
      )}

      {/* Create Event Tab */}
      {activeTab === 'create' && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Create New Audit Event</h2>
              <p className="text-sm text-gray-600">Manually create an audit event for testing or documentation purposes</p>
            </div>
            <button
              onClick={() => setActiveTab('logs')}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Logs
            </button>
          </div>

          <form onSubmit={handleCreateEvent} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-900">Basic Information</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Event Type *
                  </label>
                  <input
                    type="text"
                    value={formData.event_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, event_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    User ID
                  </label>
                  <input
                    type="text"
                    value={formData.user_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, user_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Action *
                  </label>
                  <input
                    type="text"
                    value={formData.action}
                    onChange={(e) => setFormData(prev => ({ ...prev, action: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="success">Success</option>
                    <option value="failure">Failure</option>
                    <option value="error">Error</option>
                  </select>
                </div>
              </div>

              {/* Resource Information */}
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-900">Resource Information</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Resource Type
                  </label>
                  <input
                    type="text"
                    value={formData.resource_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, resource_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Resource ID
                  </label>
                  <input
                    type="text"
                    value={formData.resource_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, resource_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    IP Address
                  </label>
                  <input
                    type="text"
                    value={formData.ip_address}
                    onChange={(e) => setFormData(prev => ({ ...prev, ip_address: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Session ID
                  </label>
                  <input
                    type="text"
                    value={formData.session_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, session_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Additional Data */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-900">Additional Data</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Request Data (JSON)
                </label>
                <textarea
                  value={formData.request_data}
                  onChange={(e) => setFormData(prev => ({ ...prev, request_data: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"key": "value"}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Response Data (JSON)
                </label>
                <textarea
                  value={formData.response_data}
                  onChange={(e) => setFormData(prev => ({ ...prev, response_data: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"key": "value"}'
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Metadata (JSON)
                </label>
                <textarea
                  value={formData.metadata}
                  onChange={(e) => setFormData(prev => ({ ...prev, metadata: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"key": "value"}'
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setActiveTab('logs')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createEventMutation.isPending}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4 mr-2" />
                {createEventMutation.isPending ? 'Creating...' : 'Create Event'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
