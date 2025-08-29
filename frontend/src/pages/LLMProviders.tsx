import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Play, X } from 'lucide-react';

interface LLMProvider {
  provider_id: string;
  name: string;
  provider_type: string;
  status: string;
  api_key?: string;
  base_url?: string;
  model_name: string;
  litellm_config?: any;
  created_by?: string;
  created_at: string;
  updated_at: string;
  is_enabled?: boolean;
  is_default?: boolean;
}

interface ProviderType {
  value: string;
  label: string;
  description: string;
}

interface ProviderStatus {
  value: string;
  label: string;
  description: string;
}

interface Model {
  id: string;
  name: string;
  object?: string;
  created?: number;
  owned_by?: string;
}

const LLMProviders: React.FC = () => {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [providerTypes, setProviderTypes] = useState<ProviderType[]>([]);
  const [providerStatuses, setProviderStatuses] = useState<ProviderStatus[]>([]);
  const [availableModels, setAvailableModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionResult, setConnectionResult] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    provider_type: '',
    api_key: '',
    base_url: '',
    model_name: '',
    litellm_config: '',
    status: 'inactive',
    is_enabled: true,
    is_default: false
  });

  useEffect(() => {
    fetchProviders();
    fetchProviderTypes();
    fetchProviderStatuses();
  }, []);

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/v1/llm/providers');
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers || []);
      } else {
        console.error('Failed to fetch providers');
      }
    } catch (error) {
      console.error('Error fetching providers');
    } finally {
      setLoading(false);
    }
  };

  const fetchProviderTypes = async () => {
    try {
      const response = await fetch('/api/v1/llm/providers/types');
      if (response.ok) {
        const data = await response.json();
        setProviderTypes(data.provider_types);
      }
    } catch (error) {
      console.error('Error fetching provider types:', error);
    }
  };

  const fetchProviderStatuses = async () => {
    try {
      const response = await fetch('/api/v1/llm/providers/statuses');
      if (response.ok) {
        const data = await response.json();
        setProviderStatuses(data.statuses);
      }
    } catch (error) {
      console.error('Error fetching provider statuses:', error);
    }
  };

  const getDefaultBaseUrl = (providerType: string): string => {
    const defaultUrls: { [key: string]: string } = {
      'openai': 'https://api.openai.com/v1',
      'anthropic': 'https://api.anthropic.com/v1',
      'google': 'https://generativelanguage.googleapis.com/v1',
      'azure': 'https://your-resource.openai.azure.com',
      'litellm': 'https://api.openai.com/v1',
      'custom': ''
    };
    return defaultUrls[providerType] || '';
  };

  const fetchModels = async (providerType: string, apiKey?: string, baseUrl?: string, litellmConfig?: any) => {
    console.log('fetchModels called with:', { providerType, apiKey: apiKey ? '***' : undefined, baseUrl, litellmConfig });
    try {
      const formData = new FormData();
      formData.append('provider_type', providerType);
      if (apiKey) formData.append('api_key', apiKey);
      if (baseUrl) formData.append('base_url', baseUrl);
      if (litellmConfig) formData.append('litellm_config', JSON.stringify(litellmConfig));

      console.log('Making API call to fetch models...');
      const response = await fetch('/api/v1/llm/providers/models', {
        method: 'POST',
        body: formData
      });

      console.log('API response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('API response data:', data);
        if (data.success) {
          setAvailableModels(data.models || []);
          console.log('Models fetched successfully:', data.message, 'Models count:', data.models?.length);
          
          // Update form data with returned values
          setFormData(prev => ({
            ...prev,
            status: data.status || 'inactive',
            base_url: data.base_url || prev.base_url
          }));
        } else {
          console.error('Failed to fetch models:', data.message);
          setAvailableModels([]);
          setFormData(prev => ({
            ...prev,
            status: data.status || 'error'
          }));
        }
      } else {
        console.error('Error fetching models:', response.statusText);
        setAvailableModels([]);
        setFormData(prev => ({
          ...prev,
          status: 'error'
        }));
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      setAvailableModels([]);
      setFormData(prev => ({
        ...prev,
        status: 'error'
      }));
    }
  };

  const testConnection = async () => {
    if (!formData.provider_type) {
      alert('Please select a provider type first');
      return;
    }

    setTestingConnection(true);
    setConnectionResult(null);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('provider_type', formData.provider_type);
      if (formData.api_key) formDataToSend.append('api_key', formData.api_key);
      if (formData.base_url) formDataToSend.append('base_url', formData.base_url);
      if (formData.litellm_config) formDataToSend.append('litellm_config', formData.litellm_config);

      const response = await fetch('/api/v1/llm/providers/test-connection', {
        method: 'POST',
        body: formDataToSend
      });

      const result = await response.json();
      setConnectionResult(result);

      if (result.success) {
        setAvailableModels(result.models || []);
        setFormData(prev => ({
          ...prev,
          status: result.status || 'active',
          base_url: result.base_url || prev.base_url
        }));
        console.log('Connection test successful:', result.message);
      } else {
        setAvailableModels([]);
        setFormData(prev => ({
          ...prev,
          status: result.status || 'error'
        }));
        console.error('Connection test failed:', result.message);
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      setConnectionResult({
        success: false,
        message: 'Connection test failed: ' + error
      });
      setFormData(prev => ({
        ...prev,
        status: 'error'
      }));
    } finally {
      setTestingConnection(false);
    }
  };

  const handleCreateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        litellm_config: formData.litellm_config ? JSON.parse(formData.litellm_config) : undefined
      };

      const response = await fetch('/api/v1/llm/providers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        console.log('Provider created successfully');
        setShowCreateModal(false);
        resetForm();
        fetchProviders();
      } else {
        const error = await response.json();
        console.error(error.detail || 'Failed to create provider');
      }
    } catch (error) {
      console.error('Error creating provider');
    }
  };

  const handleUpdateProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProvider) return;

    try {
      const payload = {
        ...formData,
        litellm_config: formData.litellm_config ? JSON.parse(formData.litellm_config) : undefined
      };

      const response = await fetch(`/api/v1/llm/providers/${editingProvider.provider_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        console.log('Provider updated successfully');
        setShowEditModal(false);
        setEditingProvider(null);
        resetForm();
        fetchProviders();
      } else {
        const error = await response.json();
        console.error(error.detail || 'Failed to update provider');
      }
    } catch (error) {
      console.error('Error updating provider');
    }
  };

  const handleDeleteProvider = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) return;

    try {
      const response = await fetch(`/api/v1/llm/providers/${providerId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        console.log('Provider deleted successfully');
        fetchProviders();
      } else {
        console.error('Failed to delete provider');
      }
    } catch (error) {
      console.error('Error deleting provider');
    }
  };

  const handleTestProvider = async (providerId: string) => {
    setTestingProvider(providerId);
    try {
      const response = await fetch(`/api/v1/llm/providers/${providerId}/test`, {
        method: 'POST',
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          console.log('Provider test successful!');
        } else {
          console.error(`Provider test failed: ${result.error}`);
        }
      } else {
        console.error('Failed to test provider');
      }
    } catch (error) {
      console.error('Error testing provider');
    } finally {
      setTestingProvider(null);
    }
  };

  const handleProviderTypeChange = (providerType: string) => {
    console.log('Provider type changed to:', providerType);
    const defaultUrl = getDefaultBaseUrl(providerType);
    
    setFormData(prev => ({ 
      ...prev, 
      provider_type: providerType, 
      model_name: '',
      base_url: defaultUrl,
      status: 'inactive'
    }));
    setAvailableModels([]);
    setConnectionResult(null);
    
    // Fetch models for the selected provider type
    if (providerType) {
      console.log('Fetching models for provider type:', providerType);
      fetchModels(providerType, formData.api_key, defaultUrl, formData.litellm_config ? JSON.parse(formData.litellm_config) : undefined);
    }
  };

  const handleApiKeyChange = (apiKey: string) => {
    setFormData(prev => ({ ...prev, api_key: apiKey }));
    
    // Re-fetch models if we have a provider type selected
    if (formData.provider_type && apiKey) {
      fetchModels(formData.provider_type, apiKey, formData.base_url, formData.litellm_config ? JSON.parse(formData.litellm_config) : undefined);
    }
  };

  const handleBaseUrlChange = (baseUrl: string) => {
    setFormData(prev => ({ ...prev, base_url: baseUrl }));
    
    // Re-fetch models if we have a provider type selected
    if (formData.provider_type && baseUrl) {
      fetchModels(formData.provider_type, formData.api_key, baseUrl, formData.litellm_config ? JSON.parse(formData.litellm_config) : undefined);
    }
  };

  const handleLiteLLMConfigChange = (config: string) => {
    setFormData(prev => ({ ...prev, litellm_config: config }));
    
    // Re-fetch models if we have a provider type selected
    if (formData.provider_type && config) {
      try {
        const parsedConfig = JSON.parse(config);
        fetchModels(formData.provider_type, formData.api_key, formData.base_url, parsedConfig);
      } catch (error) {
        console.error('Invalid JSON in LiteLLM config:', error);
      }
    }
  };

  const toggleProviderStatus = async (providerId: string, currentStatus: boolean) => {
    try {
      const response = await fetch(`/api/v1/llm/providers/${providerId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_enabled: !currentStatus
        }),
      });

      if (response.ok) {
        console.log('Provider status updated successfully');
        fetchProviders();
      } else {
        console.error('Failed to update provider status');
      }
    } catch (error) {
      console.error('Error updating provider status:', error);
    }
  };

  const setDefaultProvider = async (providerId: string) => {
    try {
      const response = await fetch(`/api/v1/llm/providers/${providerId}/set-default`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('Default provider set successfully');
        fetchProviders();
      } else {
        console.error('Failed to set default provider');
      }
    } catch (error) {
      console.error('Error setting default provider:', error);
    }
  };

  const openEditModal = (provider: LLMProvider) => {
    setEditingProvider(provider);
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      api_key: provider.api_key || '',
      base_url: provider.base_url || '',
      model_name: provider.model_name,
      litellm_config: provider.litellm_config ? JSON.stringify(provider.litellm_config, null, 2) : '',
      status: provider.status,
      is_enabled: provider.is_enabled || true,
      is_default: provider.is_default || false
    });
    setAvailableModels([]); // Clear models when opening edit modal
    if (provider.provider_type) {
      fetchModels(provider.provider_type, provider.api_key, provider.base_url, provider.litellm_config ? JSON.parse(JSON.stringify(provider.litellm_config)) : undefined);
    }
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      provider_type: '',
      api_key: '',
      base_url: '',
      model_name: '',
      litellm_config: '',
      status: 'inactive',
      is_enabled: true,
      is_default: false
    });
    setAvailableModels([]);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">LLM Providers</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Provider
        </button>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Configured Providers</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Enabled
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Default
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {providers.map((provider) => (
                <tr key={provider.provider_id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{provider.name}</div>
                    <div className="text-sm text-gray-500">{provider.provider_id}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900 capitalize">
                      {provider.provider_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">{provider.model_name}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(provider.status)}`}>
                      {provider.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => toggleProviderStatus(provider.provider_id, provider.is_enabled || false)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        provider.is_enabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                      title={provider.is_enabled ? 'Disable Provider' : 'Enable Provider'}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          provider.is_enabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => setDefaultProvider(provider.provider_id)}
                      disabled={provider.is_default}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        provider.is_default ? 'bg-green-600' : 'bg-gray-200'
                      } ${provider.is_default ? 'cursor-default' : 'cursor-pointer'}`}
                      title={provider.is_default ? 'Default Provider' : 'Set as Default'}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          provider.is_default ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleTestProvider(provider.provider_id)}
                        disabled={testingProvider === provider.provider_id}
                        className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                        title="Test Provider"
                      >
                        {testingProvider === provider.provider_id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={() => openEditModal(provider)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="Edit Provider"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteProvider(provider.provider_id)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete Provider"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {providers.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No LLM providers configured. Add your first provider to enable AI-powered summarization.
            </div>
          )}
          
          {/* Default Provider Info */}
          {providers.length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Default Provider</h3>
                  <p className="text-sm text-gray-500">
                    {providers.find(p => p.is_default) ? (
                      <>
                        Current default: <span className="font-medium">{providers.find(p => p.is_default)?.name}</span>
                        <span className="text-xs text-gray-400 ml-2">(Used automatically for MCP queries when no provider is specified)</span>
                      </>
                    ) : (
                      "No default provider set. MCP queries will return raw results without LLM analysis."
                    )}
                  </p>
                </div>
                {!providers.find(p => p.is_default) && (
                  <div className="text-sm text-amber-600 bg-amber-50 px-3 py-1 rounded-md">
                    ⚠️ Set a default provider to enable automatic LLM analysis
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || showEditModal) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">
                {showCreateModal ? 'Add LLM Provider' : 'Edit LLM Provider'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setShowEditModal(false);
                  setEditingProvider(null);
                  setFormData({
                    name: '',
                    provider_type: '',
                    api_key: '',
                    base_url: '',
                    model_name: '',
                    litellm_config: '',
                    status: 'inactive',
                    is_enabled: true,
                    is_default: false
                  });
                  setAvailableModels([]);
                  setConnectionResult(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={showCreateModal ? handleCreateProvider : handleUpdateProvider} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider Type *
                </label>
                <select
                  value={formData.provider_type}
                  onChange={(e) => handleProviderTypeChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Provider Type</option>
                  {providerTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={formData.api_key}
                    onChange={(e) => handleApiKeyChange(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter API key"
                  />
                  <button
                    type="button"
                    onClick={testConnection}
                    disabled={testingConnection || !formData.provider_type}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {testingConnection ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      'Test'
                    )}
                  </button>
                </div>
                {connectionResult && (
                  <div className={`mt-2 p-2 rounded text-sm ${connectionResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {connectionResult.message}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base URL
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => handleBaseUrlChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Base URL will be auto-filled"
                />
              </div>

              {formData.provider_type === 'litellm' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    LiteLLM Configuration (JSON)
                  </label>
                  <textarea
                    value={formData.litellm_config}
                    onChange={(e) => handleLiteLLMConfigChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder='{"provider": "openai", "custom_llm_provider": "..."}'
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model *
                </label>
                {formData.provider_type === 'custom' ? (
                  <input
                    type="text"
                    value={formData.model_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter custom model name"
                    required
                  />
                ) : availableModels.length > 0 ? (
                  <select
                    value={formData.model_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Select Model</option>
                    {availableModels.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={formData.model_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter model name manually"
                    required
                  />
                )}
                {formData.provider_type && formData.provider_type !== 'custom' && availableModels.length === 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    Enter API key and click Test to fetch available models, or enter model name manually.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <div className="flex items-center gap-2">
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {providerStatuses.map((status) => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-700">Enabled</label>
                    <input
                      type="checkbox"
                      checked={formData.is_enabled}
                      onChange={(e) => setFormData(prev => ({ ...prev, is_enabled: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-700">Default</label>
                    <input
                      type="checkbox"
                      checked={formData.is_default}
                      onChange={(e) => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-xs text-gray-500">(Only one provider can be default)</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setShowEditModal(false);
                    setEditingProvider(null);
                    setFormData({
                      name: '',
                      provider_type: '',
                      api_key: '',
                      base_url: '',
                      model_name: '',
                      litellm_config: '',
                      status: 'inactive',
                      is_enabled: true,
                      is_default: false
                    });
                    setAvailableModels([]);
                    setConnectionResult(null);
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {showCreateModal ? 'Create' : 'Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Test Modal */}
      {testingProvider && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Testing Provider</h3>
              <p>Testing provider: {testingProvider}</p>
              <button
                onClick={() => handleTestProvider(testingProvider)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Test Again
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LLMProviders;
