import { useState, useCallback } from 'react';
import { api, type Task } from '../apis/api';

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

  const deleteTasks = useCallback(async (taskIds: number[]) => {
    setError(null);
    try {
      await api.deleteTasks(taskIds);
      setTasks(prevTasks => prevTasks.filter(task => !taskIds.includes(task.id)));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete tasks';
      setError(errorMessage);
      throw err;
    }
  }, []);

  return {
    tasks,
    loading,
    error,
    loadTasks,
    deleteTasks,
  };
}

