import React from 'react';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { Dayjs } from 'dayjs';
import { BreadFormData, TeamMake, TemperatureSettings } from '../types/bread.ts';
import { TemperatureSection } from './TemperatureSection.tsx';
import { AddMakeModal } from './AddMakeModal.tsx';

interface CreateTabProps {
  formData: BreadFormData;
  teamMakes: TeamMake[];
  isLoadingMakes: boolean;
  loading: boolean;
  error: string | null;
  success: boolean;
  isStretchFoldsExpanded: boolean;
  onDateChange: (date: Dayjs | null) => void;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  onTemperatureChange: (field: keyof TemperatureSettings, value: string) => void;
  onToggleTemperatureUnit: (unit: any) => void;
  onProcessTimeChange: (step: string, time: Dayjs | null) => void;
  onStretchFoldsToggle: () => void;
  onAddStretchFold: () => void;
  onRemoveStretchFold: (id: number) => void;
  onUpdateStretchFold: (id: number, updates: any) => void;
  onSubmit: () => void;
  // Modal props
  isAddMakeModalOpen: boolean;
  newMakeName: string;
  onNewMakeNameChange: (name: string) => void;
  onOpenAddMakeModal: () => void;
  onCloseAddMakeModal: () => void;
  onAddMake: () => void;
  isAddingMake: boolean;
  addMakeError: string | null;
}

export const CreateTab: React.FC<CreateTabProps> = ({
  formData,
  teamMakes,
  isLoadingMakes,
  loading,
  error,
  success,
  isStretchFoldsExpanded,
  onDateChange,
  onInputChange,
  onTemperatureChange,
  onToggleTemperatureUnit,
  onProcessTimeChange,
  onStretchFoldsToggle,
  onAddStretchFold,
  onRemoveStretchFold,
  onUpdateStretchFold,
  onSubmit,
  isAddMakeModalOpen,
  newMakeName,
  onNewMakeNameChange,
  onOpenAddMakeModal,
  onCloseAddMakeModal,
  onAddMake,
  isAddingMake,
  addMakeError,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">

      {/* Temperature Section */}
      <TemperatureSection
        temperatures={formData.temperatures}
        onTemperatureChange={onTemperatureChange}
        onToggleUnit={onToggleTemperatureUnit}
      />

      {/* Process Section */}
      <div className="space-y-4 p-4 border rounded-lg bg-blue-50">
        <h2 className="text-xl font-bold text-gray-800">Process</h2>
        
        {/* First part: Autolyse, Start, Pull */}
        <div className="space-y-4">
          {formData.processes.slice(0, 3).map((process) => (
            <div key={process.step} className="flex items-center gap-4">
              <label className="w-20 text-sm font-medium">
                {process.step}
              </label>
              <div className="flex-1">
                <div className="relative">
                  <span className="absolute left-2 top-1 text-xs text-gray-500 z-10">Time</span>
                  <TimePicker
                    value={process.time}
                    onChange={(newTime) => onProcessTimeChange(process.step, newTime)}
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                        sx: { '& .MuiInputBase-input': { paddingTop: '20px' } }
                      },
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Stretch & Folds Section */}
        <div className="space-y-4">
          <button
            type="button"
            onClick={onStretchFoldsToggle}
            className="flex items-center justify-between w-full p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <span className="font-medium">Stretch & Folds</span>
            <svg
              className={`h-5 w-5 transform transition-transform ${
                isStretchFoldsExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {isStretchFoldsExpanded && (
            <div className="space-y-3 pl-4">
              {formData.stretchFolds.map((stretchFold) => (
                <div key={stretchFold.id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <input
                    type="checkbox"
                    checked={stretchFold.performed}
                    onChange={(e) =>
                      onUpdateStretchFold(stretchFold.id, { performed: e.target.checked })
                    }
                    className="rounded"
                  />
                  <span className="text-sm font-medium min-w-0">S&F #{stretchFold.id}</span>
                  <div className="flex-1">
                    <TimePicker
                      value={stretchFold.time}
                      onChange={(newTime) =>
                        onUpdateStretchFold(stretchFold.id, { time: newTime })
                      }
                      disabled={!stretchFold.performed}
                      slotProps={{
                        textField: {
                          size: 'small',
                          fullWidth: true,
                        },
                      }}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => onRemoveStretchFold(stretchFold.id)}
                    className="text-red-500 hover:text-red-700 p-1"
                    disabled={formData.stretchFolds.length <= 1}
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={onAddStretchFold}
                className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors"
              >
                + Add Stretch & Fold
              </button>
            </div>
          )}
        </div>

        {/* Remaining process steps: Preshape, Final Shape, Fridge */}
        <div className="space-y-4">
          {formData.processes.slice(3).map((process) => (
            <div key={process.step} className="flex items-center gap-4">
              <label className="w-20 text-sm font-medium">
                {process.step}
              </label>
              <div className="flex-1">
                <div className="relative">
                  <span className="absolute left-2 top-1 text-xs text-gray-500 z-10">Time</span>
                  <TimePicker
                    value={process.time}
                    onChange={(newTime) => onProcessTimeChange(process.step, newTime)}
                    slotProps={{
                      textField: {
                        size: 'small',
                        fullWidth: true,
                        sx: { '& .MuiInputBase-input': { paddingTop: '20px' } }
                      },
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Notes Section */}
      <div>
        <label className="block text-sm font-medium mb-1">Notes</label>
        <textarea
          placeholder="Add any notes about this make..."
          name="notes"
          value={formData.notes}
          onChange={onInputChange}
          className="w-full border rounded p-2 h-24 resize-none"
        />
      </div>

      {/* Error and Success Messages */}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {success && <div className="text-green-500 mb-4">Form submitted successfully!</div>}

      {/* Submit Button */}
      <div className="flex justify-center">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-400 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded"
        >
          {loading ? 'Submitting...' : 'SUBMIT'}
        </button>
      </div>

      {/* Add Make Modal */}
      <AddMakeModal
        isOpen={isAddMakeModalOpen}
        newMakeName={newMakeName}
        onNameChange={onNewMakeNameChange}
        onClose={onCloseAddMakeModal}
        onAdd={onAddMake}
        isAdding={isAddingMake}
        error={addMakeError}
      />
    </form>
  );
};