export type FetchEmailsParams = {
  provider?: string;
  window?: string;
  max?: number;
  since_hours?: number;
  since?: string;
  q?: string;
  dry_run?: boolean;
};

export type Task = {
  provider: string;
  provider_task_id: string;
  created_at: string;
  email_subject: string;
  email_sender: string;
  email_received_at: string;
  task_title?: string;
  task_link?: string;
  task_due?: string;
};

export type CalendarEvent = {
  google_event_id?: string;
  summary: string;
  location?: string;
  start_datetime?: string;
  end_datetime?: string;
  html_link?: string;
  created_at: string;
  email_subject: string;
  email_sender: string;
  email_received_at: string;
};

export type FetchEmailsResponse = {
  processed: number;
  query: string;
  created: Array<{
    message_id: string;
    provider: string;
    task: {
      id?: string;
      title?: string;
      due?: string;
      status?: string;
      selfLink?: string;
      webLink?: string;
      [key: string]: string | undefined;
    };
  }>;
  total_found: number;
  already_processed: number;
  considered: number;
  calendar_events?: Array<{
    summary: string;
    htmlLink: string;
    start?: string;
    location?: string;
  }>;
};

class ApiService {
  private baseUrl = import.meta.env.VITE_API_BASE_URL || '';

  async checkAuth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/status`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        console.error(`Auth check failed: ${response.status} ${response.statusText}`);
        return false;
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('Auth check failed: Expected JSON but got:', text.substring(0, 100));
        return false;
      }
      
      const data = await response.json();
      return data.authenticated === true;
    } catch (error) {
      console.error('Auth check failed:', error);
      return false;
    }
  }

  async authorize(): Promise<void> {
    window.location.href = `${this.baseUrl}/authorize`;
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/logout`, { 
        method: 'POST',
        credentials: 'include',
      });
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }

  async fetchEmails(params: FetchEmailsParams): Promise<FetchEmailsResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.provider) queryParams.append('provider', params.provider);
    if (params.window) queryParams.append('window', params.window);
    if (params.max) queryParams.append('max', params.max.toString());
    if (params.since_hours) queryParams.append('since_hours', params.since_hours.toString());
    if (params.since) queryParams.append('since', params.since);
    if (params.q) queryParams.append('q', params.q);
    if (params.dry_run !== undefined) queryParams.append('dry_run', params.dry_run.toString());

    const response = await fetch(`${this.baseUrl}/fetch-emails?${queryParams}`, {
      method: 'POST',
      credentials: 'include', // Include cookies
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || 'Failed to fetch emails');
    }

    return await response.json();
  }

  async getAllTasks(): Promise<{ tasks: Task[]; total: number }> {
    const response = await fetch(`${this.baseUrl}/tasks/all`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || 'Failed to fetch tasks');
    }

    return await response.json();
  }

  async getAllCalendarEvents(): Promise<{ events: CalendarEvent[]; total: number }> {
    const response = await fetch(`${this.baseUrl}/calendar-events/all`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || 'Failed to fetch calendar events');
    }

    return await response.json();
  }

  async getSettings(): Promise<Settings> {
    const response = await fetch(`${this.baseUrl}/settings`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || 'Failed to fetch settings');
    }

    return await response.json();
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
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || 'Failed to update settings');
    }

    return await response.json();
  }
}

export type Settings = {
  max?: number;
  window: string;
  dry_run: boolean;
};

export const api = new ApiService();

