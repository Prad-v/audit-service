import React from 'react';
import { Clock, Calendar } from 'lucide-react';

interface TimeRangeSelectorProps {
  showHistorical: boolean;
  timeRange: number; // hours
  onToggleHistorical: (show: boolean) => void;
  onTimeRangeChange: (hours: number) => void;
}

export const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  showHistorical,
  timeRange,
  onToggleHistorical,
  onTimeRangeChange
}) => {
  const timeRangeOptions = [
    { label: '1 Hour', value: 1 },
    { label: '6 Hours', value: 6 },
    { label: '24 Hours', value: 24 },
    { label: '3 Days', value: 72 },
    { label: '1 Week', value: 168 },
    { label: '1 Month', value: 720 }
  ];

  const formatTimeRange = (hours: number) => {
    if (hours < 24) return `${hours}h`;
    if (hours < 168) return `${Math.round(hours / 24)}d`;
    return `${Math.round(hours / 168)}w`;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Data View:</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onToggleHistorical(false)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                !showHistorical
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              Current
            </button>
            <button
              onClick={() => onToggleHistorical(true)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                showHistorical
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              Historical
            </button>
          </div>
        </div>

        {showHistorical && (
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Time Range:</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="1"
                max="720"
                step="1"
                value={timeRange}
                onChange={(e) => onTimeRangeChange(parseInt(e.target.value))}
                className="w-32 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                style={{
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((timeRange - 1) / (720 - 1)) * 100}%, #e5e7eb ${((timeRange - 1) / (720 - 1)) * 100}%, #e5e7eb 100%)`
                }}
              />
              <span className="text-sm font-medium text-gray-700 min-w-[3rem]">
                {formatTimeRange(timeRange)}
              </span>
            </div>
          </div>
        )}
      </div>

      {showHistorical && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex flex-wrap gap-2">
            {timeRangeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => onTimeRangeChange(option.value)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  timeRange === option.value
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
