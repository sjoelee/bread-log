import React, { useState } from 'react';

interface Ingredient {
  name: string;
  amount: number;
  unit: string;
  notes?: string;
}

interface RecipeStep {
  instruction: string;
}

interface RecipeFormData {
  name: string;
  description?: string;
  flourIngredients: Ingredient[];
  otherIngredients: Ingredient[];
  instructions: RecipeStep[];
}

interface RecipeTabProps {
  loading?: boolean;
  error?: string | null;
  success?: boolean;
  onSubmit?: (data: RecipeFormData) => void;
}

export const RecipeTab: React.FC<RecipeTabProps> = ({
  loading = false,
  error = null,
  success = false,
  onSubmit
}) => {
  const [formData, setFormData] = useState<RecipeFormData>({
    name: '',
    description: '',
    flourIngredients: [{ name: '', amount: 0, unit: 'grams', notes: '' }],
    otherIngredients: [{ name: '', amount: 0, unit: 'grams', notes: '' }],
    instructions: [{ instruction: '' }]
  });

  const handleInputChange = (field: keyof RecipeFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleIngredientChange = (
    type: 'flourIngredients' | 'otherIngredients',
    index: number,
    field: keyof Ingredient,
    value: string | number
  ) => {
    setFormData(prev => ({
      ...prev,
      [type]: prev[type].map((ingredient, i) =>
        i === index ? { ...ingredient, [field]: value } : ingredient
      )
    }));
  };

  const addIngredient = (type: 'flourIngredients' | 'otherIngredients') => {
    setFormData(prev => ({
      ...prev,
      [type]: [...prev[type], { name: '', amount: 0, unit: 'grams', notes: '' }]
    }));
  };

  const removeIngredient = (type: 'flourIngredients' | 'otherIngredients', index: number) => {
    if (formData[type].length <= 1) return; // Keep at least one ingredient
    
    setFormData(prev => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index)
    }));
  };

  const handleInstructionChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.map((instruction, i) =>
        i === index ? { instruction: value } : instruction
      )
    }));
  };

  const addInstruction = () => {
    setFormData(prev => ({
      ...prev,
      instructions: [...prev.instructions, { instruction: '' }]
    }));
  };

  const removeInstruction = (index: number) => {
    if (formData.instructions.length <= 1) return; // Keep at least one instruction
    
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
  };

  const renderIngredientSection = (
    title: string,
    type: 'flourIngredients' | 'otherIngredients',
    backgroundColor: string
  ) => (
    <div className="mb-6">
      <h3 className="font-medium mb-3">{title}</h3>
      <div className={`p-4 rounded-lg ${backgroundColor} space-y-3`}>
        <div className="grid grid-cols-2 gap-4 font-medium text-sm text-gray-600">
          <div>Name</div>
          <div>Amount</div>
        </div>
        
        {formData[type].map((ingredient, index) => (
          <div key={index} className="grid grid-cols-2 gap-4 items-center">
            <input
              type="text"
              value={ingredient.name}
              onChange={(e) => handleIngredientChange(type, index, 'name', e.target.value)}
              placeholder="Ingredient name"
              className="border rounded p-2 bg-white"
            />
            <div className="flex gap-2 items-center">
              <input
                type="number"
                value={ingredient.amount || ''}
                onChange={(e) => handleIngredientChange(type, index, 'amount', parseFloat(e.target.value) || 0)}
                placeholder="Amount"
                className="border rounded p-2 bg-white flex-1"
              />
              <select
                value={ingredient.unit}
                onChange={(e) => handleIngredientChange(type, index, 'unit', e.target.value)}
                className="border rounded p-2 bg-white"
              >
                <option value="grams">g</option>
                <option value="kg">kg</option>
                <option value="ml">ml</option>
                <option value="cups">cups</option>
                <option value="tbsp">tbsp</option>
                <option value="tsp">tsp</option>
              </select>
              {formData[type].length > 1 && (
                <button
                  type="button"
                  onClick={() => removeIngredient(type, index)}
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
        ))}
        
        <button
          type="button"
          onClick={() => addIngredient(type)}
          className="flex items-center justify-center w-8 h-8 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-full border border-blue-300 hover:border-blue-400"
          title="Add ingredient"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </button>
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
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          placeholder="Brief description (optional)"
          className="w-full border rounded p-2"
        />
      </div>

      {/* Flour Ingredients */}
      {renderIngredientSection('Flour Ingredients', 'flourIngredients', 'bg-gray-100')}

      {/* Other Ingredients */}
      {renderIngredientSection('Other Ingredients', 'otherIngredients', 'bg-blue-100')}

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

      {/* Error and Success Messages */}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {success && <div className="text-green-500 mb-4">Recipe saved successfully!</div>}

      {/* Submit Button */}
      <div className="flex justify-center">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-400 hover:bg-blue-500 text-white font-medium py-2 px-6 rounded"
        >
          {loading ? 'Saving...' : 'SUBMIT'}
        </button>
      </div>
    </form>
  );
};