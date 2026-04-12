interface ValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: any;
}

interface ValidationErrorResponse {
  detail: ValidationError[];
}

const fieldDisplayNames: Record<string, string> = {
  'bulk_ts': 'Bulk fermentation time',
  'preshape_ts': 'Preshape time',
  'final_shape_ts': 'Final shape time',
  'fridge_ts': 'Fridge time',
  'autolyse_ts': 'Autolyse time',
  'mix_ts': 'Mix time',
  'room_temp': 'Room temperature',
  'water_temp': 'Water temperature',
  'flour_temp': 'Flour temperature',
  'preferment_temp': 'Preferment temperature',
  'dough_temp': 'Dough temperature',
  'temperature_unit': 'Temperature unit',
  'stretch_folds': 'Stretch & folds',
  'notes': 'Notes',
  'date': 'Date',
};

export const parseValidationErrors = (errorResponse: any): string[] => {
  if (!errorResponse?.detail || !Array.isArray(errorResponse.detail)) {
    return ['An unexpected error occurred'];
  }

  const errors: string[] = [];
  
  for (const error of errorResponse.detail) {
    const fieldPath = error.loc?.join('.') || 'unknown field';
    
    // Handle nested field locations - if the first element is "body", use the second element
    const fieldName = error.loc?.[0] === 'body' ? error.loc?.[1] : error.loc?.[0] || 'unknown field';
    const displayName = fieldDisplayNames[fieldName] || fieldName;
    
    switch (error.type) {
      case 'missing':
        errors.push(`${displayName} is required`);
        break;
      case 'value_error':
        errors.push(`${displayName} has an invalid value`);
        break;
      case 'type_error':
        errors.push(`${displayName} must be the correct type`);
        break;
      case 'string_too_short':
        errors.push(`${displayName} is too short`);
        break;
      case 'string_too_long':
        errors.push(`${displayName} is too long`);
        break;
      case 'greater_than_equal':
        errors.push(`${displayName} must be greater than or equal to ${error.ctx?.ge || 'the minimum value'}`);
        break;
      case 'less_than_equal':
        errors.push(`${displayName} must be less than or equal to ${error.ctx?.le || 'the maximum value'}`);
        break;
      default:
        // Fallback to the original message if we don't have a specific handler
        errors.push(`${displayName}: ${error.msg || 'Invalid value'}`);
    }
  }
  
  return errors.length > 0 ? errors : ['Validation failed'];
};