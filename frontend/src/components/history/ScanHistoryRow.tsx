/**
 * ScanHistoryRow - Individual row in the scan history table.
 */

import { SavedScanSummary, formatFrequencyRange, formatDate } from '../../hooks/useHistory'

interface ScanHistoryRowProps {
  scan: SavedScanSummary
  onSelect: (id: number) => void
  onDelete: (id: number) => void
  isSelected: boolean
}

export default function ScanHistoryRow({
  scan,
  onSelect,
  onDelete,
  isSelected,
}: ScanHistoryRowProps) {
  return (
    <tr
      className={`border-b border-gray-700 hover:bg-gray-700/50 cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-900/30' : ''
      }`}
      onClick={() => onSelect(scan.id)}
    >
      <td className="px-4 py-3">
        <div className="font-medium text-white">{scan.name}</div>
        {scan.preset_name && (
          <div className="text-xs text-gray-400">Preset: {scan.preset_name}</div>
        )}
      </td>
      <td className="px-4 py-3 text-gray-300 font-mono text-sm">
        {formatFrequencyRange(scan.start_freq_hz, scan.stop_freq_hz)}
      </td>
      <td className="px-4 py-3 text-gray-300">
        {scan.location || <span className="text-gray-500 italic">No location</span>}
      </td>
      <td className="px-4 py-3 text-gray-400 text-sm">
        {formatDate(scan.scan_completed_at || scan.created_at)}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => onSelect(scan.id)}
            className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            View
          </button>
          <button
            onClick={() => onDelete(scan.id)}
            className="px-3 py-1 text-sm bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded transition-colors"
          >
            Delete
          </button>
        </div>
      </td>
    </tr>
  )
}
