/**
 * ExportDialog component - modal dialog for exporting scan data.
 * Provides format selection, preview, and download functionality.
 */

import { useState, useCallback } from 'react'
import FormatSelector, { FORMAT_OPTIONS } from './FormatSelector'
import ExportPreview from './ExportPreview'
import type { ExportFormat, ScanDataForPreview } from './ExportPreview'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ExportDialogProps {
  isOpen: boolean
  onClose: () => void
  scanId: number
  scanName: string
  scanData: ScanDataForPreview | null
}

export default function ExportDialog({
  isOpen,
  onClose,
  scanId,
  scanName,
  scanData,
}: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('wwb')
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDownload = useCallback(async () => {
    setIsDownloading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/export/${scanId}/${selectedFormat}`,
        {
          method: 'GET',
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(
          errorData?.detail || `Export failed: ${response.statusText}`
        )
      }

      // Get filename from Content-Disposition header or generate one
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `${scanName.replace(/[^a-zA-Z0-9-_]/g, '_')}_${selectedFormat}`

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/)
        if (match) {
          filename = match[1]
        }
      } else {
        // Add appropriate extension
        const formatOption = FORMAT_OPTIONS.find((f) => f.id === selectedFormat)
        filename += formatOption?.fileExtension || '.csv'
      }

      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      // Close dialog on successful download
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export scan')
    } finally {
      setIsDownloading(false)
    }
  }, [scanId, scanName, selectedFormat, onClose])

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isDownloading) {
        onClose()
      }
    },
    [onClose, isDownloading]
  )

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gray-800 px-6 py-4 border-b border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Export Scan</h2>
            <p className="text-sm text-gray-400 mt-0.5">{scanName}</p>
          </div>
          <button
            onClick={onClose}
            disabled={isDownloading}
            className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
            aria-label="Close dialog"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Error message */}
          {error && (
            <div className="p-3 rounded bg-red-900/50 border border-red-700 text-red-200 text-sm">
              {error}
            </div>
          )}

          {/* Format selection */}
          <FormatSelector
            selectedFormat={selectedFormat}
            onFormatChange={setSelectedFormat}
            disabled={isDownloading}
          />

          {/* Preview */}
          <ExportPreview format={selectedFormat} scanData={scanData} />

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              disabled={isDownloading}
              className="flex-1 px-4 py-2.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDownload}
              disabled={isDownloading || !scanData}
              className="flex-1 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isDownloading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Downloading...
                </>
              ) : (
                <>
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Download
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export type { ExportDialogProps }
