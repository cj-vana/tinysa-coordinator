"""
API routes for frequency preset management.

Provides CRUD operations for frequency presets with protection for built-in presets.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import BuiltinPresetModificationError, PresetNotFoundError
from backend.core.rate_limit import get_limiter, get_rate_limit_config
from backend.db.database import get_async_session
from backend.schemas.preset import (
    FrequencyPresetCreate,
    FrequencyPresetResponse,
    FrequencyPresetUpdate,
)
from backend.services.preset_service import PresetService

limiter = get_limiter()
rate_config = get_rate_limit_config()

router = APIRouter(prefix="/api/presets", tags=["presets"])


async def get_preset_service(
    session: AsyncSession = Depends(get_async_session),
) -> PresetService:
    """Dependency to get PresetService instance."""
    return PresetService(session)


@router.get("/", response_model=list[FrequencyPresetResponse])
@limiter.limit(rate_config.preset_limit)
async def list_presets(
    request: Request,
    service: PresetService = Depends(get_preset_service),
) -> list[FrequencyPresetResponse]:
    """
    List all frequency presets.

    Returns presets ordered by category (UHF, VHF, ISM, Custom) then by name.
    """
    presets = await service.get_all()
    return [FrequencyPresetResponse.model_validate(p) for p in presets]


@router.post("/", response_model=FrequencyPresetResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(rate_config.preset_limit)
async def create_preset(
    request: Request,
    preset_data: FrequencyPresetCreate,
    service: PresetService = Depends(get_preset_service),
) -> FrequencyPresetResponse:
    """
    Create a new frequency preset.

    The preset will be marked as non-built-in (user-created).
    """
    preset = await service.create(preset_data)
    return FrequencyPresetResponse.model_validate(preset)


@router.get("/{preset_id}", response_model=FrequencyPresetResponse)
@limiter.limit(rate_config.preset_limit)
async def get_preset(
    request: Request,
    preset_id: int,
    service: PresetService = Depends(get_preset_service),
) -> FrequencyPresetResponse:
    """
    Get a specific frequency preset by ID.

    Raises 404 if the preset is not found.
    """
    preset = await service.get_by_id(preset_id)
    if not preset:
        raise PresetNotFoundError(preset_id=preset_id)
    return FrequencyPresetResponse.model_validate(preset)


@router.put("/{preset_id}", response_model=FrequencyPresetResponse)
@limiter.limit(rate_config.preset_limit)
async def update_preset(
    request: Request,
    preset_id: int,
    preset_data: FrequencyPresetUpdate,
    service: PresetService = Depends(get_preset_service),
) -> FrequencyPresetResponse:
    """
    Update an existing frequency preset.

    Built-in presets cannot be modified. Attempting to update a built-in
    preset will result in a 403 Forbidden error.

    Raises 404 if the preset is not found.
    """
    existing = await service.get_by_id(preset_id)
    if not existing:
        raise PresetNotFoundError(preset_id=preset_id)

    if existing.is_builtin:
        raise BuiltinPresetModificationError(operation="modify", preset_id=preset_id)

    preset = await service.update(preset_id, preset_data)
    return FrequencyPresetResponse.model_validate(preset)


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_config.preset_limit)
async def delete_preset(
    request: Request,
    preset_id: int,
    service: PresetService = Depends(get_preset_service),
) -> None:
    """
    Delete a frequency preset.

    Built-in presets cannot be deleted. Attempting to delete a built-in
    preset will result in a 403 Forbidden error.

    Raises 404 if the preset is not found.
    """
    existing = await service.get_by_id(preset_id)
    if not existing:
        raise PresetNotFoundError(preset_id=preset_id)

    if existing.is_builtin:
        raise BuiltinPresetModificationError(operation="delete", preset_id=preset_id)

    await service.delete(preset_id)
