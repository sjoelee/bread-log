import { 
  TeamMake, 
  BreadTiming,
  BreadTimingCreate,
  BreadTimingUpdate,
  BreadTimingListResponse
} from '../types/bread';
import { parseValidationErrors } from '../utils/errorParser.ts';

const getApiBaseUrl = (): string => {
  const isDevelopment = window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1';
  return isDevelopment ? 'http://localhost:8000' : 'https://your-production-api.com';
};

const getHeaders = () => ({
  'Authorization': 'Bearer test-token', // TODO: Replace with actual token management
  'Content-Type': 'application/json'
});

export const teamMakesApi = {
  async getAll(): Promise<TeamMake[]> {
    try {
      const response = await fetch(`${getApiBaseUrl()}/makes`, {
        headers: getHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        return data.map((make: any) => ({
          key: make.key,
          displayName: make.display_name,
        }));
      }
      return [];
    } catch (error) {
      console.error('Error fetching team makes:', error);
      return [];
    }
  },

  async create(request: CreateMakeRequest): Promise<TeamMake> {
    const response = await fetch(`${getApiBaseUrl()}/makes`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      if (response.status === 422 && errorData.detail) {
        const validationErrors = parseValidationErrors(errorData);
        throw new Error(validationErrors.join(', '));
      }
      throw new Error(errorData.detail || 'Failed to create make');
    }

    const data = await response.json();
    return {
      key: data.key,
      displayName: data.display_name
    };
  }
};


// New Bread Timing REST API
export const breadTimingApi = {
  async create(timing: BreadTimingCreate): Promise<BreadTiming> {
    const response = await fetch(`${getApiBaseUrl()}/timings`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(timing)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      if (response.status === 422 && errorData.detail) {
        const validationErrors = parseValidationErrors(errorData);
        throw new Error(validationErrors.join(', '));
      }
      throw new Error(errorData.detail || 'Failed to create timing');
    }

    return await response.json();
  },

  async getById(timingId: string): Promise<BreadTiming> {
    const response = await fetch(`${getApiBaseUrl()}/timings/${timingId}`, {
      headers: getHeaders()
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Timing not found');
      }
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to get timing');
    }

    return await response.json();
  },

  async list(params: {
    page?: number;
    limit?: number;
    recipe_name?: string;
    date?: string;
    date_from?: string;
    date_to?: string;
    search?: string;
    order_by?: string;
    order_direction?: string;
  } = {}): Promise<BreadTimingListResponse> {
    const queryParams = new URLSearchParams();
    
    // Add parameters if they exist
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.limit) queryParams.set('limit', params.limit.toString());
    if (params.recipe_name) queryParams.set('recipe_name', params.recipe_name);
    if (params.date) queryParams.set('date', params.date);
    if (params.date_from) queryParams.set('date_from', params.date_from);
    if (params.date_to) queryParams.set('date_to', params.date_to);
    if (params.search) queryParams.set('search', params.search);
    if (params.order_by) queryParams.set('order_by', params.order_by);
    if (params.order_direction) queryParams.set('order_direction', params.order_direction);

    const url = `${getApiBaseUrl()}/timings${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    
    const response = await fetch(url, {
      headers: getHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to list timings');
    }

    return await response.json();
  },

  async update(timingId: string, updates: BreadTimingUpdate): Promise<BreadTiming> {
    const response = await fetch(`${getApiBaseUrl()}/timings/${timingId}`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      if (response.status === 422 && errorData.detail) {
        const validationErrors = parseValidationErrors(errorData);
        throw new Error(validationErrors.join(', '));
      }
      if (response.status === 404) {
        throw new Error('Timing not found');
      }
      throw new Error(errorData.detail || 'Failed to update timing');
    }

    return await response.json();
  },

  async delete(timingId: string): Promise<void> {
    const response = await fetch(`${getApiBaseUrl()}/timings/${timingId}`, {
      method: 'DELETE',
      headers: getHeaders()
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Timing not found');
      }
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to delete timing');
    }
  },

  // Convenience method to get timings by date (uses the list API with date filter)
  async getByDate(date: string): Promise<BreadTiming[]> {
    const response = await this.list({ 
      date, 
      limit: 100, // Get all timings for the date
      order_by: 'created_at',
      order_direction: 'desc'
    });
    return response.timings;
  }
};