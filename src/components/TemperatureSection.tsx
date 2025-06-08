import React from 'react';
import { TemperatureUnit, TemperatureSettings } from '../types/bread.ts';

interface TemperatureSectionProps {
  temperatures: TemperatureSettings;
  onTemperatureChange: (field: keyof TemperatureSettings, value: string) => void;
  onToggleUnit: (unit: TemperatureUnit) => void;
}

export const TemperatureSection: React.FC<TemperatureSectionProps> = ({
  temperatures,
  onTemperatureChange,
  onToggleUnit,
}) => {
  const temperatureFields = [
    { key: 'roomTemp' as const, label: 'Room' },
    { key: 'flourTemp' as const, label: 'Flour' },
    { key: 'prefermentTemp' as const, label: 'Preferment' },
    { key: 'waterTemp' as const, label: 'Water' },
    { key: 'doughTemp' as const, label: 'Dough' },
  ];

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Temperatures</h2>
        <div className="flex rounded-lg border border-gray-300 overflow-hidden">
          <button
            type="button"
            onClick={() => onToggleUnit(TemperatureUnit.FAHRENHEIT)}
            className={`px-3 py-1 text-sm font-medium ${
              temperatures.unit === TemperatureUnit.FAHRENHEIT
                ? 'bg-blue-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            F
          </button>
          <button
            type="button"
            onClick={() => onToggleUnit(TemperatureUnit.CELSIUS)}
            className={`px-3 py-1 text-sm font-medium ${
              temperatures.unit === TemperatureUnit.CELSIUS
                ? 'bg-blue-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            C
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {temperatureFields.map(({ key, label }) => (
          <div key={key} className="text-center">
            <label className="block text-sm font-medium mb-2">{label}</label>
            <input
              type="number"
              value={temperatures[key]}
              onChange={(e) => onTemperatureChange(key, e.target.value)}
              className="w-full border rounded p-2 text-center"
              placeholder="0"
            />
          </div>
        ))}
      </div>
    </div>
  );
};