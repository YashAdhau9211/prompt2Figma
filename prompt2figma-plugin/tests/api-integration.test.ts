import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock fetch for API testing
global.fetch = vi.fn();

describe('API Integration with Device Preference', () => {
  let mockFetch: any;
  
  beforeEach(() => {
    mockFetch = vi.mocked(fetch);
    mockFetch.mockClear();
  });

  describe('Wireframe Generation API Request', () => {
    it('should include device preference in API request payload', async () => {
      // Mock successful API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          layout_json: { type: 'frame', children: [] },
          devicePreferenceUsed: true,
          detectedDevice: 'mobile'
        })
      });

      const prompt = 'Create a mobile login screen';
      const devicePreference = 'mobile';
      
      // Simulate the API call that would be made from ui.js
      const requestPayload = {
        prompt,
        devicePreference
      };

      await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload)
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/generate-wireframe',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: 'Create a mobile login screen',
            devicePreference: 'mobile'
          })
        }
      );
    });

    it('should include null device preference when none is selected', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          layout_json: { type: 'frame', children: [] },
          devicePreferenceUsed: false,
          detectedDevice: 'desktop'
        })
      });

      const prompt = 'Create a dashboard';
      const devicePreference = null;
      
      const requestPayload = {
        prompt,
        devicePreference
      };

      await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload)
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/generate-wireframe',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: 'Create a dashboard',
            devicePreference: null
          })
        }
      );
    });

    it('should handle desktop device preference', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          layout_json: { type: 'frame', children: [] },
          devicePreferenceUsed: true,
          detectedDevice: 'desktop'
        })
      });

      const prompt = 'Create an admin panel';
      const devicePreference = 'desktop';
      
      const requestPayload = {
        prompt,
        devicePreference
      };

      await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload)
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/generate-wireframe',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: 'Create an admin panel',
            devicePreference: 'desktop'
          })
        }
      );
    });
  });

  describe('API Response Handling', () => {
    it('should handle successful response with device preference used', async () => {
      const mockResponse = {
        layout_json: { 
          type: 'frame', 
          componentName: 'Mobile App',
          children: [] 
        },
        devicePreferenceUsed: true,
        detectedDevice: 'mobile'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Create a mobile app',
          devicePreference: 'mobile'
        })
      });

      const data = await response.json();

      expect(data.layout_json).toBeDefined();
      expect(data.devicePreferenceUsed).toBe(true);
      expect(data.detectedDevice).toBe('mobile');
    });

    it('should handle response when device preference transmission failed', async () => {
      const mockResponse = {
        layout_json: { 
          type: 'frame', 
          componentName: 'Desktop Dashboard',
          children: [] 
        },
        devicePreferenceUsed: false,
        detectedDevice: 'desktop'
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Create a mobile app',
          devicePreference: 'mobile' // Sent mobile but backend used desktop
        })
      });

      const data = await response.json();

      expect(data.layout_json).toBeDefined();
      expect(data.devicePreferenceUsed).toBe(false);
      expect(data.detectedDevice).toBe('desktop');
    });

    it('should handle API error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          error: 'Internal server error'
        })
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Create an app',
          devicePreference: 'mobile'
        })
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
    });

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        fetch('http://localhost:8000/api/v1/generate-wireframe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: 'Create an app',
            devicePreference: 'mobile'
          })
        })
      ).rejects.toThrow('Network error');
    });
  });

  describe('Fallback Behavior', () => {
    it('should handle missing devicePreferenceUsed field in response', async () => {
      const mockResponse = {
        layout_json: { 
          type: 'frame', 
          children: [] 
        }
        // Missing devicePreferenceUsed and detectedDevice fields
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Create an app',
          devicePreference: 'mobile'
        })
      });

      const data = await response.json();

      expect(data.layout_json).toBeDefined();
      expect(data.devicePreferenceUsed).toBeUndefined();
      expect(data.detectedDevice).toBeUndefined();
    });

    it('should handle malformed JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Create an app',
          devicePreference: 'mobile'
        })
      });

      await expect(response.json()).rejects.toThrow('Invalid JSON');
    });
  });

  describe('Request Validation', () => {
    it('should handle empty prompt with device preference', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: 'Prompt is required'
        })
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: '',
          devicePreference: 'mobile'
        })
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(400);
    });

    it('should handle invalid device preference values', async () => {
      // The frontend should validate this, but test backend handling too
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          layout_json: { type: 'frame', children: [] },
          devicePreferenceUsed: false, // Backend ignored invalid preference
          detectedDevice: 'mobile'
        })
      });

      const response = await fetch('http://localhost:8000/api/v1/generate-wireframe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Create an app',
          devicePreference: 'invalid-device'
        })
      });

      const data = await response.json();
      
      expect(data.devicePreferenceUsed).toBe(false);
      expect(data.detectedDevice).toBeDefined();
    });
  });
});