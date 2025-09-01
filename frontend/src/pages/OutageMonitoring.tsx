import { useState, useEffect } from 'react'
import { RefreshCw, AlertTriangle, CheckCircle, Clock, Activity, Calendar, BarChart3, Filter, Circle, X, ExternalLink } from 'lucide-react'
import { eventsApi } from '@/lib/api'
import { OutageProgressSlider } from '../components/OutageProgressSlider'

interface OutageMonitoringStatus {
  service_status: string
  check_interval_seconds: number
  last_check_time: string | null
  monitored_providers: Array<{
    provider: string
    last_check: string | null
    known_outages_count: number
  }>
}

interface OutageEvent {
  event_id: string
  provider: string
  service: string
  region: string | null
  severity: string
  status: string
  title: string
  description: string
  event_time: string
  resolved_at: string | null
  outage_status: string
  affected_services: string[]
  affected_regions: string[]
}

interface OutageHistoryResponse {
  outages: OutageEvent[]
  total_count: number
  statistics: Record<string, {
    count: number
    first_outage: string | null
    last_outage: string | null
  }>
  period: {
    days: number
    start_date: string
    end_date: string
  }
}

interface ProviderResult {
  status: 'success' | 'error' | 'pending'
  outages_found?: number
  checked_at?: string
  error?: string
  details?: {
    rss_feed: string
    api_url: string
  }
}

interface TimelineEvent {
  time: string
  description: string
  type: 'start' | 'update' | 'resolution' | 'milestone'
}

// Timeline parsing utility functions
const parseTimelineFromDescription = (description: string): TimelineEvent[] => {
  const timeline: TimelineEvent[] = []
  
  // Remove HTML tags for better parsing
  const cleanDescription = description.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
  
  // Try to parse JSON updates first (if description contains structured data)
  try {
    // Look for JSON-like structure in the description
    const jsonMatch = cleanDescription.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const jsonStr = jsonMatch[0]
      const parsed = JSON.parse(jsonStr)
      
      // If there are updates with timestamps, use them
      if (parsed.updates && Array.isArray(parsed.updates)) {
        parsed.updates.forEach((update: any) => {
          if (update.modified && update.message) {
            const date = new Date(update.modified)
            const formattedTime = date.toLocaleString()
            
            timeline.push({
              time: formattedTime,
              description: update.message,
              type: 'milestone'
            })
          }
        })
        
        // Sort by timestamp
        timeline.sort((a, b) => {
          const timeA = new Date(a.time).getTime()
          const timeB = new Date(b.time).getTime()
          return timeA - timeB
        })
        
        return timeline
      }
    }
  } catch (e) {
    // If JSON parsing fails, continue with text parsing
  }
  
  // Enhanced timeline patterns for GCP incidents
  const patterns = [
    // GCP specific timeline patterns
    {
      pattern: /(\d{1,2}:\d{2}\s+(?:US\/Pacific|UTC|EST|PST|CST|MST|GMT|PDT|EDT|CDT|MDT)):\s*(.+?)(?=\n|\.|$)/gi,
      type: 'milestone' as const
    },
    // Date-time ranges like "18 July 2025 07:50 - 09:47"
    {
      pattern: /(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s+\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})/gi,
      type: 'start' as const
    },
    // Alert patterns
    {
      pattern: /(Alert Time|Alerted by|Engineers were alerted|Monitoring system alerted):\s*(.+?)(?=\n|\.|$)/gi,
      type: 'start' as const
    },
    // Resolution patterns
    {
      pattern: /(Resolved|Fixed|Restored|Recovered|Mitigated|Stable|Completed):\s*(.+?)(?=\n|\.|$)/gi,
      type: 'resolution' as const
    },
    // Timeline patterns
    {
      pattern: /(Timeline|Events|Updates|Chronology):\s*(.+?)(?=\n|\.|$)/gi,
      type: 'milestone' as const
    },
    // Root cause patterns
    {
      pattern: /(Root cause|Cause|Issue|Problem):\s*(.+?)(?=\n|\.|$)/gi,
      type: 'milestone' as const
    },
    // Impact patterns
    {
      pattern: /(Impact|Affected|Disruption):\s*(.+?)(?=\n|\.|$)/gi,
      type: 'milestone' as const
    }
  ]
  
  patterns.forEach(({ pattern, type }) => {
    const matches = cleanDescription.matchAll(pattern)
    for (const match of matches) {
      const time = match[1] || 'Unknown'
      const description = match[2] || match[0]
      
      // Clean up the description
      const cleanDesc = description
        .replace(/^\s*[-•*]\s*/, '') // Remove bullet points
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim()
      
      if (cleanDesc && cleanDesc.length > 3) {
        timeline.push({
          time: time.trim(),
          description: cleanDesc,
          type
        })
      }
    }
  })
  
  // Add specific GCP incident timeline events if found
  if (cleanDescription.includes('GCP:') && cleanDescription.includes('GWS:')) {
    const gcpMatch = cleanDescription.match(/GCP:\s*([^G]+?)(?=GWS:|$)/i)
    const gwsMatch = cleanDescription.match(/GWS:\s*([^G]+?)(?=GCP:|$)/i)
    
    if (gcpMatch) {
      timeline.push({
        time: 'GCP Impact',
        description: gcpMatch[1].trim(),
        type: 'milestone'
      })
    }
    
    if (gwsMatch) {
      timeline.push({
        time: 'GWS Impact',
        description: gwsMatch[1].trim(),
        type: 'milestone'
      })
    }
  }
  
  // Sort timeline events by time if possible
  timeline.sort((a, b) => {
    const timeA = extractTimeFromString(a.time)
    const timeB = extractTimeFromString(b.time)
    if (timeA && timeB) {
      return timeA.getTime() - timeB.getTime()
    }
    return 0
  })
  
  // Remove duplicates
  const uniqueTimeline = timeline.filter((event, index, self) => 
    index === self.findIndex(e => e.description === event.description)
  )
  
  return uniqueTimeline
}

const extractTimeFromString = (timeStr: string): Date | null => {
  // Try to parse various time formats
  const patterns = [
    /(\d{1,2}):(\d{2})\s+(US\/Pacific|UTC|EST|PST|CST|MST|GMT|PDT|EDT|CDT|MDT)/i,
    /(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\s+(\d{1,2}):(\d{2})/i
  ]
  
  for (const pattern of patterns) {
    const match = timeStr.match(pattern)
    if (match) {
      try {
        // Create a date object (simplified parsing)
        const now = new Date()
        const hour = parseInt(match[1] || match[4])
        const minute = parseInt(match[2] || match[5])
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hour, minute)
        return date
      } catch (e) {
        console.warn('Failed to parse time:', timeStr)
      }
    }
  }
  
  return null
}

// Timeline Component
function TimelineView({ timeline }: { timeline: TimelineEvent[] }) {
  if (timeline.length === 0) return null
  
  return (
    <div className="space-y-4">
      <div className="text-gray-500 font-medium">Timeline:</div>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300"></div>
        
        <div className="space-y-4">
          {timeline.map((event, index) => (
            <div key={index} className="relative flex items-start space-x-4">
              {/* Timeline dot */}
              <div className="relative z-10 flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  event.type === 'start' ? 'bg-green-500' :
                  event.type === 'resolution' ? 'bg-blue-500' :
                  event.type === 'milestone' ? 'bg-yellow-500' :
                  'bg-gray-500'
                }`}>
                  <Circle className="w-4 h-4 text-white" fill="currentColor" />
                </div>
              </div>
              
              {/* Event content */}
              <div className="flex-1 min-w-0 bg-white rounded-lg border p-3 shadow-sm">
                <div className="text-sm font-medium text-gray-900 mb-1">
                  {event.time}
                </div>
                <div className="text-sm text-gray-600">
                  {event.description}
                </div>
                <div className="mt-1">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    event.type === 'start' ? 'bg-green-100 text-green-800' :
                    event.type === 'resolution' ? 'bg-blue-100 text-blue-800' :
                    event.type === 'milestone' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {event.type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Summary Component for better readability
function IncidentSummary({ outage, onViewDetails }: { outage: OutageEvent; onViewDetails: (outage: OutageEvent) => void }) {
  const cleanDescription = outage.description.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
  
  // Calculate duration from start and end times
  const calculateDuration = () => {
    if (!outage.event_time || !outage.resolved_at) return null
    
    try {
      const startTime = new Date(outage.event_time)
      const endTime = new Date(outage.resolved_at)
      const durationMs = endTime.getTime() - startTime.getTime()
      
      if (durationMs <= 0) return null
      
      const hours = Math.floor(durationMs / (1000 * 60 * 60))
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))
      
      if (hours > 0 && minutes > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''} ${minutes} minute${minutes > 1 ? 's' : ''}`
      } else if (hours > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''}`
      } else if (minutes > 0) {
        return `${minutes} minute${minutes > 1 ? 's' : ''}`
      } else {
        return 'Less than 1 minute'
      }
    } catch (e) {
      console.warn('Failed to calculate duration:', e)
      return null
    }
  }
  
  // Extract most recent update from description
  const extractMostRecentUpdate = () => {
    // Look for the most recent timeline entry or update
    const timeline = parseTimelineFromDescription(outage.description)
    
    if (timeline.length > 0) {
      // Return the most recent update (last in timeline)
      const mostRecent = timeline[timeline.length - 1]
      return {
        time: mostRecent.time,
        description: mostRecent.description
      }
    }
    
    // Fallback: look for common update patterns
    const updatePatterns = [
      /(?:Update|Status|Latest)[:\s]+([^.]+)/i,
      /(?:Resolved|Fixed|Completed)[:\s]+([^.]+)/i,
      /(?:Current|Present)[:\s]+([^.]+)/i
    ]
    
    for (const pattern of updatePatterns) {
      const match = cleanDescription.match(pattern)
      if (match) {
        return {
          time: 'Latest Update',
          description: match[1].trim()
        }
      }
    }
    
    // If no specific update found, return the first meaningful sentence
    const sentences = cleanDescription.split(/[.!?]+/).filter(s => s.trim().length > 20)
    if (sentences.length > 0) {
      return {
        time: 'Current Status',
        description: sentences[0].trim()
      }
    }
    
    return null
  }
  
  const calculatedDuration = calculateDuration()
  const mostRecentUpdate = extractMostRecentUpdate()
  
  return (
    <div className="space-y-4">
      <div className="text-gray-500 font-medium">Summary:</div>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="space-y-4">
          {mostRecentUpdate && (
            <div>
              <div className="text-sm font-medium text-blue-900 mb-1">{mostRecentUpdate.time}:</div>
              <div className="text-sm text-blue-800">{mostRecentUpdate.description}</div>
            </div>
          )}
          {calculatedDuration && (
            <div>
              <div className="text-sm font-medium text-blue-900 mb-1">Duration:</div>
              <div className="text-sm text-blue-800">{calculatedDuration}</div>
            </div>
          )}
          <div className="pt-2 border-t border-blue-200">
            <button
              onClick={() => onViewDetails(outage)}
              className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors"
            >
              <ExternalLink className="w-3 h-3 mr-1.5" />
              View Details
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Detailed Incident Slider Component
function DetailedIncidentSlider({ 
  outage, 
  isOpen, 
  onClose,
  getSeverityColor,
  getStatusColor,
  formatDateTime
}: { 
  outage: OutageEvent | null
  isOpen: boolean
  onClose: () => void
  getSeverityColor: (severity: string) => string
  getStatusColor: (status: string) => string
  formatDateTime: (dateString: string) => string
}) {
  if (!outage || !isOpen) return null

  const timeline = parseTimelineFromDescription(outage.description)
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-semibold text-gray-900">Incident Details</h2>
            <div className="flex space-x-2">
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${getSeverityColor(outage.severity)}`}>
                {outage.severity}
              </span>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(outage.resolved_at ? 'resolved' : outage.status)}`}>
                {outage.resolved_at ? 'resolved' : outage.status}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          <div className="p-6 space-y-6">
            {/* Incident Overview */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3">Incident Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 font-medium">Title:</span>
                  <span className="ml-2 text-gray-900">{outage.title}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-medium">ID:</span>
                  <a 
                    href={`https://status.cloud.google.com/incidents/${outage.event_id.replace(/^historical-gcp-/, '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-blue-600 hover:text-blue-800 underline font-mono text-xs"
                  >
                    {outage.event_id.replace(/^historical-gcp-/, '')}
                  </a>
                </div>
                <div>
                  <span className="text-gray-500 font-medium">Service:</span>
                  <span className="ml-2 text-gray-900">{outage.service}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-medium">Region:</span>
                  <span className="ml-2 text-gray-900">{outage.region || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-medium">Begin Time:</span>
                  <span className="ml-2 text-gray-900">{formatDateTime(outage.event_time)}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-medium">End Time:</span>
                  <span className="ml-2 text-gray-900">
                    {outage.resolved_at ? formatDateTime(outage.resolved_at) : 'Ongoing'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 font-medium">Status:</span>
                  <span className="ml-2 text-gray-900 capitalize">
                    {outage.resolved_at ? 'resolved' : outage.status}
                  </span>
                </div>
              </div>
            </div>

            {/* Enhanced Timeline */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Detailed Timeline</h3>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300"></div>
                
                <div className="space-y-6">
                  {timeline.length > 0 ? timeline.map((event, index) => (
                    <div key={index} className="relative flex items-start space-x-6">
                      {/* Timeline dot */}
                      <div className="relative z-10 flex-shrink-0">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                          event.type === 'start' ? 'bg-green-500' :
                          event.type === 'resolution' ? 'bg-blue-500' :
                          event.type === 'milestone' ? 'bg-yellow-500' :
                          'bg-gray-500'
                        }`}>
                          <Circle className="w-6 h-6 text-white" fill="currentColor" />
                        </div>
                      </div>
                      
                      {/* Event content */}
                      <div className="flex-1 min-w-0 bg-white rounded-lg border p-4 shadow-sm">
                        <div className="text-base font-medium text-gray-900 mb-2">
                          {event.time}
                        </div>
                        <div className="text-sm text-gray-600 mb-3">
                          {event.description}
                        </div>
                        <div>
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                            event.type === 'start' ? 'bg-green-100 text-green-800' :
                            event.type === 'resolution' ? 'bg-blue-100 text-blue-800' :
                            event.type === 'milestone' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {event.type}
                          </span>
                        </div>
                      </div>
                    </div>
                  )) : (
                    <div className="text-center py-8 text-gray-500">
                      No timeline events found in the incident description.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Full Description */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Full Description</h3>
              <div 
                className="text-sm text-gray-700 bg-gray-50 p-4 rounded border prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: outage.description }}
              />
            </div>

            {/* Affected Resources */}
            {(outage.affected_services.length > 0 || outage.affected_regions.length > 0) && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Affected Resources</h3>
                <div className="space-y-4">
                  {outage.affected_services.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-gray-700 mb-2">Affected Services:</div>
                      <div className="flex flex-wrap gap-2">
                        {outage.affected_services.map((service, index) => (
                          <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                            {service}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {outage.affected_regions.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-gray-700 mb-2">Affected Regions:</div>
                      <div className="flex flex-wrap gap-2">
                        {outage.affected_regions.map((region, index) => (
                          <span key={index} className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                            {region}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function OutageMonitoring() {
  const [status, setStatus] = useState<OutageMonitoringStatus | null>(null)
  const [outageHistory, setOutageHistory] = useState<OutageEvent[]>([])
  const [historyStats, setHistoryStats] = useState<OutageHistoryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeOutagesCount, setActiveOutagesCount] = useState(0)
  
  // Progress slider state
  const [showProgressSlider, setShowProgressSlider] = useState(false)
  const [progress, setProgress] = useState(0)
  const [providerResults, setProviderResults] = useState<Record<string, ProviderResult>>({})
  const [currentProvider, setCurrentProvider] = useState<string>('')
  const [totalOutagesFound, setTotalOutagesFound] = useState(0)
  
  // Filter state
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedDays, setSelectedDays] = useState<number>(365)
  const [dataSource, setDataSource] = useState<'database' | 'providers'>('database')
  
  // Tab state
  const [activeTab, setActiveTab] = useState<'active' | 'historical'>('active')
  
  // Detailed slider state
  const [selectedOutage, setSelectedOutage] = useState<OutageEvent | null>(null)
  const [isDetailSliderOpen, setIsDetailSliderOpen] = useState(false)

  useEffect(() => {
    loadStatus()
    loadOutageHistory()
  }, [selectedProvider, selectedDays, dataSource])

  const loadStatus = async () => {
    try {
      setLoading(true)
      const response = await eventsApi.getOutageMonitoringStatus()
      setStatus(response)
      setError(null)
    } catch (err) {
      console.error('Failed to load outage monitoring status:', err)
      setError('Failed to load status')
    } finally {
      setLoading(false)
    }
  }

  const loadOutageHistory = async () => {
    try {
      setLoadingHistory(true)
      setError(null)
      const response = await eventsApi.getOutageHistory(selectedProvider || undefined, 100, selectedDays, dataSource)
      setOutageHistory(response.outages || [])
      setHistoryStats(response)
    } catch (err) {
      console.error('Failed to load outage history:', err)
      setError('Failed to load outage history')
    } finally {
      setLoadingHistory(false)
    }
  }

  // Helper functions
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'investigating': return 'bg-blue-100 text-blue-800'
      case 'resolved': return 'bg-green-100 text-green-800'
      case 'monitoring': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDateTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString()
    } catch (e) {
      return dateString
    }
  }

  const handleViewDetails = (outage: OutageEvent) => {
    setSelectedOutage(outage)
    setIsDetailSliderOpen(true)
  }

  const handleCloseDetails = () => {
    setIsDetailSliderOpen(false)
    setSelectedOutage(null)
  }

  const pauseMonitoring = async () => {
    try {
      await eventsApi.pauseOutageMonitoring()
      await loadStatus()
    } catch (err) {
      console.error('Failed to pause monitoring:', err)
      setError('Failed to pause monitoring')
    }
  }

  const resumeMonitoring = async () => {
    try {
      await eventsApi.resumeOutageMonitoring()
      await loadStatus()
    } catch (err) {
      console.error('Failed to resume monitoring:', err)
      setError('Failed to resume monitoring')
    }
  }

  const checkAllProviders = async () => {
    try {
      setChecking(true)
      setShowProgressSlider(true)
      setProgress(0)
      setProviderResults({})
      setTotalOutagesFound(0)
      
      const response = await eventsApi.checkAllProvidersOutages()
      
      setProviderResults(response.provider_results || {})
      setTotalOutagesFound(response.total_outages_found || 0)
      setProgress(100)
      
      // Reload status after checking
      await loadStatus()
      
      setTimeout(() => {
        setShowProgressSlider(false)
        setChecking(false)
      }, 2000)
      
    } catch (err) {
      console.error('Failed to check all providers:', err)
      setError('Failed to check providers')
      setChecking(false)
      setShowProgressSlider(false)
    }
  }

  const handleProviderFilter = (provider: string) => {
    setSelectedProvider(provider === selectedProvider ? '' : provider)
  }

  const handleDaysFilter = (days: number) => {
    setSelectedDays(days)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }








  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Outage Monitoring</h1>
          <p className="text-gray-600 mt-2">
            Monitor cloud provider outages and status pages
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={checkAllProviders}
            disabled={checking}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${checking ? 'animate-spin' : ''}`} />
            {checking ? 'Checking...' : 'Check All'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('active')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'active'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Active Outages
            </div>
          </button>
          <button
            onClick={() => setActiveTab('historical')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'historical'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Historical Outages
            </div>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'active' ? (
        <ActiveOutagesTab 
          status={status}
          loading={loading}
          onRefresh={loadStatus}
          formatDateTime={formatDateTime}
          activeOutagesCount={activeOutagesCount}
          onActiveCountChange={setActiveOutagesCount}
        />
      ) : (
        <HistoricalOutagesTab 
          outageHistory={outageHistory}
          historyStats={historyStats}
          loadingHistory={loadingHistory}
          selectedProvider={selectedProvider}
          selectedDays={selectedDays}
          dataSource={dataSource}
          onProviderFilter={handleProviderFilter}
          onDaysFilter={handleDaysFilter}
          onDataSourceChange={setDataSource}
          onRefresh={loadOutageHistory}
          onViewDetails={handleViewDetails}
          getSeverityColor={getSeverityColor}
          getStatusColor={getStatusColor}
          formatDate={formatDate}
          formatDateTime={formatDateTime}
        />
      )}

      {/* Progress Slider */}
      <OutageProgressSlider
        isOpen={showProgressSlider}
        onClose={() => setShowProgressSlider(false)}
        isChecking={checking}
        progress={progress}
        providerResults={providerResults}
        totalOutagesFound={totalOutagesFound}
        currentProvider={currentProvider}
      />

      {/* Detailed Incident Slider */}
      <DetailedIncidentSlider
        outage={selectedOutage}
        isOpen={isDetailSliderOpen}
        onClose={handleCloseDetails}
        getSeverityColor={getSeverityColor}
        getStatusColor={getStatusColor}
        formatDateTime={formatDateTime}
      />
    </div>
  )
}

// Active Outages Tab Component
interface ActiveOutagesTabProps {
  status: OutageMonitoringStatus | null
  loading: boolean
  onRefresh: () => void
  formatDateTime: (dateString: string) => string
  activeOutagesCount: number
  onActiveCountChange: (count: number) => void
}

function ActiveOutagesTab({ status, loading, onRefresh, formatDateTime, activeOutagesCount, onActiveCountChange }: ActiveOutagesTabProps) {
  return (
    <div className="space-y-6">
      {/* Service Status */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Service Status</h2>
          <div className="flex space-x-2">
            <button
              onClick={onRefresh}
              disabled={loading}
              className="bg-gray-600 text-white px-3 py-1 rounded-md hover:bg-gray-700 disabled:opacity-50 flex items-center text-sm"
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading status...</p>
          </div>
        ) : status ? (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-lg font-medium">
                Status: Running (Scheduled every 5 minutes)
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900">Check Interval</h3>
                <p className="text-2xl font-bold text-blue-600">
                  {Math.round(status.check_interval_seconds / 60)} min
                </p>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900">Monitored Providers</h3>
                <p className="text-2xl font-bold text-green-600">
                  {status.monitored_providers.length}
                </p>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900">Active Outages</h3>
                <p className="text-2xl font-bold text-orange-600">
                  {activeOutagesCount}
                </p>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900">Last Scanned</h3>
                <p className="text-sm font-medium text-purple-600">
                  {status.last_check_time ? formatDateTime(status.last_check_time) : 'Never'}
                </p>
              </div>
            </div>

            {/* Provider Status */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Provider Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {status.monitored_providers.map((provider) => (
                  <div key={provider.provider} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900 capitalize">
                        {provider.provider}
                      </h4>
                      <span className="text-sm text-gray-500">
                        {provider.known_outages_count} outages
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      Last check: {provider.last_check ? formatDateTime(provider.last_check) : 'Never'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600">No status information available</p>
          </div>
        )}
      </div>

      {/* Active Incidents */}
      <ActiveIncidentsSection onActiveCountChange={onActiveCountChange} />
    </div>
  )
}

// Active Incidents Section Component
function ActiveIncidentsSection({ onActiveCountChange }: { onActiveCountChange?: (count: number) => void }) {
  const [activeOutages, setActiveOutages] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadActiveOutages = async () => {
    setLoading(true)
    setError(null)
    try {
      // Use direct events service port for now until API Gateway is fixed
      const response = await fetch('http://localhost:8003/api/v1/outages/active')
      if (response.ok) {
        const data = await response.json()
        const outages = data.outages || []
        setActiveOutages(outages)
        // Notify parent component of the active outages count
        if (onActiveCountChange) {
          onActiveCountChange(outages.length)
        }
      } else {
        setError('Failed to load active outages')
      }
    } catch (err) {
      setError('Error loading active outages')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadActiveOutages()
    // Refresh every 5 minutes
    const interval = setInterval(loadActiveOutages, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'investigating': return 'bg-blue-100 text-blue-800'
      case 'identified': return 'bg-yellow-100 text-yellow-800'
      case 'monitoring': return 'bg-purple-100 text-purple-800'
      case 'resolved': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDateTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading active incidents...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-center py-8">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadActiveOutages}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Active Incidents</h2>
        <button
          onClick={loadActiveOutages}
          disabled={loading}
          className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center text-sm"
        >
          <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {activeOutages.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-green-600 mb-2">
            <CheckCircle className="w-12 h-12 mx-auto" />
          </div>
          <p className="text-gray-600">No active incidents detected</p>
          <p className="text-sm text-gray-500 mt-1">All cloud services are operating normally</p>
        </div>
      ) : (
        <div className="space-y-4">
          {activeOutages.map((outage) => (
            <div key={outage.event_id} className="border rounded-lg p-4 bg-red-50 border-red-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(outage.severity)}`}>
                      {outage.severity}
                    </span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(outage.status)}`}>
                      {outage.status}
                    </span>
                  </div>
                  
                  <h3 className="font-medium text-gray-900 mb-1">{outage.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{outage.description}</p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Provider:</span>
                      <span className="ml-2 font-medium capitalize">{outage.provider}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Service:</span>
                      <span className="ml-2 font-medium">{outage.service}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Region:</span>
                      <span className="ml-2 font-medium">{outage.region || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Started:</span>
                      <span className="ml-2 font-medium">{formatDateTime(outage.event_time)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Historical Outages Tab Component
interface HistoricalOutagesTabProps {
  outageHistory: OutageEvent[]
  historyStats: OutageHistoryResponse | null
  loadingHistory: boolean
  selectedProvider: string
  selectedDays: number
  dataSource: 'database' | 'providers'
  onProviderFilter: (provider: string) => void
  onDaysFilter: (days: number) => void
  onDataSourceChange: (source: 'database' | 'providers') => void
  onRefresh: () => void
  onViewDetails: (outage: OutageEvent) => void
  getSeverityColor: (severity: string) => string
  getStatusColor: (status: string) => string
  formatDate: (dateString: string) => string
  formatDateTime: (dateString: string) => string
}

function HistoricalOutagesTab({ 
  outageHistory, 
  historyStats, 
  loadingHistory, 
  selectedProvider, 
  selectedDays, 
  dataSource, 
  onProviderFilter, 
  onDaysFilter, 
  onDataSourceChange, 
  onRefresh, 
  onViewDetails,
  getSeverityColor, 
  getStatusColor, 
  formatDate,
  formatDateTime
}: HistoricalOutagesTabProps) {
  return (
    <div className="space-y-6">
      {/* Historical Statistics */}
      {historyStats && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Historical Statistics (Last {selectedDays} days)
            </h2>
            <div className="flex items-center space-x-4">
              {/* Data Source Toggle */}
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">Data Source:</span>
                <div className="flex bg-gray-100 rounded-md p-1">
                  <button
                    onClick={() => onDataSourceChange('database')}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                      dataSource === 'database'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Database
                  </button>
                  <button
                    onClick={() => onDataSourceChange('providers')}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                      dataSource === 'providers'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Cloud APIs
                  </button>
                </div>
              </div>

              {/* Time Range Dropdown */}
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">Time Range:</span>
                <select
                  value={selectedDays}
                  onChange={(e) => onDaysFilter(Number(e.target.value))}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 3 months</option>
                  <option value={180}>Last 6 months</option>
                  <option value={365}>Last 1 year</option>
                </select>
              </div>
            </div>
          </div>

          {/* Statistics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900">Total Outages</h3>
              <p className="text-2xl font-bold text-blue-600">
                {historyStats.total_count}
              </p>
            </div>
            
            {historyStats.statistics && Object.entries(historyStats.statistics).map(([provider, stats]) => (
              <div key={provider} className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900 capitalize">{provider}</h3>
                <p className="text-2xl font-bold text-green-600">
                  {stats.count}
                </p>
                <p className="text-sm text-gray-600">
                  {stats.first_outage && formatDate(stats.first_outage)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </h2>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onProviderFilter('')}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
              selectedProvider === ''
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Providers
          </button>
          <button
            onClick={() => onProviderFilter('gcp')}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
              selectedProvider === 'gcp'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            GCP
          </button>
          <button
            onClick={() => onProviderFilter('aws')}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
              selectedProvider === 'aws'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            AWS
          </button>
          <button
            onClick={() => onProviderFilter('azure')}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
              selectedProvider === 'azure'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Azure
          </button>
          <button
            onClick={() => onProviderFilter('oci')}
            className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
              selectedProvider === 'oci'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            OCI
          </button>
        </div>
      </div>

      {/* Outage History */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Outage History (total: {outageHistory.length})
          </h2>
          <button
            onClick={onRefresh}
            disabled={loadingHistory}
            className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
          >
            <RefreshCw className={`w-4 h-4 ${loadingHistory ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {loadingHistory ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading outage history...</p>
          </div>
        ) : outageHistory.length === 0 ? (
          <div className="text-center py-8 text-gray-600">
            <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
            <p>No outages detected</p>
          </div>
        ) : (
          <div className="space-y-4">
            {outageHistory.map((outage) => (
              <div key={outage.event_id} className="border rounded-lg p-6 hover:bg-gray-50">
                <div className="space-y-4">
                  {/* Header with severity and status badges */}
                  <div className="flex items-center space-x-2 mb-4">
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${getSeverityColor(outage.severity)}`}>
                      {outage.severity}
                    </span>
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(outage.resolved_at ? 'resolved' : outage.status)}`}>
                      {outage.resolved_at ? 'resolved' : outage.status}
                    </span>
                  </div>

                  {/* Incident Details Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="space-y-2">
                      <div className="flex">
                        <span className="text-gray-500 font-medium w-24">Description:</span>
                        <span className="text-gray-900">{outage.title}</span>
                      </div>
                      <div className="flex">
                        <span className="text-gray-500 font-medium w-24">ID:</span>
                        <a 
                          href={`https://status.cloud.google.com/incidents/${outage.event_id.replace(/^historical-gcp-/, '')}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline font-mono text-xs"
                        >
                          {outage.event_id.replace(/^historical-gcp-/, '')}
                        </a>
                      </div>
                      <div className="flex">
                        <span className="text-gray-500 font-medium w-24">Status:</span>
                        <span className="text-gray-900 capitalize">
                          {outage.resolved_at ? 'resolved' : outage.status}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex">
                        <span className="text-gray-500 font-medium w-24">Begin Time:</span>
                        <span className="text-gray-900">{formatDateTime(outage.event_time)}</span>
                      </div>
                      <div className="flex">
                        <span className="text-gray-500 font-medium w-24">End Time:</span>
                        <span className="text-gray-900">
                          {outage.resolved_at ? formatDateTime(outage.resolved_at) : 'Ongoing'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Service and Region Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="flex">
                      <span className="text-gray-500 font-medium w-24">Service:</span>
                      <span className="text-gray-900">{outage.service}</span>
                    </div>
                    <div className="flex">
                      <span className="text-gray-500 font-medium w-24">Region:</span>
                      <span className="text-gray-900">{outage.region || 'N/A'}</span>
                    </div>
                  </div>

                  {/* Summary */}
                  <IncidentSummary outage={outage} onViewDetails={onViewDetails} />
                  


                  {/* Affected Services */}
                  {outage.affected_services.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-gray-500 font-medium">Affected Services:</div>
                      <div className="flex flex-wrap gap-2">
                        {outage.affected_services.map((service, index) => (
                          <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                            {service}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Affected Regions */}
                  {outage.affected_regions.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-gray-500 font-medium">Affected Regions:</div>
                      <div className="flex flex-wrap gap-2">
                        {outage.affected_regions.map((region, index) => (
                          <span key={index} className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                            {region}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
