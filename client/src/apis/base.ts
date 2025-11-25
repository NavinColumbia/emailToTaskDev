export abstract class BaseApiService {
  protected baseUrl = import.meta.env.VITE_API_BASE_URL || '';

  protected async handleResponse<T>(response: Response, errorMessage: string): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || errorMessage);
    }
    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return undefined as T;
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return undefined as T;
  }
}

