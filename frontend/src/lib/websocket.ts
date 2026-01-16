/**
 * WebSocket utility for real-time scan data streaming.
 * Handles connection management, reconnection logic, and message parsing.
 */

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';

export interface ReconnectionState {
  isReconnecting: boolean;
  attempt: number;
  maxAttempts: number;
}

export interface ScanPoint {
  index: number;
  frequency_hz: number;
  amplitude_dbm: number;
}

export interface ScanStartedMessage {
  type: 'scan_started';
  total_points: number;
  start_freq_hz: number;
  stop_freq_hz: number;
}

export interface ScanPointMessage {
  type: 'scan_point';
  index: number;
  frequency_hz: number;
  amplitude_dbm: number;
}

export interface ScanCompletedMessage {
  type: 'scan_completed';
  total_points: number;
  duration_ms: number;
}

export interface ScanErrorMessage {
  type: 'scan_error';
  error: string;
}

export interface ScanStoppedMessage {
  type: 'scan_stopped';
}

export interface ServerShutdownMessage {
  type: 'server_shutdown';
  reason: string;
}

export type ScanMessage =
  | ScanStartedMessage
  | ScanPointMessage
  | ScanCompletedMessage
  | ScanErrorMessage
  | ScanStoppedMessage
  | ServerShutdownMessage;

export interface WebSocketCallbacks {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: ScanMessage) => void;
  onReconnecting?: (state: ReconnectionState) => void;
  onReconnectFailed?: () => void;
  onServerShutdown?: (reason: string) => void;
}

const DEFAULT_WS_URL = 'ws://localhost:8000/ws/scan';
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export class ScanWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: WebSocketCallbacks;
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private _isReconnecting = false;
  private readonly maxReconnectAttempts = MAX_RECONNECT_ATTEMPTS;

  constructor(url: string = DEFAULT_WS_URL, callbacks: WebSocketCallbacks = {}) {
    this.url = url;
    this.callbacks = callbacks;
  }

  getReconnectionState(): ReconnectionState {
    return {
      isReconnecting: this._isReconnecting,
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
    };
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.shouldReconnect = true;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this._isReconnecting = false;
      this.callbacks.onOpen?.();
    };

    this.ws.onclose = () => {
      this.callbacks.onClose?.();
      this.attemptReconnect();
    };

    this.ws.onerror = (event) => {
      this.callbacks.onError?.(event);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as ScanMessage;

        // Handle server shutdown: disable reconnection and notify callback
        if (message.type === 'server_shutdown') {
          this.shouldReconnect = false;
          this._isReconnecting = false;
          this.callbacks.onServerShutdown?.(message.reason);
        }

        this.callbacks.onMessage?.(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this._isReconnecting = false;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  startScan(params: {
    start_freq_hz: number;
    stop_freq_hz: number;
    points: number;
    rbw_khz?: number;
  }): void {
    this.send({ action: 'start_scan', config: params });
  }

  stopScan(): void {
    this.send({ action: 'stop_scan' });
  }

  getStatus(): WebSocketStatus {
    if (!this.ws) return 'disconnected';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
      default:
        return 'disconnected';
    }
  }

  private attemptReconnect(): void {
    if (!this.shouldReconnect) {
      this._isReconnecting = false;
      return;
    }

    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      this._isReconnecting = false;
      this.callbacks.onReconnectFailed?.();
      return;
    }

    this._isReconnecting = true;
    this.reconnectAttempts++;

    // Notify about reconnection attempt
    this.callbacks.onReconnecting?.(this.getReconnectionState());

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, RECONNECT_DELAY_MS);
  }
}

export function createScanWebSocket(
  callbacks: WebSocketCallbacks,
  url?: string
): ScanWebSocket {
  return new ScanWebSocket(url, callbacks);
}
