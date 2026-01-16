/**
 * ScanDetail - Detailed view of a saved scan with chart, metadata, and export options.
 */

import { useState, useMemo } from 'react'
import {
  useScan,
  useUpdateScan,
  useExportScan,
  formatFrequencyRange,
  formatDate,
  parseTags,
  ScanUpdateData,
} from '../../hooks/useHistory'
import FrequencyChart from '../scan/FrequencyChart'
import MetadataEditor from './MetadataEditor'
import { ScanPoint } from '../../lib/websocket'

interface ScanDetailProps {
  scanId: number
  onClose: () => void
}

export default function ScanDetail({ scanId, onClose }: ScanDetailProps) {
  const [isEditing, setIsEditing] = useState(false)

  const { data: scan, isLoading, error } = useScan(scanId)
  const updateMutation = useUpdateScan()
  const exportMutation = useExportScan()

  // Transform scan data points to chart format
  const dataPoints = scan?.data_points
  const chartData: ScanPoint[] = useMemo(() => {
    if (!dataPoints) return []
    return dataPoints.map((point) => ({
      index: point.index,
      frequency_hz: point.frequency_hz,
      amplitude_dbm: point.amplitude_dbm,
    }))
  }, [dataPoints])

  // Find peak point
  const peakPoint: ScanPoint | null = useMemo(() => {
    if (chartData.length === 0) return null
    return chartData.reduce((peak, point) =>
      point.amplitude_dbm > peak.amplitude_dbm ? point : peak
    )
  }, [chartData])

  const handleSaveMetadata = (data: ScanUpdateData) => {
    updateMutation.mutate(
      { id: scanId, data },
      {
        onSuccess: () => setIsEditing(false),
      }
    )
  }

  const handleExport = (format: 'wwb' | 'wsm' | 'raw') => {
    exportMutation.mutate({ id: scanId, format })
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 h-full flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-400">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading scan details...
        </div>
      </div>
    )
  }

  if (error || !scan) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 h-full">
        <div className="text-red-400 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Failed to load scan: {error ? (error as Error).message : 'Scan not found'}
        </div>
      </div>
    )
  }

  const tags = parseTags(scan.tags)

  return (
    <div className="bg-gray-800 rounded-lg h-full flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-gray-700">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white truncate">{scan.name}</h2>
            <button
              onClick={() => setIsEditing(true)}
              className="p-1 text-gray-400 hover:text-white transition-colors"
              title="Edit metadata"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-sm text-gray-400">
            <span className="font-mono">{formatFrequencyRange(scan.start_freq_hz, scan.stop_freq_hz)}</span>
            <span>{scan.points} points</span>
            {scan.rbw_khz && <span>RBW: {scan.rbw_khz} kHz</span>}
          </div>
        </div>
        <button
          onClick={onClose}
          className="ml-4 p-2 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Metadata */}
      <div className="px-4 py-3 border-b border-gray-700 space-y-2">
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {scan.location && (
            <div>
              <span className="text-gray-500">Location:</span>{' '}
              <span className="text-gray-300">{scan.location}</span>
            </div>
          )}
          {scan.preset_name && (
            <div>
              <span className="text-gray-500">Preset:</span>{' '}
              <span className="text-gray-300">{scan.preset_name}</span>
            </div>
          )}
          <div>
            <span className="text-gray-500">Date:</span>{' '}
            <span className="text-gray-300">{formatDate(scan.scan_completed_at || scan.created_at)}</span>
          </div>
        </div>

        {scan.notes && (
          <div className="text-sm">
            <span className="text-gray-500">Notes:</span>{' '}
            <span className="text-gray-300">{scan.notes}</span>
          </div>
        )}

        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.map((tag, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 text-xs bg-blue-600/30 text-blue-300 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Export buttons */}
      <div className="px-4 py-3 border-b border-gray-700 flex flex-wrap items-center gap-2">
        <span className="text-sm text-gray-400 mr-2">Export:</span>
        <button
          onClick={() => handleExport('wwb')}
          disabled={exportMutation.isPending}
          className="px-3 py-1.5 text-sm bg-green-600/20 hover:bg-green-600/40 text-green-400 rounded transition-colors disabled:opacity-50"
        >
          WWB
        </button>
        <button
          onClick={() => handleExport('wsm')}
          disabled={exportMutation.isPending}
          className="px-3 py-1.5 text-sm bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 rounded transition-colors disabled:opacity-50"
        >
          WSM
        </button>
        <button
          onClick={() => handleExport('raw')}
          disabled={exportMutation.isPending}
          className="px-3 py-1.5 text-sm bg-yellow-600/20 hover:bg-yellow-600/40 text-yellow-400 rounded transition-colors disabled:opacity-50"
        >
          Raw CSV
        </button>
        {exportMutation.isPending && (
          <span className="text-xs text-gray-400 ml-2">Exporting...</span>
        )}
        {exportMutation.isError && (
          <span className="text-xs text-red-400 ml-2">Export failed</span>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[300px] p-4">
        <FrequencyChart
          data={chartData}
          peakPoint={peakPoint}
          isScanning={false}
        />
      </div>

      {/* Metadata Editor Modal */}
      <MetadataEditor
        scan={scan}
        isOpen={isEditing}
        onClose={() => setIsEditing(false)}
        onSave={handleSaveMetadata}
        isSaving={updateMutation.isPending}
      />
    </div>
  )
}
