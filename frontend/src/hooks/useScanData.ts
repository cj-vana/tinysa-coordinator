/**
 * React hook for managing scan data via WebSocket connection.
 * Provides real-time scan data streaming and control functions.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ScanWebSocket,
} from '../lib/websocket';
import type {
  ScanPoint,
  ScanMessage,
  WebSocketStatus,
  ReconnectionState,
} from '../lib/websocket';

export interface ScanConfig {
  start_freq_hz: number;
  stop_freq_hz: number;
  points: number;
  rbw_khz?: number;
}

export interface ScanState {
  scanData: ScanPoint[];
  isScanning: boolean;
  progress: number;
  totalPoints: number;
  wsStatus: WebSocketStatus;
  error: string | null;
  scanDuration: number | null;
  reconnectionState: ReconnectionState;
}

export interface UseScanDataReturn extends ScanState {
  startScan: (config: ScanConfig) => void;
  stopScan: () => void;
  clearData: () => void;
  connect: () => void;
  disconnect: () => void;
  peakPoint: ScanPoint | null;
}

export function useScanData(wsUrl?: string): UseScanDataReturn {
  const [scanData, setScanData] = useState<ScanPoint[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalPoints, setTotalPoints] = useState(0);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [scanDuration, setScanDuration] = useState<number | null>(null);
  const [reconnectionState, setReconnectionState] = useState<ReconnectionState>({
    isReconnecting: false,
    attempt: 0,
    maxAttempts: 5,
  });

  const wsRef = useRef<ScanWebSocket | null>(null);

  const handleMessage = useCallback((message: ScanMessage) => {
    switch (message.type) {
      case 'scan_started':
        setIsScanning(true);
        setTotalPoints(message.total_points);
        setProgress(0);
        setScanData([]);
        setError(null);
        setScanDuration(null);
        break;

      case 'scan_point':
        setScanData((prev) => {
          const newPoint: ScanPoint = {
            index: message.index,
            frequency_hz: message.frequency_hz,
            amplitude_dbm: message.amplitude_dbm,
          };
          // Insert in order by index
          const updated = [...prev];
          const insertIndex = updated.findIndex((p) => p.index > message.index);
          if (insertIndex === -1) {
            updated.push(newPoint);
          } else {
            updated.splice(insertIndex, 0, newPoint);
          }
          return updated;
        });
        setProgress((prev) => {
          const newProgress = Math.round(((message.index + 1) / totalPoints) * 100);
          return Math.max(prev, newProgress);
        });
        break;

      case 'scan_completed':
        setIsScanning(false);
        setProgress(100);
        setScanDuration(message.duration_ms);
        break;

      case 'scan_error':
        setIsScanning(false);
        setError(message.error);
        break;

      case 'scan_stopped':
        setIsScanning(false);
        break;
    }
  }, [totalPoints]);

  useEffect(() => {
    const ws = new ScanWebSocket(wsUrl, {
      onOpen: () => {
        setWsStatus('connected');
        setReconnectionState({ isReconnecting: false, attempt: 0, maxAttempts: 5 });
      },
      onClose: () => setWsStatus('disconnected'),
      onError: () => setWsStatus('error'),
      onMessage: handleMessage,
      onReconnecting: (state) => {
        setWsStatus('reconnecting');
        setReconnectionState(state);
      },
      onReconnectFailed: () => {
        setWsStatus('error');
        setReconnectionState((prev) => ({ ...prev, isReconnecting: false }));
        setError('Connection lost. Max reconnection attempts reached.');
      },
    });

    wsRef.current = ws;
    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, [wsUrl, handleMessage]);

  const startScan = useCallback((config: ScanConfig) => {
    setError(null);
    setTotalPoints(config.points);
    wsRef.current?.startScan(config);
  }, []);

  const stopScan = useCallback(() => {
    wsRef.current?.stopScan();
  }, []);

  const clearData = useCallback(() => {
    setScanData([]);
    setProgress(0);
    setError(null);
    setScanDuration(null);
  }, []);

  const connect = useCallback(() => {
    wsRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.disconnect();
  }, []);

  // Calculate peak point (highest amplitude)
  const peakPoint = scanData.length > 0
    ? scanData.reduce((max, point) =>
        point.amplitude_dbm > max.amplitude_dbm ? point : max
      )
    : null;

  return {
    scanData,
    isScanning,
    progress,
    totalPoints,
    wsStatus,
    error,
    scanDuration,
    reconnectionState,
    startScan,
    stopScan,
    clearData,
    connect,
    disconnect,
    peakPoint,
  };
}
