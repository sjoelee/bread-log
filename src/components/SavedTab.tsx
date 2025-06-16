import React from 'react';
import { Dayjs } from 'dayjs';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { DoughMake, TeamMake, BreadFormData, TemperatureSettings } from '../types/bread';
import { TemperatureSection } from './TemperatureSection.tsx';

interface SavedTabProps {
  savedMakes: DoughMake[];
  isLoading: boolean;
  teamMakes: TeamMake[];
  formattedDate: string;
  onViewMake: (make: DoughMake) => void;
  selectedDough: DoughMake | null;
  setSelectedDough: (dough: DoughMake | null) => void;
  formData: BreadFormData;
  loading: boolean;
  error: string | null;
  success: boolean;
  customSuccessMessage: string | null;
  isStretchFoldsExpanded: boolean;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  onTemperatureChange: (field: keyof TemperatureSettings, value: string) => void;
  onToggleTemperatureUnit: (unit: any) => void;
  onProcessTimeChange: (step: string, time: Dayjs | null) => void;
  onStretchFoldsToggle: () => void;
  onAddStretchFold: () => void;
  onRemoveStretchFold: (id: number) => void;
  onUpdateStretchFold: (id: number, updates: any) => void;
  onSubmit: () => void;
  onUpdate: (selectedDough: DoughMake) => void;
}

export const SavedTab: React.FC<SavedTabProps> = ({
  savedMakes,
  isLoading,
  teamMakes,
  formattedDate,
  onViewMake,
  selectedDough,
  setSelectedDough,
  formData,
  loading,
  error,
  success,
  customSuccessMessage,
  isStretchFoldsExpanded,
  onInputChange,
  onTemperatureChange,
  onToggleTemperatureUnit,
  onProcessTimeChange,
  onStretchFoldsToggle,
  onAddStretchFold,
  onRemoveStretchFold,
  onUpdateStretchFold,
  onSubmit,
  onUpdate,
}) => {
  if (!formattedDate) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Please select a date to view saved makes</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Loading saved makes...</p>
      </div>
    );
  }

  if (savedMakes.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div className="space-y-2">
          <p className="font-medium">No saved makes found</p>
          <p className="text-sm">for {formattedDate}</p>
          <p className="text-sm mt-4">Switch to the Create tab to start a new make</p>
        </div>
      </div>
    );
  }

  // Create the update form handler
  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Pass the selectedDough to the update function
    if (selectedDough) {
      onUpdate(selectedDough);
    }
  };

  return (
    <div className="space-y-6">
      {/* Saved Makes List - Hidden when editing */}
      {!selectedDough && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-blue-800 font-medium">
                Saved makes for {formattedDate}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {savedMakes.map((make, index) => {
              // Find the displayName for this make's key
              const teamMake = teamMakes.find(tm => tm.key === make.name);
              const displayName = teamMake?.displayName || make.name;
              
              return (
                <div key={index} className="border rounded-lg p-4 transition-colors border-gray-200 hover:bg-gray-50">
                  <button
                    onClick={() => onViewMake(make)}
                    className="text-left w-full"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-blue-600 hover:text-blue-800">
                          {displayName}
                        </h3>
                        <p className="text-sm text-gray-600 mt-1">
                          {make.notes ? make.notes.substring(0, 100) + '...' : 'No notes'}
                        </p>
                        <div className="text-xs text-gray-500 mt-2">
                          Created: {make.created_at.toLocaleString()}
                        </div>
                      </div>
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Show detailed form if a dough is selected */}
      {selectedDough && (
        <div className="border-t pt-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <p className="text-green-800 font-medium">
                Editing: {teamMakes.find(tm => tm.key === selectedDough.name)?.displayName || selectedDough.name}
              </p>
              <button
                onClick={() => setSelectedDough(null)}
                className="ml-auto text-green-600 hover:text-green-800"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          {/* Inline form content for editing */}
          <form onSubmit={handleUpdateSubmit} className="space-y-6">
            
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

            {/* Error Messages */}
            {error && <div className="text-red-500 mb-4">{error}</div>}

            {/* Update Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={loading}
                className="bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-6 rounded"
              >
                {loading ? 'Updating...' : 'UPDATE'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Custom Success Message - Show at bottom when not editing */}
      {!selectedDough && customSuccessMessage && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <p className="text-green-800 font-medium">{customSuccessMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
};