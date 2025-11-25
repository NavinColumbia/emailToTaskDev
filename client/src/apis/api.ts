import { AuthService } from './auth';
import { EmailService } from './emails';
import { TaskService } from './tasks';
import { CalendarService } from './calendar';
import { SettingsService } from './settings';
import type {
  FetchEmailsParams,
  FetchEmailsResponse,
  Task,
  CalendarEvent,
  Settings,
} from './types';

// Export all types
export type {
  FetchEmailsParams,
  FetchEmailsResponse,
  Task,
  CalendarEvent,
  Settings,
} from './types';

// Combined API service that includes all services
class ApiService {
  auth = new AuthService();
  emails = new EmailService();
  tasks = new TaskService();
  calendar = new CalendarService();
  settings = new SettingsService();

  // Convenience methods for backward compatibility
  async checkAuth(): Promise<boolean> {
    return this.auth.checkAuth();
  }

  async authorize(): Promise<void> {
    return this.auth.authorize();
  }

  async logout(): Promise<void> {
    return this.auth.logout();
  }

  async fetchEmails(params: FetchEmailsParams): Promise<FetchEmailsResponse> {
    return this.emails.fetchEmails(params);
  }

  async getAllTasks(): Promise<{ tasks: Task[]; total: number }> {
    return this.tasks.getAllTasks();
  }

  async getAllCalendarEvents(): Promise<{ events: CalendarEvent[]; total: number }> {
    return this.calendar.getAllCalendarEvents();
  }

  async deleteTasks(taskIds: number[]): Promise<void> {
    return this.tasks.deleteTasks(taskIds);
  }

  async deleteCalendarEvents(eventIds: number[]): Promise<void> {
    return this.calendar.deleteCalendarEvents(eventIds);
  }

  async getSettings(): Promise<Settings> {
    return this.settings.getSettings();
  }

  async updateSettings(settings: Settings): Promise<Settings> {
    return this.settings.updateSettings(settings);
  }
}

export const api = new ApiService();

