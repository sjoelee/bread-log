import { Dayjs } from 'dayjs';

export enum TemperatureUnit {
  CELSIUS = 'Celsius',
  FAHRENHEIT = 'Fahrenheit'
}

export interface TemperatureSettings {
  unit: TemperatureUnit;
  roomTemp: number;
  flourTemp: number;
  prefermentTemp: number;
  waterTemp: number;
  doughTemp: number;
}

export interface DoughProcess {
  step: string;
  time: Dayjs | null;
}

export interface StretchFold {
  id: number;
  performed: boolean;
  time: Dayjs | null;
}

export interface BreadFormData {
  date: Dayjs | null;
  teamMake: string;
  temperatures: TemperatureSettings;
  processes: DoughProcess[];
  stretchFolds: StretchFold[];
  notes: string;
}

export interface TeamMake {
  displayName: string;
  key: string;
}

export interface DoughMake {
  name: string;
  date: string;
  created_at: Date;
  created_at_original: string; // Keep original timestamp string for API calls
  autolyse_ts?: Date;
  mix_ts?: Date;
  bulk_ts?: Date;
  preshape_ts?: Date;
  final_shape_ts?: Date;
  fridge_ts?: Date;
  room_temp?: number;
  water_temp?: number;
  flour_temp?: number;
  preferment_temp?: number;
  dough_temp?: number;
  temperature_unit?: string;
  stretch_folds?: any[];
  notes?: string;
}

export interface Make {
  key: string;
  display_name: string;
}

export interface FormattedMake {
  key: string;
  displayName: string;
}

export interface CreateMakeRequest {
  display_name: string;
  key: string;
}

export type TabType = 'create' | 'saved';

export interface DropdownOption {
  value: string;           // The actual name to use
  displayName: string;     // What to show in dropdown
  type: 'make' | 'recipe' | 'recent'; // Source type
  lastUsed?: Date;         // When last used in timing entry
}

// Default values
export const DEFAULT_TEAM_MAKES: TeamMake[] = [
  { displayName: 'Select a make...', key: '' },
  { displayName: 'Hoagie', key: 'hoagie' },
  { displayName: 'Demi', key: 'demi' },
  { displayName: 'Ube', key: 'ube' }
];

export const INITIAL_TEMP_SETTINGS: TemperatureSettings = {
  unit: TemperatureUnit.FAHRENHEIT,
  roomTemp: 0,
  flourTemp: 0,
  prefermentTemp: 0,
  waterTemp: 0,
  doughTemp: 0,
};

export const INITIAL_STRETCH_FOLDS: StretchFold[] = [
  { id: 1, performed: false, time: null },
];