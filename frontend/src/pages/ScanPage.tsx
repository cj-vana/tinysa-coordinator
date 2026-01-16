/**
 * ScanPage - Main page for running frequency scans on the TinySA Ultra.
 * Integrates scan controls, frequency chart, and progress display.
 */

import { useScanData } from '../hooks/useScanData';
import ScanControls from '../components/scan/ScanControls';
import FrequencyChart from '../components/scan/FrequencyChart';
import ScanProgress from '../components/scan/ScanProgress';
import WebSocketStatusIndicator from '../components/scan/WebSocketStatusIndicator';

export default function ScanPage() {
  const {
    scanData,
    isScanning,
    progress,
    totalPoints,
    wsStatus,
    error,
    scanDuration,
    reconnectionState,
    startScan,
    stopScan,
    connect,
    peakPoint,
  } = useScanData();

  return (
    <div className="p-6 h-[calc(100vh-4rem)]">
      {/* WebSocket connection status banner */}
      <div className="mb-4">
        <WebSocketStatusIndicator
          status={wsStatus}
          reconnectionState={reconnectionState}
          onReconnect={connect}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
        {/* Left sidebar - Controls */}
        <div className="lg:col-span-1 space-y-4">
          <ScanControls
            onStartScan={startScan}
            onStopScan={stopScan}
            isScanning={isScanning}
            wsStatus={wsStatus}
          />
          <ScanProgress
            progress={progress}
            totalPoints={totalPoints}
            currentPoints={scanData.length}
            isScanning={isScanning}
            scanDuration={scanDuration}
            error={error}
          />
        </div>

        {/* Main area - Chart */}
        <div className="lg:col-span-3 min-h-[400px]">
          <FrequencyChart
            data={scanData}
            peakPoint={peakPoint}
            isScanning={isScanning}
          />
        </div>
      </div>
    </div>
  );
}
