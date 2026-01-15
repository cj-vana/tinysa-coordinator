import { useState } from 'react'
import {
  Preset,
  PresetCategory,
  useDeletePreset,
  usePresets,
} from '../../hooks/usePresets'
import PresetCard from './PresetCard'
import PresetForm from './PresetForm'

interface PresetListProps {
  onSelectPreset?: (preset: Preset) => void
  selectedPresetId?: number | null
}

const CATEGORIES: (PresetCategory | 'All')[] = ['All', 'UHF', 'VHF', 'ISM', 'Custom']

export default function PresetList({ onSelectPreset, selectedPresetId }: PresetListProps) {
  const [filterCategory, setFilterCategory] = useState<PresetCategory | undefined>(undefined)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingPreset, setEditingPreset] = useState<Preset | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<Preset | null>(null)

  const { data, isLoading, error } = usePresets(filterCategory)
  const deleteMutation = useDeletePreset()

  const handleEdit = (preset: Preset) => {
    setEditingPreset(preset)
    setIsFormOpen(true)
  }

  const handleDelete = (preset: Preset) => {
    setDeleteConfirm(preset)
  }

  const confirmDelete = async () => {
    if (deleteConfirm) {
      await deleteMutation.mutateAsync(deleteConfirm.id)
      setDeleteConfirm(null)
    }
  }

  const handleFormClose = () => {
    setIsFormOpen(false)
    setEditingPreset(null)
  }

  const handleAddNew = () => {
    setEditingPreset(null)
    setIsFormOpen(true)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg bg-red-900/30 border border-red-700 text-red-200">
        Failed to load presets: {error.message}
      </div>
    )
  }

  const presets = data?.items || []

  return (
    <div className="space-y-4">
      {/* Header with filters and add button */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">Filter:</span>
          <div className="flex gap-1">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat === 'All' ? undefined : cat)}
                className={`
                  px-3 py-1 text-sm rounded-lg transition-colors
                  ${(cat === 'All' && !filterCategory) || cat === filterCategory
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }
                `}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleAddNew}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center gap-2"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Preset
        </button>
      </div>

      {/* Preset grid */}
      {presets.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>No presets found.</p>
          <button
            onClick={handleAddNew}
            className="mt-2 text-blue-400 hover:text-blue-300"
          >
            Create your first preset
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {presets.map((preset) => (
            <PresetCard
              key={preset.id}
              preset={preset}
              isSelected={selectedPresetId === preset.id}
              onSelect={onSelectPreset}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Create/Edit Form Modal */}
      <PresetForm
        preset={editingPreset}
        isOpen={isFormOpen}
        onClose={handleFormClose}
      />

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setDeleteConfirm(null)}
          />
          <div className="relative bg-gray-800 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold text-white mb-2">Delete Preset</h3>
            <p className="text-gray-300 mb-4">
              Are you sure you want to delete "{deleteConfirm.name}"? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white transition-colors disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
