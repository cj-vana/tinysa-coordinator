/**
 * React hook for managing device connection state.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deviceApi, type SerialPort, type DeviceStatus, type DeviceInfo } from '../lib/api';

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'disconnecting';

export interface UseDeviceResult {
  /** List of available serial ports */
  ports: SerialPort[];
  /** Whether ports are being fetched */
  isLoadingPorts: boolean;
  /** Error fetching ports */
  portsError: Error | null;
  /** Refresh the ports list */
  refreshPorts: () => void;

  /** Current device status */
  status: DeviceStatus | null;
  /** Whether status is being fetched */
  isLoadingStatus: boolean;
  /** Error fetching status */
  statusError: Error | null;

  /** Current connection state */
  connectionState: ConnectionState;

  /** Connect to a device */
  connect: (port: string) => Promise<DeviceInfo>;
  /** Whether connection is in progress */
  isConnecting: boolean;
  /** Error from last connection attempt */
  connectError: Error | null;

  /** Disconnect from the device */
  disconnect: () => Promise<void>;
  /** Whether disconnection is in progress */
  isDisconnecting: boolean;
  /** Error from last disconnection attempt */
  disconnectError: Error | null;
}

export function useDevice(): UseDeviceResult {
  const queryClient = useQueryClient();

  // Query for available ports
  const portsQuery = useQuery({
    queryKey: ['device', 'ports'],
    queryFn: deviceApi.getPorts,
    staleTime: 10000, // Cache for 10 seconds
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Query for device status
  const statusQuery = useQuery({
    queryKey: ['device', 'status'],
    queryFn: deviceApi.getStatus,
    staleTime: 5000, // Cache for 5 seconds
    refetchInterval: 5000, // Poll status every 5 seconds
  });

  // Mutation for connecting
  const connectMutation = useMutation({
    mutationFn: deviceApi.connect,
    onSuccess: () => {
      // Invalidate status to fetch updated info
      queryClient.invalidateQueries({ queryKey: ['device', 'status'] });
    },
  });

  // Mutation for disconnecting
  const disconnectMutation = useMutation({
    mutationFn: deviceApi.disconnect,
    onSuccess: () => {
      // Invalidate status to fetch updated info
      queryClient.invalidateQueries({ queryKey: ['device', 'status'] });
    },
  });

  // Determine connection state
  const getConnectionState = (): ConnectionState => {
    if (connectMutation.isPending) return 'connecting';
    if (disconnectMutation.isPending) return 'disconnecting';
    if (statusQuery.data?.connected) return 'connected';
    return 'disconnected';
  };

  return {
    // Ports
    ports: portsQuery.data ?? [],
    isLoadingPorts: portsQuery.isLoading,
    portsError: portsQuery.error,
    refreshPorts: () => queryClient.invalidateQueries({ queryKey: ['device', 'ports'] }),

    // Status
    status: statusQuery.data ?? null,
    isLoadingStatus: statusQuery.isLoading,
    statusError: statusQuery.error,

    // Connection state
    connectionState: getConnectionState(),

    // Connect
    connect: connectMutation.mutateAsync,
    isConnecting: connectMutation.isPending,
    connectError: connectMutation.error,

    // Disconnect
    disconnect: disconnectMutation.mutateAsync,
    isDisconnecting: disconnectMutation.isPending,
    disconnectError: disconnectMutation.error,
  };
}
