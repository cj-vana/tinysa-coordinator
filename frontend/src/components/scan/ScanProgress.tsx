/**
 * ScanProgress component for displaying scan progress and status.
 * Shows progress bar, point count, and completion time.
 */

interface ScanProgressProps {
  progress: number;
  totalPoints: number;
  currentPoints: number;
  isScanning: boolean;
  scanDuration: number | null;
  error: string | null;
}

export default function ScanProgress({
  progress,
  totalPoints,
  currentPoints,
  isScanning,
  scanDuration,
  error,
}: ScanProgressProps) {
  // Format duration in seconds with one decimal
  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-300">
            {isScanning ? 'Scanning...' : progress === 100 ? 'Complete' : 'Ready'}
          </span>
          <span className="text-sm text-gray-400">{progress}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-150 ${
              isScanning
                ? 'bg-blue-500'
                : progress === 100
                ? 'bg-green-500'
                : 'bg-gray-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-gray-400">Points: </span>
          <span className="text-white font-medium">
            {currentPoints} / {totalPoints || '-'}
          </span>
        </div>
        {scanDuration !== null && (
          <div>
            <span className="text-gray-400">Duration: </span>
            <span className="text-white font-medium">
              {formatDuration(scanDuration)}
            </span>
          </div>
        )}
        {isScanning && totalPoints > 0 && (
          <div>
            <span className="text-gray-400">Rate: </span>
            <span className="text-white font-medium">
              {currentPoints > 0
                ? `~${Math.round((currentPoints / (progress / 100)) / (Date.now() - (Date.now() - 1000)) * 1000)} pts/s`
                : '-'}
            </span>
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="mt-3 p-3 bg-red-900/30 border border-red-700 rounded-md">
          <div className="flex items-start gap-2">
            <svg
              className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <p className="text-red-400 font-medium text-sm">Scan Error</p>
              <p className="text-red-300 text-sm mt-0.5">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
