import { useState } from 'react'
import {
  Preset,
  PresetCategory,
  PresetCreate,
  useCreatePreset,
  useUpdatePreset,
} from '../../hooks/usePresets'

interface PresetFormProps {
  preset?: Preset | null
  isOpen: boolean
  onClose: () => void
  onSuccess?: (preset: Preset) => void
}

interface FormData {
  name: string
  description: string
  start_freq_mhz: string
  stop_freq_mhz: string
  points: string
  rbw_khz: string
  category: PresetCategory
}

interface FormErrors {
  name?: string
  start_freq_mhz?: string
  stop_freq_mhz?: string
  points?: string
  rbw_khz?: string
  general?: string
}

const CATEGORIES: PresetCategory[] = ['UHF', 'VHF', 'ISM', 'Custom']

/**
 * Get initial form data from preset or defaults
 */
function getInitialFormData(preset?: Preset | null): FormData {
  if (preset) {
    return {
      name: preset.name,
      description: preset.description || '',
      start_freq_mhz: (preset.start_freq_hz / 1e6).toString(),
      stop_freq_mhz: (preset.stop_freq_hz / 1e6).toString(),
      points: preset.points.toString(),
      rbw_khz: preset.rbw_khz?.toString() || '',
      category: preset.category,
    }
  }
  return {
    name: '',
    description: '',
    start_freq_mhz: '',
    stop_freq_mhz: '',
    points: '450',
    rbw_khz: '',
    category: 'Custom',
  }
}

/**
 * Inner form component - uses key prop from parent to reset state
 */
function PresetFormInner({ preset, onClose, onSuccess }: Omit<PresetFormProps, 'isOpen'>) {
  // Initialize state directly from props - parent uses key to force remount
  const [formData, setFormData] = useState<FormData>(() => getInitialFormData(preset))
  const [errors, setErrors] = useState<FormErrors>({})

  const createMutation = useCreatePreset()
  const updateMutation = useUpdatePreset()

  const isEditing = !!preset
  const isSubmitting = createMutation.isPending || updateMutation.isPending

  const validate = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }

    const startFreq = parseFloat(formData.start_freq_mhz)
    const stopFreq = parseFloat(formData.stop_freq_mhz)

    if (isNaN(startFreq) || startFreq <= 0) {
      newErrors.start_freq_mhz = 'Start frequency must be a positive number'
    }

    if (isNaN(stopFreq) || stopFreq <= 0) {
      newErrors.stop_freq_mhz = 'Stop frequency must be a positive number'
    }

    if (!newErrors.start_freq_mhz && !newErrors.stop_freq_mhz && stopFreq <= startFreq) {
      newErrors.stop_freq_mhz = 'Stop frequency must be greater than start frequency'
    }

    const points = parseInt(formData.points)
    if (isNaN(points) || points < 10 || points > 10000) {
      newErrors.points = 'Points must be between 10 and 10,000'
    }

    if (formData.rbw_khz) {
      const rbw = parseFloat(formData.rbw_khz)
      if (isNaN(rbw) || rbw <= 0) {
        newErrors.rbw_khz = 'RBW must be a positive number'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    const data: PresetCreate = {
      name: formData.name.trim(),
      description: formData.description.trim() || null,
      start_freq_hz: Math.round(parseFloat(formData.start_freq_mhz) * 1e6),
      stop_freq_hz: Math.round(parseFloat(formData.stop_freq_mhz) * 1e6),
      points: parseInt(formData.points),
      rbw_khz: formData.rbw_khz ? parseFloat(formData.rbw_khz) : null,
      category: formData.category,
    }

    try {
      let result: Preset
      if (isEditing && preset) {
        result = await updateMutation.mutateAsync({ id: preset.id, data })
      } else {
        result = await createMutation.mutateAsync(data)
      }
      onSuccess?.(result)
      onClose()
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'An error occurred',
      })
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    // Clear field error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gray-800 px-6 py-4 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">
            {isEditing ? 'Edit Preset' : 'Create Preset'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errors.general && (
            <div className="p-3 rounded bg-red-900/50 border border-red-700 text-red-200 text-sm">
              {errors.general}
            </div>
          )}

          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
              Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className={`
                w-full px-3 py-2 rounded-lg bg-gray-700 border text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500
                ${errors.name ? 'border-red-500' : 'border-gray-600'}
              `}
              placeholder="My Preset"
            />
            {errors.name && <p className="mt-1 text-sm text-red-400">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={2}
              className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional description..."
            />
          </div>

          {/* Frequency Range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="start_freq_mhz"
                className="block text-sm font-medium text-gray-300 mb-1"
              >
                Start Freq (MHz) *
              </label>
              <input
                type="number"
                id="start_freq_mhz"
                name="start_freq_mhz"
                value={formData.start_freq_mhz}
                onChange={handleChange}
                step="0.001"
                min="0"
                className={`
                  w-full px-3 py-2 rounded-lg bg-gray-700 border text-white
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${errors.start_freq_mhz ? 'border-red-500' : 'border-gray-600'}
                `}
                placeholder="470.000"
              />
              {errors.start_freq_mhz && (
                <p className="mt-1 text-sm text-red-400">{errors.start_freq_mhz}</p>
              )}
            </div>
            <div>
              <label
                htmlFor="stop_freq_mhz"
                className="block text-sm font-medium text-gray-300 mb-1"
              >
                Stop Freq (MHz) *
              </label>
              <input
                type="number"
                id="stop_freq_mhz"
                name="stop_freq_mhz"
                value={formData.stop_freq_mhz}
                onChange={handleChange}
                step="0.001"
                min="0"
                className={`
                  w-full px-3 py-2 rounded-lg bg-gray-700 border text-white
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${errors.stop_freq_mhz ? 'border-red-500' : 'border-gray-600'}
                `}
                placeholder="698.000"
              />
              {errors.stop_freq_mhz && (
                <p className="mt-1 text-sm text-red-400">{errors.stop_freq_mhz}</p>
              )}
            </div>
          </div>

          {/* Points and RBW */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="points" className="block text-sm font-medium text-gray-300 mb-1">
                Points
              </label>
              <input
                type="number"
                id="points"
                name="points"
                value={formData.points}
                onChange={handleChange}
                min="10"
                max="10000"
                className={`
                  w-full px-3 py-2 rounded-lg bg-gray-700 border text-white
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${errors.points ? 'border-red-500' : 'border-gray-600'}
                `}
                placeholder="450"
              />
              {errors.points && <p className="mt-1 text-sm text-red-400">{errors.points}</p>}
            </div>
            <div>
              <label htmlFor="rbw_khz" className="block text-sm font-medium text-gray-300 mb-1">
                RBW (kHz)
              </label>
              <input
                type="number"
                id="rbw_khz"
                name="rbw_khz"
                value={formData.rbw_khz}
                onChange={handleChange}
                step="0.1"
                min="0"
                className={`
                  w-full px-3 py-2 rounded-lg bg-gray-700 border text-white
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${errors.rbw_khz ? 'border-red-500' : 'border-gray-600'}
                `}
                placeholder="Auto"
              />
              {errors.rbw_khz && <p className="mt-1 text-sm text-red-400">{errors.rbw_khz}</p>}
            </div>
          </div>

          {/* Category */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-300 mb-1">
              Category
            </label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Preset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/**
 * PresetForm wrapper - handles open/close and uses key prop to reset form state
 */
export default function PresetForm({ preset, isOpen, onClose, onSuccess }: PresetFormProps) {
  if (!isOpen) return null

  // Use preset?.id as key to force remount when editing different presets
  // For new presets (no id), use 'new' as key
  return (
    <PresetFormInner
      key={preset?.id ?? 'new'}
      preset={preset}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  )
}
