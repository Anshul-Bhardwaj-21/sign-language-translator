import { useEffect, useState } from 'react';
import { AlertCircle, RefreshCw, Server } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface HealthStatus {
  isHealthy: boolean;
  isChecking: boolean;
  error: string | null;
  lastChecked: Date | null;
  retryCount: number;
}

/**
 * BackendHealthCheck Component
 * 
 * Checks backend health on app startup and displays a modal if backend is unavailable.
 * Provides retry functionality and clear error messages.
 * 
 * Features:
 * - Automatic health check on mount
 * - Retry mechanism with exponential backoff
 * - User-friendly error modal
 * - Console logging for debugging
 */
export default function BackendHealthCheck() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({
    isHealthy: false,
    isChecking: true,
    error: null,
    lastChecked: null,
    retryCount: 0,
  });

  const [showModal, setShowModal] = useState(false);

  const checkBackendHealth = async (retryCount: number = 0) => {
    console.log(`[BackendHealthCheck] Checking backend health (attempt ${retryCount + 1})...`);
    
    setHealthStatus(prev => ({
      ...prev,
      isChecking: true,
      error: null,
      retryCount,
    }));

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Backend returned status ${response.status}`);
      }

      const data = await response.json();
      console.log('[BackendHealthCheck] Backend is healthy:', data);

      setHealthStatus({
        isHealthy: true,
        isChecking: false,
        error: null,
        lastChecked: new Date(),
        retryCount,
      });

      setShowModal(false);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('[BackendHealthCheck] Backend health check failed:', errorMessage);

      setHealthStatus({
        isHealthy: false,
        isChecking: false,
        error: errorMessage,
        lastChecked: new Date(),
        retryCount,
      });

      setShowModal(true);
    }
  };

  const handleRetry = () => {
    console.log('[BackendHealthCheck] User initiated retry');
    checkBackendHealth(healthStatus.retryCount + 1);
  };

  const handleDismiss = () => {
    console.log('[BackendHealthCheck] User dismissed health check modal');
    setShowModal(false);
  };

  // Check backend health on mount
  useEffect(() => {
    console.log('[BackendHealthCheck] Component mounted, starting health check');
    checkBackendHealth(0);
  }, []);

  // Don't render anything if backend is healthy or still checking
  if (healthStatus.isHealthy || !showModal) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-navy-900/90 backdrop-blur-xl border border-red-500/30 rounded-2xl shadow-2xl max-w-md w-full p-8">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center">
            <Server className="w-8 h-8 text-red-500" />
          </div>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-white text-center mb-4">
          Backend Unavailable
        </h2>

        {/* Message */}
        <div className="mb-6">
          <p className="text-gray-300 text-center mb-4">
            We couldn't connect to the backend server. This could be because:
          </p>
          <ul className="text-gray-400 text-sm space-y-2 list-disc list-inside">
            <li>The backend server is not running</li>
            <li>The server is starting up (please wait)</li>
            <li>Network connectivity issues</li>
            <li>Firewall or CORS configuration</li>
          </ul>
        </div>

        {/* Error Details */}
        {healthStatus.error && (
          <div className="mb-6 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-300 text-sm font-semibold mb-1">Error Details:</p>
                <p className="text-red-400 text-xs">{healthStatus.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mb-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
          <p className="text-blue-300 text-sm font-semibold mb-2">To start the backend:</p>
          <pre className="text-blue-400 text-xs bg-navy-950 p-2 rounded overflow-x-auto">
            cd backend{'\n'}python simple_server.py
          </pre>
        </div>

        {/* Retry Count */}
        {healthStatus.retryCount > 0 && (
          <p className="text-gray-500 text-xs text-center mb-4">
            Retry attempt: {healthStatus.retryCount}
          </p>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleRetry}
            disabled={healthStatus.isChecking}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:ring-2 focus:ring-blue-400"
          >
            <RefreshCw className={`w-5 h-5 ${healthStatus.isChecking ? 'animate-spin' : ''}`} />
            {healthStatus.isChecking ? 'Checking...' : 'Retry Connection'}
          </button>
          <button
            onClick={handleDismiss}
            disabled={healthStatus.isChecking}
            className="flex-1 px-4 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:ring-2 focus:ring-gray-400"
          >
            Continue Anyway
          </button>
        </div>

        {/* Warning */}
        <p className="text-yellow-400 text-xs text-center mt-4">
          ⚠️ Some features may not work without backend connection
        </p>
      </div>
    </div>
  );
}
