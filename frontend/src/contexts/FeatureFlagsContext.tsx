import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface FeatureFlags {
  eventFramework: boolean;
  eventPipeline: boolean;
  // Add more feature flags as needed
}

interface FeatureFlagsContextType {
  featureFlags: FeatureFlags;
  updateFeatureFlag: (key: keyof FeatureFlags, value: boolean) => void;
  isFeatureEnabled: (key: keyof FeatureFlags) => boolean;
  loading: boolean;
}

const FeatureFlagsContext = createContext<FeatureFlagsContextType | undefined>(undefined);

// Default feature flags (disabled by default as requested)
const DEFAULT_FEATURE_FLAGS: FeatureFlags = {
  eventFramework: false,
  eventPipeline: false,
};

interface FeatureFlagsProviderProps {
  children: ReactNode;
}

export const FeatureFlagsProvider: React.FC<FeatureFlagsProviderProps> = ({ children }) => {
  const [featureFlags, setFeatureFlags] = useState<FeatureFlags>(DEFAULT_FEATURE_FLAGS);
  const [loading, setLoading] = useState(true);

  // Load feature flags from localStorage on mount
  useEffect(() => {
    try {
      const savedFlags = localStorage.getItem('featureFlags');
      if (savedFlags) {
        const parsedFlags = JSON.parse(savedFlags);
        setFeatureFlags({ ...DEFAULT_FEATURE_FLAGS, ...parsedFlags });
      }
    } catch (error) {
      console.error('Error loading feature flags:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Save feature flags to localStorage whenever they change
  useEffect(() => {
    if (!loading) {
      localStorage.setItem('featureFlags', JSON.stringify(featureFlags));
    }
  }, [featureFlags, loading]);

  const updateFeatureFlag = (key: keyof FeatureFlags, value: boolean) => {
    setFeatureFlags(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const isFeatureEnabled = (key: keyof FeatureFlags): boolean => {
    return featureFlags[key];
  };

  const value: FeatureFlagsContextType = {
    featureFlags,
    updateFeatureFlag,
    isFeatureEnabled,
    loading
  };

  return (
    <FeatureFlagsContext.Provider value={value}>
      {children}
    </FeatureFlagsContext.Provider>
  );
};

export const useFeatureFlags = (): FeatureFlagsContextType => {
  const context = useContext(FeatureFlagsContext);
  if (context === undefined) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagsProvider');
  }
  return context;
};
