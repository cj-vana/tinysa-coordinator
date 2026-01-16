"""
Pydantic schemas for FrequencyPreset API serialization.

These models handle request/response validation for the preset endpoints.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PresetCategory(str, Enum):
    """Valid categories for frequency presets."""

    UHF = "UHF"
    VHF = "VHF"
    ISM = "ISM"
    CUSTOM = "Custom"


class FrequencyPresetBase(BaseModel):
    """Base schema with common preset fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Preset name")
    description: str | None = Field(None, description="Optional description")
    start_freq_hz: int = Field(
        ..., gt=0, description="Start frequency in Hz (must be positive)"
    )
    stop_freq_hz: int = Field(
        ..., gt=0, description="Stop frequency in Hz (must be greater than start)"
    )
    points: int = Field(
        default=450, ge=10, le=10000, description="Number of scan points"
    )
    rbw_khz: float | None = Field(
        None, gt=0, description="Resolution bandwidth in kHz"
    )
    category: PresetCategory = Field(
        default=PresetCategory.CUSTOM, description="Preset category"
    )

    @field_validator("stop_freq_hz")
    @classmethod
    def stop_must_be_greater_than_start(cls, v: int, info) -> int:
        """Ensure stop frequency is greater than start frequency."""
        start = info.data.get("start_freq_hz")
        if start is not None and v <= start:
            raise ValueError("stop_freq_hz must be greater than start_freq_hz")
        return v


class FrequencyPresetCreate(FrequencyPresetBase):
    """Schema for creating a new preset."""

    pass


class FrequencyPresetUpdate(BaseModel):
    """Schema for updating an existing preset (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    start_freq_hz: int | None = Field(None, gt=0)
    stop_freq_hz: int | None = Field(None, gt=0)
    points: int | None = Field(None, ge=10, le=10000)
    rbw_khz: float | None = Field(None, gt=0)
    category: PresetCategory | None = None


class FrequencyPresetResponse(FrequencyPresetBase):
    """Schema for preset responses (includes ID and timestamps)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_builtin: bool = False
    created_at: datetime
    updated_at: datetime


class FrequencyPresetSummary(BaseModel):
    """Minimal preset info for lists and references."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: PresetCategory
    start_freq_hz: int
    stop_freq_hz: int
    is_builtin: bool

    @property
    def frequency_range_mhz(self) -> str:
        """Human-readable frequency range."""
        return f"{self.start_freq_hz / 1e6:.3f} - {self.stop_freq_hz / 1e6:.3f} MHz"


class FrequencyPresetList(BaseModel):
    """Paginated list of presets."""

    items: list[FrequencyPresetSummary]
    total: int
    page: int = 1
    per_page: int = 20
