import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Filter, Database, X, Plus as PlusIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlertCondition {
  field: string
  operator: string
  value: string | number | boolean | (string | number)[]
  case_sensitive: boolean
}

interface AlertRule {
  rule_id: string
  name: string
  description?: string
  rule_type: string
  field?: string
  operator?: string
  value?: string | number | boolean
  case_sensitive?: boolean
  conditions?: AlertCondition[]
  group_operator?: string
  enabled: boolean
  created_by: string
  created_at: string
  updated_at: string
}

interface AlertRuleCreate {
  name: string
  description?: string
  rule_type: 'simple' | 'compound'
  field?: string
  operator?: string
  value?: string | number | boolean
  case_sensitive?: boolean
  conditions?: AlertCondition[]
  group_operator?: 'AND' | 'OR'
  enabled: boolean
}

export function AlertRules() {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [formData, setFormData] = useState<AlertRuleCreate>({
    name: '',
    description: '',
    rule_type: 'simple',
    field: '',
    operator: 'eq',
    value: '',
    case_sensitive: true,
    conditions: [],
    group_operator: 'AND',
    enabled: true
  })

  const operators = [
    { value: 'eq', label: 'Equals' },
    { value: 'ne', label: 'Not Equals' },
    { value: 'gt', label: 'Greater Than' },
    { value: 'lt', label: 'Less Than' },
    { value: 'gte', label: 'Greater Than or Equal' },
    { value: 'lte', label: 'Less Than or Equal' },
    { value: 'in', label: 'In List' },
    { value: 'not_in', label: 'Not In List' },
    { value: 'contains', label: 'Contains' },
    { value: 'regex', label: 'Regex Match' }
  ]

  const commonFields = [
    'event_type',
    'user_id',
    'status',
    'ip_address',
    'resource_id',
    'action',
    'timestamp',
    'severity',
    'category',
    'source'
  ]

  const addCondition = () => {
    const newCondition: AlertCondition = {
      field: '',
      operator: 'eq',
      value: '',
      case_sensitive: true
    }
    setFormData({
      ...formData,
      conditions: [...(formData.conditions || []), newCondition]
    })
  }

  const removeCondition = (index: number) => {
    const newConditions = formData.conditions?.filter((_, i) => i !== index) || []
    setFormData({
      ...formData,
      conditions: newConditions
    })
  }

  const updateCondition = (index: number, field: keyof AlertCondition, value: any) => {
    const newConditions = [...(formData.conditions || [])]
    newConditions[index] = { ...newConditions[index], [field]: value }
    setFormData({
      ...formData,
      conditions: newConditions
    })
  }

  useEffect(() => {
    fetchRules()
  }, [])

  const fetchRules = async () => {
    try {
      const response = await fetch('/api/v1/alerts/rules', {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setRules(data.rules || [])
      }
    } catch (error) {
      console.error('Failed to fetch rules:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateRule = async () => {
    try {
      let response

      if (formData.rule_type === 'simple') {
        // For simple rules, use the main endpoint
        const requestData = {
          name: formData.name,
          description: formData.description,
          rule_type: formData.rule_type,
          field: formData.field,
          operator: formData.operator,
          value: formData.value,
          case_sensitive: formData.case_sensitive,
          enabled: formData.enabled
        }

        response = await fetch('/api/v1/alerts/rules', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          },
          body: JSON.stringify(requestData)
        })
      } else {
        // For compound rules, use the compound endpoint
        const requestData = {
          name: formData.name,
          description: formData.description,
          conditions: formData.conditions,
          group_operator: formData.group_operator,
          enabled: formData.enabled
        }

        response = await fetch('/api/v1/alerts/rules/compound', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          },
          body: JSON.stringify(requestData)
        })
      }

      if (response.ok) {
        setShowCreateModal(false)
        resetFormData()
        fetchRules()
      } else {
        const error = await response.text()
        console.error('Failed to create rule:', error)
      }
    } catch (error) {
      console.error('Failed to create rule:', error)
    }
  }

  const handleUpdateRule = async () => {
    if (!editingRule) return
    
    try {
      const response = await fetch(`/api/v1/alerts/rules/${editingRule.rule_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify(formData)
      })
      if (response.ok) {
        setShowCreateModal(false)
        setEditingRule(null)
        resetFormData()
        fetchRules()
      }
    } catch (error) {
      console.error('Failed to update rule:', error)
    }
  }

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return
    
    try {
      const response = await fetch(`/api/v1/alerts/rules/${ruleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        fetchRules()
      }
    } catch (error) {
      console.error('Failed to delete rule:', error)
    }
  }

  const handleEditRule = (rule: AlertRule) => {
    setEditingRule(rule)
    setFormData({
      name: rule.name,
      description: rule.description || '',
      rule_type: (rule.rule_type as 'simple' | 'compound') || 'simple',
      field: rule.field || '',
      operator: rule.operator || 'eq',
      value: rule.value || '',
      case_sensitive: rule.case_sensitive || true,
      conditions: rule.conditions || [],
      group_operator: (rule.group_operator as 'AND' | 'OR') || 'AND',
      enabled: rule.enabled
    })
    setShowCreateModal(true)
  }

  const resetFormData = () => {
    setFormData({
      name: '',
      description: '',
      rule_type: 'simple',
      field: '',
      operator: 'eq',
      value: '',
      case_sensitive: true,
      conditions: [],
      group_operator: 'AND',
      enabled: true
    })
  }

  const getOperatorLabel = (operator: string) => {
    const op = operators.find(o => o.value === operator)
    return op ? op.label : operator
  }

  const formatValue = (value: any) => {
    if (typeof value === 'boolean') {
      return value ? 'true' : 'false'
    }
    if (Array.isArray(value)) {
      return value.join(', ')
    }
    return String(value)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alert Rules</h1>
          <p className="text-gray-600">Manage reusable alert rules and conditions</p>
        </div>
        <button
          onClick={() => {
            setEditingRule(null)
            resetFormData()
            setShowCreateModal(true)
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Rule
        </button>
      </div>

      {/* Rules List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {rules.map((rule) => (
            <li key={rule.rule_id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Filter className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-4">
                    <div className="flex items-center">
                      <h3 className="text-sm font-medium text-gray-900">{rule.name}</h3>
                      <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded-full', rule.enabled ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100')}>
                        {rule.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    {rule.description && (
                      <p className="text-sm text-gray-500 mt-1">{rule.description}</p>
                    )}
                    <div className="flex items-center mt-2 text-xs text-gray-500">
                      <Database className="w-3 h-3 mr-1" />
                      {rule.rule_type === 'simple' ? (
                        <>
                          {rule.field} {getOperatorLabel(rule.operator || '')} {formatValue(rule.value)}
                          {rule.case_sensitive && (
                            <span className="ml-2 text-blue-600">Case Sensitive</span>
                          )}
                        </>
                      ) : (
                        <>
                          <span className="text-purple-600 font-medium">Compound Rule</span>
                          <span className="ml-2">({rule.group_operator})</span>
                          <span className="ml-2">{rule.conditions?.length || 0} conditions</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditRule(rule)}
                    className="text-gray-400 hover:text-gray-600"
                    title="Edit Rule"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteRule(rule.rule_id)}
                    className="text-gray-400 hover:text-red-600"
                    title="Delete Rule"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {rules.length === 0 && (
          <div className="text-center py-12">
            <Filter className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No rules</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new alert rule.</p>
            <div className="mt-6">
              <button
                onClick={() => {
                  setEditingRule(null)
                  resetFormData()
                  setShowCreateModal(true)
                }}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Rule
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-[800px] shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingRule ? 'Edit Alert Rule' : 'Create Alert Rule'}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Rule Type</label>
                  <select
                    value={formData.rule_type}
                    onChange={(e) => setFormData({ ...formData, rule_type: e.target.value as 'simple' | 'compound' })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="simple">Simple Rule (Single Condition)</option>
                    <option value="compound">Compound Rule (Multiple Conditions)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Field</label>
                  <select
                    value={formData.field}
                    onChange={(e) => setFormData({ ...formData, field: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Select a field</option>
                    {commonFields.map(field => (
                      <option key={field} value={field}>{field}</option>
                    ))}
                    <option value="custom">Custom Field</option>
                  </select>
                  {formData.field === 'custom' && (
                    <input
                      type="text"
                      placeholder="Enter custom field name"
                      onChange={(e) => setFormData({ ...formData, field: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    />
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Operator</label>
                  <select
                    value={formData.operator}
                    onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    {operators.map(op => (
                      <option key={op.value} value={op.value}>{op.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Value</label>
                  <input
                    type="text"
                    value={String(formData.value)}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    placeholder="Enter value to compare against"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.case_sensitive}
                    onChange={(e) => setFormData({ ...formData, case_sensitive: e.target.checked })}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">Case Sensitive</label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">Enabled</label>
                </div>

                {/* Compound Rule Fields */}
                {formData.rule_type === 'compound' && (
                  <>
                    <div className="border-t pt-4">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-sm font-medium text-gray-900">Conditions</h4>
                        <button
                          type="button"
                          onClick={addCondition}
                          className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200"
                        >
                          <PlusIcon className="w-3 h-3 mr-1" />
                          Add Condition
                        </button>
                      </div>
                      
                      <div className="space-y-3">
                        {formData.conditions?.map((condition, index) => (
                          <div key={index} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-gray-700">Condition {index + 1}</span>
                              <button
                                type="button"
                                onClick={() => removeCondition(index)}
                                className="text-red-500 hover:text-red-700"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="block text-xs font-medium text-gray-700">Field</label>
                                <select
                                  value={condition.field}
                                  onChange={(e) => updateCondition(index, 'field', e.target.value)}
                                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-xs"
                                >
                                  <option value="">Select a field</option>
                                  {commonFields.map(field => (
                                    <option key={field} value={field}>{field}</option>
                                  ))}
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-700">Operator</label>
                                <select
                                  value={condition.operator}
                                  onChange={(e) => updateCondition(index, 'operator', e.target.value)}
                                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-xs"
                                >
                                  {operators.map(op => (
                                    <option key={op.value} value={op.value}>{op.label}</option>
                                  ))}
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-700">Value</label>
                                <input
                                  type="text"
                                  value={String(condition.value)}
                                  onChange={(e) => updateCondition(index, 'value', e.target.value)}
                                  placeholder="Enter value"
                                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-xs"
                                />
                              </div>
                              <div className="flex items-center">
                                <input
                                  type="checkbox"
                                  checked={condition.case_sensitive}
                                  onChange={(e) => updateCondition(index, 'case_sensitive', e.target.checked)}
                                  className="h-3 w-3 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                />
                                <label className="ml-1 block text-xs text-gray-900">Case Sensitive</label>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      {formData.conditions && formData.conditions.length > 1 && (
                        <div className="mt-4">
                          <label className="block text-sm font-medium text-gray-700">Group Operator</label>
                          <select
                            value={formData.group_operator}
                            onChange={(e) => setFormData({ ...formData, group_operator: e.target.value as 'AND' | 'OR' })}
                            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                          >
                            <option value="AND">AND (All conditions must match)</option>
                            <option value="OR">OR (Any condition can match)</option>
                          </select>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingRule(null)
                    resetFormData()
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={editingRule ? handleUpdateRule : handleCreateRule}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                >
                  {editingRule ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
