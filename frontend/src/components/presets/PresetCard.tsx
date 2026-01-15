import { Preset, formatFrequencyRange } from '../../hooks/usePresets'

interface PresetCardProps {
  preset: Preset
  onEdit?: (preset: Preset) => void
  onDelete?: (preset: Preset) => void
  onSelect?: (preset: Preset) => void
  isSelected?: boolean
}

const categoryColors: Record<string, string> = {
  UHF: 'bg-purple-600',
  VHF: 'bg-green-600',
  ISM: 'bg-orange-600',
  Custom: 'bg-blue-600',
}

export default function PresetCard({
  preset,
  onEdit,
  onDelete,
  onSelect,
  isSelected = false,
}: PresetCardProps) {
  const handleSelect = () => {
    onSelect?.(preset)
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit?.(preset)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete?.(preset)
  }

  return (
    <div
      onClick={handleSelect}
      className={`
        rounded-lg border p-4 transition-all cursor-pointer
        ${isSelected
          ? 'border-blue-500 bg-blue-900/30 ring-2 ring-blue-500/50'
          : 'border-gray-700 bg-gray-800 hover:border-gray-600 hover:bg-gray-750'
        }
      `}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-white truncate">{preset.name}</h3>
            {preset.is_builtin && (
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
                Built-in
              </span>
            )}
          </div>
          <span
            className={`
              inline-block text-xs px-2 py-0.5 rounded text-white mb-2
              ${categoryColors[preset.category] || 'bg-gray-600'}
            `}
          >
            {preset.category}
          </span>
          <p className="text-sm text-gray-400">
            {formatFrequencyRange(preset.start_freq_hz, preset.stop_freq_hz)}
          </p>
          {preset.description && (
            <p className="text-sm text-gray-500 mt-1 line-clamp-2">{preset.description}</p>
          )}
          <div className="flex gap-4 mt-2 text-xs text-gray-500">
            <span>{preset.points} points</span>
            {preset.rbw_khz && <span>RBW: {preset.rbw_khz} kHz</span>}
          </div>
        </div>
      </div>

      {!preset.is_builtin && (onEdit || onDelete) && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-gray-700">
          {onEdit && (
            <button
              onClick={handleEdit}
              className="flex-1 px-3 py-1.5 text-sm rounded bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
            >
              Edit
            </button>
          )}
          {onDelete && (
            <button
              onClick={handleDelete}
              className="flex-1 px-3 py-1.5 text-sm rounded bg-red-900/50 hover:bg-red-900 text-red-200 transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      )}
    </div>
  )
}
