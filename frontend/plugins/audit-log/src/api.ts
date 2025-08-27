import { 
  AuditLogApiClient, 
  AuditLogEvent, 
  AuditLogQuery, 
  PaginatedAuditLogs, 
  AuditLogSummary, 
  AuditLogExport 
} from './types';

export class AuditLogApi implements AuditLogApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
  }

  private async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const token = localStorage.getItem('backstage-token');
    
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  }

  private buildQueryString(query: AuditLogQuery, page?: number, size?: number): string {
    const params = new URLSearchParams();

    if (page !== undefined) params.append('page', page.toString());
    if (size !== undefined) params.append('size', size.toString());
    if (query.start_date) params.append('start_date', query.start_date);
    if (query.end_date) params.append('end_date', query.end_date);
    if (query.search) params.append('search', query.search);
    if (query.sort_by) params.append('sort_by', query.sort_by);
    if (query.sort_order) params.append('sort_order', query.sort_order);

    // Handle array parameters
    query.event_types?.forEach(type => params.append('event_types', type));
    query.resource_types?.forEach(type => params.append('resource_types', type));
    query.resource_ids?.forEach(id => params.append('resource_ids', id));
    query.actions?.forEach(action => params.append('actions', action));
    query.severities?.forEach(severity => params.append('severities', severity));
    query.user_ids?.forEach(id => params.append('user_ids', id));
    query.ip_addresses?.forEach(ip => params.append('ip_addresses', ip));
    query.session_ids?.forEach(id => params.append('session_ids', id));
    query.correlation_ids?.forEach(id => params.append('correlation_ids', id));

    return params.toString();
  }

  async getEvents(query: AuditLogQuery, page: number = 1, size: number = 50): Promise<PaginatedAuditLogs> {
    const queryString = this.buildQueryString(query, page, size);
    const url = `${this.baseUrl}/events?${queryString}`;
    
    const response = await this.fetchWithAuth(url);
    return response.json();
  }

  async getEvent(id: string): Promise<AuditLogEvent> {
    const url = `${this.baseUrl}/events/${id}`;
    
    const response = await this.fetchWithAuth(url);
    return response.json();
  }

  async getSummary(query: AuditLogQuery): Promise<AuditLogSummary> {
    const queryString = this.buildQueryString(query);
    const url = `${this.baseUrl}/summary?${queryString}`;
    
    const response = await this.fetchWithAuth(url);
    return response.json();
  }

  async exportEvents(query: AuditLogQuery, format: string = 'json'): Promise<AuditLogExport> {
    const queryString = this.buildQueryString(query);
    const url = `${this.baseUrl}/events/export?format=${format}&${queryString}`;
    
    const response = await this.fetchWithAuth(url);
    return response.json();
  }

  async createEvent(event: Partial<AuditLogEvent>): Promise<AuditLogEvent> {
    const url = `${this.baseUrl}/events`;
    
    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      body: JSON.stringify(event),
    });
    
    return response.json();
  }

  async createEventsBatch(events: Partial<AuditLogEvent>[]): Promise<AuditLogEvent[]> {
    const url = `${this.baseUrl}/events/batch`;
    
    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      body: JSON.stringify({ audit_logs: events }),
    });
    
    return response.json();
  }

  async downloadExport(query: AuditLogQuery, format: string = 'json'): Promise<Blob> {
    const queryString = this.buildQueryString(query);
    const url = `${this.baseUrl}/events/export?format=${format}&${queryString}`;
    
    const response = await this.fetchWithAuth(url);
    
    if (format === 'csv') {
      const exportData = await response.json() as AuditLogExport;
      const csvContent = this.convertToCSV(exportData.data);
      return new Blob([csvContent], { type: 'text/csv' });
    } else {
      const exportData = await response.json() as AuditLogExport;
      const jsonContent = JSON.stringify(exportData.data, null, 2);
      return new Blob([jsonContent], { type: 'application/json' });
    }
  }

  private convertToCSV(data: any[]): string {
    if (data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const csvRows = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header];
          if (value === null || value === undefined) return '';
          if (typeof value === 'object') return JSON.stringify(value);
          if (typeof value === 'string' && value.includes(',')) return `"${value}"`;
          return value;
        }).join(',')
      )
    ];

    return csvRows.join('\n');
  }

  // Utility method to get available filter options
  async getFilterOptions(): Promise<{
    eventTypes: string[];
    resourceTypes: string[];
    severities: string[];
  }> {
    // This could be enhanced to fetch dynamic options from the API
    return {
      eventTypes: [
        'authentication',
        'authorization', 
        'data_access',
        'data_modification',
        'system_event',
        'user_action',
        'api_call',
        'error'
      ],
      resourceTypes: [
        'user',
        'role',
        'permission',
        'audit_log',
        'api_key',
        'tenant',
        'system'
      ],
      severities: [
        'critical',
        'error',
        'warning',
        'info',
        'debug'
      ]
    };
  }
}

// Factory function to create API client
export const createAuditLogApi = (baseUrl: string): AuditLogApi => {
  return new AuditLogApi(baseUrl);
};