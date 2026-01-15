/**
 * Component for displaying device connection status and info.
 */

import type { DeviceStatus as DeviceStatusType } from '../../lib/api';
import type { ConnectionState } from '../../hooks/useDevice';

interface DeviceStatusProps {
  status: DeviceStatusType | null;
  connectionState: ConnectionState;
}

function StatusIndicator({ state }: { state: ConnectionState }) {
  const configs: Record<ConnectionState, { color: string; label: string; animate?: boolean }> = {
    disconnected: { color: 'bg-gray-500', label: 'Disconnected' },
    connecting: { color: 'bg-yellow-500', label: 'Connecting', animate: true },
    connected: { color: 'bg-green-500', label: 'Connected' },
    disconnecting: { color: 'bg-yellow-500', label: 'Disconnecting', animate: true },
  };

  const config = configs[state];

  return (
    <div className="flex items-center gap-2">
      <span
        className={`w-3 h-3 rounded-full ${config.color} ${config.animate ? 'animate-pulse' : ''}`}
        aria-hidden="true"
      />
      <span className="text-sm font-medium text-gray-300">{config.label}</span>
    </div>
  );
}

export default function DeviceStatus({ status, connectionState }: DeviceStatusProps) {
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
          Device Status
        </h3>
        <StatusIndicator state={connectionState} />
      </div>

      {status?.connected && (
        <div className="space-y-3">
          {status.device_type && (
            <InfoRow label="Device" value={status.device_type} />
          )}
          {status.version && (
            <InfoRow label="Firmware" value={status.version} />
          )}
          {status.hardware && (
            <InfoRow label="Hardware" value={status.hardware} />
          )}
          {status.port && (
            <InfoRow label="Port" value={status.port} mono />
          )}
        </div>
      )}

      {!status?.connected && connectionState === 'disconnected' && (
        <p className="text-sm text-gray-500">
          No device connected. Select a port and click Connect.
        </p>
      )}

      {connectionState === 'connecting' && (
        <p className="text-sm text-gray-500">
          Establishing connection...
        </p>
      )}
    </div>
  );
}

function InfoRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm text-gray-200 ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  );
}
