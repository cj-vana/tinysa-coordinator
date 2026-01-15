/**
 * HistoryPage - Browse, search, and manage saved frequency scans.
 */

import { useState } from 'react'
import { useDeleteScan } from '../hooks/useHistory'
import ScanHistoryList from '../components/history/ScanHistoryList'
import ScanDetail from '../components/history/ScanDetail'

export default function HistoryPage() {
  const [selectedScanId, setSelectedScanId] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const deleteMutation = useDeleteScan()

  const handleSelectScan = (id: number) => {
    setSelectedScanId(id)
  }

  const handleCloseScan = () => {
    setSelectedScanId(null)
  }

  const handleDeleteRequest = (id: number) => {
    setDeleteConfirm(id)
  }

  const handleDeleteConfirm = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm, {
        onSuccess: () => {
          if (selectedScanId === deleteConfirm) {
            setSelectedScanId(null)
          }
          setDeleteConfirm(null)
        },
      })
    }
  }

  const handleDeleteCancel = () => {
    setDeleteConfirm(null)
  }

  return (
    <div className="p-6 h-[calc(100vh-4rem)]">
      {/* Header with search */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Scan History</h1>
          <p className="text-gray-400 text-sm mt-1">
            View and manage your saved frequency scans
          </p>
        </div>

        {/* Search box */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search scans..."
            className="w-64 px-4 py-2 pl-10 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Main content area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100%-5rem)]">
        {/* Scan list */}
        <div className="overflow-auto">
          <ScanHistoryList
            onSelectScan={handleSelectScan}
            onDeleteScan={handleDeleteRequest}
            selectedScanId={selectedScanId}
            searchQuery={searchQuery}
          />
        </div>

        {/* Detail panel */}
        <div className="overflow-auto">
          {selectedScanId ? (
            <ScanDetail scanId={selectedScanId} onClose={handleCloseScan} />
          ) : (
            <div className="bg-gray-800 rounded-lg h-full flex items-center justify-center">
              <div className="text-center text-gray-400">
                <svg
                  className="w-16 h-16 mx-auto mb-4 text-gray-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
                <p>Select a scan to view details</p>
                <p className="text-sm text-gray-500 mt-1">
                  Click on any scan in the list to see its data
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={handleDeleteCancel}
        >
          <div
            className="bg-gray-800 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-600/20 rounded-full">
                <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white">Delete Scan</h3>
            </div>

            <p className="text-gray-300 mb-6">
              Are you sure you want to delete this scan? This action cannot be undone.
            </p>

            <div className="flex justify-end gap-3">
              <button
                onClick={handleDeleteCancel}
                className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
                disabled={deleteMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {deleteMutation.isPending && (
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                )}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
