import { BaseApiService } from './base';
import type { FetchEmailsParams, FetchEmailsResponse } from './types';

export class EmailService extends BaseApiService {
  async fetchEmails(params: FetchEmailsParams): Promise<FetchEmailsResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.provider) queryParams.append('provider', params.provider);
    if (params.window) queryParams.append('window', params.window);
    if (params.max) queryParams.append('max', params.max.toString());
    if (params.since) queryParams.append('since', params.since);
    if (params.q) queryParams.append('q', params.q);
    if (params.timezone) queryParams.append('timezone', params.timezone);

    const response = await fetch(`${this.baseUrl}/fetch-emails?${queryParams}`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    return this.handleResponse<FetchEmailsResponse>(response, 'Failed to fetch emails');
  }
}

