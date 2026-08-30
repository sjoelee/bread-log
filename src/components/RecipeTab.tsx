import React, { useState, useEffect } from 'react';

const RECIPE_DRAFT_KEY = 'bread-log:recipe-draft';

interface Ingredient {
  id?: string;
  name: string;
  amount: number;
  unit: string;
  type: string;
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
  recipe?: RecipeResponse | null;
  isTemplate?: boolean;
  onSubmit?: (data: RecipeFormData) => void;
}

export const RecipeTab: React.FC<RecipeTabProps> = ({
  loading = false,
  error = null,
  success = false,
  successMessage = null,
  recipe = null,
  isTemplate = false,
  onSubmit
}) => {
  const [formData, setFormData] = useState<RecipeFormData>(() => {
    if (recipe) {
      return {
        name: recipe.name,
        description: recipe.description || '',
        category: recipe.category || '',
        ingredients: recipe.current_version.ingredients,
        instructions: recipe.current_version.instructions
      };
    }

    try {
      const raw = localStorage.getItem(RECIPE_DRAFT_KEY);
      if (raw) return JSON.parse(raw);
    } catch {}

    return {
      name: '',
      description: '',
      category: '',
      ingredients: [
        { name: '', amount: 0, unit: 'grams', type: 'flour', notes: '' },
        { name: '', amount: 0, unit: 'grams', type: 'other', notes: '' }
      ],
      instructions: [{ order: 1, instruction: '' }]
    };
  });


  useEffect(() => {
    if (!recipe) {
      try { localStorage.setItem(RECIPE_DRAFT_KEY, JSON.stringify(formData)); } catch {}
    }
  }, [formData, recipe]);

  useEffect(() => {
    if (success) {
      try { localStorage.removeItem(RECIPE_DRAFT_KEY); } catch {}
    }
  }, [success]);

  const handleInputChange = (field: keyof RecipeFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleIngredientChange = (index: number, field: keyof Ingredient, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      ingredients: prev.ingredients.map((ing, i) =>
        i === index ? { ...ing, [field]: value } : ing
      )
    }));
  };

  const toggleFlour = (index: number, isFlour: boolean) => {
    handleIngredientChange(index, 'type', isFlour ? 'flour' : 'other');
  };

  const addIngredient = () => {
    setFormData(prev => ({
      ...prev,
      ingredients: [...prev.ingredients, { name: '', amount: 0, unit: 'grams', type: 'other', notes: '' }]
    }));
  };

  const removeIngredient = (index: number) => {
    if (formData.ingredients.length <= 1) return;
    setFormData(prev => ({
      ...prev,
      ingredients: prev.ingredients.filter((_, i) => i !== index)
    }));
  };

  const handleInstructionChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.map((inst, i) =>
        i === index ? { ...inst, instruction: value } : inst
      )
    }));
  };

  const addInstruction = () => {
    setFormData(prev => ({
      ...prev,
      instructions: [...prev.instructions, { order: prev.instructions.length + 1, instruction: '' }]
    }));
  };

  const removeInstruction = (index: number) => {
    if (formData.instructions.length <= 1) return;
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.filter((_, i) => i !== index).map((inst, i) => ({ ...inst, order: i + 1 }))
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
  };

  const totalFlourWeight = formData.ingredients
    .filter(ing => ing.type === 'flour')
    .reduce((sum, ing) => sum + (ing.amount || 0), 0);

  const bakersPercentage = (amount: number) =>
    totalFlourWeight > 0 ? ((amount / totalFlourWeight) * 100).toFixed(1) + '%' : '—';

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Name */}
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

      {/* Ingredients */}
      <div>
        <label className="block text-sm font-medium mb-3">Ingredients</label>

        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b text-gray-600 text-left">
              <th className="py-2 pr-3 font-medium w-24">Amount</th>
              <th className="py-2 pr-3 font-medium w-20">Unit</th>
              <th className="py-2 pr-3 font-medium">Ingredient</th>
              <th className="py-2 pr-3 font-medium text-right w-28">Baker's %</th>
              <th className="py-2 pr-3 font-medium text-center w-16">Flour</th>
              <th className="py-2 w-8"></th>
            </tr>
          </thead>
          <tbody>
            {formData.ingredients.map((ing, index) => (
              <tr key={index} className={`border-b last:border-b-0 ${index % 2 === 1 ? 'bg-blue-50' : ''}`}>
                <td className="py-2 pr-3">
                  <input
                    type="number"
                    value={ing.amount || ''}
                    onChange={(e) => handleIngredientChange(index, 'amount', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    className="w-full border rounded p-1 text-right"
                  />
                </td>
                <td className="py-2 pr-3">
                  <select
                    value={ing.unit}
                    onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                    className="w-full border rounded p-1"
                  >
                    <option value="grams">g</option>
                    <option value="kg">kg</option>
                    <option value="ml">ml</option>
                    <option value="cups">cups</option>
                    <option value="tbsp">tbsp</option>
                    <option value="tsp">tsp</option>
                  </select>
                </td>
                <td className="py-2 pr-3">
                  <input
                    type="text"
                    value={ing.name}
                    onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                    placeholder="Ingredient name"
                    className="w-full border rounded p-1"
                  />
                </td>
                <td className="py-2 pr-3 text-right text-gray-600">
                  {ing.amount > 0 ? bakersPercentage(ing.amount) : '—'}
                </td>
                <td className="py-2 pr-3 text-center">
                  <input
                    type="checkbox"
                    checked={ing.type === 'flour'}
                    onChange={(e) => toggleFlour(index, e.target.checked)}
                    className="w-4 h-4 accent-blue-600"
                  />
                </td>
                <td className="py-2">
                  {formData.ingredients.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeIngredient(index)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      ×
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {totalFlourWeight > 0 && (
          <div className="mt-2 text-xs text-gray-500 text-right">
            Total flour: {totalFlourWeight}g
          </div>
        )}

        <button
          type="button"
          onClick={addIngredient}
          className="mt-3 w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors text-sm"
        >
          + Add Ingredient
        </button>
      </div>

      {/* Instructions */}
      <div>
        <label className="block text-sm font-medium mb-3">Instructions</label>
        <div className="space-y-2">
          {formData.instructions.map((instruction, index) => (
            <div key={index} className="flex gap-2 items-start">
              <span className="text-sm font-medium text-gray-500 mt-2 min-w-[20px]">
                {index + 1}.
              </span>
              <textarea
                value={instruction.instruction}
                onChange={(e) => handleInstructionChange(index, e.target.value)}
                placeholder="Describe this step..."
                className="flex-1 border rounded p-2 resize-none"
                rows={2}
              />
              {formData.instructions.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeInstruction(index)}
                  className="text-gray-400 hover:text-red-500 mt-2"
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={addInstruction}
            className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors text-sm"
          >
            + Add Step
          </button>
        </div>
      </div>

      {/* Version Info */}
      {recipe && (
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-sm text-gray-600">Current Version</div>
              <div className="font-medium">v{recipe.current_version.version_number}</div>
              {recipe.current_version.description && (
                <div className="text-sm text-gray-500 mt-1">{recipe.current_version.description}</div>
              )}
            </div>
            <div className="text-sm text-gray-500">
              Last updated: {new Date(recipe.updated_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      )}

      {error && <div className="text-red-500">{error}</div>}
      {success && (
        <div className="text-green-500">
          {successMessage || 'Recipe saved successfully!'}
          {recipe && !successMessage && ` New version: v${recipe.current_version.version_number}`}
        </div>
      )}

      <div className="flex justify-center">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-400 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded"
        >
          {loading ? 'Saving...' : (recipe && !isTemplate) ? 'Save Changes' : 'Create Recipe'}
        </button>
      </div>
    </form>
  );
};
