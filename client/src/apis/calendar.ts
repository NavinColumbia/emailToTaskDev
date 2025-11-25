import { BaseApiService } from './base';
import type { CalendarEvent } from './types';

export class CalendarService extends BaseApiService {
  async getAllCalendarEvents(): Promise<{ events: CalendarEvent[]; total: number }> {
    const response = await fetch(`${this.baseUrl}/calendar-events/all`, {
      credentials: 'include',
    });
    
    return this.handleResponse<{ events: CalendarEvent[]; total: number }>(
      response,
      'Failed to fetch calendar events'
    );
  }

  async deleteCalendarEvents(eventIds: number[]): Promise<void> {
    const response = await fetch(`${this.baseUrl}/calendar-events`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ event_ids: eventIds }),
    });
    
    await this.handleResponse<void>(response, 'Failed to delete calendar events');
  }
}

