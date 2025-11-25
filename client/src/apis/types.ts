export type FetchEmailsParams = {
  provider?: string;
  window?: string;
  max?: number;
  since?: string;
  q?: string;
  timezone?: string;
};

export type Task = {
  id: number;
  provider: string;
  provider_task_id: string;
  created_at: string;
  email_subject: string;
  email_sender: string;
  email_received_at: string;
  task_title?: string;
  task_link?: string;
  task_due?: string;
  status: 'created' | 'skipped';
};

export type CalendarEvent = {
  id: number;
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
  status: 'created' | 'skipped';
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

export type Settings = {
  max?: number;
  window: string;
};

