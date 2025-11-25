import { BaseApiService } from './base';
import type { Task } from './types';

export class TaskService extends BaseApiService {
  async getAllTasks(): Promise<{ tasks: Task[]; total: number }> {
    const response = await fetch(`${this.baseUrl}/tasks/all`, {
      credentials: 'include',
    });
    
    return this.handleResponse<{ tasks: Task[]; total: number }>(response, 'Failed to fetch tasks');
  }

  async deleteTasks(taskIds: number[]): Promise<void> {
    const response = await fetch(`${this.baseUrl}/tasks`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ task_ids: taskIds }),
    });
    
    await this.handleResponse<void>(response, 'Failed to delete tasks');
  }
}

