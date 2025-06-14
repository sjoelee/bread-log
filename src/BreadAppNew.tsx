import React, { useState } from 'react';
import dayjs from 'dayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TabType, DoughMake } from './types/bread.ts';
import { useBreadForm } from './hooks/useBreadForm.ts';
import { useTeamMakes } from './hooks/useTeamMakes.ts';
import { useSavedMakes } from './hooks/useSavedMakes.ts';
import { CreateTab } from './components/CreateTab.tsx';
import { SavedTab } from './components/SavedTab.tsx';

const BreadApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('create');
  const [isStretchFoldsExpanded, setIsStretchFoldsExpanded] = useState(false);
  const [selectedDough, setSelectedDough] = useState<DoughMake | null>(null);

  // Custom hooks for state management
  const {
    formData,
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
    updateForm,
    populateFormWithDough,
  } = useBreadForm();

  const {
    teamMakes,
    isLoading: isLoadingMakes,
    isAddMakeModalOpen,
    newMakeName,
    setNewMakeName,
    isAddingMake,
    addMakeError,
    openAddMakeModal,
    closeAddMakeModal,
    handleAddMake,
  } = useTeamMakes();

  const {
    savedMakes,
    isLoading: isLoadingSavedMakes,
    handleViewMake,
  } = useSavedMakes(activeTab, formData.date, selectedDough, setSelectedDough, populateFormWithDough);

  // Local handlers
  const handleStretchFoldsToggle = () => {
    setIsStretchFoldsExpanded(!isStretchFoldsExpanded);
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
      {/* Date and Make Name Row - Always visible */}
      <div className="flex gap-4 mb-6">
        <div className="w-1/2">
          <label className="block text-sm font-medium mb-1">Date</label>
          <DatePicker
            value={formData.date}
            onChange={handleDateChange}
            slotProps={{
              textField: {
                size: 'small',
                fullWidth: true,
              },
            }}
          />
        </div>
        <div className="w-1/2">
          <label className="block text-sm font-medium mb-1">Make Name</label>
          <div className="relative">
            <select
              name="teamMake"
              value={formData.teamMake}
              onChange={handleInputChange}
              className="w-full border rounded p-2 appearance-none pr-8 bg-white"
              disabled={isLoadingMakes}
            >
              {isLoadingMakes ? (
                <option>Loading...</option>
              ) : (
                teamMakes.map((make) => (
                  <option key={make.key} value={make.key}>
                    {make.displayName}
                  </option>
                ))
              )}
            </select>
            <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
              <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </span>
          </div>
          <button
            type="button"
            onClick={openAddMakeModal}
            className="text-red-500 text-sm mt-1 hover:underline"
            disabled={isLoadingMakes}
          >
            + Add new make
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex mb-6 border-b">
        <button
          onClick={() => {
            setActiveTab('create');
            setSelectedDough(null);
          }}
          className={`px-4 py-2 font-medium ${
            activeTab === 'create'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Create
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'saved'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Saved
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'create' ? (
        <CreateTab
          formData={formData}
          teamMakes={teamMakes}
          isLoadingMakes={isLoadingMakes}
          loading={loading}
          error={error}
          success={success}
          isStretchFoldsExpanded={isStretchFoldsExpanded}
          onDateChange={handleDateChange}
          onInputChange={handleInputChange}
          onTemperatureChange={handleTemperatureChange}
          onToggleTemperatureUnit={toggleTemperatureUnit}
          onProcessTimeChange={handleProcessTimeChange}
          onStretchFoldsToggle={handleStretchFoldsToggle}
          onAddStretchFold={addStretchFold}
          onRemoveStretchFold={removeStretchFold}
          onUpdateStretchFold={updateStretchFold}
          onSubmit={submitForm}
          isAddMakeModalOpen={isAddMakeModalOpen}
          newMakeName={newMakeName}
          onNewMakeNameChange={setNewMakeName}
          onOpenAddMakeModal={openAddMakeModal}
          onCloseAddMakeModal={closeAddMakeModal}
          onAddMake={handleAddMake}
          isAddingMake={isAddingMake}
          addMakeError={addMakeError}
        />
      ) : (
        <SavedTab
          savedMakes={savedMakes}
          isLoading={isLoadingSavedMakes}
          teamMakes={teamMakes}
          formattedDate={formData.date?.format('YYYY-MM-DD') || ''}
          onViewMake={handleViewMake}
          selectedDough={selectedDough}
          setSelectedDough={setSelectedDough}
          formData={formData}
          loading={loading}
          error={error}
          success={success}
          isStretchFoldsExpanded={isStretchFoldsExpanded}
          onInputChange={handleInputChange}
          onTemperatureChange={handleTemperatureChange}
          onToggleTemperatureUnit={toggleTemperatureUnit}
          onProcessTimeChange={handleProcessTimeChange}
          onStretchFoldsToggle={handleStretchFoldsToggle}
          onAddStretchFold={addStretchFold}
          onRemoveStretchFold={removeStretchFold}
          onUpdateStretchFold={updateStretchFold}
          onSubmit={submitForm}
          onUpdate={updateForm}
        />
      )}
    </div>
  );
};

export default BreadApp;