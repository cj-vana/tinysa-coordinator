/**
 * ScanHistoryList - Table view of saved scans with sorting and pagination.
 */

import { useState, useMemo } from 'react'
import { useScans, ScanListParams, SavedScanSummary } from '../../hooks/useHistory'
import ScanHistoryRow from './ScanHistoryRow'

interface ScanHistoryListProps {
  onSelectScan: (id: number) => void
  onDeleteScan: (id: number) => void
  selectedScanId: number | null
  searchQuery: string
}

type SortColumn = 'name' | 'created_at' | 'start_freq_hz' | 'location'
type SortOrder = 'asc' | 'desc'

const ITEMS_PER_PAGE = 10

interface SortIconProps {
  column: SortColumn
  sortBy: SortColumn
  sortOrder: SortOrder
}

function SortIcon({ column, sortBy, sortOrder }: SortIconProps) {
  if (sortBy !== column) {
    return (
      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
      </svg>
    )
  }
  return sortOrder === 'asc' ? (
    <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ) : (
    <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  )
}

export default function ScanHistoryList({
  onSelectScan,
  onDeleteScan,
  selectedScanId,
  searchQuery,
}: ScanHistoryListProps) {
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<SortColumn>('created_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const params: ScanListParams = useMemo(
    () => ({
      page,
      per_page: ITEMS_PER_PAGE,
      search: searchQuery || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    }),
    [page, searchQuery, sortBy, sortOrder]
  )

  const { data, isLoading, error } = useScans(params)

  const handleSort = (column: SortColumn) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
    setPage(1) // Reset to first page when sorting changes
  }

  const totalPages = data ? Math.ceil(data.total / ITEMS_PER_PAGE) : 0

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-400">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading scans...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-8">
        <div className="text-red-400 flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Failed to load scans: {(error as Error).message}
        </div>
      </div>
    )
  }

  if (!data?.items.length) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-gray-400 mb-2">No scans found</p>
        <p className="text-gray-500 text-sm">
          {searchQuery ? 'Try a different search term' : 'Save a scan to see it here'}
        </p>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700/50">
            <tr>
              <th
                className="px-4 py-3 text-left text-sm font-medium text-gray-300 cursor-pointer hover:bg-gray-700"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-2">
                  Name
                  <SortIcon column="name" sortBy={sortBy} sortOrder={sortOrder} />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-medium text-gray-300 cursor-pointer hover:bg-gray-700"
                onClick={() => handleSort('start_freq_hz')}
              >
                <div className="flex items-center gap-2">
                  Frequency Range
                  <SortIcon column="start_freq_hz" sortBy={sortBy} sortOrder={sortOrder} />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-medium text-gray-300 cursor-pointer hover:bg-gray-700"
                onClick={() => handleSort('location')}
              >
                <div className="flex items-center gap-2">
                  Location
                  <SortIcon column="location" sortBy={sortBy} sortOrder={sortOrder} />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-sm font-medium text-gray-300 cursor-pointer hover:bg-gray-700"
                onClick={() => handleSort('created_at')}
              >
                <div className="flex items-center gap-2">
                  Date
                  <SortIcon column="created_at" sortBy={sortBy} sortOrder={sortOrder} />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((scan: SavedScanSummary) => (
              <ScanHistoryRow
                key={scan.id}
                scan={scan}
                onSelect={onSelectScan}
                onDelete={onDeleteScan}
                isSelected={selectedScanId === scan.id}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-700">
          <div className="text-sm text-gray-400">
            Showing {(page - 1) * ITEMS_PER_PAGE + 1} to{' '}
            {Math.min(page * ITEMS_PER_PAGE, data.total)} of {data.total} scans
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-sm bg-gray-700 text-gray-300 rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 text-sm bg-gray-700 text-gray-300 rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
