import React, { useState, useEffect } from 'react';
import { AlertTriangle, Activity, WifiOff, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SummaryData {
  incidents: {
    active: number;
    resolved: number;
    total: number;
    trend: 'up' | 'down' | 'stable';
  };
  outages: {
    active: number;
    resolved: number;
    total: number;
    trend: 'up' | 'down' | 'stable';
  };
  alerts: {
    active: number;
    resolved: number;
    total: number;
    trend: 'up' | 'down' | 'stable';
  };
}

interface ExecutiveSummaryProps {
  showHistorical: boolean;
  timeRange: number; // hours
}

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ showHistorical, timeRange }) => {
  const [summaryData, setSummaryData] = useState<SummaryData>({
    incidents: { active: 0, resolved: 0, total: 0, trend: 'stable' },
    outages: { active: 0, resolved: 0, total: 0, trend: 'stable' },
    alerts: { active: 0, resolved: 0, total: 0, trend: 'stable' }
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSummaryData();
  }, [showHistorical, timeRange]);

  const fetchSummaryData = async () => {
    setIsLoading(true);
    try {
      // Fetch incidents data
      const incidentsResponse = await fetch(`/api/v1/incidents/?${showHistorical ? `start_time=${new Date(Date.now() - timeRange * 60 * 60 * 1000).toISOString()}&` : ''}limit=100`);
      const incidentsData = incidentsResponse.ok ? await incidentsResponse.json() : { incidents: [] };

      // Fetch outages data
      const outagesResponse = await fetch(`/api/v1/outages/${showHistorical ? 'history' : 'active'}`);
      const outagesData = outagesResponse.ok ? await outagesResponse.json() : { outages: [] };

      // Fetch alerts data
      const alertsResponse = await fetch(`/api/v1/alerts/alerts?${showHistorical ? `start_time=${new Date(Date.now() - timeRange * 60 * 60 * 1000).toISOString()}&` : ''}status=active`);
      const alertsData = alertsResponse.ok ? await alertsResponse.json() : { alerts: [] };

      // Process data
      const incidents = incidentsData.incidents || [];
      const outages = outagesData.outages || [];
      const alerts = alertsData.alerts || [];

      setSummaryData({
        incidents: {
          active: incidents.filter((i: any) => i.status === 'active' || i.status === 'investigating').length,
          resolved: incidents.filter((i: any) => i.status === 'resolved').length,
          total: incidents.length,
          trend: 'stable' // TODO: Calculate actual trend
        },
        outages: {
          active: outages.filter((o: any) => o.status === 'active').length,
          resolved: outages.filter((o: any) => o.status === 'resolved').length,
          total: outages.length,
          trend: 'stable' // TODO: Calculate actual trend
        },
        alerts: {
          active: alerts.filter((a: any) => a.status === 'active').length,
          resolved: alerts.filter((a: any) => a.status === 'resolved').length,
          total: alerts.length,
          trend: 'stable' // TODO: Calculate actual trend
        }
      });
    } catch (error) {
      console.error('Error fetching summary data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-green-500" />;
      default: return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return 'text-red-600';
      case 'down': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Executive Summary {showHistorical && `(${timeRange}h)`}
        </h2>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Incidents Summary */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Incidents</h3>
            </div>
            {getTrendIcon(summaryData.incidents.trend)}
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Active</span>
              <span className="text-2xl font-bold text-red-600">{summaryData.incidents.active}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Resolved</span>
              <span className="text-lg font-semibold text-green-600">{summaryData.incidents.resolved}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-gray-100">
              <span className="text-sm text-gray-600">Total</span>
              <span className="text-lg font-semibold text-gray-900">{summaryData.incidents.total}</span>
            </div>
          </div>
        </div>

        {/* Outages Summary */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <WifiOff className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Outages</h3>
            </div>
            {getTrendIcon(summaryData.outages.trend)}
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Active</span>
              <span className="text-2xl font-bold text-red-600">{summaryData.outages.active}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Resolved</span>
              <span className="text-lg font-semibold text-green-600">{summaryData.outages.resolved}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-gray-100">
              <span className="text-sm text-gray-600">Total</span>
              <span className="text-lg font-semibold text-gray-900">{summaryData.outages.total}</span>
            </div>
          </div>
        </div>

        {/* Alerts Summary */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Alerts</h3>
            </div>
            {getTrendIcon(summaryData.alerts.trend)}
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Active</span>
              <span className="text-2xl font-bold text-red-600">{summaryData.alerts.active}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Resolved</span>
              <span className="text-lg font-semibold text-green-600">{summaryData.alerts.resolved}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-gray-100">
              <span className="text-sm text-gray-600">Total</span>
              <span className="text-lg font-semibold text-gray-900">{summaryData.alerts.total}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
