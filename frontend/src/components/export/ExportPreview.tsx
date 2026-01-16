/**
 * ExportPreview component - displays a preview of the export format.
 * Shows first few lines of the export in a code block with monospace font.
 */

import { useMemo } from 'react'

export type ExportFormat = 'wwb' | 'wsm' | 'csv' | 'json'

export interface ScanDataForPreview {
  name: string
  start_freq_hz: number
  stop_freq_hz: number
  points: Array<{ frequency_hz: number; amplitude_dbm: number }>
  location?: string | null
  scan_completed_at?: string | null
}

interface ExportPreviewProps {
  format: ExportFormat
  scanData: ScanDataForPreview | null
  maxLines?: number
}

// Helper to format frequency in MHz
const formatFreqMHz = (hz: number): string => (hz / 1_000_000).toFixed(6)

// Generate preview content based on format
function generatePreview(
  format: ExportFormat,
  scan: ScanDataForPreview,
  maxLines: number
): string {
  const previewPoints = scan.points.slice(0, maxLines)

  switch (format) {
    case 'wwb': {
      // WWB: 2-column CSV (freq MHz, dBm), no headers
      return previewPoints
        .map((p) => `${formatFreqMHz(p.frequency_hz)},${p.amplitude_dbm.toFixed(1)}`)
        .join('\n')
    }

    case 'wsm': {
      // WSM: semicolon-delimited CSV with header
      const header = 'Frequency;Level'
      const rows = previewPoints.map(
        (p) => `${formatFreqMHz(p.frequency_hz)};${p.amplitude_dbm.toFixed(1)}`
      )
      return [header, ...rows].join('\n')
    }

    case 'csv': {
      // Raw CSV: full CSV with timestamps and metadata
      const header = 'index,frequency_hz,frequency_mhz,amplitude_dbm'
      const rows = previewPoints.map(
        (p, i) =>
          `${i},${p.frequency_hz},${formatFreqMHz(p.frequency_hz)},${p.amplitude_dbm.toFixed(2)}`
      )
      return [header, ...rows].join('\n')
    }

    case 'json': {
      // JSON: structured JSON format
      const jsonData = {
        name: scan.name,
        start_freq_hz: scan.start_freq_hz,
        stop_freq_hz: scan.stop_freq_hz,
        location: scan.location,
        scan_completed_at: scan.scan_completed_at,
        points: previewPoints.slice(0, 3).map((p) => ({
          frequency_hz: p.frequency_hz,
          amplitude_dbm: p.amplitude_dbm,
        })),
        // Indicate more data
        _preview: `... and ${scan.points.length - 3} more points`,
      }
      return JSON.stringify(jsonData, null, 2)
    }

    default:
      return 'Unknown format'
  }
}

export default function ExportPreview({
  format,
  scanData,
  maxLines = 8,
}: ExportPreviewProps) {
  const preview = useMemo(() => {
    if (!scanData || scanData.points.length === 0) {
      return 'No data available for preview'
    }
    return generatePreview(format, scanData, maxLines)
  }, [format, scanData, maxLines])

  const totalPoints = scanData?.points.length ?? 0
  const showingCount = Math.min(maxLines, totalPoints)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-300">Preview</span>
        {totalPoints > showingCount && (
          <span className="text-xs text-gray-500">
            Showing {showingCount} of {totalPoints} points
          </span>
        )}
      </div>
      <div className="relative">
        <pre className="bg-gray-900 border border-gray-700 rounded-lg p-4 overflow-x-auto text-sm text-gray-300 font-mono max-h-64 overflow-y-auto">
          {preview}
        </pre>
        {totalPoints > showingCount && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-gray-900 to-transparent rounded-b-lg pointer-events-none" />
        )}
      </div>
    </div>
  )
}
