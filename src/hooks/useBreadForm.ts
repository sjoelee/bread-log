import { useState, useRef } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import {
  BreadFormData,
  TemperatureUnit,
  TemperatureSettings,
  DoughProcess,
  INITIAL_TEMP_SETTINGS,
} from '../types/bread.ts';
import { convertTemperature } from '../utils/temperature.ts';
import { breadTimingApi } from '../services/api.ts';
import { BreadTiming, BreadTimingCreate } from '../types/bread.ts';

const INITIAL_PROCESSES: DoughProcess[] = [
  { step: 'Autolyse', time: null },
  { step: 'Mix', time: null },
  { step: 'Bulk', time: null },
  { step: 'Preshape', time: null },
  { step: 'Final Shape', time: null },
  { step: 'Fridge', time: null },
];

const INITIAL_FORM_DATA: BreadFormData = {
  date: dayjs(),
  teamMake: '',
  temperatures: INITIAL_TEMP_SETTINGS,
  processes: INITIAL_PROCESSES,
  stretchFoldCount: 0,
  notes: '',
};

export const useBreadForm = () => {
  const [formData, setFormData] = useState<BreadFormData>(INITIAL_FORM_DATA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [customSuccessMessage, setCustomSuccessMessage] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

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
    setFormData((prev) => {
      const updatedProcesses = prev.processes.map((process) =>
        process.step === step ? { ...process, time } : process
      );

      return {
        ...prev,
        processes: updatedProcesses,
      };
    });

    // Progressive time logic: Use a debounced approach to auto-fill next slot
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set a new timeout to auto-fill the next process after a brief delay
    // This ensures the user has finished selecting both hour and minute
    if (time && time.isValid()) {
      timeoutRef.current = setTimeout(() => {
        setFormData((prev) => {
          const currentIndex = prev.processes.findIndex(p => p.step === step);
          const nextIndex = currentIndex + 1;
          
          // Only auto-fill if next process exists and doesn't have a time set
          if (nextIndex < prev.processes.length && !prev.processes[nextIndex].time) {
            const updatedProcesses = [...prev.processes];
            updatedProcesses[nextIndex] = { ...updatedProcesses[nextIndex], time };
            
            return {
              ...prev,
              processes: updatedProcesses,
            };
          }
          
          return prev;
        });
      }, 1000); // 1 second delay to ensure complete selection
    }
  };

  const resetForm = () => {
    setFormData({
      date: dayjs(),
      teamMake: '',
      temperatures: INITIAL_TEMP_SETTINGS,
      processes: INITIAL_PROCESSES,
      stretchFoldCount: 0,
      notes: '',
    });
    setError(null);
    setSuccess(false);
    setCustomSuccessMessage(null);
  };

  const validateForm = (): string | null => {
    if (!formData.teamMake.trim()) {
      return 'Bread name is required. Type any name — it doesn\'t have to be a saved recipe.';
    }
    return null;
  };

  const populateFormWithBreadTiming = (timing: BreadTiming) => {
    // Convert timestamp strings to dayjs objects
    const convertToDayjs = (timestamp: string | undefined) => 
      timestamp ? dayjs(timestamp) : null;

    // Convert temperature unit string to enum
    const tempUnit = timing.temperature_unit === 'Celsius' ? TemperatureUnit.CELSIUS : TemperatureUnit.FAHRENHEIT;

    // Create updated processes array with times from timing
    const updatedProcesses = [
      { step: 'Autolyse', time: convertToDayjs(timing.autolyse_ts) },
      { step: 'Mix', time: convertToDayjs(timing.mix_ts) },
      { step: 'Bulk', time: convertToDayjs(timing.bulk_ts) },
      { step: 'Preshape', time: convertToDayjs(timing.preshape_ts) },
      { step: 'Final Shape', time: convertToDayjs(timing.final_shape_ts) },
      { step: 'Fridge', time: convertToDayjs(timing.fridge_ts) },
    ];

    setFormData({
      date: timing.date ? dayjs(timing.date) : dayjs(),
      teamMake: timing.recipe_name || '',
      temperatures: {
        unit: tempUnit,
        roomTemp: timing.room_temp ?? 0,
        flourTemp: timing.flour_temp ?? 0,
        prefermentTemp: timing.preferment_temp ?? 0,
        waterTemp: timing.water_temp ?? 0,
        doughTemp: timing.dough_temp ?? 0,
      },
      processes: updatedProcesses,
      stretchFoldCount: timing.stretch_fold_count ?? 0,
      notes: timing.notes || '',
    });
  };

  // Backward compatibility function for old DoughMake structure
  const populateFormWithDough = (dough: DoughMake) => {
    // Convert timestamps to dayjs objects
    const convertToDayjs = (timestamp: Date | undefined) => 
      timestamp ? dayjs(timestamp) : null;

    // Convert temperature unit string to enum
    const tempUnit = dough.temperature_unit === 'Celsius' ? TemperatureUnit.CELSIUS : TemperatureUnit.FAHRENHEIT;

    // Create updated processes array with times from dough
    const updatedProcesses = [
      { step: 'Autolyse', time: convertToDayjs(dough.autolyse_ts) },
      { step: 'Mix', time: convertToDayjs(dough.mix_ts) },
      { step: 'Bulk', time: convertToDayjs(dough.bulk_ts) },
      { step: 'Preshape', time: convertToDayjs(dough.preshape_ts) },
      { step: 'Final Shape', time: convertToDayjs(dough.final_shape_ts) },
      { step: 'Fridge', time: convertToDayjs(dough.fridge_ts) },
    ];

    setFormData({
      date: dayjs(dough.date),
      teamMake: dough.recipe_name || '',
      temperatures: {
        unit: tempUnit,
        roomTemp: dough.room_temp ?? 0,
        flourTemp: dough.flour_temp ?? 0,
        prefermentTemp: dough.preferment_temp ?? 0,
        waterTemp: dough.water_temp ?? 0,
        doughTemp: dough.dough_temp ?? 0,
      },
      processes: updatedProcesses,
      stretchFoldCount: 0,
      notes: dough.notes || '',
    });
  };

  const prepareSubmissionData = (): BreadTimingCreate => {
    // Prepare data, allowing all fields to be optional
    const data: BreadTimingCreate = {};
    
    // Only include fields that have values
    if (formData.teamMake && formData.teamMake.trim()) {
      data.recipe_name = formData.teamMake;
    }
    
    if (formData.date) {
      data.date = formData.date.format('YYYY-MM-DD');
    }
    
    // Process timestamps - only include if time is set
    const autolyse = formData.processes.find(p => p.step === 'Autolyse')?.time;
    if (autolyse) data.autolyse_ts = autolyse.toISOString();
    
    const mix = formData.processes.find(p => p.step === 'Mix')?.time;
    if (mix) data.mix_ts = mix.toISOString();
    
    const bulk = formData.processes.find(p => p.step === 'Bulk')?.time;
    if (bulk) data.bulk_ts = bulk.toISOString();
    
    const preshape = formData.processes.find(p => p.step === 'Preshape')?.time;
    if (preshape) data.preshape_ts = preshape.toISOString();
    
    const finalShape = formData.processes.find(p => p.step === 'Final Shape')?.time;
    if (finalShape) data.final_shape_ts = finalShape.toISOString();
    
    const fridge = formData.processes.find(p => p.step === 'Fridge')?.time;
    if (fridge) data.fridge_ts = fridge.toISOString();
    
    // Temperature data - only include if set
    if (formData.temperatures.roomTemp !== null) data.room_temp = formData.temperatures.roomTemp;
    if (formData.temperatures.waterTemp !== null) data.water_temp = formData.temperatures.waterTemp;
    if (formData.temperatures.flourTemp !== null) data.flour_temp = formData.temperatures.flourTemp;
    if (formData.temperatures.prefermentTemp !== null) data.preferment_temp = formData.temperatures.prefermentTemp;
    if (formData.temperatures.doughTemp !== null) data.dough_temp = formData.temperatures.doughTemp;
    
    // Always include temperature unit if we have any temperatures
    if (formData.temperatures.roomTemp !== null || formData.temperatures.waterTemp !== null ||
        formData.temperatures.flourTemp !== null || formData.temperatures.prefermentTemp !== null ||
        formData.temperatures.doughTemp !== null) {
      data.temperature_unit = formData.temperatures.unit;
    }
    
    // Stretch & fold count
    data.stretch_fold_count = formData.stretchFoldCount;

    // Notes
    if (formData.notes && formData.notes.trim()) {
      data.notes = formData.notes;
    }
    
    return data;
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
      const submissionData = prepareSubmissionData();
      const createdTiming = await breadTimingApi.create(submissionData);
      
      // Show different message based on completeness
      const statusMessage = createdTiming.status === 'completed' 
        ? 'Timing saved successfully!' 
        : 'Draft saved! You can continue editing later.';
      
      setCustomSuccessMessage(statusMessage);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  // New function for updating bread timings with UUID
  const updateBreadTiming = async (timingId: string, onUpdateSuccess?: () => void) => {
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
      const submissionData = prepareSubmissionData();
      
      // Convert to update format (include only changed fields)
      const updates = {
        recipe_name: submissionData.recipe_name,
        autolyse_ts: submissionData.autolyse_ts || null,
        mix_ts: submissionData.mix_ts || null,
        bulk_ts: submissionData.bulk_ts || null,
        preshape_ts: submissionData.preshape_ts || null,
        final_shape_ts: submissionData.final_shape_ts || null,
        fridge_ts: submissionData.fridge_ts || null,
        room_temp: submissionData.room_temp || null,
        water_temp: submissionData.water_temp || null,
        flour_temp: submissionData.flour_temp || null,
        preferment_temp: submissionData.preferment_temp || null,
        dough_temp: submissionData.dough_temp || null,
        temperature_unit: submissionData.temperature_unit,
        stretch_fold_count: submissionData.stretch_fold_count ?? 0,
        notes: submissionData.notes || null,
      };

      const updatedTiming = await breadTimingApi.update(timingId, updates);
      
      // Show different message based on completeness
      const statusMessage = updatedTiming.status === 'completed' 
        ? `Timing updated successfully!`
        : `Draft updated! ${updatedTiming.status === 'in_progress' ? 'Continue editing to complete.' : ''}`;
      
      setCustomSuccessMessage(statusMessage);
      setSuccess(true);
      
      // Call the callback to clear selected timing and show the list again
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
    resetForm,
    submitForm,
    populateFormWithDough,
    // New functions for bread timing API
    updateBreadTiming,
    populateFormWithBreadTiming,
  };
};