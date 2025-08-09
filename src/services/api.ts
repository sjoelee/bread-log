import { TeamMake, DoughMake, CreateMakeRequest } from '../types/bread';

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
      throw new Error(errorData.detail || 'Failed to create make');
    }

    const data = await response.json();
    return {
      key: data.key,
      displayName: data.display_name
    };
  }
};

export const doughMakesApi = {
  async getByDate(date: string): Promise<DoughMake[]> {
    try {
      const [year, month, day] = date.split('-');
      const response = await fetch(`${getApiBaseUrl()}/makes/${year}/${month}/${day}`, {
        headers: getHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        // Convert timestamp strings to Date objects
        return (data || []).map((make: any) => {
          if (!make.created_at) {
            throw new Error('Backend did not return created_at timestamp');
          }
          return {
            ...make,
            created_at: new Date(make.created_at),
            created_at_original: make.created_at, // Preserve original string
            autolyse_ts: make.autolyse_ts ? new Date(make.autolyse_ts) : undefined,
            mix_ts: make.mix_ts ? new Date(make.mix_ts) : undefined,
            bulk_ts: make.bulk_ts ? new Date(make.bulk_ts) : undefined,
            preshape_ts: make.preshape_ts ? new Date(make.preshape_ts) : undefined,
            final_shape_ts: make.final_shape_ts ? new Date(make.final_shape_ts) : undefined,
            fridge_ts: make.fridge_ts ? new Date(make.fridge_ts) : undefined,
          };
        });
      }
      return [];
    } catch (error) {
      console.error('Error fetching saved makes:', error);
      return [];
    }
  },

  async create(year: number, month: number, day: number, makeName: string, doughMakeData: any): Promise<void> {
    const response = await fetch(`${getApiBaseUrl()}/makes/${year}/${month}/${day}/${makeName}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(doughMakeData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to create dough make');
    }
  },

  async update(year: number, month: number, day: number, makeName: string, createdAt: string, updates: any): Promise<void> {
    const response = await fetch(`${getApiBaseUrl()}/makes/${year}/${month}/${day}/${makeName}/${encodeURIComponent(createdAt)}`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to update dough make');
    }
  },

  async delete(year: number, month: number, day: number, makeName: string, createdAt: string): Promise<void> {
    const response = await fetch(`${getApiBaseUrl()}/makes/${year}/${month}/${day}/${makeName}/${encodeURIComponent(createdAt)}`, {
      method: 'DELETE',
      headers: getHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to delete dough make');
    }
  }
};