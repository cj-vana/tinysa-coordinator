import { Preset, usePresets, formatFrequencyRange } from '../../hooks/usePresets'

interface PresetQuickBarProps {
  selectedPresetId?: number | null
  onSelectPreset: (preset: Preset) => void
}

const categoryColors: Record<string, string> = {
  UHF: 'border-purple-500 hover:bg-purple-900/30',
  VHF: 'border-green-500 hover:bg-green-900/30',
  ISM: 'border-orange-500 hover:bg-orange-900/30',
  Custom: 'border-blue-500 hover:bg-blue-900/30',
}

const selectedCategoryColors: Record<string, string> = {
  UHF: 'border-purple-500 bg-purple-900/50 ring-2 ring-purple-500/50',
  VHF: 'border-green-500 bg-green-900/50 ring-2 ring-green-500/50',
  ISM: 'border-orange-500 bg-orange-900/50 ring-2 ring-orange-500/50',
  Custom: 'border-blue-500 bg-blue-900/50 ring-2 ring-blue-500/50',
}

export default function PresetQuickBar({ selectedPresetId, onSelectPreset }: PresetQuickBarProps) {
  const { data, isLoading, error } = usePresets()

  if (isLoading) {
    return (
      <div className="flex gap-2 overflow-x-auto pb-2">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="flex-shrink-0 w-48 h-16 bg-gray-700 rounded-lg animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-400">
        Failed to load presets
      </div>
    )
  }

  const presets = data?.items || []

  if (presets.length === 0) {
    return (
      <div className="text-sm text-gray-400 py-2">
        No presets available. Create one in the Settings page.
      </div>
    )
  }

  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
      {presets.map((preset) => {
        const isSelected = selectedPresetId === preset.id
        const baseColor = categoryColors[preset.category] || categoryColors.Custom
        const activeColor = selectedCategoryColors[preset.category] || selectedCategoryColors.Custom

        return (
          <button
            key={preset.id}
            onClick={() => onSelectPreset(preset)}
            className={`
              flex-shrink-0 px-4 py-2 rounded-lg border-2 text-left transition-all
              ${isSelected ? activeColor : `${baseColor} bg-gray-800`}
            `}
          >
            <div className="flex items-center gap-2 mb-0.5">
              <span className="font-medium text-white text-sm truncate max-w-32">
                {preset.name}
              </span>
              {preset.is_builtin && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-400">
                  Built-in
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400 block">
              {formatFrequencyRange(preset.start_freq_hz, preset.stop_freq_hz)}
            </span>
          </button>
        )
      })}
    </div>
  )
}
