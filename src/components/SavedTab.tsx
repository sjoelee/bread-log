import React from 'react';
import { DoughMake, TeamMake } from '../types/bread';

interface SavedTabProps {
  savedMakes: DoughMake[];
  isLoading: boolean;
  teamMakes: TeamMake[];
  formattedDate: string;
  onViewMake: (make: DoughMake) => void;
}

export const SavedTab: React.FC<SavedTabProps> = ({
  savedMakes,
  isLoading,
  teamMakes,
  formattedDate,
  onViewMake
}) => {
  if (!formattedDate) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Please select a date to view saved makes</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Loading saved makes...</p>
      </div>
    );
  }

  if (savedMakes.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div className="space-y-2">
          <p className="font-medium">No saved makes found</p>
          <p className="text-sm">for {formattedDate}</p>
          <p className="text-sm mt-4">Switch to the Create tab to start a new make</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-blue-800 font-medium">
            Saved makes for {formattedDate}
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {savedMakes.map((make, index) => {
          // Find the displayName for this make's key
          const teamMake = teamMakes.find(tm => tm.key === make.name);
          const displayName = teamMake?.displayName || make.name;
          
          return (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <button
                onClick={() => onViewMake(make)}
                className="text-left w-full"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-blue-600 hover:text-blue-800">
                      {displayName}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {make.notes ? make.notes.substring(0, 100) + '...' : 'No notes'}
                    </p>
                    <div className="text-xs text-gray-500 mt-2">
                      {make.start_ts && `Started: ${make.start_ts.toLocaleTimeString()}`}
                    </div>
                  </div>
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};