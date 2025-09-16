import React, { useState } from 'react'
import { X } from 'lucide-react'

interface TestConfigurationProps {
  test: any
  onUpdate: (updates: any) => void
  onClose: () => void
}

export function TestConfiguration({ test, onUpdate, onClose }: TestConfigurationProps) {
  const [formData, setFormData] = useState({
    name: test.name || '',
    description: test.description || '',
    enabled: test.enabled !== false,
    tags: test.tags ? test.tags.join(', ') : ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const updates = {
      name: formData.name,
      description: formData.description,
      enabled: formData.enabled,
      tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
    }
    
    onUpdate(updates)
    onClose()
  }

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Test Name *
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => handleChange('name', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter test name"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          placeholder="Describe what this test does"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tags
        </label>
        <input
          type="text"
          value={formData.tags}
          onChange={(e) => handleChange('tags', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="tag1, tag2, tag3"
        />
        <p className="text-xs text-gray-500 mt-1">
          Separate tags with commas
        </p>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="enabled"
          checked={formData.enabled}
          onChange={(e) => handleChange('enabled', e.target.checked)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="enabled" className="ml-2 block text-sm text-gray-700">
          Enable this test
        </label>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Save Configuration
        </button>
      </div>
    </form>
  )
}
