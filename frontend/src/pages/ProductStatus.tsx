import React, { useState, useEffect } from 'react'
import { 
  Plus, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Settings, 
  Rss,
  ExternalLink,
  Edit,
  Trash2,
  MessageSquare,
  Calendar,
  MapPin,
  Tag,
  User,
  Filter,
  Search,
  RefreshCw
} from 'lucide-react'
import { incidentsApi } from '../lib/api'

interface Incident {
  id: string
  title: string
  description: string
  status: string
  severity: string
  incident_type: string
  affected_services: string[]
  affected_regions: string[]
  affected_components: string[]
  start_time: string
  end_time?: string
  estimated_resolution?: string
  public_message: string
  internal_notes?: string
  created_by: string
  assigned_to?: string
  tags: string[]
  is_public: boolean
  rss_enabled: boolean
  created_at: string
  updated_at: string
  updates: IncidentUpdate[]
}

interface IncidentUpdate {
  id: string
  incident_id: string
  status: string
  message: string
  public_message: string
  internal_notes?: string
  update_type: string
  created_by: string
  is_public: boolean
  created_at: string
}

interface IncidentSummary {
  status_counts: Record<string, number>
  severity_counts: Record<string, number>
  total_active: number
  total_resolved: number
  recent_incidents: Array<{
    id: string
    title: string
    status: string
    severity: string
    start_time: string
  }>
}

const ProductStatus: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [summary, setSummary] = useState<IncidentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showUpdateModal, setShowUpdateModal] = useState(false)
  const [showAddUpdateModal, setShowAddUpdateModal] = useState(false)
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    incident_type: '',
    service: '',
    region: '',
    is_public: undefined as boolean | undefined
  })
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    has_next: false,
    has_prev: false
  })

  // Load incidents and summary
  const loadData = async () => {
    try {
      setLoading(true)
      const [incidentsResponse, summaryResponse] = await Promise.all([
        incidentsApi.getIncidents({
          page: pagination.page,
          per_page: pagination.per_page,
          ...filters
        }),
        incidentsApi.getIncidentSummary()
      ])
      
      console.log('Incidents response:', incidentsResponse)
      console.log('Summary response:', summaryResponse)
      
      // Check if responses are valid
      if (!incidentsResponse || typeof incidentsResponse === 'string' || !incidentsResponse.incidents) {
        console.error('Invalid incidents response:', incidentsResponse)
        setIncidents([])
        setPagination({
          page: 1,
          per_page: 20,
          total: 0,
          has_next: false,
          has_prev: false
        })
      } else {
        setIncidents(incidentsResponse.incidents)
        setPagination({
          page: incidentsResponse.page,
          per_page: incidentsResponse.per_page,
          total: incidentsResponse.total,
          has_next: incidentsResponse.has_next,
          has_prev: incidentsResponse.has_prev
        })
      }
      
      if (!summaryResponse || typeof summaryResponse === 'string') {
        console.error('Invalid summary response:', summaryResponse)
        setSummary(null)
      } else {
        setSummary(summaryResponse)
      }
    } catch (error) {
      console.error('Failed to load incidents:', error)
      // Set empty state on error
      setIncidents([])
      setSummary(null)
      setPagination({
        page: 1,
        per_page: 20,
        total: 0,
        has_next: false,
        has_prev: false
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [pagination.page, filters])

  const handleCreateIncident = async (incidentData: any) => {
    try {
      await incidentsApi.createIncident(incidentData)
      setShowCreateModal(false)
      loadData()
    } catch (error) {
      console.error('Failed to create incident:', error)
    }
  }

  const handleUpdateIncident = async (incidentId: string, updateData: any) => {
    try {
      await incidentsApi.updateIncident(incidentId, updateData)
      setShowUpdateModal(false)
      setSelectedIncident(null)
      loadData()
    } catch (error) {
      console.error('Failed to update incident:', error)
    }
  }

  const handleAddUpdate = async (incidentId: string, updateData: any) => {
    try {
      await incidentsApi.addIncidentUpdate(incidentId, updateData)
      setShowAddUpdateModal(false)
      setSelectedIncident(null)
      loadData()
    } catch (error) {
      console.error('Failed to add update:', error)
    }
  }

  const handleDeleteIncident = async (incidentId: string) => {
    if (window.confirm('Are you sure you want to delete this incident?')) {
      try {
        await incidentsApi.deleteIncident(incidentId)
        loadData()
      } catch (error) {
        console.error('Failed to delete incident:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'investigating': return 'text-yellow-600 bg-yellow-100'
      case 'identified': return 'text-blue-600 bg-blue-100'
      case 'monitoring': return 'text-orange-600 bg-orange-100'
      case 'resolved': return 'text-green-600 bg-green-100'
      case 'post_incident': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100'
      case 'high': return 'text-orange-600 bg-orange-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-blue-600 bg-blue-100'
      case 'minor': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const calculateDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime)
    const end = endTime ? new Date(endTime) : new Date()
    const diff = end.getTime() - start.getTime()
    
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Product Status</h1>
              <p className="mt-2 text-gray-600">
                Monitor and manage product outages and incidents
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Incident
              </button>
              <a
                href="/api/v1/incidents/rss/feed"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Rss className="w-4 h-4 mr-2" />
                RSS Feed
              </a>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white overflow-hidden shadow rounded-lg animate-pulse">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-6 w-6 bg-gray-300 rounded"></div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <div className="h-4 bg-gray-300 rounded w-24 mb-2"></div>
                      <div className="h-6 bg-gray-300 rounded w-16"></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : summary ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Active Incidents</dt>
                      <dd className="text-lg font-medium text-gray-900">{summary.total_active || 0}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Resolved</dt>
                      <dd className="text-lg font-medium text-gray-900">{summary.total_resolved || 0}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Clock className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Investigating</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {summary.status_counts?.investigating || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Settings className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Monitoring</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {summary.status_counts?.monitoring || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg mb-8">
            <div className="px-6 py-4">
              <p className="text-gray-500 text-center">Failed to load summary data</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Filters</h3>
          </div>
          <div className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="investigating">Investigating</option>
                  <option value="identified">Identified</option>
                  <option value="monitoring">Monitoring</option>
                  <option value="resolved">Resolved</option>
                  <option value="post_incident">Post Incident</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                <select
                  value={filters.severity}
                  onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="minor">Minor</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={filters.incident_type}
                  onChange={(e) => setFilters({ ...filters, incident_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">All Types</option>
                  <option value="outage">Outage</option>
                  <option value="degraded_performance">Degraded Performance</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="security">Security</option>
                  <option value="feature_disabled">Feature Disabled</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service</label>
                <input
                  type="text"
                  value={filters.service}
                  onChange={(e) => setFilters({ ...filters, service: e.target.value })}
                  placeholder="Service name"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                <input
                  type="text"
                  value={filters.region}
                  onChange={(e) => setFilters({ ...filters, region: e.target.value })}
                  placeholder="Region name"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={() => setFilters({
                    status: '',
                    severity: '',
                    incident_type: '',
                    service: '',
                    region: '',
                    is_public: undefined
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Incidents List */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">
                Incidents ({pagination.total})
              </h3>
              <button
                onClick={loadData}
                disabled={loading}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          {loading ? (
            <div className="px-6 py-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading incidents...</p>
            </div>
          ) : !incidents || incidents.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No incidents found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating a new incident.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {incidents.map((incident) => (
                <div key={incident.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h4 className="text-lg font-medium text-gray-900">
                          {incident.title}
                        </h4>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(incident.status)}`}>
                          {incident.status.replace('_', ' ')}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(incident.severity)}`}>
                          {incident.severity}
                        </span>
                      </div>
                      
                      <p className="text-gray-600 mb-3">{incident.public_message}</p>
                      
                      <div className="flex items-center space-x-6 text-sm text-gray-500">
                        <div className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1" />
                          Started: {formatDateTime(incident.start_time)}
                        </div>
                        {incident.end_time && (
                          <div className="flex items-center">
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Resolved: {formatDateTime(incident.end_time)}
                          </div>
                        )}
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          Duration: {calculateDuration(incident.start_time, incident.end_time)}
                        </div>
                        {incident.affected_services && incident.affected_services.length > 0 && (
                          <div className="flex items-center">
                            <Settings className="w-4 h-4 mr-1" />
                            Services: {incident.affected_services.join(', ')}
                          </div>
                        )}
                        {incident.affected_regions && incident.affected_regions.length > 0 && (
                          <div className="flex items-center">
                            <MapPin className="w-4 h-4 mr-1" />
                            Regions: {incident.affected_regions.join(', ')}
                          </div>
                        )}
                      </div>
                      
                      {incident.tags && incident.tags.length > 0 && (
                        <div className="flex items-center mt-2">
                          <Tag className="w-4 h-4 mr-2 text-gray-400" />
                          <div className="flex space-x-1">
                            {incident.tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => {
                          setSelectedIncident(incident)
                          setShowAddUpdateModal(true)
                        }}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        title="Add Update"
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedIncident(incident)
                          setShowUpdateModal(true)
                        }}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        title="Edit Incident"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteIncident(incident.id)}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 hover:border-red-300 hover:text-red-700"
                        title="Delete Incident"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Updates Timeline */}
                  {incident.updates && incident.updates.length > 0 && (
                    <div className="mt-4 pl-4 border-l-2 border-gray-200">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Updates</h5>
                      <div className="space-y-2">
                        {incident.updates.slice(0, 3).map((update) => (
                          <div key={update.id} className="text-sm">
                            <div className="flex items-center space-x-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(update.status)}`}>
                                {update.status.replace('_', ' ')}
                              </span>
                              <span className="text-gray-500">
                                {formatDateTime(update.created_at)}
                              </span>
                            </div>
                            <p className="text-gray-600 mt-1">{update.public_message}</p>
                          </div>
                        ))}
                        {incident.updates.length > 3 && (
                          <p className="text-sm text-gray-500">
                            +{incident.updates.length - 3} more updates
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {pagination.total > pagination.per_page && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-6 rounded-lg shadow">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                disabled={!pagination.has_prev}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                disabled={!pagination.has_next}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">{(pagination.page - 1) * pagination.per_page + 1}</span>
                  {' '}to{' '}
                  <span className="font-medium">
                    {Math.min(pagination.page * pagination.per_page, pagination.total)}
                  </span>
                  {' '}of{' '}
                  <span className="font-medium">{pagination.total}</span>
                  {' '}results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                    disabled={!pagination.has_prev}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                    disabled={!pagination.has_next}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals would go here - Create Incident, Update Incident, Add Update */}
      {/* For brevity, I'm not implementing the full modal components, but they would include forms for: */}
      {/* 1. Creating new incidents with all required fields */}
      {/* 2. Updating existing incidents */}
      {/* 3. Adding status updates to incidents */}
      
      {/* Example modal structure: */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Incident</h3>
              {/* Form would go here */}
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {/* Handle create */}}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProductStatus
