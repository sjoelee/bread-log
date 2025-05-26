import React, { useEffect, useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';

enum TemperatureUnit {
  CELSIUS = 'Celsius',
  FAHRENHEIT = 'Fahrenheit'
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

// Add new interface for stretch and folds
interface StretchFold {
  id: number;
  performed: boolean;
  time: Dayjs | null;
}

interface BreadFormData {
  date: Dayjs | null;
  teamMake: string;
  temperatures: TemperatureSettings;
  processes: DoughProcess[];
  stretchFolds: StretchFold[];
  notes: string;
}

interface TeamMake {
  displayName: string;
  key: string;
}

const DEFAULT_TEAM_MAKES: TeamMake[] = [
  { displayName: 'Hoagie', key: 'hoagie' },
  { displayName: 'Demi', key: 'demi' },
  { displayName: 'Ube', key: 'ube' }
];

const initialTempSettings: TemperatureSettings = {
  unit: TemperatureUnit.FAHRENHEIT,
  roomTemp: 65,
  flourTemp: 65,
  prefermentTemp: 76,
  waterTemp: 45,
  doughTemp: 76,
};

// Initialize default stretch and folds (typically 3-4 sets)
const initialStretchFolds: StretchFold[] = [
  { id: 1, performed: false, time: null },
  { id: 2, performed: false, time: null },
  { id: 3, performed: false, time: null },
  { id: 4, performed: false, time: null },
];

interface Make {
  key: string;
  display_name: string;
  // other properties...
}

interface FormattedMake {
  key: string;
  displayName: string;
  // other properties with camelCase...
}

// Add new interface for create make request
interface CreateMakeRequest {
  display_name: string;
}

const BreadApp = () => {
  const [formData, setFormData] = useState<BreadFormData>({
    date: dayjs(),
    teamMake: 'Hoagie',
    temperatures: initialTempSettings,
    processes: [
      { step: 'Autolyse', time: dayjs() },
      { step: 'Start', time: dayjs() },
      { step: 'Pull', time: dayjs() },
      { step: 'Preshape', time: dayjs() },
      { step: 'Final Shape', time: dayjs() },
      { step: 'Fridge', time: dayjs() },
    ],
    stretchFolds: initialStretchFolds,
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [teamMakes, setTeamMakes] = useState<TeamMake[]>([]);
  const [isLoadingMakes, setIsLoadingMakes] = useState(false);
  const [isAddMakeModalOpen, setIsAddMakeModalOpen] = useState(false);
  const [newMakeName, setNewMakeName] = useState('');
  const [isAddingMake, setIsAddingMake] = useState(false);
  const [addMakeError, setAddMakeError] = useState<string | null>(null);
  
  // Add state for collapsible stretch and folds section
  const [isStretchFoldsExpanded, setIsStretchFoldsExpanded] = useState(false);

  // fetch team makes when component mounts
  useEffect(() => {
    const fetchTeamMakes = async () => {
      // Check localStorage first
      const cachedMakes = localStorage.getItem('teamMakes');
      // if (cachedMakes) {
      //   setTeamMakes(JSON.parse(cachedMakes));
      //   return;
      // }

      setIsLoadingMakes(true);
      try {
        const isDevelopment = window.location.hostname === 'localhost' ||
          window.location.hostname === '127.0.0.1';

        const apiBaseUrl = isDevelopment
          ? 'http://localhost:8000'
          : 'https://your-production-api.com';

        const response = await fetch(`${apiBaseUrl}/makes`, {
          headers: {
            'Authorization': 'Bearer test-token', // TODO: Replace with token
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          // Map the data to transform display_name to displayName
          const formattedMakes = data.map((make) => ({
            key: make.key,
            displayName: make.display_name,
            // map other properties as needed
          }));

          setTeamMakes(formattedMakes);
          localStorage.setItem('teamMakes', JSON.stringify(formattedMakes));
        } else {
          setTeamMakes(DEFAULT_TEAM_MAKES);
        }
      } catch (error) {
        console.error('Error fetching team makes:', error);
        setTeamMakes(DEFAULT_TEAM_MAKES);
      } finally {
        setIsLoadingMakes(false);
      }
    };

    fetchTeamMakes();
  }, []);;

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

  // Handle stretch and fold checkbox change
  const handleStretchFoldCheck = (id: number, performed: boolean) => {
    const updatedStretchFolds = formData.stretchFolds.map(sf => 
      sf.id === id 
        ? { ...sf, performed, time: performed ? sf.time || dayjs() : null }
        : sf
    );

    setFormData({
      ...formData,
      stretchFolds: updatedStretchFolds
    });
  };

  // Handle stretch and fold time change
  const handleStretchFoldTimeChange = (id: number, newTime: Dayjs | null) => {
    const updatedStretchFolds = formData.stretchFolds.map(sf => 
      sf.id === id ? { ...sf, time: newTime } : sf
    );

    setFormData({
      ...formData,
      stretchFolds: updatedStretchFolds
    });
  };

  // Update addNewDough function to open modal
  const addNewDough = () => {
    setIsAddMakeModalOpen(true);
    setNewMakeName('');
    setAddMakeError(null);
  };

  // Function to handle modal close
  const handleModalClose = () => {
    setIsAddMakeModalOpen(false);
  };

  // Function to create a new make
  const handleCreateMake = async () => {
    if (!newMakeName.trim()) {
      setAddMakeError('Please enter a make name');
      return;
    }

    setIsAddingMake(true);
    setAddMakeError(null);

    try {
      // Generate key from the display name (convert to kebab-case)
      const key = newMakeName.trim()
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')  // Remove special characters
        .replace(/\s+/g, '-');     // Replace spaces with hyphense

      const isDevelopment = window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1';

      const apiBaseUrl = isDevelopment
        ? 'http://localhost:8000'
        : 'https://your-production-api.com';

      const response = await fetch(`${apiBaseUrl}/makes`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test-token', // TODO: Replace with token
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          display_name: newMakeName,
          key: key
        } as CreateMakeRequest)
      });

      if (response.ok) {
        const newMake = await response.json();

        // Map the response to our frontend model
        const formattedMake: TeamMake = {
          key: newMake.key,
          displayName: newMake.display_name
        };

        // Update the makes list with the new item
        const updatedMakes = [...teamMakes, formattedMake];
        setTeamMakes(updatedMakes);

        // Update localStorage
        localStorage.setItem('teamMakes', JSON.stringify(updatedMakes));

        // Set the form to use the new make
        setFormData({
          ...formData,
          teamMake: formattedMake.key
        });

        // Close the modal
        setIsAddMakeModalOpen(false);
      } else {
        const errorData = await response.json();
        setAddMakeError(errorData.detail || 'Failed to create make');
      }
    } catch (error) {
      console.error('Error creating make:', error);
      setAddMakeError('An error occurred while creating the make');
    } finally {
      setIsAddingMake(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    // Get selected team make key
    const selectedMake = teamMakes.find(make => make.key === formData.teamMake);
    if (!selectedMake) {
      setError('Invalid team make selected. Please choose a valid option.');
      setLoading(false);
      return;
    }
    const makeKey = selectedMake.key;

    // Format date from Dayjs
    const formattedDate = formData.date ? formData.date.format('YYYY/MM/DD') : '';
    // Determine API endpoint based on environment
    const isDevelopment = window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';

    const apiBaseUrl = isDevelopment
      ? `http://localhost:8000/makes/${formattedDate}/${makeKey}` //hardcoded, will need to update based on date and make
      : `https://your-production-api.com/${formattedDate}/${makeKey}`;

    const endpoint = `${apiBaseUrl}`;
    
    // Create stretch folds data for API
    const stretchFoldsData = formData.stretchFolds
      .filter(sf => sf.performed && sf.time)
      .map(sf => ({
        fold_number: sf.id,
        timestamp: combineDateTime(formData.date, sf.time)
      }));

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

      // Include stretch folds data
      stretch_folds: stretchFoldsData,

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
            <label className="block text-sm font-medium mb-1">Make Name</label>
            <div className="relative">
              <select
                name="teamMake"
                value={formData.teamMake}
                onChange={handleInputChange}
                className="w-full border rounded p-2 appearance-none pr-8"
              >
                {isLoadingMakes ? (
                  <option>Loading...</option>
                ) : (
                  teamMakes.map((make) => (
                    <option key={make.key} value={make.key}>
                      {make.displayName}
                    </option>
                  ))
                )}
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
              + Add new make
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

        {/* Process Steps - Modified to include stretch and folds */}
        <div className="space-y-6 mb-6">
          {formData.processes.map((process, index) => (
            <div key={index}>
              <div className="flex justify-between items-center">
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

              {/* Insert Stretch & Folds section after Pull */}
              {process.step === 'Pull' && (
                <div className="mt-4 border rounded-lg">
                  <button
                    type="button"
                    onClick={() => setIsStretchFoldsExpanded(!isStretchFoldsExpanded)}
                    className="w-full p-3 text-left font-medium bg-gray-50 hover:bg-gray-100 rounded-t-lg flex justify-between items-center"
                  >
                    <span>Stretch & Folds</span>
                    <svg
                      className={`h-5 w-5 transform transition-transform ${isStretchFoldsExpanded ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isStretchFoldsExpanded && (
                    <div className="p-4 space-y-3">
                      {formData.stretchFolds.map((stretchFold) => (
                        <div key={stretchFold.id} className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              id={`stretch-fold-${stretchFold.id}`}
                              checked={stretchFold.performed}
                              onChange={(e) => handleStretchFoldCheck(stretchFold.id, e.target.checked)}
                              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                            />
                            <label htmlFor={`stretch-fold-${stretchFold.id}`} className="text-sm font-medium min-w-[60px]">
                              Fold {stretchFold.id}
                            </label>
                          </div>

                          <div className="flex-1">
                            <TimePicker
                              label="Time"
                              value={stretchFold.time}
                              onChange={(newTime) => handleStretchFoldTimeChange(stretchFold.id, newTime)}
                              disabled={!stretchFold.performed}
                              slotProps={{
                                textField: {
                                  size: 'small',
                                  fullWidth: true,
                                  disabled: !stretchFold.performed
                                }
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
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
      <Modal
        open={isAddMakeModalOpen}
        onClose={handleModalClose}
        aria-labelledby="add-make-modal-title"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4,
          borderRadius: 2
        }}>
          <h2 id="add-make-modal-title" className="text-xl font-medium mb-4">Add New Make</h2>

          {addMakeError && (
            <div className="text-red-500 mb-4">{addMakeError}</div>
          )}

          <TextField
            label="Name Of New Make"
            variant="outlined"
            fullWidth
            value={newMakeName}
            onChange={(e) => setNewMakeName(e.target.value)}
            margin="normal"
            disabled={isAddingMake}
            placeholder="Enter a name for the new dough type"
          />

          <div className="flex justify-end gap-2 mt-4">
            <Button
              onClick={handleModalClose}
              variant="outlined"
              disabled={isAddingMake}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateMake}
              variant="contained"
              disabled={isAddingMake || !newMakeName.trim()}
              sx={{ bgcolor: 'rgb(96, 165, 250)', '&:hover': { bgcolor: 'rgb(59, 130, 246)' } }}
            >
              {isAddingMake ? 'Adding...' : 'Add New Make'}
            </Button>
          </div>
        </Box>
      </Modal>
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