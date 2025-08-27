/**
 * Type definitions for the Audit Log plugin
 */

export enum EventType {
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  DATA_ACCESS = 'data_access',
  DATA_MODIFICATION = 'data_modification',
  SYSTEM_EVENT = 'system_event',
  USER_ACTION = 'user_action',
  API_CALL = 'api_call',
  ERROR = 'error',
}

export enum Severity {
  CRITICAL = 'critical',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
  DEBUG = 'debug',
}

export interface AuditLogEvent {
  id: string;
  tenant_id: string;
  user_id?: string;
  event_type: EventType;
  resource_type: string;
  resource_id?: string;
  action: string;
  severity: Severity;
  description: string;
  metadata?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  correlation_id?: string;
  timestamp: string;
  created_at: string;
}

export interface AuditLogQuery {
  start_date?: string;
  end_date?: string;
  event_types?: EventType[];
  resource_types?: string[];
  resource_ids?: string[];
  actions?: string[];
  severities?: Severity[];
  user_ids?: string[];
  ip_addresses?: string[];
  session_ids?: string[];
  correlation_ids?: string[];
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedAuditLogs {
  items: AuditLogEvent[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AuditLogSummary {
  total_count: number;
  event_types: Record<string, number>;
  severities: Record<string, number>;
  resource_types: Record<string, number>;
  date_range: {
    start?: string;
    end?: string;
  };
}

export interface AuditLogExport {
  data: any[];
  format: string;
  count: number;
  generated_at: string;
}

export interface FilterOption {
  name: string;
  value: string;
  count?: number;
}

export interface DateRangeFilter {
  name: string;
  startDate: string;
  endDate?: string;
}

export interface AuditLogConfig {
  apiUrl: string;
  refreshInterval: number;
  pageSize: number;
  maxExportSize: number;
  enableRealTimeUpdates: boolean;
  defaultFilters: DateRangeFilter[];
  eventTypeColors: Record<string, string>;
  severityColors: Record<string, string>;
}

export interface AuditLogApiClient {
  getEvents(query: AuditLogQuery, page: number, size: number): Promise<PaginatedAuditLogs>;
  getEvent(id: string): Promise<AuditLogEvent>;
  getSummary(query: AuditLogQuery): Promise<AuditLogSummary>;
  exportEvents(query: AuditLogQuery, format: string): Promise<AuditLogExport>;
}