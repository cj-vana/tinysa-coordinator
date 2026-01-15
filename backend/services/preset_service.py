"""
Service layer for FrequencyPreset CRUD operations.

Uses async SQLAlchemy for database operations.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import FrequencyPreset
from backend.schemas.preset import FrequencyPresetCreate, FrequencyPresetUpdate


class PresetService:
    """Service class for preset CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[FrequencyPreset]:
        """
        Get all presets ordered by category then name.

        Returns:
            List of all presets sorted alphabetically within each category.
        """
        result = await self.session.execute(
            select(FrequencyPreset).order_by(
                FrequencyPreset.category, FrequencyPreset.name
            )
        )
        return list(result.scalars().all())

    async def get_by_id(self, preset_id: int) -> Optional[FrequencyPreset]:
        """
        Get a single preset by ID.

        Args:
            preset_id: The preset's primary key.

        Returns:
            The preset if found, None otherwise.
        """
        result = await self.session.execute(
            select(FrequencyPreset).where(FrequencyPreset.id == preset_id)
        )
        return result.scalar_one_or_none()

    async def create(self, preset_data: FrequencyPresetCreate) -> FrequencyPreset:
        """
        Create a new preset.

        Args:
            preset_data: Pydantic schema with preset fields.

        Returns:
            The newly created preset.
        """
        preset = FrequencyPreset(
            name=preset_data.name,
            description=preset_data.description,
            start_freq_hz=preset_data.start_freq_hz,
            stop_freq_hz=preset_data.stop_freq_hz,
            points=preset_data.points,
            rbw_khz=preset_data.rbw_khz,
            category=preset_data.category.value,
            is_builtin=False,
        )
        self.session.add(preset)
        await self.session.flush()
        await self.session.refresh(preset)
        return preset

    async def update(
        self, preset_id: int, preset_data: FrequencyPresetUpdate
    ) -> Optional[FrequencyPreset]:
        """
        Update an existing preset.

        Args:
            preset_id: The preset's primary key.
            preset_data: Pydantic schema with fields to update.

        Returns:
            The updated preset if found, None otherwise.

        Note:
            Built-in presets cannot be updated (checked at route level).
        """
        preset = await self.get_by_id(preset_id)
        if not preset:
            return None

        update_data = preset_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "category" and value is not None:
                setattr(preset, field, value.value)
            else:
                setattr(preset, field, value)

        await self.session.flush()
        await self.session.refresh(preset)
        return preset

    async def delete(self, preset_id: int) -> bool:
        """
        Delete a preset by ID.

        Args:
            preset_id: The preset's primary key.

        Returns:
            True if deleted, False if not found.

        Note:
            Built-in presets cannot be deleted (checked at route level).
        """
        preset = await self.get_by_id(preset_id)
        if not preset:
            return False

        await self.session.delete(preset)
        await self.session.flush()
        return True

    async def get_by_category(self, category: str) -> list[FrequencyPreset]:
        """
        Get all presets in a specific category.

        Args:
            category: The category to filter by (UHF, VHF, ISM, Custom).

        Returns:
            List of presets in the specified category.
        """
        result = await self.session.execute(
            select(FrequencyPreset)
            .where(FrequencyPreset.category == category)
            .order_by(FrequencyPreset.name)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Get total count of presets.

        Returns:
            Total number of presets in the database.
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count()).select_from(FrequencyPreset)
        )
        return result.scalar() or 0
