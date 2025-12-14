import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAuth } from '../useAuth';
import * as apiModule from '../../apis/api';

// Mock the API module
vi.mock('../../apis/api', () => ({
  api: {
    checkAuth: vi.fn(),
    authorize: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock base module
vi.mock('../../apis/base', () => ({
  getToken: vi.fn(() => null),
}));

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with authenticated false when no token', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.authenticated).toBe(false);
  });

  it('should check authentication status', async () => {
    vi.mocked(apiModule.api.checkAuth).mockResolvedValue(true);
    
    const { result } = renderHook(() => useAuth());
    
    const isAuth = await result.current.checkAuth();
    
    expect(isAuth).toBe(true);
    expect(result.current.authenticated).toBe(true);
    expect(apiModule.api.checkAuth).toHaveBeenCalledOnce();
  });

  it('should handle authentication check failure', async () => {
    vi.mocked(apiModule.api.checkAuth).mockRejectedValue(new Error('Auth failed'));
    
    const { result } = renderHook(() => useAuth());
    
    const isAuth = await result.current.checkAuth();
    
    expect(isAuth).toBe(false);
    expect(result.current.authenticated).toBe(false);
  });

  it('should call authorize', async () => {
    vi.mocked(apiModule.api.authorize).mockResolvedValue(undefined);
    
    const { result } = renderHook(() => useAuth());
    
    await result.current.authorize();
    
    expect(apiModule.api.authorize).toHaveBeenCalledOnce();
  });

  it('should call logout and set authenticated to false', async () => {
    vi.mocked(apiModule.api.logout).mockResolvedValue(undefined);
    
    const { result } = renderHook(() => useAuth());
    
    // Set authenticated to true first
    result.current.authenticated = true;
    
    await result.current.logout();
    
    expect(apiModule.api.logout).toHaveBeenCalledOnce();
    expect(result.current.authenticated).toBe(false);
  });
});
