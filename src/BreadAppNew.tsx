import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TabType, DoughMake } from './types/bread.ts';
import { useBreadForm } from './hooks/useBreadForm.ts';
import { useTeamMakes } from './hooks/useTeamMakes.ts';
import { useSavedMakes } from './hooks/useSavedMakes.ts';
import { CreateTab } from './components/CreateTab.tsx';
import { SavedTab } from './components/SavedTab.tsx';
import { RecipeTab } from './components/RecipeTab.tsx';
import { AddMakeModal } from './components/AddMakeModal.tsx';

// Add main tab types
type MainTabType = 'recipe' | 'timing';

const BreadApp: React.FC = () => {
  const [activeMainTab, setActiveMainTab] = useState<MainTabType>('timing');
  const [activeTab, setActiveTab] = useState<TabType>('create');
  const [activeRecipeTab, setActiveRecipeTab] = useState<TabType>('create');
  const [isStretchFoldsExpanded, setIsStretchFoldsExpanded] = useState(false);
  const [selectedDough, setSelectedDough] = useState<DoughMake | null>(null);
  const [savedCreateFormData, setSavedCreateFormData] = useState<any>(null);

  // Custom hooks for state management
  const {
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
    addStretchFold,
    removeStretchFold,
    updateStretchFold,
    resetForm,
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
    refreshSavedMakes,
  } = useSavedMakes(activeTab, formData.date, selectedDough, setSelectedDough, populateFormWithDough);

  // Local handlers
  const handleStretchFoldsToggle = () => {
    setIsStretchFoldsExpanded(!isStretchFoldsExpanded);
  };

  const handleUpdateWithCallback = (selectedDough: DoughMake) => {
    updateForm(selectedDough, () => {
      setSelectedDough(null); // Clear selected dough to show the list again
      refreshSavedMakes(); // Refresh the list to get updated data
    });
  };

  const handleViewMakeWithClearSave = (make: DoughMake) => {
    setSavedCreateFormData(null); // Clear saved Create data when viewing a saved make
    handleViewMake(make);
  };

  // Clear saved Create data when form is successfully submitted
  useEffect(() => {
    if (success && activeTab === 'create') {
      setSavedCreateFormData(null);
    }
  }, [success, activeTab]);

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow p-6">
      <div className="flex gap-6">
        {/* Left Sidebar - Tab Navigation */}
        <div className="w-16 flex-shrink-0">
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setActiveMainTab('recipe')}
              className={`w-full h-24 px-2 font-medium text-sm border rounded-r-lg transition-all flex items-center justify-center ${
                activeMainTab === 'recipe'
                  ? 'bg-blue-50 text-blue-600 border-blue-300 border-l-4 border-l-blue-600'
                  : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
              }`}
            >
              <span className="transform -rotate-90 whitespace-nowrap">Recipe</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveMainTab('timing')}
              className={`w-full h-24 px-2 font-medium text-sm border rounded-r-lg transition-all flex items-center justify-center ${
                activeMainTab === 'timing'
                  ? 'bg-blue-50 text-blue-600 border-blue-300 border-l-4 border-l-blue-600'
                  : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
              }`}
            >
              <span className="transform -rotate-90 whitespace-nowrap">Timing</span>
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1">
          {/* Date and Make Name Row - Only for Timing tab */}
          {activeMainTab === 'timing' && (
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
          )}

          {/* Sub Tab Navigation for Recipe tab */}
          {activeMainTab === 'recipe' && (
            <div className="flex mb-6 border-b">
              <button
                onClick={() => setActiveRecipeTab('create')}
                className={`px-4 py-2 font-medium ${
                  activeRecipeTab === 'create'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Create
              </button>
              <button
                onClick={() => setActiveRecipeTab('saved')}
                className={`px-4 py-2 font-medium ${
                  activeRecipeTab === 'saved'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Saved
              </button>
            </div>
          )}

          {/* Sub Tab Navigation for Timing tab */}
          {activeMainTab === 'timing' && (
            <div className="flex mb-6 border-b">
              <button
                onClick={() => {
                  if (activeTab === 'saved') {
                    // Switching from Saved to Create
                    setActiveTab('create');
                    setSelectedDough(null);
                    // Restore saved Create form data if it exists
                    if (savedCreateFormData) {
                      setFormData(savedCreateFormData);
                    } else {
                      resetForm(); // Only reset if no saved data
                    }
                  }
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
                onClick={() => {
                  if (activeTab === 'create') {
                    // Switching from Create to Saved - save the current form data
                    setSavedCreateFormData(formData);
                  }
                  setActiveTab('saved');
                }}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'saved'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Saved
              </button>
            </div>
          )}

          {/* Tab Content */}
          {activeMainTab === 'recipe' ? (
            activeRecipeTab === 'create' ? (
              <RecipeTab
                loading={loading}
                error={error}
                success={success}
                onSubmit={async (recipeData) => {
                  try {
                    const isDevelopment = window.location.hostname === 'localhost' ||
                      window.location.hostname === '127.0.0.1';

                    const apiBaseUrl = isDevelopment
                      ? 'http://localhost:8000'
                      : 'https://your-production-api.com';

                    const response = await fetch(`${apiBaseUrl}/recipes/`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        name: recipeData.name,
                        description: recipeData.description,
                        instructions: recipeData.instructions,
                        flour_ingredients: recipeData.flourIngredients,
                        other_ingredients: recipeData.otherIngredients
                      }),
                    });

                    if (response.ok) {
                      const result = await response.json();
                      console.log('Recipe created successfully:', result);
                      // TODO: Add success handling
                    } else {
                      console.error('Failed to create recipe:', response.statusText);
                      // TODO: Add error handling
                    }
                  } catch (error) {
                    console.error('Error creating recipe:', error);
                    // TODO: Add error handling
                  }
                }}
              />
            ) : (
              // Recipe Saved tab content - placeholder for now
              <div className="text-center py-12 text-gray-500">
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <div className="space-y-2">
                  <p className="font-medium">Saved Recipes</p>
                  <p className="text-sm">Your saved recipes will appear here</p>
                  <p className="text-sm mt-4">Switch to the Create tab to add a new recipe</p>
                </div>
              </div>
            )
          ) : (
            // Timing tab content
            activeTab === 'create' ? (
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
              />
            ) : (
              <SavedTab
                savedMakes={savedMakes}
                isLoading={isLoadingSavedMakes}
                teamMakes={teamMakes}
                formattedDate={formData.date?.format('YYYY-MM-DD') || ''}
                onViewMake={handleViewMakeWithClearSave}
                selectedDough={selectedDough}
                setSelectedDough={setSelectedDough}
                formData={formData}
                loading={loading}
                error={error}
                success={success}
                customSuccessMessage={customSuccessMessage}
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
                onUpdate={handleUpdateWithCallback}
              />
            )
          )}
        </div>
      </div>
      
      {/* Add Make Modal */}
      <AddMakeModal
        isOpen={isAddMakeModalOpen}
        newMakeName={newMakeName}
        onNameChange={setNewMakeName}
        onClose={closeAddMakeModal}
        onAdd={handleAddMake}
        isAdding={isAddingMake}
        error={addMakeError}
      />
    </div>
  );
};

export default BreadApp;