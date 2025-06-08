import React from 'react';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { Dayjs } from 'dayjs';
import { DoughProcess } from '../types/bread';

interface ProcessSectionProps {
  processes: DoughProcess[];
  onProcessTimeChange: (step: string, time: Dayjs | null) => void;
}

export const ProcessSection: React.FC<ProcessSectionProps> = ({
  processes,
  onProcessTimeChange,
}) => {
  return (
    <div className="space-y-4">
      {processes.map((process) => (
        <div key={process.step} className="flex items-center gap-4">
          <label className="w-20 text-sm font-medium">
            {process.step}
          </label>
          <div className="flex-1">
            <div className="relative">
              <span className="absolute left-2 top-1 text-xs text-gray-500 z-10">Time</span>
              <TimePicker
                value={process.time}
                onChange={(newTime) => onProcessTimeChange(process.step, newTime)}
                slotProps={{
                  textField: {
                    size: 'small',
                    fullWidth: true,
                    sx: { '& .MuiInputBase-input': { paddingTop: '20px' } }
                  },
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};