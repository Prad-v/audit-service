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
  RefreshCw,
  Eye,
  X
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
  jira_ticket_id?: string
  jira_ticket_url?: string
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
  const [showViewModal, setShowViewModal] = useState(false)
  const [updateForm, setUpdateForm] = useState({
    status: '',
    message: '',
    public_message: '',
    internal_notes: '',
    update_type: 'status_update'
  })
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    status: '',
    severity: '',
    incident_type: '',
    affected_services: [] as string[],
    affected_regions: [] as string[],
    affected_components: [] as string[],
    public_message: '',
    internal_notes: '',
    assigned_to: '',
    tags: [] as string[],
    is_public: true,
    rss_enabled: true
  })
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    severity: '',
    incident_type: '',
    affected_services: [] as string[],
    affected_regions: [] as string[],
    affected_components: [] as string[],
    start_time: new Date().toISOString(),
    estimated_resolution: '',
    public_message: '',
    internal_notes: '',
    assigned_to: '',
    tags: [] as string[],
    is_public: true,
    rss_enabled: true
  })
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
  const [jiraConfig, setJiraConfig] = useState<any>(null)
  const [creatingJiraTicket, setCreatingJiraTicket] = useState<string | null>(null)

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
    loadJiraConfig()
  }, [pagination.page, filters])

  // Load Jira configuration
  const loadJiraConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/jira/config')
      if (response.ok) {
        const config = await response.json()
        setJiraConfig(config.enabled ? config : null)
      }
    } catch (error) {
      console.error('Failed to load Jira configuration:', error)
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

  const handleAddUpdate = async () => {
    if (!selectedIncident) return
    
    try {
      await incidentsApi.addIncidentUpdate(selectedIncident.id, updateForm)
      setShowAddUpdateModal(false)
      setUpdateForm({
        status: '',
        message: '',
        public_message: '',
        internal_notes: '',
        update_type: 'status_update'
      })
      loadData()
    } catch (error) {
      console.error('Failed to add update:', error)
    }
  }

  const handleEditIncident = async () => {
    if (!selectedIncident) return
    
    try {
      await incidentsApi.updateIncident(selectedIncident.id, editForm)
      setShowUpdateModal(false)
      setEditForm({
        title: '',
        description: '',
        status: '',
        severity: '',
        incident_type: '',
        affected_services: [],
        affected_regions: [],
        affected_components: [],
        public_message: '',
        internal_notes: '',
        assigned_to: '',
        tags: [],
        is_public: true,
        rss_enabled: true
      })
        loadData()
      } catch (error) {
      console.error('Failed to update incident:', error)
    }
  }

  const populateEditForm = (incident: Incident) => {
    setEditForm({
      title: incident.title,
      description: incident.description,
      status: incident.status,
      severity: incident.severity,
      incident_type: incident.incident_type,
      affected_services: incident.affected_services || [],
      affected_regions: incident.affected_regions || [],
      affected_components: incident.affected_components || [],
      public_message: incident.public_message,
      internal_notes: incident.internal_notes || '',
      assigned_to: incident.assigned_to || '',
      tags: incident.tags || [],
      is_public: incident.is_public,
      rss_enabled: incident.rss_enabled
    })
  }

  const handleCreateIncident = async () => {
    try {
      await incidentsApi.createIncident(createForm)
      setShowCreateModal(false)
      setCreateForm({
        title: '',
        description: '',
        severity: '',
        incident_type: '',
        affected_services: [],
        affected_regions: [],
        affected_components: [],
        start_time: new Date().toISOString(),
        estimated_resolution: '',
        public_message: '',
        internal_notes: '',
        assigned_to: '',
        tags: [],
        is_public: true,
        rss_enabled: true
      })
      loadData()
    } catch (error) {
      console.error('Failed to create incident:', error)
    }
  }

  // Create Jira ticket for incident
  const handleCreateJiraTicket = async (incident: Incident) => {
    setCreatingJiraTicket(incident.id)
    
    try {
      const response = await fetch('/api/v1/integrations/jira/create-ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          incident_id: incident.id,
          incident_data: incident
        })
      })

      const result = await response.json()
      
      if (response.ok) {
        // Update the incident with Jira ticket ID
        await incidentsApi.updateIncident(incident.id, {
          jira_ticket_id: result.jira_ticket_id,
          jira_ticket_url: result.jira_ticket_url
        })
        
        alert(`Jira ticket created successfully! Ticket ID: ${result.jira_ticket_id}`)
        loadData() // Refresh the incident list
      } else {
        alert(`Failed to create Jira ticket: ${result.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to create Jira ticket:', error)
      alert('Failed to create Jira ticket. Please try again.')
    } finally {
      setCreatingJiraTicket(null)
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
              <h1 className="text-3xl font-bold text-gray-900">Incident Management</h1>
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
                          setShowViewModal(true)
                        }}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
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
                          populateEditForm(incident)
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
                      {jiraConfig && !incident.jira_ticket_id && (
                        <button
                          onClick={() => handleCreateJiraTicket(incident)}
                          disabled={creatingJiraTicket === incident.id}
                          className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 hover:border-blue-300 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Create Jira Ticket"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      )}
                      {incident.jira_ticket_id && (
                        <a
                          href={incident.jira_ticket_url || `https://${jiraConfig?.base_url?.replace('https://', '')}/browse/${incident.jira_ticket_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 hover:border-blue-300 hover:text-blue-700"
                          title="View Jira Ticket"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
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
      {/* Create Incident Slider */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="fixed right-0 top-0 h-full w-11/12 max-w-4xl bg-white shadow-xl transform transition-transform duration-300 ease-in-out">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-900">Create New Incident</h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <div className="px-6 py-6 max-h-96 overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                    <input
                      type="text"
                      value={createForm.title}
                      onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      value={createForm.description}
                      onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                      rows={3}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Severity *</label>
                    <select
                      value={createForm.severity}
                      onChange={(e) => setCreateForm({ ...createForm, severity: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      required
                    >
                      <option value="">Select Severity</option>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                      <option value="minor">Minor</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Incident Type *</label>
                    <select
                      value={createForm.incident_type}
                      onChange={(e) => setCreateForm({ ...createForm, incident_type: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      required
                    >
                      <option value="">Select Type</option>
                      <option value="outage">Outage</option>
                      <option value="degraded_performance">Degraded Performance</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="security">Security</option>
                      <option value="feature_disabled">Feature Disabled</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                    <input
                      type="datetime-local"
                      value={createForm.start_time.slice(0, 16)}
                      onChange={(e) => setCreateForm({ ...createForm, start_time: new Date(e.target.value).toISOString() })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Estimated Resolution</label>
                    <input
                      type="datetime-local"
                      value={createForm.estimated_resolution ? new Date(createForm.estimated_resolution).toISOString().slice(0, 16) : ''}
                      onChange={(e) => setCreateForm({ ...createForm, estimated_resolution: e.target.value ? new Date(e.target.value).toISOString() : '' })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Affected Services</label>
                    <input
                      type="text"
                      value={createForm.affected_services.join(', ')}
                      onChange={(e) => setCreateForm({ ...createForm, affected_services: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="service1, service2, service3"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Affected Regions</label>
                    <input
                      type="text"
                      value={createForm.affected_regions.join(', ')}
                      onChange={(e) => setCreateForm({ ...createForm, affected_regions: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="us-east-1, eu-west-1"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Affected Components</label>
                    <input
                      type="text"
                      value={createForm.affected_components.join(', ')}
                      onChange={(e) => setCreateForm({ ...createForm, affected_components: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="api, database, cache"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
                    <input
                      type="text"
                      value={createForm.assigned_to}
                      onChange={(e) => setCreateForm({ ...createForm, assigned_to: e.target.value })}
                      placeholder="username or email"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                    <input
                      type="text"
                      value={createForm.tags.join(', ')}
                      onChange={(e) => setCreateForm({ ...createForm, tags: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="tag1, tag2, tag3"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Public Message *</label>
                  <textarea
                    value={createForm.public_message}
                    onChange={(e) => setCreateForm({ ...createForm, public_message: e.target.value })}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Internal Notes</label>
                  <textarea
                    value={createForm.internal_notes}
                    onChange={(e) => setCreateForm({ ...createForm, internal_notes: e.target.value })}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div className="flex items-center space-x-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={createForm.is_public}
                      onChange={(e) => setCreateForm({ ...createForm, is_public: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Public Incident</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={createForm.rss_enabled}
                      onChange={(e) => setCreateForm({ ...createForm, rss_enabled: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">RSS Enabled</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 rounded-b-md">
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateIncident}
                  disabled={!createForm.title || !createForm.severity || !createForm.incident_type || !createForm.public_message}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Incident
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Incident Slider */}
      {showViewModal && selectedIncident && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="fixed right-0 top-0 h-full w-11/12 max-w-4xl bg-white shadow-xl transform transition-transform duration-300 ease-in-out">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-900">Incident Details</h3>
                <button
                  onClick={() => setShowViewModal(false)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <div className="px-6 py-6 max-h-96 overflow-y-auto">
              {/* Incident Header */}
              <div className="mb-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">{selectedIncident.title}</h1>
                    <div className="flex items-center space-x-3 mb-3">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedIncident.status)}`}>
                        {selectedIncident.status.replace('_', ' ')}
                      </span>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(selectedIncident.severity)}`}>
                        {selectedIncident.severity}
                      </span>
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                        {selectedIncident.incident_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>
                
                <p className="text-gray-700 text-lg mb-4">{selectedIncident.public_message}</p>
                
                {selectedIncident.description && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
                    <p className="text-gray-600">{selectedIncident.description}</p>
                  </div>
                )}
              </div>

              {/* Incident Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Timeline</h4>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm text-gray-600">
                        <Calendar className="w-4 h-4 mr-2" />
                        <span className="font-medium">Started:</span>
                        <span className="ml-2">{formatDateTime(selectedIncident.start_time)}</span>
                      </div>
                      {selectedIncident.end_time && (
                        <div className="flex items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 mr-2" />
                          <span className="font-medium">Resolved:</span>
                          <span className="ml-2">{formatDateTime(selectedIncident.end_time)}</span>
                        </div>
                      )}
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock className="w-4 h-4 mr-2" />
                        <span className="font-medium">Duration:</span>
                        <span className="ml-2">{calculateDuration(selectedIncident.start_time, selectedIncident.end_time)}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Affected Resources</h4>
                    <div className="space-y-2">
                      {selectedIncident.affected_services && selectedIncident.affected_services.length > 0 && (
                        <div className="flex items-center text-sm text-gray-600">
                          <Settings className="w-4 h-4 mr-2" />
                          <span className="font-medium">Services:</span>
                          <span className="ml-2">{selectedIncident.affected_services.join(', ')}</span>
                        </div>
                      )}
                      {selectedIncident.affected_regions && selectedIncident.affected_regions.length > 0 && (
                        <div className="flex items-center text-sm text-gray-600">
                          <MapPin className="w-4 h-4 mr-2" />
                          <span className="font-medium">Regions:</span>
                          <span className="ml-2">{selectedIncident.affected_regions.join(', ')}</span>
                        </div>
                      )}
                      {selectedIncident.affected_components && selectedIncident.affected_components.length > 0 && (
                        <div className="flex items-center text-sm text-gray-600">
                          <Settings className="w-4 h-4 mr-2" />
                          <span className="font-medium">Components:</span>
                          <span className="ml-2">{selectedIncident.affected_components.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Metadata</h4>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm text-gray-600">
                        <User className="w-4 h-4 mr-2" />
                        <span className="font-medium">Created by:</span>
                        <span className="ml-2">{selectedIncident.created_by}</span>
                      </div>
                      {selectedIncident.assigned_to && (
                        <div className="flex items-center text-sm text-gray-600">
                          <User className="w-4 h-4 mr-2" />
                          <span className="font-medium">Assigned to:</span>
                          <span className="ml-2">{selectedIncident.assigned_to}</span>
                        </div>
                      )}
                      <div className="flex items-center text-sm text-gray-600">
                        <Calendar className="w-4 h-4 mr-2" />
                        <span className="font-medium">Created:</span>
                        <span className="ml-2">{formatDateTime(selectedIncident.created_at)}</span>
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <Calendar className="w-4 h-4 mr-2" />
                        <span className="font-medium">Updated:</span>
                        <span className="ml-2">{formatDateTime(selectedIncident.updated_at)}</span>
                      </div>
                    </div>
                  </div>

                  {selectedIncident.tags && selectedIncident.tags.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Tags</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedIncident.tags.map((tag) => (
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
              </div>

              {/* Internal Notes */}
              {selectedIncident.internal_notes && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Internal Notes</h4>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <p className="text-sm text-gray-700">{selectedIncident.internal_notes}</p>
                  </div>
                </div>
              )}

              {/* Updates Timeline */}
              {selectedIncident.updates && selectedIncident.updates.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-4">Updates Timeline</h4>
                  <div className="space-y-4">
                    {selectedIncident.updates.map((update, index) => (
                      <div key={update.id} className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          <div className={`w-3 h-3 rounded-full ${
                            index === 0 ? 'bg-blue-500' : 'bg-gray-300'
                          }`}></div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              update.status === 'investigating' ? 'text-yellow-600 bg-yellow-100' :
                              update.status === 'identified' ? 'text-blue-600 bg-blue-100' :
                              update.status === 'monitoring' ? 'text-orange-600 bg-orange-100' :
                              update.status === 'resolved' ? 'text-green-600 bg-green-100' :
                              'text-gray-600 bg-gray-100'
                            }`}>
                              {update.status.replace('_', ' ')}
                            </span>
                            <span className="text-xs text-gray-500">
                              {formatDateTime(update.created_at)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-1">{update.message}</p>
                          {update.public_message && update.public_message !== update.message && (
                            <div className="bg-blue-50 border border-blue-200 rounded-md p-2">
                              <p className="text-xs text-blue-700 font-medium mb-1">Public Message:</p>
                              <p className="text-xs text-blue-600">{update.public_message}</p>
                            </div>
                          )}
                          {update.internal_notes && (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-2 mt-2">
                              <p className="text-xs text-yellow-700 font-medium mb-1">Internal Notes:</p>
                              <p className="text-xs text-yellow-600">{update.internal_notes}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 rounded-b-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => {
                      setShowViewModal(false)
                      setShowAddUpdateModal(true)
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Add Update
                  </button>
                  <button
                    onClick={() => {
                      setShowViewModal(false)
                      setShowUpdateModal(true)
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Edit Incident
                  </button>
                </div>
                <button
                  onClick={() => setShowViewModal(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Update Slider */}
      {showAddUpdateModal && selectedIncident && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-xl transform transition-transform duration-300 ease-in-out">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Add Update to Incident</h3>
                <button
                  onClick={() => setShowAddUpdateModal(false)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mt-2">Adding update to: <strong>{selectedIncident.title}</strong></p>
            </div>
            
            <div className="px-6 py-6 max-h-96 overflow-y-auto">
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={updateForm.status}
                    onChange={(e) => setUpdateForm({ ...updateForm, status: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="">Select Status</option>
                    <option value="investigating">Investigating</option>
                    <option value="identified">Identified</option>
                    <option value="monitoring">Monitoring</option>
                    <option value="resolved">Resolved</option>
                    <option value="post_incident">Post Incident</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Update Type</label>
                  <select
                    value={updateForm.update_type}
                    onChange={(e) => setUpdateForm({ ...updateForm, update_type: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="status_update">Status Update</option>
                    <option value="investigation_update">Investigation Update</option>
                    <option value="resolution_update">Resolution Update</option>
                    <option value="incident_created">Incident Created</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                  <textarea
                    value={updateForm.message}
                    onChange={(e) => setUpdateForm({ ...updateForm, message: e.target.value })}
                    placeholder="Internal message for the update"
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Public Message</label>
                  <textarea
                    value={updateForm.public_message}
                    onChange={(e) => setUpdateForm({ ...updateForm, public_message: e.target.value })}
                    placeholder="Public message for customers"
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Internal Notes</label>
                  <textarea
                    value={updateForm.internal_notes}
                    onChange={(e) => setUpdateForm({ ...updateForm, internal_notes: e.target.value })}
                    placeholder="Internal notes (optional)"
                    rows={2}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>

            </div>
            
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4">
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowAddUpdateModal(false)
                    setUpdateForm({
                      status: '',
                      message: '',
                      public_message: '',
                      internal_notes: '',
                      update_type: 'status_update'
                    })
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddUpdate}
                  disabled={!updateForm.message || !updateForm.public_message}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add Update
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Incident Slider */}
      {showUpdateModal && selectedIncident && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="fixed right-0 top-0 h-full w-11/12 max-w-4xl bg-white shadow-xl transform transition-transform duration-300 ease-in-out">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-gray-900">Edit Incident</h3>
                <button
                  onClick={() => setShowUpdateModal(false)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <div className="px-6 py-6 max-h-96 overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                    <input
                      type="text"
                      value={editForm.title}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      value={editForm.description}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                      rows={3}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                    <select
                      value={editForm.status}
                      onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
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
                      value={editForm.severity}
                      onChange={(e) => setEditForm({ ...editForm, severity: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                      <option value="minor">Minor</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Incident Type</label>
                    <select
                      value={editForm.incident_type}
                      onChange={(e) => setEditForm({ ...editForm, incident_type: e.target.value })}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="outage">Outage</option>
                      <option value="degraded_performance">Degraded Performance</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="security">Security</option>
                      <option value="feature_disabled">Feature Disabled</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Affected Services</label>
                    <input
                      type="text"
                      value={editForm.affected_services.join(', ')}
                      onChange={(e) => setEditForm({ ...editForm, affected_services: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="service1, service2, service3"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Affected Regions</label>
                    <input
                      type="text"
                      value={editForm.affected_regions.join(', ')}
                      onChange={(e) => setEditForm({ ...editForm, affected_regions: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="us-east-1, eu-west-1"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Affected Components</label>
                    <input
                      type="text"
                      value={editForm.affected_components.join(', ')}
                      onChange={(e) => setEditForm({ ...editForm, affected_components: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="api, database, cache"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
                    <input
                      type="text"
                      value={editForm.assigned_to}
                      onChange={(e) => setEditForm({ ...editForm, assigned_to: e.target.value })}
                      placeholder="username or email"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                    <input
                      type="text"
                      value={editForm.tags.join(', ')}
                      onChange={(e) => setEditForm({ ...editForm, tags: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                      placeholder="tag1, tag2, tag3"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Public Message</label>
                  <textarea
                    value={editForm.public_message}
                    onChange={(e) => setEditForm({ ...editForm, public_message: e.target.value })}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Internal Notes</label>
                  <textarea
                    value={editForm.internal_notes}
                    onChange={(e) => setEditForm({ ...editForm, internal_notes: e.target.value })}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div className="flex items-center space-x-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editForm.is_public}
                      onChange={(e) => setEditForm({ ...editForm, is_public: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Public Incident</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editForm.rss_enabled}
                      onChange={(e) => setEditForm({ ...editForm, rss_enabled: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">RSS Enabled</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 rounded-b-md">
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowUpdateModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditIncident}
                  disabled={!editForm.title || !editForm.public_message}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update Incident
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
