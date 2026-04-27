import React from 'react';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { Dayjs } from 'dayjs';
import { BreadFormData, TemperatureSettings } from '../types/bread.ts';
import { TemperatureSection } from './TemperatureSection.tsx';

interface CreateTabProps {
  formData: BreadFormData;
  loading: boolean;
  error: string | null;
  success: boolean;
  onDateChange: (date: Dayjs | null) => void;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  onTemperatureChange: (field: keyof TemperatureSettings, value: string) => void;
  onToggleTemperatureUnit: (unit: any) => void;
  onProcessTimeChange: (step: string, time: Dayjs | null) => void;
  onStretchFoldCountChange: (count: number) => void;
  onSubmit: () => void;
}

export const CreateTab: React.FC<CreateTabProps> = ({
  formData,
  loading,
  error,
  success,
  onDateChange,
  onInputChange,
  onTemperatureChange,
  onToggleTemperatureUnit,
  onProcessTimeChange,
  onStretchFoldCountChange,
  onSubmit,
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle Cmd+Enter (Mac) or Ctrl+Enter (PC) to submit form
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      onSubmit();
    }
    // Prevent plain Enter from submitting when inside TimePicker inputs
    else if (e.key === 'Enter') {
      e.preventDefault();
      // Move focus to next focusable element
      const form = e.currentTarget as HTMLElement;
      const focusableElements = form.querySelectorAll(
        'input, button, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const currentIndex = Array.from(focusableElements).indexOf(e.target as Element);
      const nextElement = focusableElements[currentIndex + 1] as HTMLElement;
      if (nextElement) {
        nextElement.focus();
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} onKeyDown={handleKeyDown} className="space-y-6">

      {/* Temperature Section */}
      <TemperatureSection
        temperatures={formData.temperatures}
        onTemperatureChange={onTemperatureChange}
        onToggleUnit={onToggleTemperatureUnit}
      />

      {/* Process Section */}
      <div className="space-y-4 p-4 border rounded-lg bg-blue-50">
        <h2 className="text-xl font-bold text-gray-800">Process</h2>
        
        {/* First part: Autolyse, Mix, Bulk */}
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

        {/* Stretch & Folds Counter */}
        <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
          <span className="font-medium text-sm">Stretch &amp; Folds</span>
          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              onClick={() => onStretchFoldCountChange(Math.max(0, formData.stretchFoldCount - 1))}
              className="w-8 h-8 rounded-full border border-gray-300 bg-white hover:bg-gray-100 flex items-center justify-center text-lg leading-none"
              disabled={formData.stretchFoldCount <= 0}
            >
              −
            </button>
            <span className="w-8 text-center font-medium">{formData.stretchFoldCount}</span>
            <button
              type="button"
              onClick={() => onStretchFoldCountChange(Math.min(50, formData.stretchFoldCount + 1))}
              className="w-8 h-8 rounded-full border border-gray-300 bg-white hover:bg-gray-100 flex items-center justify-center text-lg leading-none"
            >
              +
            </button>
          </div>
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
      <div className="flex flex-col items-center space-y-2">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-400 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded"
        >
          {loading ? 'Submitting...' : 'SUBMIT'}
        </button>
        <div className="text-xs text-gray-500">
          Press <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">⌘+Enter</kbd> or <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs">Ctrl+Enter</kbd> to submit
        </div>
      </div>

    </form>
  );
};