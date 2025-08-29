import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Play } from 'lucide-react';

interface LLMProvider {
  provider_id: string;
  name: string;
  provider_type: string;
  status: string;
  model_name: string;
  base_url?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

interface ProviderType {
  value: string;
  label: string;
  description: string;
}



const LLMProviders: React.FC = () => {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [providerTypes, setProviderTypes] = useState<ProviderType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    provider_type: '',
    api_key: '',
    base_url: '',
    model_name: '',
    litellm_config: ''
  });

  useEffect(() => {
    fetchProviders();
    fetchProviderTypes();
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
        setProviderTypes(data.provider_types || []);
      }
    } catch (error) {
      console.error('Error fetching provider types:', error);
    }
  };



  const handleCreateProvider = async () => {
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

  const handleUpdateProvider = async () => {
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

  const openEditModal = (provider: LLMProvider) => {
    setEditingProvider(provider);
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      api_key: '',
      base_url: provider.base_url || '',
      model_name: provider.model_name,
      litellm_config: ''
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      provider_type: '',
      api_key: '',
      base_url: '',
      model_name: '',
      litellm_config: ''
    });
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
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus className="h-5 w-5" />
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
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Add LLM Provider</h3>
              <form onSubmit={(e) => { e.preventDefault(); handleCreateProvider(); }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Provider Type</label>
                    <select
                      value={formData.provider_type}
                      onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    >
                      <option value="">Select provider type</option>
                      {providerTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">API Key</label>
                    <input
                      type="password"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Base URL</label>
                    <input
                      type="url"
                      value={formData.base_url}
                      onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="https://api.openai.com/v1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Model Name</label>
                    <input
                      type="text"
                      value={formData.model_name}
                      onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="gpt-4"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">LiteLLM Config (JSON)</label>
                    <textarea
                      value={formData.litellm_config}
                      onChange={(e) => setFormData({ ...formData, litellm_config: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      rows={3}
                      placeholder='{"temperature": 0.7, "max_tokens": 1000}'
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => { setShowCreateModal(false); resetForm(); }}
                    className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Create
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingProvider && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Edit LLM Provider</h3>
              <form onSubmit={(e) => { e.preventDefault(); handleUpdateProvider(); }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Provider Type</label>
                    <select
                      value={formData.provider_type}
                      onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    >
                      {providerTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">API Key</label>
                    <input
                      type="password"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      placeholder="Leave blank to keep current"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Base URL</label>
                    <input
                      type="url"
                      value={formData.base_url}
                      onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Model Name</label>
                    <input
                      type="text"
                      value={formData.model_name}
                      onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">LiteLLM Config (JSON)</label>
                    <textarea
                      value={formData.litellm_config}
                      onChange={(e) => setFormData({ ...formData, litellm_config: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                      rows={3}
                      placeholder='{"temperature": 0.7, "max_tokens": 1000}'
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => { setShowEditModal(false); setEditingProvider(null); resetForm(); }}
                    className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Update
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LLMProviders;
