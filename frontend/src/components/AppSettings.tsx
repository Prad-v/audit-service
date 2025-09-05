import React, { useState } from 'react';
import { useAppSettings } from '../contexts/AppSettingsContext';
import { Save, RotateCcw, Info } from 'lucide-react';

export const AppSettings: React.FC = () => {
  const { appSettings, updateAppSetting, getAppSetting } = useAppSettings();
  const [appName, setAppName] = useState(getAppSetting('appName'));
  const [isEditing, setIsEditing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSave = () => {
    if (appName.trim()) {
      updateAppSetting('appName', appName.trim());
      setIsEditing(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }
  };

  const handleReset = () => {
    setAppName('Incident Manager');
    updateAppSetting('appName', 'Incident Manager');
    setIsEditing(false);
  };

  const handleCancel = () => {
    setAppName(getAppSetting('appName'));
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Application Settings</h2>
        <p className="text-gray-600">
          Customize the application name and other global settings. Changes take effect immediately.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Application Name</h3>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="appName" className="block text-sm font-medium text-gray-700 mb-2">
              Application Name
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="text"
                id="appName"
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
                onFocus={() => setIsEditing(true)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter application name"
                maxLength={50}
              />
              {isEditing && (
                <div className="flex space-x-2">
                  <button
                    onClick={handleSave}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Save className="w-4 h-4 mr-1" />
                    Save
                  </button>
                  <button
                    onClick={handleCancel}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
            <p className="mt-1 text-sm text-gray-500">
              This name will appear in the header, page titles, and welcome messages.
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Current name:</span>
              <span className="text-sm font-medium text-gray-900">{getAppSetting('appName')}</span>
            </div>
            <button
              onClick={handleReset}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              Reset to Default
            </button>
          </div>
        </div>

        {showSuccess && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">
                  Application name updated successfully!
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <Info className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">About Application Settings</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Application name changes are saved automatically to your browser's local storage</li>
                <li>Changes take effect immediately across all pages</li>
                <li>Settings persist across browser sessions</li>
                <li>You can reset to the default name at any time</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
