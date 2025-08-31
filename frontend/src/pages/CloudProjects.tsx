import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, TestTube, Cloud } from 'lucide-react'
import { cloudApi, CloudProject } from '@/lib/api'

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

const CLOUD_PROVIDERS = [
  { value: 'gcp', label: 'Google Cloud Platform', icon: '☁️' },
  { value: 'aws', label: 'Amazon Web Services', icon: '☁️' },
  { value: 'azure', label: 'Microsoft Azure', icon: '☁️' },
  { value: 'oci', label: 'Oracle Cloud Infrastructure', icon: '☁️' },
]

export function CloudProjects() {
  const [projects, setProjects] = useState<CloudProject[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<CloudProject | null>(null)
  const [testingConnection, setTestingConnection] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    cloud_provider: '',
    project_identifier: '',
    config: {} as Record<string, any>,
    enabled: true,
    auto_subscribe: true,
  })

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      setLoading(true)
      const response = await cloudApi.getCloudProjects()
      setProjects(response.projects || [])
    } catch (error) {
      console.error('Failed to load projects:', error)
      showToast('Failed to load cloud projects', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async () => {
    try {
      await cloudApi.createCloudProject(formData)
      showToast('Cloud project created successfully')
      setIsCreateDialogOpen(false)
      resetForm()
      loadProjects()
    } catch (error) {
      console.error('Failed to create project:', error)
      showToast('Failed to create cloud project', 'error')
    }
  }

  const handleUpdateProject = async () => {
    if (!selectedProject) return

    try {
      await cloudApi.updateCloudProject(selectedProject.project_id, formData)
      showToast('Cloud project updated successfully')
      setIsEditDialogOpen(false)
      resetForm()
      loadProjects()
    } catch (error) {
      console.error('Failed to update project:', error)
      showToast('Failed to update cloud project', 'error')
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return

    try {
      await cloudApi.deleteCloudProject(projectId)
      showToast('Cloud project deleted successfully')
      loadProjects()
    } catch (error) {
      console.error('Failed to delete project:', error)
      showToast('Failed to delete cloud project', 'error')
    }
  }

  const handleTestConnection = async (projectId: string) => {
    try {
      setTestingConnection(projectId)
      const result = await cloudApi.testCloudProjectConnection(projectId)
      if (result.success) {
        showToast('Connection test successful')
      } else {
        showToast(`Connection test failed: ${result.message}`, 'error')
      }
    } catch (error) {
      console.error('Connection test failed:', error)
      showToast('Connection test failed', 'error')
    } finally {
      setTestingConnection(null)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      cloud_provider: '',
      project_identifier: '',
      config: {},
      enabled: true,
      auto_subscribe: true,
    })
    setSelectedProject(null)
  }

  const openEditDialog = (project: CloudProject) => {
    setSelectedProject(project)
    setFormData({
      name: project.name,
      description: project.description || '',
      cloud_provider: project.cloud_provider,
      project_identifier: project.project_identifier,
      config: project.config,
      enabled: project.enabled,
      auto_subscribe: project.auto_subscribe,
    })
    setIsEditDialogOpen(true)
  }

  const getProviderConfigFields = (provider: string) => {
    switch (provider) {
      case 'gcp':
        return [
          { key: 'project_id', label: 'Project ID', type: 'text', required: true },
          { key: 'service_account_key', label: 'Service Account Key (JSON)', type: 'textarea', required: true },
        ]
      case 'aws':
        return [
          { key: 'access_key_id', label: 'Access Key ID', type: 'text', required: true },
          { key: 'secret_access_key', label: 'Secret Access Key', type: 'password', required: true },
          { key: 'region', label: 'Region', type: 'text', required: true },
        ]
      case 'azure':
        return [
          { key: 'subscription_id', label: 'Subscription ID', type: 'text', required: true },
          { key: 'tenant_id', label: 'Tenant ID', type: 'text', required: true },
          { key: 'client_id', label: 'Client ID', type: 'text', required: true },
          { key: 'client_secret', label: 'Client Secret', type: 'password', required: true },
        ]
      case 'oci':
        return [
          { key: 'tenancy_id', label: 'Tenancy ID', type: 'text', required: true },
          { key: 'user_id', label: 'User ID', type: 'text', required: true },
          { key: 'fingerprint', label: 'Fingerprint', type: 'text', required: true },
          { key: 'private_key', label: 'Private Key', type: 'textarea', required: true },
          { key: 'region', label: 'Region', type: 'text', required: true },
        ]
      default:
        return []
    }
  }

  const updateConfig = (key: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      config: {
        ...prev.config,
        [key]: value,
      },
    }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading cloud projects...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Cloud Projects</h1>
          <p className="text-gray-600 mt-2">
            Manage cloud provider projects for event monitoring
          </p>
        </div>
        <button
          onClick={() => setIsCreateDialogOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Cloud Project
        </button>
      </div>

      {/* Create Dialog */}
      {isCreateDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">Add Cloud Project</h2>
              <p className="text-gray-600">
                Register a new cloud provider project for event monitoring
              </p>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="My GCP Project"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="cloud_provider" className="block text-sm font-medium text-gray-700 mb-1">Cloud Provider</label>
                  <select
                    id="cloud_provider"
                    value={formData.cloud_provider}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormData(prev => ({ ...prev, cloud_provider: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select provider</option>
                    {CLOUD_PROVIDERS.map(provider => (
                      <option key={provider.value} value={provider.value}>
                        {provider.icon} {provider.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Optional description"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label htmlFor="project_identifier" className="block text-sm font-medium text-gray-700 mb-1">Project Identifier</label>
                <input
                  id="project_identifier"
                  type="text"
                  value={formData.project_identifier}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, project_identifier: e.target.value }))}
                  placeholder="project-id-123"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              {formData.cloud_provider && (
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-700">Provider Configuration</label>
                  {getProviderConfigFields(formData.cloud_provider).map(field => (
                    <div key={field.key}>
                      <label htmlFor={field.key} className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                      {field.type === 'textarea' ? (
                        <textarea
                          id={field.key}
                          value={formData.config[field.key] || ''}
                          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateConfig(field.key, e.target.value)}
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={4}
                        />
                      ) : (
                        <input
                          id={field.key}
                          type={field.type}
                          value={formData.config[field.key] || ''}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateConfig(field.key, e.target.value)}
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className="flex space-x-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={formData.enabled}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="enabled" className="text-sm text-gray-700">Enabled</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="auto_subscribe"
                    checked={formData.auto_subscribe}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, auto_subscribe: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="auto_subscribe" className="text-sm text-gray-700">Auto Subscribe</label>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setIsCreateDialogOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProject}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Projects List */}
      {projects.length === 0 ? (
        <div className="card">
          <div className="flex flex-col items-center justify-center py-12">
            <Cloud className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No cloud projects</h3>
            <p className="text-gray-600 text-center mb-4">
              Get started by adding your first cloud provider project
            </p>
            <button
              onClick={() => setIsCreateDialogOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Cloud Project
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <div key={project.project_id} className="card">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{project.name}</h3>
                    <p className="text-gray-600">{project.description}</p>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                      onClick={() => handleTestConnection(project.project_id)}
                      disabled={testingConnection === project.project_id}
                    >
                      <TestTube className="w-4 h-4" />
                    </button>
                    <button
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                      onClick={() => openEditDialog(project)}
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                      onClick={() => handleDeleteProject(project.project_id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Provider:</span>
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                      {CLOUD_PROVIDERS.find(p => p.value === project.cloud_provider)?.label || project.cloud_provider}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Project ID:</span>
                    <span className="text-sm font-mono">{project.project_identifier}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Status:</span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      project.enabled 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {project.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Auto Subscribe:</span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      project.auto_subscribe 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {project.auto_subscribe ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      {isEditDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">Edit Cloud Project</h2>
              <p className="text-gray-600">
                Update cloud provider project configuration
              </p>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                  <input
                    id="edit-name"
                    type="text"
                    value={formData.name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="edit-description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    id="edit-description"
                    type="text"
                    value={formData.description}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              {formData.cloud_provider && (
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-700">Provider Configuration</label>
                  {getProviderConfigFields(formData.cloud_provider).map(field => (
                    <div key={field.key}>
                      <label htmlFor={`edit-${field.key}`} className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                      {field.type === 'textarea' ? (
                        <textarea
                          id={`edit-${field.key}`}
                          value={formData.config[field.key] || ''}
                          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateConfig(field.key, e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={4}
                        />
                      ) : (
                        <input
                          id={`edit-${field.key}`}
                          type={field.type}
                          value={formData.config[field.key] || ''}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateConfig(field.key, e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className="flex space-x-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="edit-enabled"
                    checked={formData.enabled}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="edit-enabled" className="text-sm text-gray-700">Enabled</label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="edit-auto_subscribe"
                    checked={formData.auto_subscribe}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({ ...prev, auto_subscribe: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="edit-auto_subscribe" className="text-sm text-gray-700">Auto Subscribe</label>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setIsEditDialogOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateProject}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Update Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
