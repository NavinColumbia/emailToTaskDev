import { BaseApiService } from './base';
import type { Settings } from './types';

export class SettingsService extends BaseApiService {
  async getSettings(): Promise<Settings> {
    const response = await fetch(`${this.baseUrl}/settings`, {
      credentials: 'include',
    });
    
    return this.handleResponse<Settings>(response, 'Failed to fetch settings');
  }

  async updateSettings(settings: Settings): Promise<Settings> {
    const response = await fetch(`${this.baseUrl}/settings`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    
    return this.handleResponse<Settings>(response, 'Failed to update settings');
  }
}

