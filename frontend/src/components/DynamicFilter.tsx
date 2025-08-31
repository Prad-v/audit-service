import { useState } from 'react'
import { X, Plus, Filter } from 'lucide-react'

export interface DynamicFilterItem {
  id: string
  field: string
  operator: string
  value: string
  case_sensitive: boolean
}

interface DynamicFilterProps {
  filters: DynamicFilterItem[]
  onFiltersChange: (filters: DynamicFilterItem[]) => void
  availableFields: string[]
  supportedOperators: string[]
}

const OPERATOR_LABELS: Record<string, string> = {
  eq: 'Equals',
  ne: 'Not Equals',
  gt: 'Greater Than',
  gte: 'Greater Than or Equal',
  lt: 'Less Than',
  lte: 'Less Than or Equal',
  in: 'In List',
  not_in: 'Not In List',
  contains: 'Contains',
  not_contains: 'Not Contains',
  starts_with: 'Starts With',
  ends_with: 'Ends With',
  is_null: 'Is Null',
  is_not_null: 'Is Not Null',
  regex: 'Regex Match'
}

export function DynamicFilter({ filters, onFiltersChange, availableFields, supportedOperators }: DynamicFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const addFilter = () => {
    const newFilter: DynamicFilterItem = {
      id: Date.now().toString(),
      field: '',
      operator: 'eq',
      value: '',
      case_sensitive: true
    }
    onFiltersChange([...filters, newFilter])
  }

  const removeFilter = (id: string) => {
    onFiltersChange(filters.filter(f => f.id !== id))
  }

  const updateFilter = (id: string, field: keyof DynamicFilterItem, value: any) => {
    onFiltersChange(filters.map(f => 
      f.id === id ? { ...f, [field]: value } : f
    ))
  }

  const getFilterString = () => {
    if (filters.length === 0) return ''
    return JSON.stringify(filters.map(f => ({
      field: f.field,
      operator: f.operator,
      value: f.value,
      case_sensitive: f.case_sensitive
    })))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <h3 className="text-sm font-medium text-gray-700">Dynamic Filters</h3>
          {filters.length > 0 && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              {filters.length} active
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            {isExpanded ? 'Hide' : 'Show'} Advanced
          </button>
          <button
            onClick={addFilter}
            className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="h-3 w-3 mr-1" />
            Add Filter
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-3">
          {filters.length === 0 ? (
            <div className="text-center py-4 text-gray-500 text-sm">
              No dynamic filters added. Click "Add Filter" to get started.
            </div>
          ) : (
            filters.map((filter) => (
              <div key={filter.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Field
                    </label>
                    <select
                      value={filter.field}
                      onChange={(e) => updateFilter(filter.id, 'field', e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select field...</option>
                      {availableFields.map(field => (
                        <option key={field} value={field}>{field}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Operator
                    </label>
                    <select
                      value={filter.operator}
                      onChange={(e) => updateFilter(filter.id, 'operator', e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    >
                      {supportedOperators.map(op => (
                        <option key={op} value={op}>{OPERATOR_LABELS[op] || op}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Value
                    </label>
                    <input
                      type="text"
                      value={filter.value}
                      onChange={(e) => updateFilter(filter.id, 'value', e.target.value)}
                      placeholder="Enter value..."
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      disabled={filter.operator === 'is_null' || filter.operator === 'is_not_null'}
                    />
                  </div>
                  
                  <div className="flex items-end space-x-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filter.case_sensitive}
                        onChange={(e) => updateFilter(filter.id, 'case_sensitive', e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-xs text-gray-700">Case sensitive</span>
                    </label>
                    
                    <button
                      onClick={() => removeFilter(filter.id)}
                      className="p-1 text-red-600 hover:text-red-800"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Hidden input to store the JSON string for the API */}
      <input type="hidden" name="dynamic_filters" value={getFilterString()} />
    </div>
  )
}
