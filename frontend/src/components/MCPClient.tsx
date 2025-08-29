import React, { useState, useEffect, useCallback } from 'react';
import { MessageSquare, Send, Loader2, AlertCircle, CheckCircle, CogIcon, X } from 'lucide-react';

interface MCPMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  data?: any;
  error?: string;
}

interface LLMProvider {
  provider_id: string;
  name: string;
  provider_type: string;
  status: string;
  model_name: string;
}

interface MCPClientProps {
  onMessage?: (message: MCPMessage) => void;
  className?: string;
}

const MCPClient: React.FC<MCPClientProps> = ({ onMessage, className = '' }) => {
  const [messages, setMessages] = useState<MCPMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [showProviderSettings, setShowProviderSettings] = useState(false);

  const API_BASE = 'http://localhost:8000/api/v1/mcp';

  // Initialize MCP connection
  const initializeMCP = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (response.ok) {
        const healthData = await response.json();
        setIsConnected(true);
        
        // Load capabilities
        const capabilitiesResponse = await fetch(`${API_BASE}/capabilities`);
        if (capabilitiesResponse.ok) {
          const capabilitiesData = await capabilitiesResponse.json();
          setCapabilities(capabilitiesData);
        }

        // Load LLM providers
        await fetchProviders();

        const systemMessage: MCPMessage = {
          id: Date.now().toString(),
          type: 'system',
          content: `Connected to ${healthData.service} v${healthData.version}. You can ask questions about audit events using natural language.`,
          timestamp: new Date()
        };
        setMessages([systemMessage]);
      } else {
        throw new Error('Failed to connect to MCP server');
      }
    } catch (error) {
      setIsConnected(false);
      const errorMessage: MCPMessage = {
        id: Date.now().toString(),
        type: 'system',
        content: 'Failed to connect to MCP server. Please check if the server is running.',
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      setMessages([errorMessage]);
    }
  }, []);

  // Fetch LLM providers
  const fetchProviders = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/llm/providers');
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers || []);
      }
    } catch (error) {
      console.error('Error fetching providers:', error);
    }
  }, []);

  // Send message to MCP server
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !isConnected) return;

    const userMessage: MCPMessage = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/query${selectedProvider ? `?provider_id=${selectedProvider}` : ''}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content,
          limit: 50
        })
      });

      if (response.ok) {
        const result = await response.json();
        
        const assistantMessage: MCPMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: formatResponse(result),
          timestamp: new Date(),
          data: result.data
        };

        setMessages(prev => [...prev, assistantMessage]);
        onMessage?.(assistantMessage);
      } else {
        throw new Error('Failed to get response from MCP server');
      }
    } catch (error) {
      const errorMessage: MCPMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error'
      };

      setMessages(prev => [...prev, errorMessage]);
      onMessage?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, onMessage]);

  // Format response for display
  const formatResponse = (result: any): string => {
    if (!result.success) {
      return `Error: ${result.error || 'Unknown error occurred'}`;
    }

    const data = result.data;
    const queryType = result.query_type;

    // Check if LLM summary is available
    if (data.llm_summary && data.llm_summary.has_llm_analysis) {
      return data.llm_summary.summary;
    }

    switch (queryType) {
      case 'search_results':
        if (data.count === 0) {
          return `No audit events found matching your query. Try broadening your search criteria.`;
        }
        return `Found ${data.count} audit events matching your query. Here are the results:`;
      
      case 'analytics':
        return `Analytics Results:\n- Total Events: ${data.total_events}\n- By Event Type: ${Object.entries(data.by_event_type || {}).map(([k, v]) => `${k}: ${v}`).join(', ')}\n- By Status: ${Object.entries(data.by_status || {}).map(([k, v]) => `${k}: ${v}`).join(', ')}`;
      
      case 'trends':
        return `Trend Analysis:\n- Time Range: ${data.time_range}\n- Found ${data.trends?.length || 0} data points showing trends over time.`;
      
      case 'alerts':
        return `Alert Summary:\n- Failed Events: ${data.failed_events?.length || 0}\n- Total Alerts: ${data.alert_count || 0}`;
      
      case 'summary':
        return `Summary Report:\n- Recent Events: ${data.recent_events?.length || 0}\n- Status Breakdown: ${Object.entries(data.status_breakdown || {}).map(([k, v]) => `${k}: ${v}`).join(', ')}\n- Top Services: ${Object.entries(data.top_services || {}).map(([k, v]) => `${k}: ${v}`).join(', ')}`;
      
      default:
        return `Query processed successfully. Found ${data.count || 0} results.`;
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input);
    }
  };

  // Initialize on mount
  useEffect(() => {
    initializeMCP();
  }, [initializeMCP]);

  return (
    <div className={`flex flex-col h-full bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">MCP Assistant</h3>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <div className="flex items-center space-x-1 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm">Connected</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">Disconnected</span>
            </div>
          )}
        </div>
      </div>

      {/* LLM Provider Settings */}
      <div className="flex items-center justify-between p-3 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">LLM Provider:</span>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1 bg-white"
          >
            <option value="">No LLM (Raw Results)</option>
            {providers
              .filter(p => p.status === 'active')
              .map((provider) => (
                <option key={provider.provider_id} value={provider.provider_id}>
                  {provider.name} ({provider.model_name})
                </option>
              ))}
          </select>
        </div>
        <button
          onClick={() => setShowProviderSettings(true)}
          className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
        >
          <CogIcon className="h-4 w-4" />
          <span>Settings</span>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.type === 'system'
                  ? 'bg-gray-100 text-gray-700'
                  : 'bg-gray-50 text-gray-900 border border-gray-200'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              {message.data && (
                <div className="mt-2 text-xs text-gray-500">
                  <details>
                    <summary>View Data</summary>
                    <pre className="mt-1 text-xs overflow-auto">
                      {JSON.stringify(message.data, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
              {message.error && (
                <div className="mt-2 text-xs text-red-500">
                  Error: {message.error}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-50 text-gray-900 border border-gray-200 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Processing your query...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about audit events (e.g., 'Show me login events from today')"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={!isConnected || isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || !isConnected || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>

      {/* Quick Examples */}
      {capabilities && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Example Queries:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {capabilities.capabilities?.natural_language_search?.examples?.slice(0, 4).map((example: string, index: number) => (
              <button
                key={index}
                onClick={() => setInput(example)}
                className="text-left text-xs text-blue-600 hover:text-blue-800 p-2 rounded bg-white border border-gray-200 hover:border-blue-300 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Provider Settings Modal */}
      {showProviderSettings && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">LLM Provider Settings</h3>
                <button
                  onClick={() => setShowProviderSettings(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Configure LLM providers to enable AI-powered summarization of your audit queries.
              </p>
              <div className="space-y-3">
                {providers.length === 0 ? (
                  <div className="text-center py-4 text-gray-500">
                    No providers configured. Add your first provider to enable AI summarization.
                  </div>
                ) : (
                  providers.map((provider) => (
                    <div key={provider.provider_id} className="border rounded p-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium text-gray-900">{provider.name}</h4>
                          <p className="text-sm text-gray-500">
                            {provider.provider_type} • {provider.model_name}
                          </p>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            provider.status === 'active' ? 'bg-green-100 text-green-800' :
                            provider.status === 'inactive' ? 'bg-gray-100 text-gray-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {provider.status}
                          </span>
                        </div>
                        <button
                          onClick={() => setSelectedProvider(provider.provider_id)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Use
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => window.open('/llm-providers', '_blank')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Manage Providers
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MCPClient;
