/**
 * FormatSelector component - allows selection of export format.
 * Displays format options as cards with descriptions.
 */

import type { ExportFormat } from './ExportPreview'

interface FormatOption {
  id: ExportFormat
  name: string
  description: string
  fileExtension: string
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    id: 'wwb',
    name: 'Shure WWB',
    description: 'Shure Wireless Workbench - 2-column CSV, most compatible',
    fileExtension: '.csv',
  },
  {
    id: 'wsm',
    name: 'Sennheiser WSM',
    description: 'Sennheiser WSM - semicolon-delimited with headers',
    fileExtension: '.csv',
  },
  {
    id: 'csv',
    name: 'Raw CSV',
    description: 'Full CSV with timestamps and metadata',
    fileExtension: '.csv',
  },
  {
    id: 'json',
    name: 'JSON',
    description: 'Structured JSON for custom processing',
    fileExtension: '.json',
  },
]

interface FormatSelectorProps {
  selectedFormat: ExportFormat
  onFormatChange: (format: ExportFormat) => void
  disabled?: boolean
}

export default function FormatSelector({
  selectedFormat,
  onFormatChange,
  disabled = false,
}: FormatSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-300">
        Export Format
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {FORMAT_OPTIONS.map((option) => {
          const isSelected = selectedFormat === option.id
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => onFormatChange(option.id)}
              disabled={disabled}
              className={`
                relative flex flex-col items-start p-4 rounded-lg border-2 text-left
                transition-all duration-150
                ${
                  isSelected
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-600 bg-gray-700/50 hover:border-gray-500 hover:bg-gray-700'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {/* Radio indicator */}
              <div className="absolute top-4 right-4">
                <div
                  className={`
                    w-5 h-5 rounded-full border-2 flex items-center justify-center
                    ${isSelected ? 'border-blue-500' : 'border-gray-500'}
                  `}
                >
                  {isSelected && (
                    <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                  )}
                </div>
              </div>

              {/* Format info */}
              <div className="pr-8">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{option.name}</span>
                  <span className="text-xs text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">
                    {option.fileExtension}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-400">{option.description}</p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export { FORMAT_OPTIONS }
export type { FormatOption }
