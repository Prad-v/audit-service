import React from 'react';
import { useFeatureFlags } from '../contexts/FeatureFlagsContext';
import { Database, Workflow } from 'lucide-react';

export const FeatureFlags: React.FC = () => {
  const { featureFlags, updateFeatureFlag, isFeatureEnabled } = useFeatureFlags();

  const featureFlagConfigs = [
    {
      key: 'eventFramework' as const,
      name: 'Event Framework',
      description: 'Enable the Event Framework UI for managing event schemas and configurations',
      icon: Database,
      category: 'Event Management'
    },
    {
      key: 'eventPipeline' as const,
      name: 'Event Pipeline Builder',
      description: 'Enable the Event Pipeline Builder UI for creating and managing event processing pipelines',
      icon: Workflow,
      category: 'Event Management'
    }
  ];

  const groupedFlags = featureFlagConfigs.reduce((acc, flag) => {
    if (!acc[flag.category]) {
      acc[flag.category] = [];
    }
    acc[flag.category].push(flag);
    return acc;
  }, {} as Record<string, typeof featureFlagConfigs>);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Feature Flags</h2>
        <p className="text-gray-600">
          Control which UI features and capabilities are available in the application. 
          Changes are saved automatically and take effect immediately.
        </p>
      </div>

      {Object.entries(groupedFlags).map(([category, flags]) => (
        <div key={category} className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">{category}</h3>
          <div className="space-y-4">
            {flags.map((flag) => {
              const Icon = flag.icon;
              const isEnabled = isFeatureEnabled(flag.key);
              
              return (
                <div key={flag.key} className="flex items-start justify-between p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`p-2 rounded-lg ${isEnabled ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900">{flag.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{flag.description}</p>
                    </div>
                  </div>
                  
                  <div className="ml-4">
                    <button
                      onClick={() => updateFeatureFlag(flag.key, !isEnabled)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        isEnabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          isEnabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">How Feature Flags Work</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Feature flags control the visibility of UI components and navigation items</li>
                <li>Disabled features are completely hidden from the interface</li>
                <li>Settings are automatically saved to your browser's local storage</li>
                <li>Changes take effect immediately without requiring a page refresh</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
