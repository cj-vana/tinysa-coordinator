/**
 * ScanControls component for configuring and controlling frequency scans.
 * Provides inputs for frequency range, points, RBW, and preset selection.
 */

import { useState, useCallback, useEffect } from 'react';
import type { ScanConfig } from '../../hooks/useScanData';
import { usePresets } from '../../hooks/usePresets';

interface ScanControlsProps {
  onStartScan: (config: ScanConfig) => void;
  onStopScan: () => void;
  isScanning: boolean;
  wsStatus: 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';
}

// Convert Hz to MHz for display
const hzToMhz = (hz: number): number => hz / 1_000_000;
// Convert MHz to Hz for API
const mhzToHz = (mhz: number): number => Math.round(mhz * 1_000_000);

export default function ScanControls({
  onStartScan,
  onStopScan,
  isScanning,
  wsStatus,
}: ScanControlsProps) {
  const [startFreqMhz, setStartFreqMhz] = useState(470);
  const [stopFreqMhz, setStopFreqMhz] = useState(698);
  const [points, setPoints] = useState(450);
  const [rbwKhz, setRbwKhz] = useState<string>('');
  const [selectedPresetId, setSelectedPresetId] = useState<number | null>(null);

  // Fetch presets from API using the usePresets hook
  const { data: presetsData } = usePresets();

  const presets = presetsData?.items ?? [];

  // Handle preset selection
  const handlePresetChange = useCallback(
    (presetId: string) => {
      if (presetId === '') {
        setSelectedPresetId(null);
        return;
      }
      const id = parseInt(presetId, 10);
      const preset = presets.find((p) => p.id === id);
      if (preset) {
        setSelectedPresetId(id);
        setStartFreqMhz(hzToMhz(preset.start_freq_hz));
        setStopFreqMhz(hzToMhz(preset.stop_freq_hz));
        setPoints(preset.points);
        setRbwKhz(preset.rbw_khz ? String(preset.rbw_khz) : '');
      }
    },
    [presets]
  );

  // Clear preset selection when manual changes are made
  useEffect(() => {
    if (selectedPresetId !== null) {
      const preset = presets.find((p) => p.id === selectedPresetId);
      if (preset) {
        const presetStartMhz = hzToMhz(preset.start_freq_hz);
        const presetStopMhz = hzToMhz(preset.stop_freq_hz);
        const presetRbw = preset.rbw_khz ? String(preset.rbw_khz) : '';
        if (
          startFreqMhz !== presetStartMhz ||
          stopFreqMhz !== presetStopMhz ||
          points !== preset.points ||
          rbwKhz !== presetRbw
        ) {
          setSelectedPresetId(null);
        }
      }
    }
  }, [startFreqMhz, stopFreqMhz, points, rbwKhz, selectedPresetId, presets]);

  const handleStartScan = () => {
    const config: ScanConfig = {
      start_freq_hz: mhzToHz(startFreqMhz),
      stop_freq_hz: mhzToHz(stopFreqMhz),
      points,
    };
    if (rbwKhz) {
      config.rbw_khz = parseFloat(rbwKhz);
    }
    onStartScan(config);
  };

  const isConnected = wsStatus === 'connected';
  const canStartScan = isConnected && !isScanning && startFreqMhz < stopFreqMhz;

  const connectionStatusColor = {
    connected: 'bg-green-500',
    connecting: 'bg-yellow-500',
    reconnecting: 'bg-yellow-500',
    disconnected: 'bg-red-500',
    error: 'bg-red-500',
  }[wsStatus];

  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Scan Controls</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connectionStatusColor}`} />
          <span className="text-sm text-gray-400 capitalize">{wsStatus}</span>
        </div>
      </div>

      {/* Preset Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Preset
        </label>
        <select
          value={selectedPresetId ?? ''}
          onChange={(e) => handlePresetChange(e.target.value)}
          disabled={isScanning}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <option value="">Custom Range</option>
          {presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.name} ({hzToMhz(preset.start_freq_hz).toFixed(1)} - {hzToMhz(preset.stop_freq_hz).toFixed(1)} MHz)
            </option>
          ))}
        </select>
      </div>

      {/* Frequency Range */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Start Frequency (MHz)
          </label>
          <input
            type="number"
            value={startFreqMhz}
            onChange={(e) => setStartFreqMhz(parseFloat(e.target.value) || 0)}
            disabled={isScanning}
            min={0.1}
            max={12000}
            step={0.1}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Stop Frequency (MHz)
          </label>
          <input
            type="number"
            value={stopFreqMhz}
            onChange={(e) => setStopFreqMhz(parseFloat(e.target.value) || 0)}
            disabled={isScanning}
            min={0.1}
            max={12000}
            step={0.1}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>
      </div>

      {/* Points and RBW */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Points
          </label>
          <select
            value={points}
            onChange={(e) => setPoints(parseInt(e.target.value, 10))}
            disabled={isScanning}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value={100}>100</option>
            <option value={225}>225</option>
            <option value={450}>450 (Default)</option>
            <option value={900}>900</option>
            <option value={1800}>1800</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            RBW (kHz)
          </label>
          <input
            type="number"
            value={rbwKhz}
            onChange={(e) => setRbwKhz(e.target.value)}
            disabled={isScanning}
            placeholder="Auto"
            min={0.2}
            max={850}
            step={0.1}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white
                       placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500
                       focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>
      </div>

      {/* Validation Message */}
      {startFreqMhz >= stopFreqMhz && (
        <p className="text-red-400 text-sm">
          Stop frequency must be greater than start frequency
        </p>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-2">
        {!isScanning ? (
          <button
            onClick={handleStartScan}
            disabled={!canStartScan}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600
                       disabled:cursor-not-allowed text-white font-medium py-2 px-4
                       rounded-md transition-colors"
          >
            Start Scan
          </button>
        ) : (
          <button
            onClick={onStopScan}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium
                       py-2 px-4 rounded-md transition-colors"
          >
            Stop Scan
          </button>
        )}
      </div>
    </div>
  );
}
