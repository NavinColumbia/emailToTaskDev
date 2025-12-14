import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { getToken, setToken, removeToken } from '../base';

describe('base API utilities', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('getToken', () => {
    it('should return null when no token in localStorage', () => {
      expect(getToken()).toBeNull();
    });

    it('should return token from localStorage', () => {
      localStorage.setItem('jwt_token', 'test-token');
      expect(getToken()).toBe('test-token');
    });
  });

  describe('setToken', () => {
    it('should store token in localStorage', () => {
      setToken('new-token');
      expect(localStorage.getItem('jwt_token')).toBe('new-token');
    });
  });

  describe('removeToken', () => {
    it('should remove token from localStorage', () => {
      localStorage.setItem('jwt_token', 'test-token');
      removeToken();
      expect(localStorage.getItem('jwt_token')).toBeNull();
    });
  });
});
