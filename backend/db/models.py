"""
SQLAlchemy ORM models for the frequency scanner application.

Uses SQLAlchemy 2.0 style with Mapped[] type hints.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


class FrequencyPreset(Base):
    """
    Predefined frequency ranges for common use cases.

    Presets can be built-in (shipped with the app) or user-created.
    Categories help organize presets by frequency band type.
    """

    __tablename__ = "frequency_presets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Frequency range in Hz (use BigInteger for frequencies up to ~6GHz)
    start_freq_hz: Mapped[int] = mapped_column(BigInteger, nullable=False)
    stop_freq_hz: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Scan parameters
    points: Mapped[int] = mapped_column(default=450, nullable=False)
    rbw_khz: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Organization
    category: Mapped[str] = mapped_column(
        String(20), default="Custom", nullable=False
    )  # UHF, VHF, ISM, Custom
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to scans that used this preset
    scans: Mapped[list["SavedScan"]] = relationship(
        "SavedScan", back_populates="preset", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<FrequencyPreset(id={self.id}, name='{self.name}', "
            f"range={self.start_freq_hz/1e6:.3f}-{self.stop_freq_hz/1e6:.3f} MHz)>"
        )


class SavedScan(Base):
    """
    A saved frequency scan with metadata.

    Each scan captures a snapshot of the RF environment at a specific
    time and location. The scan parameters are stored both as a reference
    to the preset used (if any) and as explicit values to preserve the
    exact configuration even if the preset is later modified.
    """

    __tablename__ = "saved_scans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Scan parameters (stored explicitly for historical accuracy)
    start_freq_hz: Mapped[int] = mapped_column(BigInteger, nullable=False)
    stop_freq_hz: Mapped[int] = mapped_column(BigInteger, nullable=False)
    points: Mapped[int] = mapped_column(nullable=False)
    rbw_khz: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Preset reference (optional - scan may have used custom parameters)
    preset_id: Mapped[int | None] = mapped_column(
        ForeignKey("frequency_presets.id", ondelete="SET NULL"), nullable=True
    )
    preset_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # Snapshot of preset name at scan time

    # Metadata
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # Comma-separated tags

    # Timing
    scan_started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    scan_completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Relationships
    preset: Mapped[Optional["FrequencyPreset"]] = relationship(
        "FrequencyPreset", back_populates="scans", lazy="selectin"
    )
    data_points: Mapped[list["ScanDataPoint"]] = relationship(
        "ScanDataPoint",
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ScanDataPoint.index",
    )

    def __repr__(self) -> str:
        return (
            f"<SavedScan(id={self.id}, name='{self.name}', "
            f"range={self.start_freq_hz/1e6:.3f}-{self.stop_freq_hz/1e6:.3f} MHz, "
            f"points={len(self.data_points) if self.data_points else 0})>"
        )

    @property
    def duration_seconds(self) -> float | None:
        """Calculate scan duration if both timestamps are available."""
        if self.scan_started_at and self.scan_completed_at:
            return (self.scan_completed_at - self.scan_started_at).total_seconds()
        return None

    @property
    def tag_list(self) -> list[str]:
        """Parse tags string into a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]


class ScanDataPoint(Base):
    """
    Individual data point within a saved scan.

    Each point represents the measured signal amplitude at a specific
    frequency. Points are indexed for ordering and efficient retrieval.
    """

    __tablename__ = "scan_data_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(
        ForeignKey("saved_scans.id", ondelete="CASCADE"), nullable=False
    )

    # Data point values
    index: Mapped[int] = mapped_column(nullable=False)  # Position in scan (0-based)
    frequency_hz: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amplitude_dbm: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationship
    scan: Mapped["SavedScan"] = relationship("SavedScan", back_populates="data_points")

    # Index for efficient queries by scan_id
    __table_args__ = (
        Index("ix_scan_data_points_scan_id", "scan_id"),
        Index("ix_scan_data_points_scan_id_index", "scan_id", "index"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScanDataPoint(id={self.id}, scan_id={self.scan_id}, "
            f"idx={self.index}, freq={self.frequency_hz/1e6:.3f} MHz, "
            f"amp={self.amplitude_dbm:.1f} dBm)>"
        )
