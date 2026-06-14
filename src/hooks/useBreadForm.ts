import { useState, useEffect, useRef } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);
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

const TIMING_DRAFT_KEY = 'bread-log:timing-draft';

const serializeDraft = (data: BreadFormData) => ({
  ...data,
  date: data.date?.toISOString() ?? null,
  processes: data.processes.map(p => ({
    ...p,
    date: p.date?.toISOString() ?? null,
    time: p.time?.toISOString() ?? null,
  })),
});

const deserializeDraft = (raw: any): BreadFormData => ({
  ...raw,
  date: raw.date ? dayjs(raw.date) : dayjs(),
  processes: raw.processes.map((p: any) => ({
    ...p,
    date: p.date ? dayjs(p.date) : dayjs(),
    time: p.time ? dayjs(p.time) : null,
  })),
});

const loadTimingDraft = (): BreadFormData | null => {
  try {
    const raw = localStorage.getItem(TIMING_DRAFT_KEY);
    return raw ? deserializeDraft(JSON.parse(raw)) : null;
  } catch {
    return null;
  }
};

const clearTimingDraft = () => {
  try { localStorage.removeItem(TIMING_DRAFT_KEY); } catch {}
};

const INITIAL_PROCESSES: DoughProcess[] = [
  { step: 'Autolyse', date: dayjs(), time: null },
  { step: 'Mix', date: dayjs(), time: null },
  { step: 'Bulk', date: dayjs(), time: null },
  { step: 'Preshape', date: dayjs(), time: null },
  { step: 'Final Shape', date: dayjs(), time: null },
  { step: 'Final Proof', date: dayjs(), time: null },
  { step: 'Bake', date: dayjs(), time: null },
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
  const isDraftMode = useRef(true);
  const [formData, setFormData] = useState<BreadFormData>(() => loadTimingDraft() ?? INITIAL_FORM_DATA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [customSuccessMessage, setCustomSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isDraftMode.current) {
      try { localStorage.setItem(TIMING_DRAFT_KEY, JSON.stringify(serializeDraft(formData))); } catch {}
    }
  }, [formData]);

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
      processes: prev.processes.map((process, index) =>
        index === 0 ? { ...process, date: newDate } : process
      ),
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

  const handleProcessTimeOpen = (step: string) => {
    setFormData((prev) => {
      const currentIndex = prev.processes.findIndex(p => p.step === step);
      const current = prev.processes[currentIndex];
      if (current.time !== null) return prev; // already set, don't override

      const updatedProcesses = [...prev.processes];
      if (currentIndex === 0) {
        updatedProcesses[0] = { ...current, time: dayjs() };
      } else {
        const prevStep = prev.processes[currentIndex - 1];
        updatedProcesses[currentIndex] = {
          ...current,
          time: prevStep.time ?? dayjs(),
          date: prevStep.date ?? current.date,
        };
      }
      return { ...prev, processes: updatedProcesses };
    });
  };

  const handleProcessDateChange = (step: string, date: Dayjs | null) => {
    setFormData((prev) => ({
      ...prev,
      processes: prev.processes.map((process) =>
        process.step === step ? { ...process, date } : process
      ),
    }));
  };

  const resetForm = () => {
    isDraftMode.current = true;
    clearTimingDraft();
    setFormData({
      date: dayjs(),
      teamMake: '',
      recipeId: undefined,
      recipeVersionId: undefined,
      temperatures: INITIAL_TEMP_SETTINGS,
      processes: INITIAL_PROCESSES.map(p => ({ ...p, date: dayjs() })),
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
    isDraftMode.current = false;
    const tz = timing.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
    const getDate = (ts: string | undefined) => ts ? dayjs.utc(ts).tz(tz) : dayjs();
    const getTime = (ts: string | undefined) => ts ? dayjs.utc(ts).tz(tz) : null;

    // Convert temperature unit string to enum
    const tempUnit = timing.temperature_unit === 'Celsius' ? TemperatureUnit.CELSIUS : TemperatureUnit.FAHRENHEIT;

    // Create updated processes array with per-step dates and times from timing
    const updatedProcesses = [
      { step: 'Autolyse', date: getDate(timing.autolyse_ts), time: getTime(timing.autolyse_ts) },
      { step: 'Mix', date: getDate(timing.mix_ts), time: getTime(timing.mix_ts) },
      { step: 'Bulk', date: getDate(timing.bulk_ts), time: getTime(timing.bulk_ts) },
      { step: 'Preshape', date: getDate(timing.preshape_ts), time: getTime(timing.preshape_ts) },
      { step: 'Final Shape', date: getDate(timing.final_shape_ts), time: getTime(timing.final_shape_ts) },
      { step: 'Final Proof', date: getDate(timing.final_proof_ts), time: getTime(timing.final_proof_ts) },
      { step: 'Bake', date: getDate(timing.bake_ts), time: getTime(timing.bake_ts) },
    ];

    setFormData({
      date: timing.date ? dayjs(timing.date) : dayjs(),
      teamMake: timing.recipe_name || '',
      recipeId: timing.recipe_id,
      recipeVersionId: timing.recipe_version_id,
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
      { step: 'Autolyse', date: dayjs(dough.date), time: convertToDayjs(dough.autolyse_ts) },
      { step: 'Mix', date: dayjs(dough.date), time: convertToDayjs(dough.mix_ts) },
      { step: 'Bulk', date: dayjs(dough.date), time: convertToDayjs(dough.bulk_ts) },
      { step: 'Preshape', date: dayjs(dough.date), time: convertToDayjs(dough.preshape_ts) },
      { step: 'Final Shape', date: dayjs(dough.date), time: convertToDayjs(dough.final_shape_ts) },
      { step: 'Final Proof', date: dayjs(dough.date), time: convertToDayjs(dough.fridge_ts) },
      { step: 'Bake', date: dayjs(dough.date), time: null },
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

    if (formData.recipeId) data.recipe_id = formData.recipeId;
    if (formData.recipeVersionId) data.recipe_version_id = formData.recipeVersionId;
    
    if (formData.date) {
      data.date = formData.date.format('YYYY-MM-DD');
    }
    
    // Combine per-step date + time into a full ISO timestamp
    const combineDateTime = (process: DoughProcess | undefined): string | undefined => {
      if (!process?.time) return undefined;
      const d = process.date ?? dayjs();
      return d.hour(process.time.hour()).minute(process.time.minute()).second(0).millisecond(0).toISOString();
    };

    // Process timestamps - only include if time is set
    const autolyse = formData.processes.find(p => p.step === 'Autolyse');
    const autolyseTs = combineDateTime(autolyse);
    if (autolyseTs) data.autolyse_ts = autolyseTs;

    const mix = formData.processes.find(p => p.step === 'Mix');
    const mixTs = combineDateTime(mix);
    if (mixTs) data.mix_ts = mixTs;

    const bulk = formData.processes.find(p => p.step === 'Bulk');
    const bulkTs = combineDateTime(bulk);
    if (bulkTs) data.bulk_ts = bulkTs;

    const preshape = formData.processes.find(p => p.step === 'Preshape');
    const preshapeTs = combineDateTime(preshape);
    if (preshapeTs) data.preshape_ts = preshapeTs;

    const finalShape = formData.processes.find(p => p.step === 'Final Shape');
    const finalShapeTs = combineDateTime(finalShape);
    if (finalShapeTs) data.final_shape_ts = finalShapeTs;

    const finalProof = formData.processes.find(p => p.step === 'Final Proof');
    const finalProofTs = combineDateTime(finalProof);
    if (finalProofTs) data.final_proof_ts = finalProofTs;

    const bake = formData.processes.find(p => p.step === 'Bake');
    const bakeTs = combineDateTime(bake);
    if (bakeTs) data.bake_ts = bakeTs;
    
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

    data.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

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
      clearTimingDraft();

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
        final_proof_ts: submissionData.final_proof_ts || null,
        bake_ts: submissionData.bake_ts || null,
        room_temp: submissionData.room_temp || null,
        water_temp: submissionData.water_temp || null,
        flour_temp: submissionData.flour_temp || null,
        preferment_temp: submissionData.preferment_temp || null,
        dough_temp: submissionData.dough_temp || null,
        temperature_unit: submissionData.temperature_unit,
        stretch_fold_count: submissionData.stretch_fold_count ?? 0,
        notes: submissionData.notes || null,
        recipe_id: submissionData.recipe_id ?? null,
        recipe_version_id: submissionData.recipe_version_id ?? null,
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
    handleProcessTimeOpen,
    handleProcessDateChange,
    resetForm,
    submitForm,
    populateFormWithDough,
    // New functions for bread timing API
    updateBreadTiming,
    populateFormWithBreadTiming,
  };
};