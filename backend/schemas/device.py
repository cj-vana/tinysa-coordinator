"""Pydantic schemas for device-related data models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SerialPort(BaseModel):
    """Information about an available serial port."""

    port: str = Field(..., description="Serial port device path (e.g., /dev/cu.usbmodem4001)")
    description: str = Field("", description="Human-readable description of the port")
    hwid: str = Field("", description="Hardware ID for the port")
    manufacturer: str | None = Field(None, description="Device manufacturer if available")
    product: str | None = Field(None, description="Product name if available")
    serial_number: str | None = Field(None, description="Serial number if available")
    vid: int | None = Field(None, description="USB Vendor ID")
    pid: int | None = Field(None, description="USB Product ID")


class DeviceStatus(BaseModel):
    """Status information for a connected TinySA device."""

    connected: bool = Field(..., description="Whether the device is currently connected")
    port: str | None = Field(None, description="Serial port the device is connected to")
    version: str | None = Field(None, description="Firmware version string")
    hardware: str | None = Field(None, description="Hardware revision")
    device_type: str | None = Field(None, description="Device type (e.g., 'tinySA ULTRA')")


class DeviceInfo(BaseModel):
    """Detailed device information returned after connection."""

    version: str = Field(..., description="Firmware version string")
    hardware: str | None = Field(None, description="Hardware revision")
    device_type: str | None = Field(None, description="Device type identifier")
    port: str = Field(..., description="Connected serial port")


class ScanPoint(BaseModel):
    """A single point in a frequency scan."""

    frequency_hz: int = Field(..., description="Frequency in Hz")
    amplitude_dbm: float = Field(..., description="Amplitude in dBm")


class ScanConfig(BaseModel):
    """Configuration for a frequency scan."""

    start_hz: int = Field(..., ge=0, description="Start frequency in Hz")
    stop_hz: int = Field(..., ge=0, description="Stop frequency in Hz")
    points: int = Field(450, ge=10, le=10000, description="Number of scan points")
    rbw_khz: float | None = Field(None, ge=0.1, le=1000, description="Resolution bandwidth in kHz")
