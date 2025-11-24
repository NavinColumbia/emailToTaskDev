import { useState, useCallback } from 'react';
import { api, type CalendarEvent } from '../api';

export function useCalendarEvents() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAllCalendarEvents();
      setEvents(data.events);
      return data.events;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load calendar events';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteEvent = useCallback(async (eventId: number) => {
    setError(null);
    try {
      await api.deleteCalendarEvent(eventId);
      // Remove the event from local state
      setEvents(prevEvents => prevEvents.filter(event => event.id !== eventId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete calendar event';
      setError(errorMessage);
      throw err;
    }
  }, []);

  return {
    events,
    loading,
    error,
    loadEvents,
    deleteEvent,
  };
}

