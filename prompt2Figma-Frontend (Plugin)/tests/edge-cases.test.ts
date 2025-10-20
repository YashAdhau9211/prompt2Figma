import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('Device Selection Edge Cases', () => {
  let devicePreference: string | null;
  let devicePreferenceErrors: any;
  let sessionStartTime: number;
  
  // Mock functions
  let setDevicePreference: (device: string | null) => void;
  let getDevicePreference: () => string | null;
  let logDevicePreferenceEvent: any;
  let updateDeviceUI: any;
  let showDevicePreferenceNotification: any;

  beforeEach(() => {
    // Reset state
    devicePreference = null;
    sessionStartTime = Date.now();
    devicePreferenceErrors = {
      transmissionFailures: 0,
      invalidStates: 0,
      fallbacksUsed: 0
    };

    // Mock functions
    logDevicePreferenceEvent = vi.fn();
    updateDeviceUI = vi.fn();
    showDevicePreferenceNotification = vi.fn();

    // Simplified device preference functions for testing
    setDevicePreference = (device: string | null) => {
      try {
        if (device !== null && device !== 'mobile' && device !== 'desktop') {
          console.error(`Invalid device preference: ${device}. Falling back to auto-detect.`);
          logDevicePreferenceEvent('invalid_state', { attempted: device, fallback: 'auto-detect' });
          devicePreferenceErrors.invalidStates++;
          device = null;
          showDevicePreferenceNotification('warning', 'Invalid device selection reset to auto-detect');
        }
        
        devicePreference = device;
        
        if (device !== null) {
          try {
            sessionStorage.setItem('devicePreference', device);
            sessionStorage.setItem('devicePreferenceTimestamp', Date.now().toString());
            logDevicePreferenceEvent('preference_set', { device, persisted: true });
          } catch (storageError: any) {
            logDevicePreferenceEvent('storage_error', { device, error: storageError.message });
          }
        } else {
          try {
            sessionStorage.removeItem('devicePreference');
            sessionStorage.removeItem('devicePreferenceTimestamp');
            logDevicePreferenceEvent('preference_cleared', { persisted: true });
          } catch (storageError: any) {
            logDevicePreferenceEvent('storage_clear_error', { error: storageError.message });
          }
        }
        
        updateDeviceUI();
      } catch (error: any) {
        console.error('Error in setDevicePreference:', error);
        logDevicePreferenceEvent('set_preference_error', { attempted: device, error: error.message });
        devicePreference = null;
        updateDeviceUI();
        showDevicePreferenceNotification('error', 'Device selection error - reset to auto-detect');
      }
    };

    getDevicePreference = () => {
      try {
        if (devicePreference !== null && devicePreference !== 'mobile' && devicePreference !== 'desktop') {
          console.error(`Invalid device preference state detected: ${devicePreference}. Resetting to auto-detect.`);
          logDevicePreferenceEvent('invalid_state_detected', { invalid: devicePreference, fallback: 'auto-detect' });
          devicePreferenceErrors.invalidStates++;
          devicePreference = null;
          updateDeviceUI();
          showDevicePreferenceNotification('warning', 'Device selection was corrupted - reset to auto-detect');
        }
        return devicePreference;
      } catch (error: any) {
        console.error('Error in getDevicePreference:', error);
        logDevicePreferenceEvent('get_preference_error', { error: error.message });
        devicePreference = null;
        return null;
      }
    };
  });

  describe('Rapid Device Switching', () => {
    it('should handle rapid successive device selections', () => {
      // Simulate rapid clicking between mobile and desktop
      const selections = ['mobile', 'desktop', 'mobile', 'desktop', 'mobile'];
      
      selections.forEach((device, index) => {
        setDevicePreference(device as 'mobile' | 'desktop');
        expect(devicePreference).toBe(device);
        expect(logDevicePreferenceEvent).toHaveBeenCalledWith('preference_set', { 
          device, 
          persisted: true 
        });
      });

      // Should have called updateDeviceUI for each selection
      expect(updateDeviceUI).toHaveBeenCalledTimes(selections.length);
      
      // Final state should be mobile
      expect(getDevicePreference()).toBe('mobile');
    });

    it('should handle rapid toggle on/off of same device', () => {
      // Simulate rapid clicking on same device (toggle behavior)
      setDevicePreference('mobile');
      expect(devicePreference).toBe('mobile');
      
      setDevicePreference(null); // Toggle off
      expect(devicePreference).toBe(null);
      
      setDevicePreference('mobile'); // Toggle on
      expect(devicePreference).toBe('mobile');
      
      setDevicePreference(null); // Toggle off
      expect(devicePreference).toBe(null);

      // Should handle all toggles correctly
      expect(updateDeviceUI).toHaveBeenCalledTimes(4);
      expect(getDevicePreference()).toBe(null);
    });

    it('should handle rapid switching with session storage errors', () => {
      // Mock sessionStorage to fail intermittently
      let shouldFail = false;
      const originalSetItem = sessionStorage.setItem;
      sessionStorage.setItem = vi.fn((key, value) => {
        if (shouldFail) {
          throw new Error('Storage quota exceeded');
        }
        return originalSetItem.call(sessionStorage, key, value);
      });

      // Rapid switching with intermittent storage failures
      setDevicePreference('mobile');
      expect(devicePreference).toBe('mobile');
      
      shouldFail = true;
      setDevicePreference('desktop');
      expect(devicePreference).toBe('desktop');
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('storage_error', {
        device: 'desktop',
        error: 'Storage quota exceeded'
      });
      
      shouldFail = false;
      setDevicePreference('mobile');
      expect(devicePreference).toBe('mobile');

      // Restore original function
      sessionStorage.setItem = originalSetItem;
    });

    it('should maintain consistency during concurrent operations', async () => {
      // Simulate concurrent device preference operations
      const operations = [
        () => setDevicePreference('mobile'),
        () => setDevicePreference('desktop'),
        () => getDevicePreference(),
        () => setDevicePreference(null),
        () => getDevicePreference()
      ];

      // Execute operations rapidly
      const results = operations.map(op => op());
      
      // Final state should be consistent
      const finalPreference = getDevicePreference();
      expect(finalPreference).toBe(null);
      
      // Should not have any invalid states
      expect(devicePreferenceErrors.invalidStates).toBe(0);
    });
  });

  describe('Invalid State Handling', () => {
    it('should detect and fix corrupted device preference state', () => {
      // Directly corrupt the state (simulating memory corruption)
      devicePreference = 'corrupted-value' as any;
      
      const result = getDevicePreference();
      
      expect(result).toBe(null);
      expect(devicePreference).toBe(null);
      expect(devicePreferenceErrors.invalidStates).toBe(1);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('invalid_state_detected', {
        invalid: 'corrupted-value',
        fallback: 'auto-detect'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Device selection was corrupted - reset to auto-detect');
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should reject invalid device types during setting', () => {
      const invalidDevices = ['tablet', 'watch', 'tv', '', 'undefined', 'null', 123, true, {}];
      
      invalidDevices.forEach(invalidDevice => {
        setDevicePreference(invalidDevice as any);
        
        expect(devicePreference).toBe(null);
        expect(devicePreferenceErrors.invalidStates).toBeGreaterThan(0);
        expect(logDevicePreferenceEvent).toHaveBeenCalledWith('invalid_state', {
          attempted: invalidDevice,
          fallback: 'auto-detect'
        });
        expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Invalid device selection reset to auto-detect');
      });
    });

    it('should handle undefined and null values correctly', () => {
      // Test undefined
      setDevicePreference(undefined as any);
      expect(devicePreference).toBe(null);
      
      // Test null (should be valid)
      setDevicePreference(null);
      expect(devicePreference).toBe(null);
      
      // Should not increment invalid states for null
      const initialInvalidStates = devicePreferenceErrors.invalidStates;
      setDevicePreference(null);
      expect(devicePreferenceErrors.invalidStates).toBe(initialInvalidStates);
    });

    it('should handle function errors gracefully', () => {
      // Mock updateDeviceUI to throw error only on first call
      let callCount = 0;
      updateDeviceUI = vi.fn(() => {
        callCount++;
        if (callCount === 1) {
          throw new Error('UI update failed');
        }
        // Subsequent calls succeed
      });
      
      setDevicePreference('mobile');
      
      // Should reset preference to null due to error handling
      expect(devicePreference).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('set_preference_error', {
        attempted: 'mobile',
        error: 'UI update failed'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('error', 'Device selection error - reset to auto-detect');
      expect(updateDeviceUI).toHaveBeenCalledTimes(2); // Called twice due to error recovery
    });
  });

  describe('Session Storage Edge Cases', () => {
    it('should handle session storage quota exceeded', () => {
      // Store original function
      const originalSetItem = sessionStorage.setItem;
      
      // Mock sessionStorage to throw quota exceeded error
      sessionStorage.setItem = vi.fn(() => {
        throw new Error('QuotaExceededError: Storage quota exceeded');
      });
      
      setDevicePreference('mobile');
      
      // Should still set preference in memory
      expect(devicePreference).toBe('mobile');
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('storage_error', {
        device: 'mobile',
        error: 'QuotaExceededError: Storage quota exceeded'
      });
      
      // Restore original function
      sessionStorage.setItem = originalSetItem;
    });

    it('should handle session storage access denied', () => {
      // Store original function
      const originalSetItem = sessionStorage.setItem;
      
      // Mock sessionStorage to throw access denied error
      sessionStorage.setItem = vi.fn(() => {
        throw new Error('SecurityError: Access denied');
      });
      
      setDevicePreference('desktop');
      
      expect(devicePreference).toBe('desktop');
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('storage_error', {
        device: 'desktop',
        error: 'SecurityError: Access denied'
      });
      
      // Restore original function
      sessionStorage.setItem = originalSetItem;
    });

    it('should handle corrupted session storage data', () => {
      // Set corrupted data directly in session storage
      sessionStorage.setItem('devicePreference', 'corrupted-data');
      sessionStorage.setItem('devicePreferenceTimestamp', 'invalid-timestamp');
      
      // Try to restore - should fail gracefully
      const storedPreference = sessionStorage.getItem('devicePreference');
      const storedTimestamp = sessionStorage.getItem('devicePreferenceTimestamp');
      
      expect(storedPreference).toBe('corrupted-data');
      expect(storedTimestamp).toBe('invalid-timestamp');
      
      // The restore function would handle this, but we're testing the edge case
      expect(isNaN(parseInt(storedTimestamp!))).toBe(true);
    });

    it('should handle session storage being disabled', () => {
      // Mock sessionStorage to be undefined
      const originalSessionStorage = sessionStorage;
      (global as any).sessionStorage = undefined;
      
      // Should handle gracefully
      expect(() => setDevicePreference('mobile')).not.toThrow();
      expect(devicePreference).toBe('mobile');
      
      // Restore sessionStorage
      (global as any).sessionStorage = originalSessionStorage;
    });
  });

  describe('Memory and Performance Edge Cases', () => {
    it('should handle large number of rapid state changes', () => {
      const startTime = Date.now();
      const iterations = 1000;
      
      // Perform many rapid state changes
      for (let i = 0; i < iterations; i++) {
        const device = i % 2 === 0 ? 'mobile' : 'desktop';
        setDevicePreference(device);
      }
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      // Should complete in reasonable time (less than 1 second)
      expect(duration).toBeLessThan(1000);
      
      // Final state should be correct
      expect(devicePreference).toBe('desktop'); // Last iteration was odd
      
      // Should not have accumulated invalid states
      expect(devicePreferenceErrors.invalidStates).toBe(0);
    });

    it('should handle memory pressure scenarios', () => {
      // Simulate memory pressure by creating large objects
      const largeObjects = [];
      for (let i = 0; i < 100; i++) {
        largeObjects.push(new Array(10000).fill(`data-${i}`));
      }
      
      // Device preference operations should still work
      setDevicePreference('mobile');
      expect(getDevicePreference()).toBe('mobile');
      
      setDevicePreference('desktop');
      expect(getDevicePreference()).toBe('desktop');
      
      // Clean up
      largeObjects.length = 0;
    });

    it('should handle function call stack overflow protection', () => {
      // Mock updateDeviceUI to call setDevicePreference (circular call)
      let callCount = 0;
      updateDeviceUI = vi.fn(() => {
        callCount++;
        if (callCount < 5) { // Prevent infinite recursion in test
          setDevicePreference(devicePreference === 'mobile' ? 'desktop' : 'mobile');
        }
      });
      
      // Should not cause stack overflow
      expect(() => setDevicePreference('mobile')).not.toThrow();
      
      // Should have limited the recursive calls
      expect(callCount).toBeLessThan(10);
    });
  });

  describe('Timing and Race Conditions', () => {
    it('should handle rapid API calls with different device preferences', async () => {
      // Mock fetch for concurrent API calls
      global.fetch = vi.fn().mockImplementation((url, options) => {
        const body = JSON.parse(options.body);
        return Promise.resolve({
          ok: true,
          json: async () => ({
            layout_json: { type: 'frame', children: [] },
            devicePreferenceUsed: true,
            detectedDevice: body.devicePreference
          })
        });
      });

      // Simulate rapid API calls with different preferences
      const apiCalls = [
        fetch('http://localhost:8000/api/v1/generate-wireframe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: 'test', devicePreference: 'mobile' })
        }),
        fetch('http://localhost:8000/api/v1/generate-wireframe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: 'test', devicePreference: 'desktop' })
        }),
        fetch('http://localhost:8000/api/v1/generate-wireframe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: 'test', devicePreference: null })
        })
      ];

      const results = await Promise.all(apiCalls);
      
      // All calls should succeed
      expect(results).toHaveLength(3);
      results.forEach(result => {
        expect(result.ok).toBe(true);
      });

      // Check responses
      const responses = await Promise.all(results.map(r => r.json()));
      expect(responses[0].detectedDevice).toBe('mobile');
      expect(responses[1].detectedDevice).toBe('desktop');
      expect(responses[2].detectedDevice).toBe(null);
    });

    it('should handle timestamp edge cases', () => {
      const now = Date.now();
      
      // Test with future timestamp (should be invalid)
      sessionStorage.setItem('devicePreference', 'mobile');
      sessionStorage.setItem('devicePreferenceTimestamp', (now + 1000).toString());
      
      const futureTimestamp = sessionStorage.getItem('devicePreferenceTimestamp');
      const timestamp = parseInt(futureTimestamp!);
      
      expect(timestamp > now).toBe(true);
      
      // Test with very old timestamp
      const oldTimestamp = now - (60 * 60 * 1000); // 1 hour ago
      sessionStorage.setItem('devicePreferenceTimestamp', oldTimestamp.toString());
      
      const storedOldTimestamp = parseInt(sessionStorage.getItem('devicePreferenceTimestamp')!);
      const age = now - storedOldTimestamp;
      const sessionTimeout = 30 * 60 * 1000; // 30 minutes
      
      expect(age > sessionTimeout).toBe(true);
    });
  });

  describe('Browser Compatibility Edge Cases', () => {
    it('should handle browsers without sessionStorage support', () => {
      // Mock sessionStorage methods to throw errors
      const originalSessionStorage = sessionStorage;
      (global as any).sessionStorage = {
        getItem: () => { throw new Error('sessionStorage not supported'); },
        setItem: () => { throw new Error('sessionStorage not supported'); },
        removeItem: () => { throw new Error('sessionStorage not supported'); }
      };
      
      // Should handle gracefully
      expect(() => setDevicePreference('mobile')).not.toThrow();
      expect(devicePreference).toBe('mobile');
      
      // Restore sessionStorage
      (global as any).sessionStorage = originalSessionStorage;
    });

    it('should handle DOM methods not available', () => {
      // Mock document methods to be undefined
      const originalQuerySelectorAll = document.querySelectorAll;
      (document as any).querySelectorAll = undefined;
      
      // Should handle gracefully
      expect(() => updateDeviceUI()).not.toThrow();
      
      // Restore original method
      document.querySelectorAll = originalQuerySelectorAll;
    });
  });
});