/**
 * Panel for managing device connection - port selection and connect/disconnect controls.
 */

import { useState, useMemo } from 'react';
import { useDevice } from '../../hooks/useDevice';
import DeviceStatus from './DeviceStatus';

export default function ConnectionPanel() {
  const {
    ports,
    isLoadingPorts,
    portsError,
    refreshPorts,
    status,
    connectionState,
    connect,
    disconnect,
    connectError,
    disconnectError,
  } = useDevice();

  // Track user's manual port selection
  const [userSelectedPort, setUserSelectedPort] = useState<string>('');

  // Derive the effective selected port:
  // 1. If connected, show the connected port
  // 2. If user has manually selected a port, use that
  // 3. Otherwise, default to first available port
  const selectedPort = useMemo(() => {
    if (status?.connected && status.port) {
      return status.port;
    }
    if (userSelectedPort && ports.some(p => p.port === userSelectedPort)) {
      return userSelectedPort;
    }
    return ports.length > 0 ? ports[0].port : '';
  }, [status?.connected, status?.port, userSelectedPort, ports]);

  const handlePortChange = (port: string) => {
    setUserSelectedPort(port);
  };

  const handleConnect = async () => {
    if (!selectedPort) return;
    try {
      await connect(selectedPort);
    } catch {
      // Error is handled by the hook and displayed in UI
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnect();
    } catch {
      // Error is handled by the hook and displayed in UI
    }
  };

  const isConnected = connectionState === 'connected';
  const isTransitioning = connectionState === 'connecting' || connectionState === 'disconnecting';
  const error = connectError || disconnectError;

  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 bg-gray-800">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <svg
            className="w-5 h-5 text-blue-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            />
          </svg>
          TinySA Ultra Connection
        </h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Port Selection */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="port-select" className="text-sm font-medium text-gray-300">
              Serial Port
            </label>
            <button
              type="button"
              onClick={refreshPorts}
              disabled={isLoadingPorts}
              className="text-xs text-blue-400 hover:text-blue-300 disabled:text-gray-500 transition-colors"
              title="Refresh port list"
            >
              {isLoadingPorts ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          <select
            id="port-select"
            value={selectedPort}
            onChange={(e) => handlePortChange(e.target.value)}
            disabled={isConnected || isTransitioning || isLoadingPorts}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {ports.length === 0 && !isLoadingPorts && (
              <option value="">No ports available</option>
            )}
            {isLoadingPorts && (
              <option value="">Loading ports...</option>
            )}
            {ports.map((port) => (
              <option key={port.port} value={port.port}>
                {port.port}
                {port.description && ` - ${port.description}`}
                {port.manufacturer && ` (${port.manufacturer})`}
              </option>
            ))}
          </select>

          {portsError && (
            <p className="mt-1 text-xs text-red-400">
              Failed to load ports: {portsError.message}
            </p>
          )}
        </div>

        {/* Connect/Disconnect Button */}
        <button
          type="button"
          onClick={isConnected ? handleDisconnect : handleConnect}
          disabled={isTransitioning || (!selectedPort && !isConnected)}
          className={`w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-all
                     focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800
                     disabled:opacity-50 disabled:cursor-not-allowed
                     ${isConnected
                       ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white'
                       : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white'
                     }`}
        >
          {connectionState === 'connecting' && (
            <span className="flex items-center justify-center gap-2">
              <LoadingSpinner />
              Connecting...
            </span>
          )}
          {connectionState === 'disconnecting' && (
            <span className="flex items-center justify-center gap-2">
              <LoadingSpinner />
              Disconnecting...
            </span>
          )}
          {connectionState === 'connected' && 'Disconnect'}
          {connectionState === 'disconnected' && 'Connect'}
        </button>

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg">
            <p className="text-sm text-red-400">
              {error.message || 'An error occurred'}
            </p>
          </div>
        )}

        {/* Device Status */}
        <DeviceStatus status={status} connectionState={connectionState} />
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}
