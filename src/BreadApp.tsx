import React, { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { Dayjs } from 'dayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';

// Types
interface DoughProcess {
  step: string;
  time: string;
}

interface BreadFormData {
  date: string;
  teamMake: string;
  temperatures: {
    roomTemp: string;
    flourTemp: string;
    prefermentTemp: string;
    waterTemp: string;
    doughTemp: string;
  };
  processes: DoughProcess[];
  notes: string;
}

const BreadApp = () => {
  // Initial form state
  const [formData, setFormData] = useState<BreadFormData>({
    date: new Date().toISOString().split('T')[0],
    teamMake: 'Team Make #1',
    temperatures: {
      roomTemp: '68F',
      flourTemp: '68F',
      prefermentTemp: '68F',
      waterTemp: '68F',
      doughTemp: '68F',
    },
    processes: [
      { step: 'Autolyse', time: ''},
      { step: 'Start', time: ''},
      { step: 'Pull', time: ''},
      { step: 'Preshape', time: ''},
      { step: 'Fridge', time: ''},
    ],
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [value, setValue] = React.useState<Dayjs | null>(null);

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle temperature field changes
  const handleTempChange = (field: keyof BreadFormData['temperatures'], value: string) => {
    setFormData((prev) => ({
      ...prev,
      temperatures: {
        ...prev.temperatures,
        [field]: value,
      },
    }));
  };

  // Handle process field changes
  const handleProcessChange = (index: number, field: keyof DoughProcess, value: string) => {
    setFormData((prev) => {
      const updatedProcesses = [...prev.processes];
      updatedProcesses[index] = {
        ...updatedProcesses[index],
        [field]: value,
      };
      return {
        ...prev,
        processes: updatedProcesses,
      };
    });
  };

  // Show time picker
  const showTimePicker = (index: number) => {
    <TimePicker label="Basic time picker" />
    // In a real implementation, this would open a time picker
    // alert(`Show time picker for ${formData.processes[index].step}`);
  };

  // Submit form data
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    // Determine API endpoint based on environment
    const isDevelopment = window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';

    const apiBaseUrl = isDevelopment
      ? 'http://localhost:8000'
      : 'https://your-production-api.com';

    const endpoint = `${apiBaseUrl}`;

    const requestBody = JSON.stringify(formData, null, 2);
    console.log('Request Body: ', requestBody)
    try {
      // Replace with your actual API endpoint
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      console.log('Response Status:', response.status);

      if (response.ok) {
        setSuccess(true);
        // Optionally reset form or redirect
      } else {
        throw new Error('Server responded with an error');
      }
    } catch (err) {
      setError('Failed to submit form. Please try again.');
      console.error('Submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Add new dough make
  const addNewDough = () => {
    // Implementation for adding new dough records
    alert('Add new dough functionality would be implemented here');
  };
  // TODO: API get call to retrieve list of makes.

  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow p-6">
      <form onSubmit={handleSubmit}>
        {/* Date and Team Make Row */}
        <div className="flex gap-4 mb-6">
          <div className="w-1/2">
            <label className="block text-sm font-medium mb-1">Date</label>
            <div className="relative">
              <DatePicker value={value} onChange={(newValue) => setValue(newValue)} />
            </div>
          </div>

          <div className="w-1/2">
            <label className="block text-sm font-medium mb-1">Team Make</label>
            <div className="relative">
              <select
                name="teamMake"
                value={formData.teamMake}
                onChange={handleInputChange}
                className="w-full border rounded p-2 appearance-none pr-8"
              >
                <option>Team Make #1</option>
                <option>Team Make #2</option>
                <option>Team Make #3</option>
              </select>
              <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </span>
            </div>
            <button
              type="button"
              onClick={addNewDough}
              className="mt-1 text-sm text-red-500 hover:text-red-700"
            >
              + Add new dough
            </button>
          </div>
        </div>

        {/* Temperature Fields */}
        <div className="mb-6">
          <div className="grid grid-cols-5 gap-2">
            {/* Room Temp */}
            <div>
              <label className="block text-sm font-medium mb-1 text-center">Room Temp</label>
              <input
                type="text"
                value={formData.temperatures.roomTemp}
                onChange={(e) => handleTempChange('roomTemp', e.target.value)}
                className="w-full border rounded p-2 text-center"
              />
            </div>

            {/* Flour Temp */}
            <div>
              <label className="block text-sm font-medium mb-1 text-center">Flour Temp</label>
              <input
                type="text"
                value={formData.temperatures.flourTemp}
                onChange={(e) => handleTempChange('flourTemp', e.target.value)}
                className="w-full border rounded p-2 text-center"
              />
            </div>

            {/* Preferment Temp */}
            <div>
              <label className="block text-sm font-medium mb-1 text-center">Preferment Temp</label>
              <input
                type="text"
                value={formData.temperatures.prefermentTemp}
                onChange={(e) => handleTempChange('prefermentTemp', e.target.value)}
                className="w-full border rounded p-2 text-center"
              />
            </div>

            {/* Water Temp */}
            <div>
              <label className="block text-sm font-medium mb-1 text-center">Water Temp</label>
              <input
                type="text"
                value={formData.temperatures.waterTemp}
                onChange={(e) => handleTempChange('waterTemp', e.target.value)}
                className="w-full border rounded p-2 text-center"
              />
            </div>

            {/* Dough Temp */}
            <div>
              <label className="block text-sm font-medium mb-1 text-center">Dough Temp</label>
              <input
                type="text"
                value={formData.temperatures.doughTemp}
                onChange={(e) => handleTempChange('doughTemp', e.target.value)}
                className="w-full border rounded p-2 text-center"
              />
            </div>
          </div>
        </div>

        {/* Process Steps */}
        <div className="space-y-6 mb-6">
          {formData.processes.map((process, index) => (
            <div key={index} className="flex items-center">
              <div className="w-1/4">
                <span className="font-medium">{process.step}:</span>
              </div>

              <div className="w-1/2 pr-2">
                <div className="relative">
                  <TimePicker label="Basic time picker" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Notes */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1">Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            className="w-full border rounded p-2 h-24"
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
            className="bg-blue-200 hover:bg-blue-300 text-blue-800 font-medium py-2 px-6 rounded"
          >
            {loading ? 'Submitting...' : 'SUBMIT'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default BreadApp;