import { TemperatureUnit } from '../types/bread.ts';

/**
 * Convert temperature between Celsius and Fahrenheit
 */
export const convertTemperature = (
  temp: number,
  fromUnit: TemperatureUnit,
  toUnit: TemperatureUnit
): number => {
  if (fromUnit === toUnit) return temp;

  if (fromUnit === TemperatureUnit.CELSIUS && toUnit === TemperatureUnit.FAHRENHEIT) {
    return Math.round((temp * 9/5) + 32);
  }

  if (fromUnit === TemperatureUnit.FAHRENHEIT && toUnit === TemperatureUnit.CELSIUS) {
    return Math.round((temp - 32) * 5/9);
  }

  return temp;
};

/**
 * Format temperature with unit abbreviation
 */
export const formatTemperature = (temp: number, unit: TemperatureUnit): string => {
  const abbreviation = unit === TemperatureUnit.CELSIUS ? '°C' : '°F';
  return `${temp}${abbreviation}`;
};

/**
 * Validate temperature is within reasonable range
 */
export const isValidTemperature = (temp: number, unit: TemperatureUnit): boolean => {
  if (unit === TemperatureUnit.CELSIUS) {
    return temp >= -50 && temp <= 200; // -50°C to 200°C
  } else {
    return temp >= -58 && temp <= 392; // -58°F to 392°F
  }
};