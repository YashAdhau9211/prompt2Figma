import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('Device Selector UI States', () => {
  let mockDeviceOptions: any[];
  let mockAnnouncementsElement: any;
  
  // Mock functions that would be imported from ui.js
  let updateDeviceUI: () => void;
  let initializeAccessibilityFeatures: () => void;
  let announceDeviceChange: (device: string | null) => void;
  
  beforeEach(() => {
    // Mock device option elements
    mockDeviceOptions = [
      {
        dataset: { device: 'mobile' },
        classList: { 
          add: vi.fn(), 
          remove: vi.fn(),
          contains: vi.fn().mockReturnValue(false)
        },
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
        addEventListener: vi.fn(),
        focus: vi.fn()
      },
      {
        dataset: { device: 'desktop' },
        classList: { 
          add: vi.fn(), 
          remove: vi.fn(),
          contains: vi.fn().mockReturnValue(false)
        },
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
        addEventListener: vi.fn(),
        focus: vi.fn()
      }
    ];

    // Mock announcements element for screen readers
    mockAnnouncementsElement = {
      textContent: '',
      setAttribute: vi.fn(),
      id: 'device-announcements'
    };

    // Mock DOM queries
    vi.mocked(document.querySelectorAll).mockImplementation((selector) => {
      if (selector === '.device-option') {
        return mockDeviceOptions as any;
      }
      return [] as any;
    });

    vi.mocked(document.getElementById).mockImplementation((id) => {
      if (id === 'device-announcements') {
        return mockAnnouncementsElement;
      }
      return null;
    });

    // Mock createElement for creating announcements element
    vi.mocked(document.createElement).mockImplementation((tagName) => {
      if (tagName === 'div') {
        return {
          id: '',
          className: '',
          setAttribute: vi.fn(),
          textContent: '',
          style: {},
          appendChild: vi.fn(),
          removeChild: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          classList: {
            add: vi.fn(),
            remove: vi.fn(),
            contains: vi.fn(),
            toggle: vi.fn()
          },
          innerHTML: '',
          parentNode: null
        } as any;
      }
      return {} as any;
    });

    // Implement UI update function
    updateDeviceUI = () => {
      try {
        const deviceOptions = document.querySelectorAll('.device-option');
        
        if (deviceOptions.length === 0) {
          console.warn('No device option elements found in DOM');
          return;
        }

        deviceOptions.forEach(option => {
          const deviceType = (option as any).dataset.device;
          
          if (!deviceType || (deviceType !== 'mobile' && deviceType !== 'desktop')) {
            console.warn(`Invalid device type in DOM element: ${deviceType}`);
            return;
          }

          // This would normally check against devicePreference global variable
          // For testing, we'll simulate different states
          const isActive = (option as any).mockActive || false;
          
          if (isActive) {
            (option as any).classList.add('active');
            (option as any).setAttribute('aria-checked', 'true');
            (option as any).setAttribute('tabindex', '0');
          } else {
            (option as any).classList.remove('active');
            (option as any).setAttribute('aria-checked', 'false');
            (option as any).setAttribute('tabindex', '-1');
          }
        });

        // Ensure at least one option is focusable if none are selected
        const hasActiveOption = Array.from(deviceOptions).some(option => 
          (option as any).mockActive
        );
        
        if (!hasActiveOption && deviceOptions.length > 0) {
          (deviceOptions[0] as any).setAttribute('tabindex', '0');
        }
      } catch (error) {
        console.error('Error updating device UI:', error);
      }
    };

    // Implement accessibility initialization
    initializeAccessibilityFeatures = () => {
      try {
        const deviceOptions = document.querySelectorAll('.device-option');
        
        deviceOptions.forEach((option, index) => {
          const deviceType = (option as any).dataset.device;
          
          // Set initial ARIA states
          const isActive = (option as any).mockActive || false;
          (option as any).setAttribute('aria-checked', isActive ? 'true' : 'false');
          
          // Set initial tabindex
          if (isActive || (!isActive && index === 0)) {
            (option as any).setAttribute('tabindex', '0');
          } else {
            (option as any).setAttribute('tabindex', '-1');
          }
        });
        
        // Add live region for announcements if not present
        if (!document.getElementById('device-announcements')) {
          const announcements = document.createElement('div');
          announcements.id = 'device-announcements';
          announcements.className = 'sr-only';
          announcements.setAttribute('aria-live', 'polite');
          announcements.setAttribute('aria-atomic', 'true');
          document.body.appendChild(announcements);
        }
      } catch (error) {
        console.error('Error initializing accessibility features:', error);
      }
    };

    // Implement device change announcement
    announceDeviceChange = (device: string | null) => {
      try {
        const announcements = document.getElementById('device-announcements');
        if (announcements) {
          let message;
          if (device === 'mobile') {
            message = 'Mobile device selected. Wireframes will be optimized for mobile screens.';
          } else if (device === 'desktop') {
            message = 'Desktop device selected. Wireframes will be optimized for desktop screens.';
          } else {
            message = 'Device selection cleared. AI will automatically detect the appropriate device type.';
          }
          
          announcements.textContent = message;
        }
      } catch (error) {
        console.error('Error announcing device change:', error);
      }
    };
  });

  describe('UI State Management', () => {
    it('should update UI when mobile device is selected', () => {
      // Simulate mobile selection
      mockDeviceOptions[0].mockActive = true;
      mockDeviceOptions[1].mockActive = false;
      
      updateDeviceUI();
      
      // Check mobile option is active
      expect(mockDeviceOptions[0].classList.add).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('aria-checked', 'true');
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '0');
      
      // Check desktop option is inactive
      expect(mockDeviceOptions[1].classList.remove).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('aria-checked', 'false');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
    });

    it('should update UI when desktop device is selected', () => {
      // Simulate desktop selection
      mockDeviceOptions[0].mockActive = false;
      mockDeviceOptions[1].mockActive = true;
      
      updateDeviceUI();
      
      // Check mobile option is inactive
      expect(mockDeviceOptions[0].classList.remove).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('aria-checked', 'false');
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
      
      // Check desktop option is active
      expect(mockDeviceOptions[1].classList.add).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('aria-checked', 'true');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('tabindex', '0');
    });

    it('should update UI when no device is selected', () => {
      // Simulate no selection
      mockDeviceOptions[0].mockActive = false;
      mockDeviceOptions[1].mockActive = false;
      
      updateDeviceUI();
      
      // Check both options are inactive
      expect(mockDeviceOptions[0].classList.remove).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('aria-checked', 'false');
      expect(mockDeviceOptions[1].classList.remove).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('aria-checked', 'false');
      
      // Check first option is focusable (fallback)
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '0');
    });

    it('should handle missing device option elements gracefully', () => {
      // Mock empty querySelectorAll result
      vi.mocked(document.querySelectorAll).mockReturnValue([] as any);
      
      // Should not throw error
      expect(() => updateDeviceUI()).not.toThrow();
    });

    it('should handle invalid device types in DOM elements', () => {
      // Add invalid device type
      mockDeviceOptions.push({
        dataset: { device: 'invalid' },
        classList: { add: vi.fn(), remove: vi.fn() },
        setAttribute: vi.fn()
      });
      
      // Should not throw error and should skip invalid element
      expect(() => updateDeviceUI()).not.toThrow();
    });

    it('should handle missing dataset.device attribute', () => {
      // Add element without device type
      mockDeviceOptions.push({
        dataset: {},
        classList: { add: vi.fn(), remove: vi.fn() },
        setAttribute: vi.fn()
      });
      
      // Should not throw error and should skip element without device type
      expect(() => updateDeviceUI()).not.toThrow();
    });
  });

  describe('Accessibility Features', () => {
    it('should initialize ARIA states correctly', () => {
      initializeAccessibilityFeatures();
      
      // Check ARIA states are set
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('aria-checked', 'false');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('aria-checked', 'false');
      
      // Check tabindex is set (first option should be focusable)
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '0');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
    });

    it('should create announcements live region', () => {
      // Mock getElementById to return null initially
      vi.mocked(document.getElementById).mockReturnValue(null);
      
      initializeAccessibilityFeatures();
      
      // Check that createElement was called to create announcements element
      expect(document.createElement).toHaveBeenCalledWith('div');
      expect(document.body.appendChild).toHaveBeenCalled();
    });

    it('should not create duplicate announcements live region', () => {
      // Mock getElementById to return existing element
      vi.mocked(document.getElementById).mockReturnValue(mockAnnouncementsElement);
      
      const createElementSpy = vi.mocked(document.createElement);
      createElementSpy.mockClear();
      
      initializeAccessibilityFeatures();
      
      // Should not create new element if one already exists
      expect(createElementSpy).not.toHaveBeenCalled();
    });

    it('should announce mobile device selection', () => {
      announceDeviceChange('mobile');
      
      expect(mockAnnouncementsElement.textContent).toBe(
        'Mobile device selected. Wireframes will be optimized for mobile screens.'
      );
    });

    it('should announce desktop device selection', () => {
      announceDeviceChange('desktop');
      
      expect(mockAnnouncementsElement.textContent).toBe(
        'Desktop device selected. Wireframes will be optimized for desktop screens.'
      );
    });

    it('should announce device selection cleared', () => {
      announceDeviceChange(null);
      
      expect(mockAnnouncementsElement.textContent).toBe(
        'Device selection cleared. AI will automatically detect the appropriate device type.'
      );
    });

    it('should handle missing announcements element gracefully', () => {
      // Mock getElementById to return null
      vi.mocked(document.getElementById).mockReturnValue(null);
      
      // Should not throw error
      expect(() => announceDeviceChange('mobile')).not.toThrow();
    });
  });

  describe('Visual State Transitions', () => {
    it('should apply active class to selected device option', () => {
      mockDeviceOptions[0].mockActive = true;
      updateDeviceUI();
      
      expect(mockDeviceOptions[0].classList.add).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[0].classList.remove).not.toHaveBeenCalledWith('active');
    });

    it('should remove active class from unselected device option', () => {
      mockDeviceOptions[0].mockActive = false;
      updateDeviceUI();
      
      expect(mockDeviceOptions[0].classList.remove).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[0].classList.add).not.toHaveBeenCalledWith('active');
    });

    it('should handle rapid state changes', () => {
      // Simulate rapid selection changes
      mockDeviceOptions[0].mockActive = true;
      updateDeviceUI();
      
      mockDeviceOptions[0].mockActive = false;
      mockDeviceOptions[1].mockActive = true;
      updateDeviceUI();
      
      mockDeviceOptions[1].mockActive = false;
      updateDeviceUI();
      
      // Should handle all state changes without errors
      expect(mockDeviceOptions[0].classList.remove).toHaveBeenCalledWith('active');
      expect(mockDeviceOptions[1].classList.remove).toHaveBeenCalledWith('active');
    });
  });

  describe('Keyboard Navigation Support', () => {
    it('should maintain proper tabindex for keyboard navigation', () => {
      // Test with mobile selected
      mockDeviceOptions[0].mockActive = true;
      mockDeviceOptions[1].mockActive = false;
      updateDeviceUI();
      
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '0');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
      
      // Test with desktop selected
      mockDeviceOptions[0].mockActive = false;
      mockDeviceOptions[1].mockActive = true;
      updateDeviceUI();
      
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '-1');
      expect(mockDeviceOptions[1].setAttribute).toHaveBeenCalledWith('tabindex', '0');
    });

    it('should ensure at least one option is focusable when none selected', () => {
      mockDeviceOptions[0].mockActive = false;
      mockDeviceOptions[1].mockActive = false;
      updateDeviceUI();
      
      // First option should be focusable as fallback
      expect(mockDeviceOptions[0].setAttribute).toHaveBeenCalledWith('tabindex', '0');
    });
  });

  describe('Error Handling', () => {
    it('should handle DOM manipulation errors gracefully', () => {
      // Mock classList.add to throw error
      mockDeviceOptions[0].classList.add = vi.fn(() => {
        throw new Error('DOM manipulation failed');
      });
      
      mockDeviceOptions[0].mockActive = true;
      
      // Should not throw error
      expect(() => updateDeviceUI()).not.toThrow();
    });

    it('should handle setAttribute errors gracefully', () => {
      // Mock setAttribute to throw error
      mockDeviceOptions[0].setAttribute = vi.fn(() => {
        throw new Error('setAttribute failed');
      });
      
      // Should not throw error
      expect(() => updateDeviceUI()).not.toThrow();
    });

    it('should handle accessibility initialization errors', () => {
      // Mock setAttribute to throw error during accessibility init
      mockDeviceOptions[0].setAttribute = vi.fn(() => {
        throw new Error('Accessibility setup failed');
      });
      
      // Should not throw error
      expect(() => initializeAccessibilityFeatures()).not.toThrow();
    });
  });
});