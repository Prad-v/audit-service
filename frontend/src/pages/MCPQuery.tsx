import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, MessageSquare, TrendingUp, AlertTriangle, BarChart3, Clock, Filter } from 'lucide-react';
import { auditApi } from '../lib/api';

interface MCPQueryResponse {
  success: boolean;
  data?: any;
  error?: string;
  query_processed: string;
  query_type: string;
  result_count?: number;
}

interface MCPCapabilities {
  service: string;
  version: string;
  capabilities: {
    [key: string]: {
      description: string;
      examples: string[];
    };
  };
  supported_time_ranges: string[];
  supported_event_types: string[];
  supported_severities: string[];
  supported_services: string[];
}

const MCPQuery: React.FC = () => {
  const [query, setQuery] = useState('');
  const [queryHistory, setQueryHistory] = useState<string[]>([]);
  const [selectedExample, setSelectedExample] = useState<string>('');

  // Fetch MCP capabilities
  const { data: capabilities, isLoading: capabilitiesLoading } = useQuery<MCPCapabilities>({
    queryKey: ['mcp-capabilities'],
    queryFn: () => auditApi.getMCPCapabilities(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Query mutation
  const queryMutation = useMutation<MCPQueryResponse, Error, string>({
    mutationFn: (queryText: string) => auditApi.queryMCP(queryText),
    onSuccess: (data) => {
      if (data.success) {
        setQueryHistory(prev => [query, ...prev.slice(0, 9)]); // Keep last 10 queries
        setQuery('');
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      queryMutation.mutate(query.trim());
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    setSelectedExample(example);
  };

  const renderQueryResult = () => {
    if (!queryMutation.data) return null;

    const { data, query_processed, query_type, result_count, success, error } = queryMutation.data;

    if (!success) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700 font-medium">Query Error</span>
          </div>
          <p className="text-red-600 mt-2">{error}</p>
        </div>
      );
    }

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <MessageSquare className="h-5 w-5 text-blue-500 mr-2" />
            <span className="text-lg font-semibold text-gray-900">Query Results</span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>Type: {query_type}</span>
            {result_count !== undefined && <span>Results: {result_count}</span>}
          </div>
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">Query: "{query_processed}"</p>
        </div>

        {renderResultContent(data, query_type)}
      </div>
    );
  };

  const renderResultContent = (data: any, queryType: string) => {
    switch (queryType) {
      case 'search_results':
        return (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Search Results</h3>
            <div className="space-y-3">
              {data.events?.map((event: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        event.severity === 'critical' ? 'bg-red-100 text-red-800' :
                        event.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                        event.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {event.severity}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{event.event_type}</span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="mt-2">
                    <p className="text-sm text-gray-700">{event.action}</p>
                    <p className="text-xs text-gray-500">Service: {event.service_name}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'analytics':
        return (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Analytics</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900">Total Events</h4>
                <p className="text-2xl font-bold text-blue-600">{data.total_events}</p>
              </div>
              {data.by_event_type && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-medium text-green-900">By Event Type</h4>
                  <div className="space-y-1">
                    {Object.entries(data.by_event_type).map(([type, count]: [string, any]) => (
                      <div key={type} className="flex justify-between text-sm">
                        <span>{type}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {data.by_severity && (
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-medium text-purple-900">By Severity</h4>
                  <div className="space-y-1">
                    {Object.entries(data.by_severity).map(([severity, count]: [string, any]) => (
                      <div key={severity} className="flex justify-between text-sm">
                        <span>{severity}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 'trends':
        return (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Trends</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="space-y-2">
                {data.trends?.map((trend: any, index: number) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {new Date(trend.hour).toLocaleString()}
                    </span>
                    <span className="font-medium">{trend.count} events</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'summary':
        return (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900">Recent Events</h4>
                <div className="space-y-2">
                  {data.recent_events?.slice(0, 5).map((event: any, index: number) => (
                    <div key={index} className="text-sm">
                      <span className="font-medium">{event.event_type}</span>
                      <span className="text-gray-500 ml-2">
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-900">Top Services</h4>
                <div className="space-y-1">
                  {Object.entries(data.top_services || {}).map(([service, count]: [string, any]) => (
                    <div key={service} className="flex justify-between text-sm">
                      <span>{service}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'alerts':
        return (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Alerts</h3>
            <div className="space-y-4">
              {data.high_severity_events?.length > 0 && (
                <div>
                  <h4 className="font-medium text-red-900 mb-2">High Severity Events</h4>
                  <div className="space-y-2">
                    {data.high_severity_events.map((event: any, index: number) => (
                      <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-red-900">{event.event_type}</span>
                          <span className="text-sm text-red-600">{event.severity}</span>
                        </div>
                        <p className="text-sm text-red-700 mt-1">{event.action}</p>
                        <p className="text-xs text-red-500 mt-1">
                          {new Date(event.timestamp).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {data.failed_events?.length > 0 && (
                <div>
                  <h4 className="font-medium text-orange-900 mb-2">Failed Events</h4>
                  <div className="space-y-2">
                    {data.failed_events.map((event: any, index: number) => (
                      <div key={index} className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-orange-900">{event.event_type}</span>
                          <span className="text-sm text-orange-600">{event.status}</span>
                        </div>
                        <p className="text-sm text-orange-700 mt-1">{event.action}</p>
                        <p className="text-xs text-orange-500 mt-1">
                          {new Date(event.timestamp).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="text-gray-500">
            <p>Query type "{queryType}" not supported for display.</p>
            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Natural Language Query</h1>
        <p className="text-gray-600">
          Query your audit events using natural language. Ask questions about events, trends, and analytics.
        </p>
      </div>

      {/* Query Input */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Ask about your audit events
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Show me all login events from today"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={queryMutation.isPending}
              />
              <button
                type="submit"
                disabled={!query.trim() || queryMutation.isPending}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <Search className="h-4 w-4 mr-2" />
                {queryMutation.isPending ? 'Querying...' : 'Query'}
              </button>
            </div>
          </div>
        </form>

        {/* Query History */}
        {queryHistory.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Queries</h3>
            <div className="flex flex-wrap gap-2">
              {queryHistory.map((histQuery, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(histQuery)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200"
                >
                  {histQuery}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Examples */}
      {capabilities && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Example Queries</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(capabilities.capabilities).map(([capability, details]) => (
              <div key={capability} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2 capitalize">
                  {capability.replace(/_/g, ' ')}
                </h3>
                <p className="text-sm text-gray-600 mb-3">{details.description}</p>
                <div className="space-y-2">
                  {details.examples.slice(0, 2).map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleExampleClick(example)}
                      className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-2 rounded"
                    >
                      "{example}"
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Capabilities Info */}
      {capabilities && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Supported Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Time Ranges</h3>
              <div className="space-y-1">
                {capabilities.supported_time_ranges.map((range) => (
                  <span key={range} className="block text-sm text-gray-600">{range}</span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Event Types</h3>
              <div className="space-y-1">
                {capabilities.supported_event_types.map((type) => (
                  <span key={type} className="block text-sm text-gray-600">{type}</span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Severity Levels</h3>
              <div className="space-y-1">
                {capabilities.supported_severities.map((severity) => (
                  <span key={severity} className="block text-sm text-gray-600">{severity}</span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Services</h3>
              <div className="space-y-1">
                {capabilities.supported_services.map((service) => (
                  <span key={service} className="block text-sm text-gray-600">{service}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Query Results */}
      {queryMutation.data && renderQueryResult()}

      {/* Loading State */}
      {queryMutation.isPending && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Processing your query...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {queryMutation.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700 font-medium">Query Failed</span>
          </div>
          <p className="text-red-600 mt-2">{queryMutation.error.message}</p>
        </div>
      )}
    </div>
  );
};

export default MCPQuery;
