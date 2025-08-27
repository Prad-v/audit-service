import React, { useState, useEffect, useCallback } from 'react';
import {
  Content,
  Header,
  Page,
  Progress,
  ResponseErrorPanel,
} from '@backstage/core-components';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
} from '@material-ui/core';
import {
  Refresh as RefreshIcon,
  GetApp as ExportIcon,
  Visibility as ViewIcon,
} from '@material-ui/icons';
import { makeStyles } from '@material-ui/core/styles';

import { AuditLogApi, createAuditLogApi } from '../../api';
import { 
  AuditLogEvent, 
  AuditLogQuery, 
  PaginatedAuditLogs, 
  AuditLogSummary,
  EventType,
  Severity 
} from '../../types';
import { AuditLogTable } from './AuditLogTable';
import { AuditLogFilters } from './AuditLogFilters';
import { AuditLogSummaryCards } from './AuditLogSummaryCards';
import { AuditLogEventDialog } from './AuditLogEventDialog';

const useStyles = makeStyles(theme => ({
  root: {
    height: '100%',
  },
  content: {
    padding: theme.spacing(2),
  },
  headerActions: {
    display: 'flex',
    gap: theme.spacing(1),
  },
  filtersCard: {
    marginBottom: theme.spacing(2),
  },
  summaryCards: {
    marginBottom: theme.spacing(2),
  },
  tableCard: {
    minHeight: 600,
  },
}));

export const AuditLogPage = () => {
  const classes = useStyles();
  const [api] = useState(() => createAuditLogApi('/audit-api/api/v1/audit'));
  
  // State management
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<PaginatedAuditLogs | null>(null);
  const [summary, setSummary] = useState<AuditLogSummary | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<AuditLogEvent | null>(null);
  const [eventDialogOpen, setEventDialogOpen] = useState(false);
  
  // Query state
  const [query, setQuery] = useState<AuditLogQuery>({
    sort_by: 'timestamp',
    sort_order: 'desc',
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [eventsData, summaryData] = await Promise.all([
        api.getEvents(query, page, pageSize),
        api.getSummary(query),
      ]);
      
      setEvents(eventsData);
      setSummary(summaryData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [api, query, page, pageSize]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleQueryChange = (newQuery: AuditLogQuery) => {
    setQuery(newQuery);
    setPage(1); // Reset to first page when query changes
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when page size changes
  };

  const handleEventClick = async (eventId: string) => {
    try {
      const event = await api.getEvent(eventId);
      setSelectedEvent(event);
      setEventDialogOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load event details');
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await api.downloadExport(query, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-logs-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export audit logs');
    }
  };

  const headerActions = (
    <Box className={classes.headerActions}>
      <Tooltip title="Refresh">
        <IconButton onClick={loadData} disabled={loading}>
          <RefreshIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Export as JSON">
        <IconButton onClick={() => handleExport('json')} disabled={loading}>
          <ExportIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Export as CSV">
        <IconButton onClick={() => handleExport('csv')} disabled={loading}>
          <ExportIcon />
        </IconButton>
      </Tooltip>
    </Box>
  );

  if (error) {
    return (
      <Page themeId="tool">
        <Header title="Audit Logs" />
        <Content>
          <ResponseErrorPanel error={new Error(error)} />
        </Content>
      </Page>
    );
  }

  return (
    <Page themeId="tool" className={classes.root}>
      <Header title="Audit Logs" subtitle="View and analyze system audit events">
        {headerActions}
      </Header>
      
      <Content className={classes.content}>
        <Grid container spacing={2}>
          {/* Filters */}
          <Grid item xs={12}>
            <Card className={classes.filtersCard}>
              <CardContent>
                <AuditLogFilters
                  query={query}
                  onQueryChange={handleQueryChange}
                  loading={loading}
                />
              </CardContent>
            </Card>
          </Grid>

          {/* Summary Cards */}
          {summary && (
            <Grid item xs={12} className={classes.summaryCards}>
              <AuditLogSummaryCards summary={summary} />
            </Grid>
          )}

          {/* Events Table */}
          <Grid item xs={12}>
            <Card className={classes.tableCard}>
              <CardContent>
                {loading && !events ? (
                  <Box display="flex" justifyContent="center" p={4}>
                    <Progress />
                  </Box>
                ) : events ? (
                  <AuditLogTable
                    events={events}
                    loading={loading}
                    onPageChange={handlePageChange}
                    onPageSizeChange={handlePageSizeChange}
                    onEventClick={handleEventClick}
                    onQueryChange={handleQueryChange}
                    currentQuery={query}
                  />
                ) : (
                  <Box display="flex" justifyContent="center" p={4}>
                    <Typography variant="body1" color="textSecondary">
                      No audit logs found
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Event Details Dialog */}
        <AuditLogEventDialog
          event={selectedEvent}
          open={eventDialogOpen}
          onClose={() => {
            setEventDialogOpen(false);
            setSelectedEvent(null);
          }}
        />
      </Content>
    </Page>
  );
};