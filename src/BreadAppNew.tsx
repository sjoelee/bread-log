import React, { useState, useEffect } from 'react';
import dayjs from 'dayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TabType, DoughMake, DropdownOption } from './types/bread.ts';
import { useBreadForm } from './hooks/useBreadForm.ts';
import { useSavedMakes } from './hooks/useSavedMakes.ts';
import { CreateTab } from './components/CreateTab.tsx';
import { SavedTab } from './components/SavedTab.tsx';
import { RecipeTab } from './components/RecipeTab.tsx';

// Add main tab types
type MainTabType = 'recipe' | 'timing';

const BreadApp: React.FC = () => {
  const [activeMainTab, setActiveMainTab] = useState<MainTabType>('timing');
  const [activeTab, setActiveTab] = useState<TabType>('create');
  const [activeRecipeTab, setActiveRecipeTab] = useState<TabType>('create');
  const [isStretchFoldsExpanded, setIsStretchFoldsExpanded] = useState(false);
  const [selectedDough, setSelectedDough] = useState<DoughMake | null>(null);
  const [savedCreateFormData, setSavedCreateFormData] = useState<any>(null);
  
  // Recipe-specific state
  const [recipeLoading, setRecipeLoading] = useState(false);
  const [recipeError, setRecipeError] = useState<string | null>(null);
  const [recipeSuccess, setRecipeSuccess] = useState(false);
  const [recipeSuccessMessage, setRecipeSuccessMessage] = useState<string | null>(null);
  const [savedRecipes, setSavedRecipes] = useState<any[]>([]);
  const [loadingRecipes, setLoadingRecipes] = useState(false);
  
  // Timing-specific state for recent saved timings
  const [recentTimings, setRecentTimings] = useState<any[]>([]);
  const [loadingRecentTimings, setLoadingRecentTimings] = useState(false);
  const [timingsError, setTimingsError] = useState<string | null>(null);
  const [timingsPage, setTimingsPage] = useState(0);
  const [hasMoreTimings, setHasMoreTimings] = useState(true);
  
  // State for viewing/editing a specific timing
  const [editingTiming, setEditingTiming] = useState<any | null>(null);
  
  // Combined dropdown options (Makes + Recipes + Recent usage)
  const [dropdownOptions, setDropdownOptions] = useState<DropdownOption[]>([]);
  
  // Recipe preview state
  const [selectedRecipePreview, setSelectedRecipePreview] = useState<any | null>(null);
  const [isRecipePreviewExpanded, setIsRecipePreviewExpanded] = useState(false);
  
  // Dropdown state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState<DropdownOption[]>([]);

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
    savedMakes,
    isLoading: isLoadingSavedMakes,
    handleViewMake,
    refreshSavedMakes,
  } = useSavedMakes(activeTab, formData.date, selectedDough, setSelectedDough, populateFormWithDough);

  // Recipe loading function
  const loadSavedRecipes = async () => {
    try {
      setLoadingRecipes(true);
      setRecipeError(null);
      
      const isDevelopment = window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1';

      const apiBaseUrl = isDevelopment
        ? 'http://localhost:8000'
        : 'https://your-production-api.com';

      const response = await fetch(`${apiBaseUrl}/recipes/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const recipes = await response.json();
        setSavedRecipes(recipes);
      } else {
        console.error('Failed to load recipes:', response.statusText);
        setRecipeError(`Failed to load recipes: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error loading recipes:', error);
      setRecipeError(`Error loading recipes: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoadingRecipes(false);
    }
  };

  // Load ALL distinct dough makes names for dropdown (not paginated)
  const loadAllDistinctBreadNames = async () => {
    try {
      const isDevelopment = window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1';

      const apiBaseUrl = isDevelopment
        ? 'http://localhost:8000'
        : 'https://your-production-api.com';

      // New API call to get distinct bread names ordered by most recent created_at
      const response = await fetch(`${apiBaseUrl}/makes/distinct-names`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        const distinctBreadNames = result.names || result; // Handle different response formats
        
        // Process similar to recent timings but for dropdown purposes
        const processedNames = distinctBreadNames.map((item: any) => {
          return {
            name: item.name,
            created_at: new Date(item.latest_created_at), // Use latest usage
            created_at_original: item.latest_created_at,
          };
        });
        
        // Update recentTimings with ALL distinct names for dropdown
        setRecentTimings(processedNames);
      } else {
        console.error('Failed to load distinct bread names:', response.statusText);
      }
    } catch (error) {
      console.error('Error loading distinct bread names:', error);
    }
  };

  // Recent timings loading function
  const loadRecentTimings = async (page = 0, reset = false) => {
    try {
      setLoadingRecentTimings(true);
      setTimingsError(null);
      
      const isDevelopment = window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1';

      const apiBaseUrl = isDevelopment
        ? 'http://localhost:8000'
        : 'https://your-production-api.com';

      // API call to get recent dough makes (paginated)
      const response = await fetch(`${apiBaseUrl}/makes/recent?limit=10&offset=${page * 10}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header when implementing auth
          // 'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        const rawTimings = result.makes || result; // Handle different response formats
        
        // Process timings the same way as saved makes - preserve original created_at string
        const processedTimings = rawTimings.map((timing: any) => {
          if (!timing.created_at) {
            console.error('Backend did not return created_at timestamp for timing:', timing);
            return timing;
          }
          return {
            ...timing,
            created_at: new Date(timing.created_at),
            created_at_original: timing.created_at, // Preserve original string for API calls
            autolyse_ts: timing.autolyse_ts ? new Date(timing.autolyse_ts) : undefined,
            mix_ts: timing.mix_ts ? new Date(timing.mix_ts) : undefined,
            bulk_ts: timing.bulk_ts ? new Date(timing.bulk_ts) : undefined,
            preshape_ts: timing.preshape_ts ? new Date(timing.preshape_ts) : undefined,
            final_shape_ts: timing.final_shape_ts ? new Date(timing.final_shape_ts) : undefined,
            fridge_ts: timing.fridge_ts ? new Date(timing.fridge_ts) : undefined,
          };
        });
        
        if (reset || page === 0) {
          setRecentTimings(processedTimings);
        } else {
          setRecentTimings(prev => [...prev, ...processedTimings]);
        }
        
        // Check if there are more results
        setHasMoreTimings(processedTimings.length === 10);
        setTimingsPage(page);
      } else {
        console.error('Failed to load recent timings:', response.statusText);
        setTimingsError(`Failed to load recent timings: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error loading recent timings:', error);
      setTimingsError(`Error loading recent timings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoadingRecentTimings(false);
    }
  };

  // Build combined dropdown options from distinct dough_makes names and Recipes
  const buildDropdownOptions = () => {
    const options: DropdownOption[] = [];
    const usedNames = new Set<string>();
    
    // Create a set of recipe names for easy lookup
    const recipeNames = new Set(savedRecipes.map(recipe => recipe.name.toLowerCase()));

    // Add distinct names from recent timing entries (actual usage history)
    recentTimings.forEach((timing) => {
      if (timing.name && !usedNames.has(timing.name.toLowerCase())) {
        const isRecipe = recipeNames.has(timing.name.toLowerCase());
        options.push({
          value: timing.name,
          displayName: isRecipe ? `${timing.name} (Recipe)` : timing.name,
          type: isRecipe ? 'recipe' : 'recent',
          lastUsed: new Date(timing.created_at)
        });
        usedNames.add(timing.name.toLowerCase());
      }
    });

    // Add recipes that haven't been used in recent timing entries
    savedRecipes.forEach((recipe) => {
      if (recipe.name && !usedNames.has(recipe.name.toLowerCase())) {
        options.push({
          value: recipe.name,
          displayName: `${recipe.name} (Recipe)`,
          type: 'recipe',
          lastUsed: new Date(recipe.updated_at || recipe.created_at)
        });
        usedNames.add(recipe.name.toLowerCase());
      }
    });

    // Sort by most recently used (created_at), then alphabetically
    options.sort((a, b) => {
      if (a.lastUsed && b.lastUsed) {
        return b.lastUsed.getTime() - a.lastUsed.getTime();
      }
      if (a.lastUsed && !b.lastUsed) return -1;
      if (!a.lastUsed && b.lastUsed) return 1;
      return a.displayName.localeCompare(b.displayName);
    });

    setDropdownOptions(options);
  };

  // Load recipes and distinct bread names on component mount for timing dropdown
  React.useEffect(() => {
    loadSavedRecipes();
    loadAllDistinctBreadNames(); // Load ALL distinct names for dropdown
  }, []);

  // Load recipes when switching to saved tab
  React.useEffect(() => {
    if (activeMainTab === 'recipe' && activeRecipeTab === 'saved') {
      loadSavedRecipes();
    }
  }, [activeMainTab, activeRecipeTab]);

  // Load recent timings when switching to timing saved tab
  React.useEffect(() => {
    if (activeMainTab === 'timing' && activeTab === 'saved') {
      loadRecentTimings(0, true);
    }
  }, [activeMainTab, activeTab]);

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

  const handleUpdateRecentTiming = (selectedDough: DoughMake) => {
    updateForm(selectedDough, () => {
      setEditingTiming(null); // Clear editing state
      loadRecentTimings(0, true); // Refresh recent timings list
    });
  };

  // Handle recipe selection for preview and suggestions
  const handleRecipeInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    
    // Call the original handler
    handleInputChange(e);
    
    // Filter suggestions based on input
    const filtered = dropdownOptions.filter(option =>
      option.displayName.toLowerCase().includes(inputValue.toLowerCase()) ||
      option.value.toLowerCase().includes(inputValue.toLowerCase())
    );
    setFilteredOptions(filtered);
    setShowSuggestions(inputValue.length > 0 && filtered.length > 0);
    
    // Check if selected value matches a saved recipe
    const matchingRecipe = savedRecipes.find(recipe => recipe.name === inputValue);
    
    if (matchingRecipe) {
      setSelectedRecipePreview(matchingRecipe);
      setIsRecipePreviewExpanded(true);
    } else {
      setSelectedRecipePreview(null);
      setIsRecipePreviewExpanded(false);
    }
  };

  // Handle suggestion selection
  const handleSuggestionSelect = (option: DropdownOption) => {
    // Update the form data
    setFormData(prev => ({
      ...prev,
      teamMake: option.value
    }));
    
    // Hide suggestions
    setShowSuggestions(false);
    
    // Check if it's a recipe for preview
    const matchingRecipe = savedRecipes.find(recipe => recipe.name === option.value);
    if (matchingRecipe) {
      setSelectedRecipePreview(matchingRecipe);
      setIsRecipePreviewExpanded(true);
    } else {
      setSelectedRecipePreview(null);
      setIsRecipePreviewExpanded(false);
    }
  };

  // Handle input focus - show all suggestions
  const handleInputFocus = () => {
    setFilteredOptions(dropdownOptions);
    setShowSuggestions(dropdownOptions.length > 0);
  };

  // Handle input blur - hide suggestions after a small delay
  const handleInputBlur = () => {
    // Small delay to allow clicking on suggestions
    setTimeout(() => {
      setShowSuggestions(false);
    }, 200);
  };

  // Build dropdown options when data sources change
  useEffect(() => {
    buildDropdownOptions();
  }, [recentTimings, savedRecipes]);

  // Clear saved Create data and recipe preview when form is successfully submitted
  useEffect(() => {
    if (success && activeTab === 'create') {
      setSavedCreateFormData(null);
      setSelectedRecipePreview(null);
      setIsRecipePreviewExpanded(false);
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
                    // Clear editing state when switching to Create tab
                    setEditingTiming(null);
                    // Clear recipe preview when switching to Create tab
                    setSelectedRecipePreview(null);
                    setIsRecipePreviewExpanded(false);
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

          {/* Edit Mode Notification - Only for Timing Create tab when editing */}
          {activeMainTab === 'timing' && activeTab === 'create' && editingTiming && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <div>
                    <p className="text-blue-800 font-medium">Editing: {editingTiming.name}</p>
                    <p className="text-blue-600 text-sm">Made on {new Date(editingTiming.date).toLocaleDateString()}</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setEditingTiming(null);
                    resetForm();
                  }}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Cancel Edit
                </button>
              </div>
            </div>
          )}

          {/* Date and Make Name Row - Only for Timing Create tab */}
          {activeMainTab === 'timing' && activeTab === 'create' && (
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
                <label className="block text-sm font-medium mb-1">Bread</label>
                <div className="relative">
                  <input
                    type="text"
                    name="teamMake"
                    value={formData.teamMake}
                    onChange={handleRecipeInputChange}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    placeholder={loadingRecipes ? "Loading..." : "Select Bread"}
                    className="w-full border rounded p-2 pr-8"
                    disabled={loadingRecipes}
                    autoComplete="off"
                  />
                  <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                    <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                  
                  {/* Custom Suggestions Dropdown */}
                  {showSuggestions && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                      {filteredOptions.map((option, index) => (
                        <button
                          key={`${option.type}-${index}`}
                          type="button"
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                          onClick={() => handleSuggestionSelect(option)}
                        >
                          <div className="flex items-center justify-between">
                            <span>{option.displayName}</span>
                            {option.type === 'recent' && option.lastUsed && (
                              <span className="text-xs text-gray-400">
                                {new Date(option.lastUsed).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </button>
                      ))}
                      {filteredOptions.length === 0 && (
                        <div className="px-3 py-2 text-gray-500 italic">No matches found</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tab Content */}
          {activeMainTab === 'recipe' ? (
            activeRecipeTab === 'create' ? (
              <RecipeTab
                loading={recipeLoading}
                error={recipeError}
                success={recipeSuccess}
                successMessage={recipeSuccessMessage}
                onSubmit={async (recipeData) => {
                  try {
                    setRecipeLoading(true);
                    setRecipeError(null);
                    setRecipeSuccess(false);
                    setRecipeSuccessMessage(null);

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
                        category: recipeData.category,
                        ingredients: recipeData.ingredients,
                        instructions: recipeData.instructions
                      }),
                    });

                    if (response.ok) {
                      const result = await response.json();
                      console.log('Recipe created successfully:', result);
                      console.log('Version:', `${result.recipe.current_version.version_major}.${result.recipe.current_version.version_minor}`);
                      if (result.recipe.bakers_percentages) {
                        console.log('Baker\'s percentages calculated:', result.recipe.bakers_percentages);
                      }
                      
                      setRecipeSuccess(true);
                      setRecipeSuccessMessage(result.message);
                      
                      // Reload recipes list so it appears in Saved tab
                      loadSavedRecipes();
                    } else {
                      const errorText = await response.text();
                      console.error('Failed to create recipe:', response.statusText, errorText);
                      setRecipeError(`Failed to create recipe: ${response.statusText}`);
                    }
                  } catch (error) {
                    console.error('Error creating recipe:', error);
                    setRecipeError(`Error creating recipe: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  } finally {
                    setRecipeLoading(false);
                  }
                }}
              />
            ) : (
              // Recipe Saved tab content
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">Saved Recipes</h2>
                  <button
                    onClick={loadSavedRecipes}
                    disabled={loadingRecipes}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                  >
                    {loadingRecipes ? 'Loading...' : 'Refresh'}
                  </button>
                </div>

                {recipeError && (
                  <div className="text-red-500 mb-4 p-4 bg-red-50 rounded-md">
                    {recipeError}
                  </div>
                )}

                {loadingRecipes ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-500">Loading recipes...</p>
                  </div>
                ) : savedRecipes.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <div className="space-y-2">
                      <p className="font-medium">No Saved Recipes</p>
                      <p className="text-sm">Your saved recipes will appear here</p>
                      <p className="text-sm mt-4">Switch to the Create tab to add a new recipe</p>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {savedRecipes.map((recipe) => (
                      <div key={recipe.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                        <div className="mb-4">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">{recipe.name}</h3>
                          {recipe.description && (
                            <p className="text-gray-600 text-sm mb-2">{recipe.description}</p>
                          )}
                          {recipe.category && (
                            <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                              {recipe.category}
                            </span>
                          )}
                        </div>
                        
                        <div className="text-sm text-gray-500 space-y-1">
                          <p>Created: {new Date(recipe.created_at).toLocaleDateString()}</p>
                          {recipe.updated_at !== recipe.created_at && (
                            <p>Updated: {new Date(recipe.updated_at).toLocaleDateString()}</p>
                          )}
                        </div>
                        
                        <div className="mt-4 flex space-x-2">
                          <button 
                            className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 text-sm rounded-md font-medium"
                            onClick={() => {
                              console.log('View recipe:', recipe);
                              // TODO: Implement recipe viewing/editing
                            }}
                          >
                            View
                          </button>
                          <button 
                            className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 text-sm rounded-md font-medium"
                            onClick={() => {
                              console.log('Edit recipe:', recipe);
                              // TODO: Implement recipe editing
                            }}
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          ) : (
            // Timing tab content
            activeTab === 'create' ? (
              <>
                {/* Recipe Preview Section - Only show when a recipe is selected */}
                {selectedRecipePreview && (
                  <div className="mb-6">
                    <div className="space-y-4 p-4 border rounded-lg bg-green-50">
                      <button
                        type="button"
                        onClick={() => setIsRecipePreviewExpanded(!isRecipePreviewExpanded)}
                        className="flex items-center justify-between w-full p-3 bg-green-100 hover:bg-green-200 rounded-lg transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg">📝</span>
                          <div className="text-left">
                            <span className="font-medium text-green-800">Recipe Preview: {selectedRecipePreview.name}</span>
                            {selectedRecipePreview.current_version && (
                              <p className="text-sm text-green-600">
                                {selectedRecipePreview.current_version.ingredients?.length || 0} ingredients • {selectedRecipePreview.current_version.instructions?.length || 0} steps
                              </p>
                            )}
                          </div>
                        </div>
                        <svg
                          className={`h-5 w-5 transform transition-transform text-green-600 ${
                            isRecipePreviewExpanded ? 'rotate-180' : ''
                          }`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {isRecipePreviewExpanded && (
                        <div className="pl-4">
                          <div className="text-xs text-gray-700 bg-gray-50 p-4 rounded border overflow-auto max-h-96">
                            <pre className="whitespace-pre-wrap font-mono">
                              {JSON.stringify(selectedRecipePreview, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <CreateTab
                formData={formData}
                teamMakes={[]}
                isLoadingMakes={false}
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
                onSubmit={editingTiming ? () => handleUpdateRecentTiming(editingTiming) : submitForm}
                isEditing={!!editingTiming}
              />
              </>
            ) : (
              // Recent Timings Display for Timing Saved tab
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">Recent Bread Makes</h2>
                  <button
                    onClick={() => loadRecentTimings(0, true)}
                    disabled={loadingRecentTimings}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                  >
                    {loadingRecentTimings ? 'Loading...' : 'Refresh'}
                  </button>
                </div>

                {timingsError && (
                  <div className="text-red-500 mb-4 p-4 bg-red-50 rounded-md">
                    {timingsError}
                  </div>
                )}

                {loadingRecentTimings && recentTimings.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-500">Loading recent bread makes...</p>
                  </div>
                ) : recentTimings.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6l4 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="space-y-2">
                      <p className="font-medium">No Recent Bread Makes</p>
                      <p className="text-sm">Your recent bread making sessions will appear here</p>
                      <p className="text-sm mt-4">Switch to the Create tab to start a new bread make</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {recentTimings.map((timing) => (
                        <div key={`${timing.name}-${timing.date}-${timing.created_at}`} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900">{timing.name}</h3>
                              <p className="text-gray-600 text-sm">
                                {new Date(timing.date).toLocaleDateString()}
                              </p>
                            </div>
                            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                              Completed
                            </span>
                          </div>
                          
                          <div className="space-y-2 text-sm text-gray-600 mb-4">
                            <div className="flex justify-between">
                              <span>Autolyse:</span>
                              <span>{timing.autolyse_ts ? new Date(timing.autolyse_ts).toLocaleTimeString() : 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Mix:</span>
                              <span>{timing.mix_ts ? new Date(timing.mix_ts).toLocaleTimeString() : 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Bulk Ferment:</span>
                              <span>{timing.bulk_ts ? new Date(timing.bulk_ts).toLocaleTimeString() : 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Final Shape:</span>
                              <span>{timing.final_shape_ts ? new Date(timing.final_shape_ts).toLocaleTimeString() : 'N/A'}</span>
                            </div>
                            {timing.dough_temp && (
                              <div className="flex justify-between">
                                <span>Dough Temp:</span>
                                <span>{timing.dough_temp}°F</span>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex space-x-2">
                            <button 
                              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 text-sm rounded-md font-medium"
                              onClick={() => {
                                console.log('View/Edit timing details:', timing);
                                // Populate the form with timing data for editing
                                populateFormWithDough(timing);
                                // Set this timing as the one being edited
                                setEditingTiming(timing);
                                // Switch to Create tab (which will now be in edit mode)
                                setActiveTab('create');
                              }}
                            >
                              View & Edit
                            </button>
                            <button 
                              className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 text-sm rounded-md font-medium"
                              onClick={() => {
                                console.log('Use as template:', timing);
                                // Clear editing state to ensure we create a new make, not update existing
                                setEditingTiming(null);
                                // Populate form with timing data as template
                                populateFormWithDough(timing);
                                // Override the date to today for new make (template behavior)
                                setFormData(prev => ({
                                  ...prev,
                                  date: dayjs() // Set to today's date for new make
                                }));
                                // Switch to create tab (will be in create mode, not edit mode)
                                setActiveTab('create');
                              }}
                            >
                              Use Template
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {hasMoreTimings && (
                      <div className="text-center pt-6">
                        <button
                          onClick={() => loadRecentTimings(timingsPage + 1, false)}
                          disabled={loadingRecentTimings}
                          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                        >
                          {loadingRecentTimings ? 'Loading...' : 'Load More'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default BreadApp;