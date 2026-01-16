/**
 * WebSocketStatusIndicator - Visual feedback for WebSocket connection status
 * and reconnection attempts. Shows connection state, retry count, and provides
 * manual reconnect option when connection fails.
 */

import type { WebSocketStatus, ReconnectionState } from '../../lib/websocket';

interface WebSocketStatusIndicatorProps {
  status: WebSocketStatus;
  reconnectionState: ReconnectionState;
  onReconnect?: () => void;
}

const statusConfigs: Record<
  WebSocketStatus,
  { color: string; bgColor: string; label: string; animate?: boolean }
> = {
  connected: {
    color: 'text-green-400',
    bgColor: 'bg-green-500',
    label: 'Connected',
  },
  connecting: {
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500',
    label: 'Connecting',
    animate: true,
  },
  disconnected: {
    color: 'text-gray-400',
    bgColor: 'bg-gray-500',
    label: 'Disconnected',
  },
  reconnecting: {
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500',
    label: 'Reconnecting',
    animate: true,
  },
  error: {
    color: 'text-red-400',
    bgColor: 'bg-red-500',
    label: 'Connection Failed',
  },
};

export default function WebSocketStatusIndicator({
  status,
  reconnectionState,
  onReconnect,
}: WebSocketStatusIndicatorProps) {
  const config = statusConfigs[status];
  const { isReconnecting, attempt, maxAttempts } = reconnectionState;

  // Don't show anything if connected and stable
  if (status === 'connected' && !isReconnecting) {
    return null;
  }

  return (
    <div
      className={`flex items-center justify-between px-4 py-2 rounded-lg border ${
        status === 'error'
          ? 'bg-red-900/30 border-red-700'
          : status === 'reconnecting'
            ? 'bg-yellow-900/30 border-yellow-700'
            : 'bg-gray-800 border-gray-700'
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-3">
        {/* Status indicator dot */}
        <span
          className={`w-2.5 h-2.5 rounded-full ${config.bgColor} ${
            config.animate ? 'animate-pulse' : ''
          }`}
          aria-hidden="true"
        />

        {/* Status text */}
        <div className="flex flex-col">
          <span className={`text-sm font-medium ${config.color}`}>
            {config.label}
          </span>

          {/* Reconnection progress */}
          {isReconnecting && (
            <span className="text-xs text-gray-400">
              Attempt {attempt} of {maxAttempts}
            </span>
          )}

          {/* Max attempts reached message */}
          {status === 'error' && !isReconnecting && attempt >= maxAttempts && (
            <span className="text-xs text-gray-400">
              Max reconnection attempts reached
            </span>
          )}
        </div>
      </div>

      {/* Manual reconnect button */}
      {(status === 'error' || status === 'disconnected') && onReconnect && (
        <button
          onClick={onReconnect}
          className="px-3 py-1 text-xs font-medium text-white bg-blue-600
                     hover:bg-blue-700 rounded transition-colors"
        >
          Reconnect
        </button>
      )}

      {/* Reconnecting spinner */}
      {isReconnecting && (
        <div className="flex items-center gap-2">
          <svg
            className="animate-spin h-4 w-4 text-yellow-400"
            xmlns="http://www.w3.org/2000/svg"
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
          <span className="text-xs text-gray-400">Retrying...</span>
        </div>
      )}
    </div>
  );
}
