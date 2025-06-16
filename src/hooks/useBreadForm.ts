import { useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import { 
  BreadFormData, 
  TemperatureUnit, 
  TemperatureSettings,
  DoughProcess,
  StretchFold,
  DoughMake,
  INITIAL_TEMP_SETTINGS,
  INITIAL_STRETCH_FOLDS
} from '../types/bread.ts';
import { convertTemperature } from '../utils/temperature.ts';
import { doughMakesApi } from '../services/api.ts';

const INITIAL_PROCESSES: DoughProcess[] = [
  { step: 'Autolyse', time: dayjs() },
  { step: 'Start', time: dayjs() },
  { step: 'Pull', time: dayjs() },
  { step: 'Preshape', time: dayjs() },
  { step: 'Final Shape', time: dayjs() },
  { step: 'Fridge', time: dayjs() },
];

const INITIAL_FORM_DATA: BreadFormData = {
  date: dayjs(),
  teamMake: 'hoagie', // Use lowercase to match API keys
  temperatures: INITIAL_TEMP_SETTINGS,
  processes: INITIAL_PROCESSES,
  stretchFolds: INITIAL_STRETCH_FOLDS,
  notes: '',
};

export const useBreadForm = () => {
  const [formData, setFormData] = useState<BreadFormData>(INITIAL_FORM_DATA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [customSuccessMessage, setCustomSuccessMessage] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDateChange = (newDate: Dayjs | null) => {
    setFormData((prev) => ({
      ...prev,
      date: newDate,
    }));
  };

  const handleTemperatureChange = (field: keyof TemperatureSettings, value: string) => {
    const numValue = parseFloat(value) || 0;
    setFormData((prev) => ({
      ...prev,
      temperatures: {
        ...prev.temperatures,
        [field]: numValue,
      },
    }));
  };

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

  const handleProcessTimeChange = (step: string, time: Dayjs | null) => {
    setFormData((prev) => ({
      ...prev,
      processes: prev.processes.map((process) =>
        process.step === step ? { ...process, time } : process
      ),
    }));
  };

  const addStretchFold = () => {
    const newId = Math.max(...formData.stretchFolds.map(sf => sf.id), 0) + 1;
    setFormData((prev) => ({
      ...prev,
      stretchFolds: [
        ...prev.stretchFolds,
        { id: newId, performed: false, time: null }
      ],
    }));
  };

  const removeStretchFold = (id: number) => {
    setFormData((prev) => ({
      ...prev,
      stretchFolds: prev.stretchFolds.filter(sf => sf.id !== id),
    }));
  };

  const updateStretchFold = (id: number, updates: Partial<StretchFold>) => {
    setFormData((prev) => ({
      ...prev,
      stretchFolds: prev.stretchFolds.map(sf =>
        sf.id === id ? { ...sf, ...updates } : sf
      ),
    }));
  };

  const resetForm = () => {
    const currentTime = dayjs();
    setFormData({
      date: dayjs(),
      teamMake: 'hoagie', // Use lowercase to match API keys
      temperatures: INITIAL_TEMP_SETTINGS,
      processes: [
        { step: 'Autolyse', time: currentTime },
        { step: 'Start', time: currentTime },
        { step: 'Pull', time: currentTime },
        { step: 'Preshape', time: currentTime },
        { step: 'Final Shape', time: currentTime },
        { step: 'Fridge', time: currentTime },
      ],
      stretchFolds: INITIAL_STRETCH_FOLDS,
      notes: '',
    });
    setError(null);
    setSuccess(false);
    setCustomSuccessMessage(null);
  };

  const validateForm = (): string | null => {
    if (!formData.date) {
      return 'Date is required';
    }
    if (!formData.teamMake) {
      return 'Team make is required';
    }
    // Add more validation as needed
    return null;
  };

  const populateFormWithDough = (dough: DoughMake) => {
    // Convert timestamps to dayjs objects
    const convertToDayjs = (timestamp: Date | undefined) => 
      timestamp ? dayjs(timestamp) : null;

    // Convert temperature unit string to enum
    const tempUnit = dough.temp_unit === 'Celsius' ? TemperatureUnit.CELSIUS : TemperatureUnit.FAHRENHEIT;

    // Create updated processes array with times from dough
    const updatedProcesses = [
      { step: 'Autolyse', time: convertToDayjs(dough.autolyse_ts) },
      { step: 'Start', time: convertToDayjs(dough.start_ts) },
      { step: 'Pull', time: convertToDayjs(dough.pull_ts) },
      { step: 'Preshape', time: convertToDayjs(dough.preshape_ts) },
      { step: 'Final Shape', time: convertToDayjs(dough.final_shape_ts) },
      { step: 'Fridge', time: convertToDayjs(dough.fridge_ts) },
    ];

    // Convert stretch folds data
    let stretchFolds = INITIAL_STRETCH_FOLDS;
    if (dough.stretch_folds && Array.isArray(dough.stretch_folds) && dough.stretch_folds.length > 0) {
      stretchFolds = dough.stretch_folds.map((fold: any, index: number) => ({
        id: index + 1,
        performed: true,
        time: fold.timestamp ? dayjs(fold.timestamp) : null
      }));
    }

    // Update form data with dough data
    setFormData({
      date: dayjs(dough.date),
      teamMake: dough.name,
      temperatures: {
        unit: tempUnit,
        roomTemp: dough.room_temp ?? 0,
        flourTemp: dough.flour_temp ?? 0,
        prefermentTemp: dough.preferment_temp ?? 0,
        waterTemp: dough.water_temp ?? 0,
        doughTemp: dough.dough_temp ?? 0,
      },
      processes: updatedProcesses,
      stretchFolds: stretchFolds,
      notes: dough.notes || '',
    });
  };

  const prepareSubmissionData = () => {
    const date = formData.date!;
    return {
      date: date.format('YYYY-MM-DD'),
      autolyse_ts: formData.processes.find(p => p.step === 'Autolyse')?.time?.toISOString(),
      start_ts: formData.processes.find(p => p.step === 'Start')?.time?.toISOString(),
      pull_ts: formData.processes.find(p => p.step === 'Pull')?.time?.toISOString(),
      preshape_ts: formData.processes.find(p => p.step === 'Preshape')?.time?.toISOString(),
      final_shape_ts: formData.processes.find(p => p.step === 'Final Shape')?.time?.toISOString(),
      fridge_ts: formData.processes.find(p => p.step === 'Fridge')?.time?.toISOString(),
      room_temp: formData.temperatures.roomTemp,
      water_temp: formData.temperatures.waterTemp,
      flour_temp: formData.temperatures.flourTemp,
      preferment_temp: formData.temperatures.prefermentTemp,
      dough_temp: formData.temperatures.doughTemp,
      temp_unit: formData.temperatures.unit,
      stretch_folds: formData.stretchFolds.filter(sf => sf.performed).map(sf => ({
        fold_number: sf.id,
        timestamp: sf.time?.toISOString()
      })),
      notes: formData.notes || null,
    };
  };

  const submitForm = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const date = formData.date!;
      const year = date.year();
      const month = date.month() + 1; // dayjs months are 0-indexed
      const day = date.date();

      const submissionData = prepareSubmissionData();
      await doughMakesApi.create(year, month, day, formData.teamMake, submissionData);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const updateForm = async (selectedDough: DoughMake, onUpdateSuccess?: () => void) => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);
    setCustomSuccessMessage(null);

    try {
      const date = formData.date!;
      const year = date.year();
      const month = date.month() + 1; // dayjs months are 0-indexed
      const day = date.date();

      const submissionData = prepareSubmissionData();
      // Lowercase the make name for PATCH requests
      const lowerCaseMakeName = formData.teamMake.toLowerCase();
      // Use original timestamp string for the API to avoid timezone conversion
      const createdAtString = selectedDough.created_at_original;
      await doughMakesApi.update(year, month, day, lowerCaseMakeName, createdAtString, submissionData);
      
      // Find the display name for the success message
      const displayName = selectedDough.name;
      const createdAtFormatted = selectedDough.created_at.toLocaleString();
      setCustomSuccessMessage(`Updated ${displayName} created at ${createdAtFormatted} successfully`);
      setSuccess(true);
      
      // Call the callback to clear selected dough and show the list again
      if (onUpdateSuccess) {
        onUpdateSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return {
    formData,
    setFormData,
    loading,
    error,
    success,
    customSuccessMessage,
    handleInputChange,
    handleDateChange,
    handleTemperatureChange,
    toggleTemperatureUnit,
    handleProcessTimeChange,
    addStretchFold,
    removeStretchFold,
    updateStretchFold,
    resetForm,
    submitForm,
    updateForm,
    populateFormWithDough,
  };
};