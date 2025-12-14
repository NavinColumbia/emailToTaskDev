import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  formatDate,
  formatDateTime,
  formatDateOnly,
  formatTimeOnly,
} from '../dateUtils';

describe('dateUtils', () => {
  beforeEach(() => {
    // Mock current date to 2024-01-15 12:00:00
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('formatDate', () => {
    it('should return "—" for null or undefined', () => {
      expect(formatDate(null)).toBe('—');
      expect(formatDate(undefined)).toBe('—');
    });

    it('should format today as time only', () => {
      const today = new Date('2024-01-15T14:30:00Z').toISOString();
      const result = formatDate(today);
      expect(result).toMatch(/\d{2}:\d{2}/); // Time format
    });

    it('should format other dates as date', () => {
      const date = new Date('2024-01-10T12:00:00Z').toISOString();
      const result = formatDate(date);
      expect(result).toMatch(/Jan \d+/);
    });

    it('should handle invalid date strings', () => {
      expect(formatDate('invalid')).toBe('invalid');
    });
  });

  describe('formatDateTime', () => {
    it('should return "—" for null or undefined', () => {
      expect(formatDateTime(null)).toBe('—');
      expect(formatDateTime(undefined)).toBe('—');
    });

    it('should format date and time', () => {
      const date = new Date('2024-01-10T14:30:00Z').toISOString();
      const result = formatDateTime(date);
      expect(result).toMatch(/Jan \d+/);
      expect(result).toMatch(/\d{2}:\d{2}/);
    });

    it('should handle invalid date strings', () => {
      expect(formatDateTime('invalid')).toBe('invalid');
    });
  });

  describe('formatDateOnly', () => {
    it('should return "—" for null or undefined', () => {
      expect(formatDateOnly(null)).toBe('—');
      expect(formatDateOnly(undefined)).toBe('—');
    });

    it('should return "Today" for today', () => {
      const today = new Date('2024-01-15T12:00:00Z').toISOString();
      expect(formatDateOnly(today)).toBe('Today');
    });

    it('should return "Yesterday" for yesterday', () => {
      const yesterday = new Date('2024-01-14T12:00:00Z').toISOString();
      expect(formatDateOnly(yesterday)).toBe('Yesterday');
    });

    it('should format other dates', () => {
      const date = new Date('2024-01-10T12:00:00Z').toISOString();
      const result = formatDateOnly(date);
      expect(result).toMatch(/Jan \d+/);
    });
  });

  describe('formatTimeOnly', () => {
    it('should return "—" for null or undefined', () => {
      expect(formatTimeOnly(null)).toBe('—');
      expect(formatTimeOnly(undefined)).toBe('—');
    });

    it('should format time only', () => {
      const date = new Date('2024-01-10T14:30:00Z').toISOString();
      const result = formatTimeOnly(date);
      expect(result).toMatch(/\d{2}:\d{2}/);
    });

    it('should handle invalid date strings', () => {
      expect(formatTimeOnly('invalid')).toBe('—');
    });
  });
});
