import { useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import { 
  BreadFormData, 
  TemperatureUnit, 
  TemperatureSettings,
  DoughProcess,
  StretchFold,
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
  teamMake: 'Hoagie',
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

      // Prepare the data for API submission
      const submissionData = {
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

      await doughMakesApi.create(year, month, day, formData.teamMake, submissionData);
      setSuccess(true);
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
    handleInputChange,
    handleDateChange,
    handleTemperatureChange,
    toggleTemperatureUnit,
    handleProcessTimeChange,
    addStretchFold,
    removeStretchFold,
    updateStretchFold,
    submitForm,
  };
};