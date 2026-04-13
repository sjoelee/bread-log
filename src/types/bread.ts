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

// New Bread Timing types for REST API
export interface BreadTimingStretchFold {
  fold_number: number;
  timestamp: string; // ISO datetime string
}

export interface BreadTimingCreate {
  recipe_name?: string;
  date?: string; // YYYY-MM-DD format
  status?: string; // 'in_progress' | 'completed'
  autolyse_ts?: string; // ISO datetime strings
  mix_ts?: string;
  bulk_ts?: string;
  preshape_ts?: string;
  final_shape_ts?: string;
  fridge_ts?: string;
  room_temp?: number;
  water_temp?: number;
  flour_temp?: number;
  preferment_temp?: number;
  dough_temp?: number;
  temperature_unit?: string;
  stretch_folds?: BreadTimingStretchFold[];
  notes?: string;
}

export interface BreadTimingUpdate {
  recipe_name?: string;
  status?: string; // 'in_progress' | 'completed'
  autolyse_ts?: string | null;
  mix_ts?: string | null;
  bulk_ts?: string | null;
  preshape_ts?: string | null;
  final_shape_ts?: string | null;
  fridge_ts?: string | null;
  room_temp?: number | null;
  water_temp?: number | null;
  flour_temp?: number | null;
  preferment_temp?: number | null;
  dough_temp?: number | null;
  temperature_unit?: string;
  stretch_folds?: BreadTimingStretchFold[] | null;
  notes?: string | null;
}

export interface BreadTiming {
  id: string; // UUID
  recipe_name?: string;
  date?: string; // YYYY-MM-DD format
  status: string; // 'in_progress' | 'completed'
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  autolyse_ts?: string;
  mix_ts?: string;
  bulk_ts?: string;
  preshape_ts?: string;
  final_shape_ts?: string;
  fridge_ts?: string;
  room_temp?: number;
  water_temp?: number;
  flour_temp?: number;
  preferment_temp?: number;
  dough_temp?: number;
  temperature_unit: string;
  stretch_folds: BreadTimingStretchFold[];
  notes?: string;
}

export interface BreadTimingListResponse {
  timings: BreadTiming[];
  total_count: number;
  page: number;
  limit: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
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