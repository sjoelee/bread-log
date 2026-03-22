import React, { useState } from 'react';

interface Ingredient {
  id?: string;
  name: string;
  amount: number;
  unit: string;
  type: string; // 'flour', 'liquid', 'preferment', 'other', etc.
  notes?: string;
}

interface RecipeStep {
  id?: string;
  order: number;
  instruction: string;
}

interface BakersPercentages {
  total_flour_weight: number;
  flour_ingredients: Array<{
    ingredient_id?: string;
    name: string;
    amount: number;
    percentage: number;
  }>;
  other_ingredients: Array<{
    ingredient_id?: string;
    name: string;
    amount: number;
    percentage: number;
  }>;
}

interface RecipeFormData {
  name: string;
  description?: string;
  category?: string;
  ingredients: Ingredient[];
  instructions: RecipeStep[];
}

interface RecipeResponse {
  id: string;
  name: string;
  description?: string;
  category?: string;
  current_version_id: string;
  current_version: {
    id: string;
    recipe_id: string;
    version_number: number;
    description?: string;
    ingredients: Ingredient[];
    instructions: RecipeStep[];
    created_at: string;
  };
  bakers_percentages?: BakersPercentages;
  created_at: string;
  updated_at: string;
}

interface RecipeTabProps {
  loading?: boolean;
  error?: string | null;
  success?: boolean;
  successMessage?: string | null;
  recipe?: RecipeResponse | null; // For editing existing recipes
  onSubmit?: (data: RecipeFormData) => void;
}

export const RecipeTab: React.FC<RecipeTabProps> = ({
  loading = false,
  error = null,
  success = false,
  successMessage = null,
  recipe = null,
  onSubmit
}) => {
  const [formData, setFormData] = useState<RecipeFormData>(() => {
    if (recipe) {
      // Load existing recipe for editing
      return {
        name: recipe.name,
        description: recipe.description || '',
        category: recipe.category || '',
        ingredients: recipe.current_version.ingredients,
        instructions: recipe.current_version.instructions
      };
    }
    
    // Default for new recipe
    return {
      name: '',
      description: '',
      category: '',
      ingredients: [
        { name: '', amount: 0, unit: 'grams', type: 'flour', notes: '' },
        { name: '', amount: 0, unit: 'grams', type: 'liquid', notes: '' }
      ],
      instructions: [{ order: 1, instruction: '' }]
    };
  });

  const handleInputChange = (field: keyof RecipeFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleIngredientChange = (
    index: number,
    field: keyof Ingredient,
    value: string | number
  ) => {
    setFormData(prev => ({
      ...prev,
      ingredients: prev.ingredients.map((ingredient, i) =>
        i === index ? { ...ingredient, [field]: value } : ingredient
      )
    }));
  };

  const addIngredient = (type: string = 'other') => {
    const newOrder = Math.max(...formData.ingredients.map((_, i) => i + 1)) + 1;
    setFormData(prev => ({
      ...prev,
      ingredients: [...prev.ingredients, { name: '', amount: 0, unit: 'grams', type, notes: '' }]
    }));
  };

  const removeIngredient = (index: number) => {
    if (formData.ingredients.length <= 1) return; // Keep at least one ingredient
    
    setFormData(prev => ({
      ...prev,
      ingredients: prev.ingredients.filter((_, i) => i !== index)
    }));
  };

  const handleInstructionChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.map((instruction, i) =>
        i === index ? { ...instruction, instruction: value } : instruction
      )
    }));
  };

  const addInstruction = () => {
    const newOrder = formData.instructions.length + 1;
    setFormData(prev => ({
      ...prev,
      instructions: [...prev.instructions, { order: newOrder, instruction: '' }]
    }));
  };

  const removeInstruction = (index: number) => {
    if (formData.instructions.length <= 1) return; // Keep at least one instruction
    
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.filter((_, i) => i !== index).map((inst, i) => ({
        ...inst,
        order: i + 1 // Reorder remaining instructions
      }))
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
  };

  // Group ingredients by type for display
  const flourIngredients = formData.ingredients.filter(ing => ing.type === 'flour');
  const liquidIngredients = formData.ingredients.filter(ing => ing.type === 'liquid');
  const otherIngredients = formData.ingredients.filter(ing => !['flour', 'liquid'].includes(ing.type));

  // Calculate baker's percentages for display
  const calculateBakersPercentages = () => {
    const totalFlourWeight = flourIngredients.reduce((sum, ing) => sum + (ing.amount || 0), 0);
    
    if (totalFlourWeight === 0) return null;

    const flourPercentages = flourIngredients.map(ing => ({
      name: ing.name,
      amount: ing.amount || 0,
      percentage: totalFlourWeight > 0 ? ((ing.amount || 0) / totalFlourWeight) * 100 : 100
    }));

    const otherPercentages = [...liquidIngredients, ...otherIngredients]
      .filter(ing => (ing.amount || 0) > 0)
      .map(ing => ({
        name: ing.name,
        amount: ing.amount || 0,
        percentage: totalFlourWeight > 0 ? ((ing.amount || 0) / totalFlourWeight) * 100 : 0
      }));

    return {
      totalFlourWeight,
      flourPercentages,
      otherPercentages
    };
  };

  const bakersPercentages = calculateBakersPercentages();

  const renderIngredientsByType = (ingredients: Ingredient[], title: string, type: string, backgroundColor: string) => (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-medium">{title}</h3>
        <button
          type="button"
          onClick={() => addIngredient(type)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          + Add {title.toLowerCase()}
        </button>
      </div>
      <div className={`p-4 rounded-lg ${backgroundColor} space-y-3`}>
        <div className="grid grid-cols-12 gap-4 font-medium text-sm text-gray-600">
          <div className="col-span-4">Name</div>
          <div className="col-span-2">Amount</div>
          <div className="col-span-2">Unit</div>
          <div className="col-span-2">Type</div>
          <div className="col-span-2">Actions</div>
        </div>
        
        {ingredients.map((ingredient) => {
          const index = formData.ingredients.findIndex(ing => ing === ingredient);
          return (
            <div key={index} className="grid grid-cols-12 gap-4 items-center">
              <input
                type="text"
                value={ingredient.name}
                onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                placeholder="Ingredient name"
                className="col-span-4 border rounded p-2 bg-white"
              />
              <input
                type="number"
                value={ingredient.amount || ''}
                onChange={(e) => handleIngredientChange(index, 'amount', parseFloat(e.target.value) || 0)}
                placeholder="Amount"
                className="col-span-2 border rounded p-2 bg-white"
              />
              <select
                value={ingredient.unit}
                onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                className="col-span-2 border rounded p-2 bg-white"
              >
                <option value="grams">g</option>
                <option value="kg">kg</option>
                <option value="ml">ml</option>
                <option value="cups">cups</option>
                <option value="tbsp">tbsp</option>
                <option value="tsp">tsp</option>
              </select>
              <select
                value={ingredient.type}
                onChange={(e) => handleIngredientChange(index, 'type', e.target.value)}
                className="col-span-2 border rounded p-2 bg-white"
              >
                <option value="flour">Flour</option>
                <option value="liquid">Liquid</option>
                <option value="preferment">Preferment</option>
                <option value="fat">Fat</option>
                <option value="other">Other</option>
              </select>
              <div className="col-span-2">
                {formData.ingredients.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeIngredient(index)}
                    className="text-red-500 hover:text-red-700 p-1"
                    title="Remove ingredient"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
                )}
              </div>
            </div>
          );
        })}
        
        {ingredients.length === 0 && (
          <div className="text-center py-4 text-gray-500">
            No {title.toLowerCase()} added yet
          </div>
        )}
      </div>
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Recipe Name */}
      <div>
        <label className="block text-sm font-medium mb-1">Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          placeholder="Recipe name"
          className="w-full border rounded p-2"
          required
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium mb-1">Description</label>
        <input
          type="text"
          value={formData.description || ''}
          onChange={(e) => handleInputChange('description', e.target.value)}
          placeholder="Brief description (optional)"
          className="w-full border rounded p-2"
        />
      </div>

      {/* Category */}
      <div>
        <label className="block text-sm font-medium mb-1">Category</label>
        <select
          value={formData.category || ''}
          onChange={(e) => handleInputChange('category', e.target.value)}
          className="w-full border rounded p-2"
        >
          <option value="">Select category (optional)</option>
          <option value="sourdough">Sourdough</option>
          <option value="enriched">Enriched Dough</option>
          <option value="lean">Lean Dough</option>
          <option value="sweet">Sweet Bread</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Flour Ingredients */}
      {renderIngredientsByType(flourIngredients, 'Flour Ingredients', 'flour', 'bg-yellow-50')}

      {/* Liquid Ingredients */}
      {renderIngredientsByType(liquidIngredients, 'Liquid Ingredients', 'liquid', 'bg-blue-50')}

      {/* Other Ingredients */}
      {renderIngredientsByType(otherIngredients, 'Other Ingredients', 'other', 'bg-gray-50')}

      {/* Baker's Percentages */}
      {bakersPercentages && (
        <div className="mb-6">
          <h3 className="font-medium mb-3">Baker's Percentages</h3>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600 mb-2">
              Total Flour Weight: {bakersPercentages.totalFlourWeight}g
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium text-gray-700 mb-1">Flour (100%)</div>
                {bakersPercentages.flourPercentages.map((flour, index) => (
                  <div key={index} className="flex justify-between">
                    <span>{flour.name}:</span>
                    <span>{flour.percentage.toFixed(1)}% ({flour.amount}g)</span>
                  </div>
                ))}
              </div>
              <div>
                <div className="font-medium text-gray-700 mb-1">Other Ingredients</div>
                {bakersPercentages.otherPercentages.map((other, index) => (
                  <div key={index} className="flex justify-between">
                    <span>{other.name}:</span>
                    <span>{other.percentage.toFixed(1)}% ({other.amount}g)</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div>
        <label className="block text-sm font-medium mb-3">Instructions</label>
        <div className="bg-gray-50 p-4 rounded-lg space-y-3">
          {formData.instructions.map((instruction, index) => (
            <div key={index} className="flex gap-2 items-start">
              <span className="text-sm font-medium text-gray-600 mt-2 min-w-[20px]">
                {index + 1}.
              </span>
              <textarea
                value={instruction.instruction}
                onChange={(e) => handleInstructionChange(index, e.target.value)}
                placeholder="Describe this step..."
                className="flex-1 border rounded p-2 bg-white resize-none"
                rows={2}
              />
              {formData.instructions.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeInstruction(index)}
                  className="text-red-500 hover:text-red-700 p-1 mt-1"
                  title="Remove step"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
          
          <button
            type="button"
            onClick={addInstruction}
            className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors"
          >
            + Add Step
          </button>
        </div>
      </div>

      {/* Version Info - Show if editing existing recipe */}
      {recipe && (
        <div className="bg-blue-50 p-4 rounded-lg mb-6">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-sm text-gray-600">Current Version</div>
              <div className="font-medium">
                v{recipe.current_version.version_number}
              </div>
              {recipe.current_version.description && (
                <div className="text-sm text-gray-500 mt-1">
                  {recipe.current_version.description}
                </div>
              )}
            </div>
            <div className="text-sm text-gray-500">
              Last updated: {new Date(recipe.updated_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      )}

      {/* Error and Success Messages */}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {success && (
        <div className="text-green-500 mb-4">
          {successMessage || 'Recipe saved successfully!'}
          {recipe && !successMessage && ` New version: v${recipe.current_version.version_number}`}
        </div>
      )}

      {/* Submit Buttons */}
      <div className="flex justify-center gap-4">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-400 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded"
        >
          {loading ? 'Saving...' : recipe ? 'Save Changes (Auto Version)' : 'Create Recipe'}
        </button>
        
        {recipe && (
          <button
            type="button"
            disabled={loading}
            onClick={() => {
              // TODO: Implement major version bump
              console.log('Major version bump requested');
              if (onSubmit) {
                const formDataWithMajorFlag = { 
                  ...formData, 
                  forceMajorVersion: true 
                };
                onSubmit(formDataWithMajorFlag as any);
              }
            }}
            className="bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-6 rounded"
          >
            Save New Major Version
          </button>
        )}
      </div>
    </form>
  );
};