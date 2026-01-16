"""
Service layer for FrequencyPreset CRUD operations.

Uses async SQLAlchemy for database operations.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import FrequencyPreset
from backend.schemas.preset import FrequencyPresetCreate, FrequencyPresetUpdate

logger = logging.getLogger(__name__)


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
        logger.debug("Fetching all presets")
        result = await self.session.execute(
            select(FrequencyPreset).order_by(
                FrequencyPreset.category, FrequencyPreset.name
            )
        )
        presets = list(result.scalars().all())
        logger.debug(f"Retrieved {len(presets)} presets")
        return presets

    async def get_by_id(self, preset_id: int) -> Optional[FrequencyPreset]:
        """
        Get a single preset by ID.

        Args:
            preset_id: The preset's primary key.

        Returns:
            The preset if found, None otherwise.
        """
        logger.debug(f"Fetching preset by id={preset_id}")
        result = await self.session.execute(
            select(FrequencyPreset).where(FrequencyPreset.id == preset_id)
        )
        preset = result.scalar_one_or_none()
        if preset:
            logger.debug(f"Found preset: name={preset.name}")
        else:
            logger.debug(f"Preset not found: id={preset_id}")
        return preset

    async def create(self, preset_data: FrequencyPresetCreate) -> FrequencyPreset:
        """
        Create a new preset.

        Args:
            preset_data: Pydantic schema with preset fields.

        Returns:
            The newly created preset.
        """
        logger.info(
            f"Creating preset: name={preset_data.name}, category={preset_data.category.value}, "
            f"range={preset_data.start_freq_hz}-{preset_data.stop_freq_hz} Hz"
        )
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
        logger.info(f"Created preset: id={preset.id}, name={preset.name}")
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
        logger.debug(f"Updating preset: id={preset_id}")
        preset = await self.get_by_id(preset_id)
        if not preset:
            logger.warning(f"Cannot update preset: id={preset_id} not found")
            return None

        update_data = preset_data.model_dump(exclude_unset=True)
        updated_fields = list(update_data.keys())
        for field, value in update_data.items():
            if field == "category" and value is not None:
                setattr(preset, field, value.value)
            else:
                setattr(preset, field, value)

        await self.session.flush()
        await self.session.refresh(preset)
        logger.info(f"Updated preset: id={preset_id}, fields={updated_fields}")
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
        logger.debug(f"Deleting preset: id={preset_id}")
        preset = await self.get_by_id(preset_id)
        if not preset:
            logger.warning(f"Cannot delete preset: id={preset_id} not found")
            return False

        preset_name = preset.name
        await self.session.delete(preset)
        await self.session.flush()
        logger.info(f"Deleted preset: id={preset_id}, name={preset_name}")
        return True

    async def get_by_category(self, category: str) -> list[FrequencyPreset]:
        """
        Get all presets in a specific category.

        Args:
            category: The category to filter by (UHF, VHF, ISM, Custom).

        Returns:
            List of presets in the specified category.
        """
        logger.debug(f"Fetching presets by category={category}")
        result = await self.session.execute(
            select(FrequencyPreset)
            .where(FrequencyPreset.category == category)
            .order_by(FrequencyPreset.name)
        )
        presets = list(result.scalars().all())
        logger.debug(f"Found {len(presets)} presets in category={category}")
        return presets

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
        count = result.scalar() or 0
        logger.debug(f"Total preset count: {count}")
        return count
