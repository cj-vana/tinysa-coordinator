"""
Database seeding for built-in frequency presets.

Seeds the database with standard frequency presets for common
wireless microphone and ISM bands.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import FrequencyPreset


# Built-in presets configuration
# Frequencies are in Hz for database storage
BUILTIN_PRESETS = [
    {
        "name": "UHF TV Band",
        "description": "US wireless microphone range (470-698 MHz). "
        "Standard UHF band for professional wireless systems.",
        "start_freq_hz": 470_000_000,
        "stop_freq_hz": 698_000_000,
        "points": 450,
        "rbw_khz": None,
        "category": "UHF",
        "is_builtin": True,
    },
    {
        "name": "UHF Full",
        "description": "Extended UHF range (470-862 MHz). "
        "Covers full UHF band including international allocations.",
        "start_freq_hz": 470_000_000,
        "stop_freq_hz": 862_000_000,
        "points": 450,
        "rbw_khz": None,
        "category": "UHF",
        "is_builtin": True,
    },
    {
        "name": "VHF Band",
        "description": "VHF wireless microphone range (174-216 MHz). "
        "Used by VHF wireless systems and some broadcast equipment.",
        "start_freq_hz": 174_000_000,
        "stop_freq_hz": 216_000_000,
        "points": 450,
        "rbw_khz": None,
        "category": "VHF",
        "is_builtin": True,
    },
    {
        "name": "900 MHz ISM",
        "description": "ISM band (902-928 MHz). "
        "License-free band used by some wireless audio systems.",
        "start_freq_hz": 902_000_000,
        "stop_freq_hz": 928_000_000,
        "points": 450,
        "rbw_khz": None,
        "category": "ISM",
        "is_builtin": True,
    },
    {
        "name": "2.4 GHz ISM",
        "description": "WiFi/Bluetooth band (2400-2483 MHz). "
        "Used by digital wireless systems, WiFi, and Bluetooth.",
        "start_freq_hz": 2_400_000_000,
        "stop_freq_hz": 2_483_000_000,
        "points": 450,
        "rbw_khz": None,
        "category": "ISM",
        "is_builtin": True,
    },
    {
        "name": "DECT",
        "description": "DECT systems band (1880-1930 MHz). "
        "Used by DECT cordless phones and some wireless headsets.",
        "start_freq_hz": 1_880_000_000,
        "stop_freq_hz": 1_930_000_000,
        "points": 450,
        "rbw_khz": None,
        "category": "ISM",
        "is_builtin": True,
    },
]


async def seed_builtin_presets(session: AsyncSession) -> int:
    """
    Seed the database with built-in presets if they don't exist.

    This function is idempotent - it will only create presets that
    don't already exist (matched by name and is_builtin flag).

    Args:
        session: Async database session.

    Returns:
        Number of presets created.
    """
    created_count = 0

    for preset_data in BUILTIN_PRESETS:
        # Check if this preset already exists
        result = await session.execute(
            select(FrequencyPreset).where(
                FrequencyPreset.name == preset_data["name"],
                FrequencyPreset.is_builtin == True,  # noqa: E712
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            preset = FrequencyPreset(**preset_data)
            session.add(preset)
            created_count += 1

    await session.flush()
    return created_count


async def get_builtin_preset_count(session: AsyncSession) -> int:
    """
    Get the count of built-in presets in the database.

    Args:
        session: Async database session.

    Returns:
        Number of built-in presets.
    """
    from sqlalchemy import func

    result = await session.execute(
        select(func.count())
        .select_from(FrequencyPreset)
        .where(FrequencyPreset.is_builtin == True)  # noqa: E712
    )
    return result.scalar() or 0
