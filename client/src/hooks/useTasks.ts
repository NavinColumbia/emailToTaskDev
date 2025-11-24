import { useState, useCallback } from 'react';
import { api, type Task } from '../api';

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAllTasks();
      setTasks(data.tasks);
      return data.tasks;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tasks';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteTask = useCallback(async (taskId: number) => {
    setError(null);
    try {
      await api.deleteTask(taskId);
      // Remove the task from local state
      setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete task';
      setError(errorMessage);
      throw err;
    }
  }, []);

  return {
    tasks,
    loading,
    error,
    loadTasks,
    deleteTask,
  };
}

