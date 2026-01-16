/**
 * API client for communicating with the backend server.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message?: string
  ) {
    super(message || `API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message: string | undefined;
    try {
      const data = await response.json();
      message = data.detail || data.message;
    } catch {
      // Response body is not JSON
    }
    throw new ApiError(response.status, response.statusText, message);
  }
  return response.json();
}

export async function get<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse<T>(response);
}

export async function post<T>(endpoint: string, data?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  return handleResponse<T>(response);
}

// Type definitions matching backend schemas

export interface SerialPort {
  port: string;
  description: string;
  hwid: string;
  manufacturer: string | null;
  product: string | null;
  serial_number: string | null;
  vid: number | null;
  pid: number | null;
}

export interface DeviceStatus {
  connected: boolean;
  port: string | null;
  version: string | null;
  hardware: string | null;
  device_type: string | null;
}

export interface DeviceInfo {
  version: string;
  hardware: string | null;
  device_type: string | null;
  port: string;
}

// Device API endpoints

export const deviceApi = {
  /** Get list of available serial ports */
  getPorts: () => get<SerialPort[]>('/api/device/ports'),

  /** Get current device connection status */
  getStatus: () => get<DeviceStatus>('/api/device/status'),

  /** Connect to a device on the specified port */
  connect: (port: string) => post<DeviceInfo>('/api/device/connect', { port }),

  /** Disconnect from the current device */
  disconnect: () => post<void>('/api/device/disconnect'),
};
