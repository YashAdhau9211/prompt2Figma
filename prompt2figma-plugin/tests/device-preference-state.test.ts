import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock the device preference functions by extracting them from ui.js
// Since ui.js is a large file, we'll create isolated versions for testing

describe('Device Preference State Management', () => {
  let devicePreference: string | null;
  let sessionStartTime: number;
  let devicePreferenceErrors: any;

  // Mock functions extracted from ui.js for testing
  let setDevicePreference: (device: string | null) => void;
  let getDevicePreference: () => string | null;
  let clearDevicePreference: () => void;
  let restoreDevicePreference: () => boolean;
  let logDevicePreferenceEvent: (eventType: string, data?: any) => void;
  let updateDeviceUI: () => void;
  let showDevicePreferenceNotification: (type: string, message: string) => void;

  beforeEach(() => {
    // Reset state
    devicePreference = null;
    sessionStartTime = Date.now();
    devicePreferenceErrors = {
      transmissionFailures: 0,
      invalidStates: 0,
      fallbacksUsed: 0
    };

    // Mock DOM elements
    const mockDeviceOptions = [
      {
        dataset: { device: 'mobile' },
        classList: { add: vi.fn(), remove: vi.fn() },
        setAttribute: vi.fn(),
        getAttribute: vi.fn()
      },
      {
        dataset: { device: 'desktop' },
        classList: { add: vi.fn(), remove: vi.fn() },
        setAttribute: vi.fn(),
        getAttribute: vi.fn()
      }
    ];

    vi.mocked(document.querySelectorAll).mockReturnValue(mockDeviceOptions as any);

    // Mock functions (simplified versions of the actual functions)
    logDevicePreferenceEvent = vi.fn();
    updateDeviceUI = vi.fn();
    showDevicePreferenceNotification = vi.fn();

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
            console.warn('Failed to persist device preference to session storage:', storageError);
            logDevicePreferenceEvent('storage_error', { device, error: storageError.message });
          }
        } else {
          try {
            sessionStorage.removeItem('devicePreference');
            sessionStorage.removeItem('devicePreferenceTimestamp');
            logDevicePreferenceEvent('preference_cleared', { persisted: true });
          } catch (storageError: any) {
            console.warn('Failed to clear device preference from session storage:', storageError);
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

    clearDevicePreference = () => {
      try {
        devicePreference = null;
        sessionStorage.removeItem('devicePreference');
        sessionStorage.removeItem('devicePreferenceTimestamp');
        updateDeviceUI();
        logDevicePreferenceEvent('preference_cleared', { manual: true });
      } catch (error: any) {
        console.error('Error clearing device preference:', error);
        logDevicePreferenceEvent('clear_error', { error: error.message });
        devicePreference = null;
        updateDeviceUI();
        showDevicePreferenceNotification('warning', 'Device preference cleared with errors');
      }
    };

    restoreDevicePreference = () => {
      try {
        const storedPreference = sessionStorage.getItem('devicePreference');
        const storedTimestamp = sessionStorage.getItem('devicePreferenceTimestamp');

        if (storedPreference && storedTimestamp) {
          if (storedPreference !== 'mobile' && storedPreference !== 'desktop') {
            console.error(`Invalid stored device preference: ${storedPreference}. Clearing session data.`);
            logDevicePreferenceEvent('invalid_stored_preference', { invalid: storedPreference });
            devicePreferenceErrors.invalidStates++;
            sessionStorage.removeItem('devicePreference');
            sessionStorage.removeItem('devicePreferenceTimestamp');
            showDevicePreferenceNotification('warning', 'Stored device preference was invalid - cleared');
            return false;
          }

          const timestamp = parseInt(storedTimestamp);
          const currentTime = Date.now();

          if (isNaN(timestamp) || timestamp > currentTime) {
            console.error(`Invalid stored timestamp: ${storedTimestamp}. Clearing session data.`);
            logDevicePreferenceEvent('invalid_stored_timestamp', { timestamp: storedTimestamp });
            sessionStorage.removeItem('devicePreference');
            sessionStorage.removeItem('devicePreferenceTimestamp');
            showDevicePreferenceNotification('warning', 'Session data was corrupted - cleared');
            return false;
          }

          const sessionTimeout = 30 * 60 * 1000; // 30 minutes

          if (currentTime - timestamp < sessionTimeout) {
            devicePreference = storedPreference;
            logDevicePreferenceEvent('preference_restored', { device: storedPreference, age: currentTime - timestamp });
            return true;
          } else {
            sessionStorage.removeItem('devicePreference');
            sessionStorage.removeItem('devicePreferenceTimestamp');
            logDevicePreferenceEvent('session_expired', { device: storedPreference, age: currentTime - timestamp });
          }
        }

        return false;
      } catch (error: any) {
        console.error('Error restoring device preference:', error);
        logDevicePreferenceEvent('restore_error', { error: error.message });
        try {
          sessionStorage.removeItem('devicePreference');
          sessionStorage.removeItem('devicePreferenceTimestamp');
        } catch (clearError) {
          console.error('Failed to clear corrupted session data:', clearError);
        }
        showDevicePreferenceNotification('error', 'Failed to restore device preference - using auto-detect');
        return false;
      }
    };
  });

  describe('setDevicePreference', () => {
    it('should set valid mobile preference', () => {
      setDevicePreference('mobile');

      expect(devicePreference).toBe('mobile');
      expect(sessionStorage.getItem('devicePreference')).toBe('mobile');
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBeTruthy();
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('preference_set', { device: 'mobile', persisted: true });
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should set valid desktop preference', () => {
      setDevicePreference('desktop');

      expect(devicePreference).toBe('desktop');
      expect(sessionStorage.getItem('devicePreference')).toBe('desktop');
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBeTruthy();
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('preference_set', { device: 'desktop', persisted: true });
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should clear preference when set to null', () => {
      // First set a preference
      setDevicePreference('mobile');
      expect(devicePreference).toBe('mobile');

      // Then clear it
      setDevicePreference(null);

      expect(devicePreference).toBe(null);
      expect(sessionStorage.getItem('devicePreference')).toBe(null);
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('preference_cleared', { persisted: true });
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should reject invalid device preference and fallback to null', () => {
      setDevicePreference('invalid' as any);

      expect(devicePreference).toBe(null);
      expect(devicePreferenceErrors.invalidStates).toBe(1);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('invalid_state', {
        attempted: 'invalid',
        fallback: 'auto-detect'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Invalid device selection reset to auto-detect');
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should handle sessionStorage errors gracefully', () => {
      // Mock sessionStorage to throw an error
      const originalSetItem = sessionStorage.setItem;
      sessionStorage.setItem = vi.fn(() => {
        throw new Error('Storage quota exceeded');
      });

      setDevicePreference('mobile');

      expect(devicePreference).toBe('mobile'); // Should still set the preference
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('storage_error', {
        device: 'mobile',
        error: 'Storage quota exceeded'
      });
      expect(updateDeviceUI).toHaveBeenCalled();

      // Restore original function
      sessionStorage.setItem = originalSetItem;
    });
  });

  describe('getDevicePreference', () => {
    it('should return current device preference', () => {
      devicePreference = 'mobile';
      expect(getDevicePreference()).toBe('mobile');

      devicePreference = 'desktop';
      expect(getDevicePreference()).toBe('desktop');

      devicePreference = null;
      expect(getDevicePreference()).toBe(null);
    });

    it('should detect and fix invalid device preference state', () => {
      devicePreference = 'invalid' as any;

      const result = getDevicePreference();

      expect(result).toBe(null);
      expect(devicePreference).toBe(null);
      expect(devicePreferenceErrors.invalidStates).toBe(1);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('invalid_state_detected', {
        invalid: 'invalid',
        fallback: 'auto-detect'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Device selection was corrupted - reset to auto-detect');
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should handle errors gracefully', () => {
      // Mock updateDeviceUI to throw an error
      updateDeviceUI = vi.fn(() => {
        throw new Error('UI update failed');
      });

      devicePreference = 'invalid' as any;

      const result = getDevicePreference();

      expect(result).toBe(null);
      expect(devicePreference).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('get_preference_error', {
        error: 'UI update failed'
      });
    });
  });

  describe('clearDevicePreference', () => {
    it('should clear device preference and session storage', () => {
      // First set a preference
      devicePreference = 'mobile';
      sessionStorage.setItem('devicePreference', 'mobile');
      sessionStorage.setItem('devicePreferenceTimestamp', Date.now().toString());

      clearDevicePreference();

      expect(devicePreference).toBe(null);
      expect(sessionStorage.getItem('devicePreference')).toBe(null);
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('preference_cleared', { manual: true });
      expect(updateDeviceUI).toHaveBeenCalled();
    });

    it('should handle sessionStorage errors gracefully', () => {
      // Mock sessionStorage to throw an error
      const originalRemoveItem = sessionStorage.removeItem;
      sessionStorage.removeItem = vi.fn(() => {
        throw new Error('Storage access denied');
      });

      devicePreference = 'mobile';

      clearDevicePreference();

      expect(devicePreference).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('clear_error', {
        error: 'Storage access denied'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Device preference cleared with errors');
      expect(updateDeviceUI).toHaveBeenCalled();

      // Restore original function
      sessionStorage.removeItem = originalRemoveItem;
    });
  });

  describe('restoreDevicePreference', () => {
    it('should restore valid device preference from session storage', () => {
      const timestamp = Date.now();
      sessionStorage.setItem('devicePreference', 'mobile');
      sessionStorage.setItem('devicePreferenceTimestamp', timestamp.toString());

      const result = restoreDevicePreference();

      expect(result).toBe(true);
      expect(devicePreference).toBe('mobile');
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('preference_restored', {
        device: 'mobile',
        age: expect.any(Number)
      });
    });

    it('should reject invalid stored device preference', () => {
      sessionStorage.setItem('devicePreference', 'invalid');
      sessionStorage.setItem('devicePreferenceTimestamp', Date.now().toString());

      const result = restoreDevicePreference();

      expect(result).toBe(false);
      expect(devicePreferenceErrors.invalidStates).toBe(1);
      expect(sessionStorage.getItem('devicePreference')).toBe(null);
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('invalid_stored_preference', {
        invalid: 'invalid'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Stored device preference was invalid - cleared');
    });

    it('should reject expired session data', () => {
      const expiredTimestamp = Date.now() - (31 * 60 * 1000); // 31 minutes ago
      sessionStorage.setItem('devicePreference', 'mobile');
      sessionStorage.setItem('devicePreferenceTimestamp', expiredTimestamp.toString());

      const result = restoreDevicePreference();

      expect(result).toBe(false);
      expect(sessionStorage.getItem('devicePreference')).toBe(null);
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('session_expired', {
        device: 'mobile',
        age: expect.any(Number)
      });
    });

    it('should handle invalid timestamp', () => {
      sessionStorage.setItem('devicePreference', 'mobile');
      sessionStorage.setItem('devicePreferenceTimestamp', 'invalid-timestamp');

      const result = restoreDevicePreference();

      expect(result).toBe(false);
      expect(sessionStorage.getItem('devicePreference')).toBe(null);
      expect(sessionStorage.getItem('devicePreferenceTimestamp')).toBe(null);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('invalid_stored_timestamp', {
        timestamp: 'invalid-timestamp'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('warning', 'Session data was corrupted - cleared');
    });

    it('should return false when no stored data exists', () => {
      const result = restoreDevicePreference();

      expect(result).toBe(false);
      expect(devicePreference).toBe(null);
    });

    it('should handle storage access errors', () => {
      // Mock sessionStorage to throw an error
      const originalGetItem = sessionStorage.getItem;
      sessionStorage.getItem = vi.fn(() => {
        throw new Error('Storage access denied');
      });

      const result = restoreDevicePreference();

      expect(result).toBe(false);
      expect(logDevicePreferenceEvent).toHaveBeenCalledWith('restore_error', {
        error: 'Storage access denied'
      });
      expect(showDevicePreferenceNotification).toHaveBeenCalledWith('error', 'Failed to restore device preference - using auto-detect');

      // Restore original function
      sessionStorage.getItem = originalGetItem;
    });
  });
});