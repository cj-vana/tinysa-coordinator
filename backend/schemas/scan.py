"""
Pydantic schemas for SavedScan and ScanDataPoint API serialization.

These models handle request/response validation for scan-related endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanDataPointBase(BaseModel):
    """Base schema for scan data points."""

    index: int = Field(..., ge=0, description="Point index (0-based)")
    frequency_hz: int = Field(..., gt=0, description="Frequency in Hz")
    amplitude_dbm: float = Field(..., ge=-200, le=50, description="Signal amplitude in dBm")


class ScanDataPointCreate(ScanDataPointBase):
    """Schema for creating data points (typically in bulk with a scan)."""

    pass


class ScanDataPointResponse(ScanDataPointBase):
    """Schema for data point responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int


class SavedScanBase(BaseModel):
    """Base schema with common scan fields."""

    name: str = Field(..., min_length=1, max_length=200, description="Scan name")
    start_freq_hz: int = Field(..., gt=0, description="Start frequency in Hz")
    stop_freq_hz: int = Field(..., gt=0, description="Stop frequency in Hz")
    points: int = Field(..., ge=10, le=10000, description="Number of data points")
    rbw_khz: float | None = Field(None, gt=0, description="Resolution bandwidth in kHz")
    location: str | None = Field(None, max_length=200, description="Scan location")
    notes: str | None = Field(None, description="Additional notes")
    tags: str | None = Field(None, max_length=500, description="Comma-separated tags")

    @field_validator("stop_freq_hz")
    @classmethod
    def stop_must_be_greater_than_start(cls, v: int, info) -> int:
        """Ensure stop frequency is greater than start frequency."""
        start = info.data.get("start_freq_hz")
        if start is not None and v <= start:
            raise ValueError("stop_freq_hz must be greater than start_freq_hz")
        return v


class SavedScanCreate(SavedScanBase):
    """Schema for creating a new scan with data points."""

    preset_id: int | None = Field(None, description="ID of the preset used (if any)")
    preset_name: str | None = Field(None, max_length=100, description="Snapshot of preset name")
    scan_started_at: datetime | None = Field(None, description="When the scan started")
    scan_completed_at: datetime | None = Field(None, description="When the scan completed")
    data_points: list[ScanDataPointCreate] = Field(
        ..., min_length=1, description="Scan data points"
    )


class SavedScanUpdate(BaseModel):
    """Schema for updating scan metadata (not data points)."""

    name: str | None = Field(None, min_length=1, max_length=200)
    location: str | None = Field(None, max_length=200)
    notes: str | None = None
    tags: str | None = Field(None, max_length=500)


class SavedScanResponse(SavedScanBase):
    """Schema for scan responses without data points (for lists)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    preset_id: int | None = None
    preset_name: str | None = None
    scan_started_at: datetime | None = None
    scan_completed_at: datetime | None = None
    created_at: datetime
    data_point_count: int = Field(default=0, description="Number of data points in this scan")

    @classmethod
    def from_orm_with_count(cls, scan, count: int) -> "SavedScanResponse":
        """Create response from ORM model with explicit point count."""
        return cls(
            id=scan.id,
            name=scan.name,
            start_freq_hz=scan.start_freq_hz,
            stop_freq_hz=scan.stop_freq_hz,
            points=scan.points,
            rbw_khz=scan.rbw_khz,
            preset_id=scan.preset_id,
            preset_name=scan.preset_name,
            location=scan.location,
            notes=scan.notes,
            tags=scan.tags,
            scan_started_at=scan.scan_started_at,
            scan_completed_at=scan.scan_completed_at,
            created_at=scan.created_at,
            data_point_count=count,
        )


class SavedScanDetail(SavedScanResponse):
    """Full scan response including all data points."""

    data_points: list[ScanDataPointResponse] = Field(
        default_factory=list, description="All scan data points"
    )


class SavedScanSummary(BaseModel):
    """Minimal scan info for lists."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_freq_hz: int
    stop_freq_hz: int
    points: int
    preset_name: str | None = None
    location: str | None = None
    scan_completed_at: datetime | None = None
    created_at: datetime

    @property
    def frequency_range_mhz(self) -> str:
        """Human-readable frequency range."""
        return f"{self.start_freq_hz / 1e6:.3f} - {self.stop_freq_hz / 1e6:.3f} MHz"


class SavedScanList(BaseModel):
    """Paginated list of scans."""

    items: list[SavedScanSummary]
    total: int
    page: int = 1
    per_page: int = 20


class ScanExportFormat(BaseModel):
    """Schema for specifying export format."""

    format: str = Field(
        ...,
        pattern="^(wwb|wsm|csv)$",
        description="Export format: wwb, wsm, or csv",
    )


class ScanDataForExport(BaseModel):
    """Minimal data structure for scan export."""

    name: str
    start_freq_hz: int
    stop_freq_hz: int
    points: list[tuple[int, float]]  # List of (frequency_hz, amplitude_dbm) tuples
    location: str | None = None
    scan_completed_at: datetime | None = None
