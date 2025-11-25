import { BaseApiService } from './base';

export class AuthService extends BaseApiService {
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
}

