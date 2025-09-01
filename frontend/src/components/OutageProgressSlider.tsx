import React from 'react';
import { 
  CheckCircle,
  XCircle,
  Clock,
  Wifi,
  Server,
  Database
} from 'lucide-react';

interface ProviderResult {
  status: 'success' | 'error' | 'pending';
  outages_found?: number;
  checked_at?: string;
  error?: string;
  details?: {
    rss_feed: string;
    api_url: string;
  };
}

interface OutageProgressSliderProps {
  isOpen: boolean;
  onClose: () => void;
  isChecking: boolean;
  progress: number;
  providerResults: Record<string, ProviderResult>;
  totalOutagesFound: number;
  currentProvider?: string;
}

const providerIcons = {
  gcp: Server,
  aws: Database,
  azure: Wifi,
  oci: Server
};

const providerColors = {
  gcp: 'bg-blue-100 text-blue-800',
  aws: 'bg-orange-100 text-orange-800',
  azure: 'bg-blue-100 text-blue-800',
  oci: 'bg-red-100 text-red-800'
};

export const OutageProgressSlider: React.FC<OutageProgressSliderProps> = ({
  isOpen,
  onClose,
  isChecking,
  progress,
  providerResults,
  totalOutagesFound,
  currentProvider
}) => {
  const providers = ['gcp', 'aws', 'azure', 'oci'];
  
  const getProviderStatus = (provider: string) => {
    if (!providerResults[provider]) {
      return isChecking && currentProvider === provider ? 'checking' : 'pending';
    }
    return providerResults[provider].status;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'checking':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return 'Completed';
      case 'error':
        return 'Failed';
      case 'checking':
        return 'Checking...';
      default:
        return 'Pending';
    }
  };

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 ${isOpen ? 'block' : 'hidden'}`}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Cloud Provider Outage Check</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            {isChecking && (
              <p className="text-sm text-gray-600">
                Currently checking: {currentProvider?.toUpperCase() || 'Initializing...'}
              </p>
            )}
          </div>

          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-4">Summary</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{totalOutagesFound}</div>
                <div className="text-sm text-gray-600">Total Outages Found</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {providers.filter(p => getProviderStatus(p) === 'success').length}
                </div>
                <div className="text-sm text-gray-600">Providers Checked</div>
              </div>
            </div>
          </div>

          {/* Provider Results */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Provider Results</h3>
            {providers.map((provider) => {
              const status = getProviderStatus(provider);
              const result = providerResults[provider];
              const Icon = providerIcons[provider as keyof typeof providerIcons];
              const colorClass = providerColors[provider as keyof typeof providerColors];

              return (
                <div key={provider} className={`border rounded-lg p-4 border-l-4 ${
                  status === 'success' ? 'border-l-green-500' :
                  status === 'error' ? 'border-l-red-500' :
                  status === 'checking' ? 'border-l-blue-500' :
                  'border-l-gray-300'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Icon className="w-6 h-6" />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-lg">
                            {provider.toUpperCase()}
                          </span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${colorClass}`}>
                            {getStatusText(status)}
                          </span>
                        </div>
                        {result && (
                          <div className="text-sm text-gray-600 mt-1">
                            {result.outages_found !== undefined && (
                              <span>{result.outages_found} outages found</span>
                            )}
                            {result.checked_at && (
                              <span className="ml-2">
                                • Checked at {new Date(result.checked_at).toLocaleTimeString()}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    {getStatusIcon(status)}
                  </div>

                  {/* Error Details */}
                  {status === 'error' && result?.error && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                      <div className="text-sm text-red-800">
                        {result.error}
                      </div>
                    </div>
                  )}

                  {/* Provider Details */}
                  {result?.details && (
                    <div className="mt-3 text-xs text-gray-500 space-y-1">
                      <div>RSS Feed: {result.details.rss_feed}</div>
                      <div>API URL: {result.details.api_url}</div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
