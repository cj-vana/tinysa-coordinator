/**
 * FrequencyChart component for displaying real-time scan data.
 * Uses Recharts LineChart with frequency on X-axis and amplitude (dBm) on Y-axis.
 */

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import type { ScanPoint } from '../../lib/websocket';

interface FrequencyChartProps {
  data: ScanPoint[];
  peakPoint: ScanPoint | null;
  isScanning: boolean;
}

interface ChartDataPoint extends ScanPoint {
  frequency_mhz: number;
}

// Convert Hz to MHz for display
const hzToMhz = (hz: number): number => hz / 1_000_000;

// Format frequency for axis labels
const formatFrequency = (hz: number): string => {
  const mhz = hzToMhz(hz);
  if (mhz >= 1000) {
    return `${(mhz / 1000).toFixed(2)} GHz`;
  }
  return `${mhz.toFixed(1)} MHz`;
};

// Format amplitude for display
const formatAmplitude = (dbm: number): string => `${dbm.toFixed(1)} dBm`;

// Custom tooltip component
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ChartDataPoint }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const data = payload[0].payload;

  return (
    <div className="bg-gray-800 border border-gray-600 rounded-md px-3 py-2 shadow-lg">
      <p className="text-gray-300 text-sm">
        <span className="text-blue-400">Frequency:</span>{' '}
        {formatFrequency(data.frequency_hz)}
      </p>
      <p className="text-gray-300 text-sm">
        <span className="text-yellow-400">Amplitude:</span>{' '}
        {formatAmplitude(data.amplitude_dbm)}
      </p>
    </div>
  );
}

export default function FrequencyChart({
  data,
  peakPoint,
  isScanning,
}: FrequencyChartProps) {
  // Transform data for the chart
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      frequency_mhz: hzToMhz(point.frequency_hz),
    }));
  }, [data]);

  // Calculate Y-axis domain (typically -120 to 0 dBm with some padding)
  const yDomain = useMemo((): [number, number] => {
    if (data.length === 0) {
      return [-120, 0];
    }
    const amplitudes = data.map((p) => p.amplitude_dbm);
    const min = Math.min(...amplitudes);
    const max = Math.max(...amplitudes);
    // Add padding and round to nice values
    const yMin = Math.floor((min - 5) / 10) * 10;
    const yMax = Math.ceil((max + 5) / 10) * 10;
    return [Math.max(yMin, -130), Math.min(yMax, 10)];
  }, [data]);

  // Calculate X-axis domain
  const xDomain = useMemo((): [number, number] | undefined => {
    if (data.length < 2) return undefined;
    return [data[0].frequency_hz, data[data.length - 1].frequency_hz];
  }, [data]);

  const hasData = data.length > 0;

  return (
    <div className="bg-gray-800 rounded-lg p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Frequency Spectrum</h2>
        {isScanning && (
          <span className="flex items-center gap-2 text-blue-400 text-sm">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            Scanning...
          </span>
        )}
      </div>

      {/* Peak info display */}
      {peakPoint && (
        <div className="flex items-center gap-4 mb-3 text-sm">
          <span className="text-gray-400">Peak:</span>
          <span className="text-yellow-400 font-medium">
            {formatFrequency(peakPoint.frequency_hz)}
          </span>
          <span className="text-green-400 font-medium">
            {formatAmplitude(peakPoint.amplitude_dbm)}
          </span>
        </div>
      )}

      {/* Chart area */}
      <div className="flex-1 min-h-[300px]">
        {!hasData ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <svg
                className="w-16 h-16 mx-auto mb-3 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <p className="text-gray-400">No scan data</p>
              <p className="text-gray-500 text-sm">Start a scan to see the frequency spectrum</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="frequency_hz"
                domain={xDomain}
                tickFormatter={formatFrequency}
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                tickLine={{ stroke: '#6B7280' }}
                axisLine={{ stroke: '#6B7280' }}
                label={{
                  value: 'Frequency',
                  position: 'insideBottom',
                  offset: -5,
                  fill: '#9CA3AF',
                }}
              />
              <YAxis
                domain={yDomain}
                tickFormatter={(value) => `${value}`}
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                tickLine={{ stroke: '#6B7280' }}
                axisLine={{ stroke: '#6B7280' }}
                label={{
                  value: 'dBm',
                  angle: -90,
                  position: 'insideLeft',
                  fill: '#9CA3AF',
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="amplitude_dbm"
                stroke="#3B82F6"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
              {/* Peak marker */}
              {peakPoint && (
                <ReferenceDot
                  x={peakPoint.frequency_hz}
                  y={peakPoint.amplitude_dbm}
                  r={6}
                  fill="#EAB308"
                  stroke="#FEF08A"
                  strokeWidth={2}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
