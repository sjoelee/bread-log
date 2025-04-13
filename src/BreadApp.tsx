import React, { useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';

enum TemperatureUnit {
  CELSIUS = 'C',
  FAHRENHEIT = 'F'
}

interface TemperatureSettings {
  unit: TemperatureUnit;
  roomTemp: number;
  flourTemp: number;
  prefermentTemp: number;
  waterTemp: number;
  doughTemp: number;
}

interface DoughProcess {
  step: string;
  time: Dayjs | null;
}

interface BreadFormData {
  date: Dayjs | null;
  teamMake: string;
  temperatures: TemperatureSettings;
  processes: DoughProcess[];
  notes: string;
}

const initialTempSettings: TemperatureSettings = {
  unit: TemperatureUnit.FAHRENHEIT,
  roomTemp: 65,
  flourTemp: 65,
  prefermentTemp: 76,
  waterTemp: 45,
  doughTemp: 76,
};

const BreadApp = () => {
  const [formData, setFormData] = useState<BreadFormData>({
    date: dayjs(),
    teamMake: 'Team Make #1',
    temperatures: initialTempSettings,
    processes: [
      { step: 'Autolyse', time: null },
      { step: 'Start', time: null },
      { step: 'Pull', time: null },
      { step: 'Preshape', time: null },
      { step: 'Final Shape', time: null },
      { step: 'Fridge', time: null },
    ],
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Toggle temperature unit
  const toggleTemperatureUnit = (unit: TemperatureUnit) => {
    const currentUnit = formData.temperatures.unit;
    if (unit === currentUnit) return;

    const convertedTemps = {
      roomTemp: convertTemperature(formData.temperatures.roomTemp, currentUnit, unit),
      flourTemp: convertTemperature(formData.temperatures.flourTemp, currentUnit, unit),
      prefermentTemp: convertTemperature(formData.temperatures.prefermentTemp, currentUnit, unit),
      waterTemp: convertTemperature(formData.temperatures.waterTemp, currentUnit, unit),
      doughTemp: convertTemperature(formData.temperatures.doughTemp, currentUnit, unit),
    };

    setFormData({
      ...formData,
      temperatures: {
        ...formData.temperatures,
        ...convertedTemps,
        unit
      }
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDateChange = (newDate: Dayjs | null) => {
    setFormData({
      ...formData,
      date: newDate
    });
  };

  const handleTempChange = (field: keyof Omit<TemperatureSettings, 'unit'>, value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) || value === '') {
      setFormData((prev) => ({
        ...prev,
        temperatures: {
          ...prev.temperatures,
          [field]: value === '' ? '' : numValue,
        },
      }));
    }
  };

  const handleTimeChange = (index: number, newTime: Dayjs | null) => {
    const updatedProcesses = [...formData.processes];
    updatedProcesses[index] = {
      ...updatedProcesses[index],
      time: newTime
    };

    setFormData({
      ...formData,
      processes: updatedProcesses
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    // Determine API endpoint based on environment
    const isDevelopment = window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';
 
    const apiBaseUrl = isDevelopment
      ? 'http://localhost:8000/makes/2025/04/05/demi' //hardcoded, will need to update based on date and make
      : 'https://your-production-api.com';
      
    const endpoint = `${apiBaseUrl}`;
    // Create API payload
    const apiPayload = {
      // Combine date and time for each process step
      autolyse_ts: combineDateTime(formData.date, formData.processes.find(p => p.step === 'Autolyse')?.time ?? null),
      start_ts: combineDateTime(formData.date, formData.processes.find(p => p.step === 'Start')?.time ?? null),
      pull_ts: combineDateTime(formData.date, formData.processes.find(p => p.step === 'Pull')?.time ?? null),
      preshape_ts: combineDateTime(formData.date, formData.processes.find(p => p.step === 'Preshape')?.time ?? null),
      final_shape_ts: combineDateTime(formData.date, formData.processes.find(p => p.step === 'Final Shape')?.time ?? null),
      fridge_ts: combineDateTime(formData.date, formData.processes.find(p => p.step === 'Fridge')?.time ?? null),

      // Temperature values
      room_temp: formData.temperatures.roomTemp,
      flour_temp: formData.temperatures.flourTemp,
      preferment_temp: formData.temperatures.prefermentTemp,
      water_temp: formData.temperatures.waterTemp,
      dough_temp: formData.temperatures.doughTemp,

      // Include temperature unit
      temp_unit: formData.temperatures.unit,

      notes: formData.notes
    };

    try {
      //update endpoint to be the date and make
      console.log('Submitting form data:', apiPayload);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiPayload),
      })
      if (response.ok) {
      // API call would go here
      setSuccess(true);
      } else {
        setError('Server responded with an error');
      }
    } catch (err) {
      setError('Failed to submit form. Please try again.');
      console.error('Submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to combine date and time into a timestamp for backend
  const combineDateTime = (date: Dayjs | null, time: Dayjs | null): string | null => {
    if (!date || !time) return null;

    // Create a new Dayjs object with the date from formData.date and time from process.time
    const combinedDateTime = date.hour(time.hour()).minute(time.minute()).second(0);

    // Format as "YYYY-MM-DD HH:MM:SS" for the backend
    return combinedDateTime.format('YYYY-MM-DD HH:mm:ss');
  };

  const addNewDough = () => {
    alert('Add new dough functionality would be implemented here');
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
      <form onSubmit={handleSubmit}>
        {/* Date and Team Make Row */}
        <div className="flex gap-4 mb-6">
          <div className="w-1/2">
            <label className="block text-sm font-medium mb-1">Date</label>
            <DatePicker
              value={formData.date}
              onChange={handleDateChange}
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
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
                <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

        {/* Temperature Fields with F/C toggle */}
        <div className="mb-6 p-4 border rounded-lg">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-medium">Temperatures</h3>
            <div className="inline-flex rounded-md shadow-sm" role="group">
              <button
                type="button"
                onClick={() => toggleTemperatureUnit(TemperatureUnit.FAHRENHEIT)}
                className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${formData.temperatures.unit === TemperatureUnit.FAHRENHEIT
                    ? 'bg-gray-200 text-gray-700'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                F
              </button>
              <button
                type="button"
                onClick={() => toggleTemperatureUnit(TemperatureUnit.CELSIUS)}
                className={`px-4 py-2 text-sm font-medium rounded-r-lg border-t border-b border-r ${formData.temperatures.unit === TemperatureUnit.CELSIUS
                    ? 'bg-gray-200 text-gray-700'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                C
              </button>
            </div>
          </div>

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
              <label className="block text-sm font-medium mb-1 text-center">Preferment</label>
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

        {/* Process Steps - Realigned as per mockup */}
        <div className="space-y-6 mb-6">
          {formData.processes.map((process, index) => (
            <div key={index} className="flex justify-between items-center">
              <div className="w-1/3">
                <span className="font-medium">{process.step}</span>
              </div>

              <div className="w-2/3">
                <TimePicker
                  label="Time"
                  value={process.time}
                  onChange={(newTime) => handleTimeChange(index, newTime)}
                  slotProps={{
                    textField: {
                      size: 'small',
                      fullWidth: true
                    }
                  }}
                />
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
      </form>
    </div>
  );
};

function convertTemperature(value: number, from: TemperatureUnit, to: TemperatureUnit): number {
  if (from === to) return value;

  if (from === TemperatureUnit.CELSIUS && to === TemperatureUnit.FAHRENHEIT) {
    return Math.round((value * 9 / 5) + 32);
  } else {
    return Math.round((value - 32) * 5 / 9);
  }
}

export default BreadApp;