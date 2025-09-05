import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface AppSettings {
  appName: string;
  // Add more app settings as needed
}

interface AppSettingsContextType {
  appSettings: AppSettings;
  updateAppSetting: (key: keyof AppSettings, value: string) => void;
  getAppSetting: (key: keyof AppSettings) => string;
  loading: boolean;
}

const AppSettingsContext = createContext<AppSettingsContextType | undefined>(undefined);

// Default app settings
const DEFAULT_APP_SETTINGS: AppSettings = {
  appName: 'Incident Manager',
};

interface AppSettingsProviderProps {
  children: ReactNode;
}

export const AppSettingsProvider: React.FC<AppSettingsProviderProps> = ({ children }) => {
  const [appSettings, setAppSettings] = useState<AppSettings>(DEFAULT_APP_SETTINGS);
  const [loading, setLoading] = useState(true);

  // Load app settings from localStorage on mount
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem('appSettings');
      if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings);
        setAppSettings({ ...DEFAULT_APP_SETTINGS, ...parsedSettings });
      }
    } catch (error) {
      console.error('Error loading app settings:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Save app settings to localStorage whenever they change
  useEffect(() => {
    if (!loading) {
      localStorage.setItem('appSettings', JSON.stringify(appSettings));
      // Update document title
      document.title = appSettings.appName;
    }
  }, [appSettings, loading]);

  const updateAppSetting = (key: keyof AppSettings, value: string) => {
    setAppSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const getAppSetting = (key: keyof AppSettings): string => {
    return appSettings[key];
  };

  const value: AppSettingsContextType = {
    appSettings,
    updateAppSetting,
    getAppSetting,
    loading
  };

  return (
    <AppSettingsContext.Provider value={value}>
      {children}
    </AppSettingsContext.Provider>
  );
};

export const useAppSettings = (): AppSettingsContextType => {
  const context = useContext(AppSettingsContext);
  if (context === undefined) {
    throw new Error('useAppSettings must be used within an AppSettingsProvider');
  }
  return context;
};
