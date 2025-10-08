let layoutJson = null; // store generated wireframe JSON

// Device selection state management
let devicePreference = null; // null = auto-detect, 'mobile', 'desktop'
let sessionStartTime = Date.now(); // Track session start for persistence logic

// Error handling and fallback state
let devicePreferenceErrors = {
  transmissionFailures: 0,
  invalidStates: 0,
  fallbacksUsed: 0
};

// Device preference functions with session persistence and error handling
function setDevicePreference(device) {
  try {
    // Validate device preference value
    if (device !== null && device !== 'mobile' && device !== 'desktop') {
      console.error(`Invalid device preference: ${device}. Falling back to auto-detect.`);
      logDevicePreferenceEvent('invalid_state', { 
        attempted: device, 
        fallback: 'auto-detect' 
      });
      devicePreferenceErrors.invalidStates++;
      device = null; // Reset to auto-detect
      showDevicePreferenceNotification('warning', 'Invalid device selection reset to auto-detect');
    }
    
    devicePreference = device;
    
    // Store in session storage for persistence during plugin session
    if (device !== null) {
      try {
        sessionStorage.setItem('devicePreference', device);
        sessionStorage.setItem('devicePreferenceTimestamp', Date.now().toString());
        logDevicePreferenceEvent('preference_set', { device, persisted: true });
      } catch (storageError) {
        console.warn('Failed to persist device preference to session storage:', storageError);
        logDevicePreferenceEvent('storage_error', { device, error: storageError.message });
        // Continue without persistence - not critical
      }
    } else {
      // Clear session storage when preference is reset
      try {
        sessionStorage.removeItem('devicePreference');
        sessionStorage.removeItem('devicePreferenceTimestamp');
        logDevicePreferenceEvent('preference_cleared', { persisted: true });
      } catch (storageError) {
        console.warn('Failed to clear device preference from session storage:', storageError);
        logDevicePreferenceEvent('storage_clear_error', { error: storageError.message });
      }
    }
    
    updateDeviceUI();
    
    // Announce change to screen readers
    announceDeviceChange(device);
    
    console.log(`Device preference set to: ${device || 'auto-detect'} and persisted to session`);
  } catch (error) {
    console.error('Error in setDevicePreference:', error);
    logDevicePreferenceEvent('set_preference_error', { 
      attempted: device, 
      error: error.message 
    });
    
    // Fallback to safe state
    devicePreference = null;
    updateDeviceUI();
    showDevicePreferenceNotification('error', 'Device selection error - reset to auto-detect');
  }
}

function getDevicePreference() {
  try {
    // Validate current device preference state
    if (devicePreference !== null && devicePreference !== 'mobile' && devicePreference !== 'desktop') {
      console.error(`Invalid device preference state detected: ${devicePreference}. Resetting to auto-detect.`);
      logDevicePreferenceEvent('invalid_state_detected', { 
        invalid: devicePreference, 
        fallback: 'auto-detect' 
      });
      devicePreferenceErrors.invalidStates++;
      devicePreference = null;
      updateDeviceUI();
      showDevicePreferenceNotification('warning', 'Device selection was corrupted - reset to auto-detect');
    }
    
    // Return null when no device is explicitly selected to trigger AI detection
    return devicePreference;
  } catch (error) {
    console.error('Error in getDevicePreference:', error);
    logDevicePreferenceEvent('get_preference_error', { error: error.message });
    
    // Fallback to safe state
    devicePreference = null;
    return null;
  }
}

function restoreDevicePreference() {
  try {
    // Restore device preference from session storage if available
    const storedPreference = sessionStorage.getItem('devicePreference');
    const storedTimestamp = sessionStorage.getItem('devicePreferenceTimestamp');
    
    if (storedPreference && storedTimestamp) {
      // Validate stored preference
      if (storedPreference !== 'mobile' && storedPreference !== 'desktop') {
        console.error(`Invalid stored device preference: ${storedPreference}. Clearing session data.`);
        logDevicePreferenceEvent('invalid_stored_preference', { 
          invalid: storedPreference 
        });
        devicePreferenceErrors.invalidStates++;
        
        // Clear invalid session data
        sessionStorage.removeItem('devicePreference');
        sessionStorage.removeItem('devicePreferenceTimestamp');
        showDevicePreferenceNotification('warning', 'Stored device preference was invalid - cleared');
        return false;
      }
      
      const timestamp = parseInt(storedTimestamp);
      const currentTime = Date.now();
      
      // Validate timestamp
      if (isNaN(timestamp) || timestamp > currentTime) {
        console.error(`Invalid stored timestamp: ${storedTimestamp}. Clearing session data.`);
        logDevicePreferenceEvent('invalid_stored_timestamp', { 
          timestamp: storedTimestamp 
        });
        
        // Clear invalid session data
        sessionStorage.removeItem('devicePreference');
        sessionStorage.removeItem('devicePreferenceTimestamp');
        showDevicePreferenceNotification('warning', 'Session data was corrupted - cleared');
        return false;
      }
      
      // Check if the stored preference is from the current session (within reasonable time)
      // Consider it the same session if stored within the last 30 minutes
      const sessionTimeout = 30 * 60 * 1000; // 30 minutes in milliseconds
      
      if (currentTime - timestamp < sessionTimeout) {
        devicePreference = storedPreference;
        console.log(`Restored device preference from session: ${storedPreference}`);
        logDevicePreferenceEvent('preference_restored', { 
          device: storedPreference, 
          age: currentTime - timestamp 
        });
        return true;
      } else {
        // Clear expired session data
        sessionStorage.removeItem('devicePreference');
        sessionStorage.removeItem('devicePreferenceTimestamp');
        console.log('Expired device preference cleared from session storage');
        logDevicePreferenceEvent('session_expired', { 
          device: storedPreference, 
          age: currentTime - timestamp 
        });
      }
    }
    
    return false;
  } catch (error) {
    console.error('Error restoring device preference:', error);
    logDevicePreferenceEvent('restore_error', { error: error.message });
    
    // Clear potentially corrupted session data
    try {
      sessionStorage.removeItem('devicePreference');
      sessionStorage.removeItem('devicePreferenceTimestamp');
    } catch (clearError) {
      console.error('Failed to clear corrupted session data:', clearError);
    }
    
    showDevicePreferenceNotification('error', 'Failed to restore device preference - using auto-detect');
    return false;
  }
}

function clearDevicePreference() {
  try {
    devicePreference = null;
    sessionStorage.removeItem('devicePreference');
    sessionStorage.removeItem('devicePreferenceTimestamp');
    updateDeviceUI();
    console.log('Device preference cleared and removed from session storage');
    logDevicePreferenceEvent('preference_cleared', { manual: true });
  } catch (error) {
    console.error('Error clearing device preference:', error);
    logDevicePreferenceEvent('clear_error', { error: error.message });
    
    // Force reset to safe state
    devicePreference = null;
    updateDeviceUI();
    showDevicePreferenceNotification('warning', 'Device preference cleared with errors');
  }
}

// Device preference logging function
function logDevicePreferenceEvent(eventType, data = {}) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    event: eventType,
    sessionId: sessionStartTime,
    currentPreference: devicePreference,
    errorCounts: { ...devicePreferenceErrors },
    ...data
  };
  
  console.log(`[DevicePreference] ${eventType}:`, logEntry);
  
  // Store recent events for debugging (keep last 50 events)
  if (!window.devicePreferenceLogs) {
    window.devicePreferenceLogs = [];
  }
  
  window.devicePreferenceLogs.push(logEntry);
  if (window.devicePreferenceLogs.length > 50) {
    window.devicePreferenceLogs.shift();
  }
}

// Device preference notification function
function showDevicePreferenceNotification(type, message) {
  // Create a brief notification that doesn't interfere with main workflow
  const notificationElement = document.createElement('div');
  notificationElement.className = `device-preference-notification ${type}`;
  
  // Add icon based on type
  const iconSvg = type === 'error' 
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
    : type === 'warning'
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
    : type === 'success'
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0;"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  
  notificationElement.innerHTML = `${iconSvg}<span>${message}</span>`;
  document.body.appendChild(notificationElement);
  
  // Auto-remove after 4 seconds with smooth fade out
  setTimeout(() => {
    if (notificationElement.parentNode) {
      notificationElement.style.animation = 'slideOutRight 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
      setTimeout(() => {
        if (notificationElement.parentNode) {
          document.body.removeChild(notificationElement);
        }
      }, 300);
    }
  }, 4000);
}

function updateDeviceUI() {
  try {
    const deviceOptions = document.querySelectorAll('.device-option');

    if (deviceOptions.length === 0) {
      console.warn('No device option elements found in DOM');
      logDevicePreferenceEvent('ui_elements_missing', {});
      return;
    }

    deviceOptions.forEach(option => {
      try {
        const deviceType = option.dataset.device;

        // Validate device type from DOM element
        if (!deviceType) {
          console.warn('Device option element missing data-device attribute');
          return;
        }

        if (deviceType !== 'mobile' && deviceType !== 'desktop') {
          console.warn(`Invalid device type in DOM element: ${deviceType}`);
          return;
        }

        const wasActive = option.classList.contains('active');
        const shouldBeActive = devicePreference === deviceType;

        if (shouldBeActive) {
          option.classList.add('active');
          option.setAttribute('aria-checked', 'true');
          option.setAttribute('tabindex', '0');
          
          // Add subtle pulse animation on activation
          if (!wasActive) {
            option.style.animation = 'none';
            setTimeout(() => {
              option.style.animation = '';
            }, 10);
          }
        } else {
          option.classList.remove('active');
          option.setAttribute('aria-checked', 'false');
          option.setAttribute('tabindex', '-1');
        }
      } catch (optionError) {
        console.error('Error updating individual device option:', optionError);
        logDevicePreferenceEvent('ui_option_update_error', { 
          error: optionError.message 
        });
      }
    });

    // Ensure at least one option is focusable if none are selected
    if (devicePreference === null) {
      const firstOption = deviceOptions[0];
      if (firstOption) {
        firstOption.setAttribute('tabindex', '0');
      }
    }

    // Add subtle visual feedback to the entire device selector
    const deviceSelector = document.querySelector('.device-selector');
    if (deviceSelector && devicePreference !== null) {
      deviceSelector.style.transform = 'scale(1.01)';
      setTimeout(() => {
        deviceSelector.style.transform = '';
      }, 200);
    }

    logDevicePreferenceEvent('ui_updated', { 
      preference: devicePreference,
      optionCount: deviceOptions.length
    });
  } catch (error) {
    console.error('Error updating device UI:', error);
    logDevicePreferenceEvent('ui_update_error', { error: error.message });
    
    // Try to show error notification if possible
    try {
      showDevicePreferenceNotification('error', 'Device selection UI update failed');
    } catch (notificationError) {
      console.error('Failed to show error notification:', notificationError);
    }
  }
}

// Initialize session persistence and accessibility features
function initializeSessionPersistence() {
  try {
    // Restore device preference from session storage
    const restored = restoreDevicePreference();
    
    if (restored) {
      console.log('Device preference restored from session storage');
      logDevicePreferenceEvent('session_restored', { 
        preference: devicePreference 
      });
    } else {
      console.log('No valid device preference found in session storage');
      logDevicePreferenceEvent('session_not_restored', {});
    }
    
    // Initialize UI state
    updateDeviceUI();
    
    // Set up accessibility features
    initializeAccessibilityFeatures();
    
  } catch (error) {
    console.error('Error initializing session persistence:', error);
    logDevicePreferenceEvent('initialization_error', { 
      error: error.message 
    });
    
    // Fallback to safe state
    devicePreference = null;
    updateDeviceUI();
    showDevicePreferenceNotification('warning', 'Session initialization failed - using defaults');
  }
}

// Announce device preference changes to screen readers
function announceDeviceChange(device) {
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
      
      logDevicePreferenceEvent('screen_reader_announcement', { 
        device, 
        message 
      });
    }
  } catch (error) {
    console.error('Error announcing device change:', error);
    logDevicePreferenceEvent('announcement_error', { 
      error: error.message 
    });
  }
}

// Initialize accessibility features
function initializeAccessibilityFeatures() {
  try {
    const deviceOptions = document.querySelectorAll('.device-option');
    
    // Ensure proper initial ARIA states
    deviceOptions.forEach((option, index) => {
      const deviceType = option.dataset.device;
      
      // Set initial ARIA states
      option.setAttribute('aria-checked', devicePreference === deviceType ? 'true' : 'false');
      
      // Set initial tabindex - first option or selected option should be focusable
      if (devicePreference === deviceType || (devicePreference === null && index === 0)) {
        option.setAttribute('tabindex', '0');
      } else {
        option.setAttribute('tabindex', '-1');
      }
    });
    
    // Add live region for announcements
    if (!document.getElementById('device-announcements')) {
      const announcements = document.createElement('div');
      announcements.id = 'device-announcements';
      announcements.className = 'sr-only';
      announcements.setAttribute('aria-live', 'polite');
      announcements.setAttribute('aria-atomic', 'true');
      document.body.appendChild(announcements);
    }
    
    logDevicePreferenceEvent('accessibility_initialized', {
      optionCount: deviceOptions.length
    });
    
  } catch (error) {
    console.error('Error initializing accessibility features:', error);
    logDevicePreferenceEvent('accessibility_init_error', { 
      error: error.message 
    });
  }
}

window.addEventListener("DOMContentLoaded", () => {
  // Initialize session persistence and restore device preference
  initializeSessionPersistence();
  
  // Get DOM elements
  const generateWireframeBtn = document.getElementById("generateWireframeBtn");
  const generateCodeBtn = document.getElementById("generateCodeBtn");
  const promptInput = document.getElementById("promptInput");
  const enhanceBtn = document.getElementById("enhanceBtn");
  const clearBtn = document.getElementById("clearBtn");
  const copyBtn = document.getElementById("copyBtn");
  const charCount = document.getElementById("charCount");
  const statusSection = document.getElementById("statusSection");
  const outputSection = document.getElementById("outputSection");
  const codeOutput = document.getElementById("codeOutput");
  const progressSection = document.getElementById("progressSection");
  const templateButtons = document.querySelectorAll(".template-btn");
  const deviceOptions = document.querySelectorAll(".device-option");

  // Character counter
  promptInput.addEventListener("input", () => {
    const count = promptInput.value.length;
    charCount.textContent = count;

    // Update character count color based on limit
    if (count > 450) {
      charCount.style.color = "#ef4444";
    } else if (count > 400) {
      charCount.style.color = "#f59e0b";
    } else {
      charCount.style.color = "#d1d5db";
    }
  });

  // Clear functionality (can be triggered by keyboard shortcut)
  function clearInput() {
    promptInput.value = "";
    charCount.textContent = "0";
    charCount.style.color = "#d1d5db";
    promptInput.focus();
  }

  // Clear button functionality
  clearBtn.addEventListener("click", clearInput);

  // Keyboard shortcuts
  promptInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      clearInput();
    }
  });

  // Template buttons functionality
  templateButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const template = btn.dataset.template;
      const templateText = getTemplate(template);
      promptInput.value = templateText;
      charCount.textContent = templateText.length;
      promptInput.focus();

      // Visual feedback
      btn.style.background = "#6366f1";
      btn.style.color = "white";
      btn.style.borderColor = "#6366f1";

      setTimeout(() => {
        btn.style.background = "";
        btn.style.color = "";
        btn.style.borderColor = "";
      }, 200);
    });
  });

  // Device selection functionality with enhanced state management, error handling, and keyboard navigation
  function handleDeviceSelection(deviceType, source = 'click') {
    try {
      // Validate device type from UI element
      if (!deviceType || (deviceType !== 'mobile' && deviceType !== 'desktop')) {
        console.error(`Invalid device type from UI element: ${deviceType}`);
        logDevicePreferenceEvent('invalid_ui_device_type', { deviceType, source });
        showDevicePreferenceNotification('error', 'Invalid device selection - please try again');
        return;
      }

      // Toggle selection - if selecting the same device, deselect it
      if (devicePreference === deviceType) {
        setDevicePreference(null);
      } else {
        setDevicePreference(deviceType);
      }
      
      // Log state change for debugging
      console.log(`Device selection changed via ${source}. Current preference: ${getDevicePreference()}`);
      logDevicePreferenceEvent('user_selection', { 
        selected: deviceType,
        wasToggleOff: devicePreference !== deviceType,
        finalState: getDevicePreference(),
        source: source
      });
    } catch (error) {
      console.error(`Error in device selection ${source} handler:`, error);
      logDevicePreferenceEvent('ui_interaction_error', { error: error.message, source });
      showDevicePreferenceNotification('error', 'Device selection failed - please try again');
      
      // Reset to safe state
      try {
        setDevicePreference(null);
      } catch (resetError) {
        console.error('Failed to reset device preference after error:', resetError);
      }
    }
  }

  deviceOptions.forEach(option => {
    // Click handler
    option.addEventListener("click", () => {
      const deviceType = option.dataset.device;
      handleDeviceSelection(deviceType, 'click');
    });

    // Keyboard navigation handler
    option.addEventListener("keydown", (e) => {
      const deviceType = option.dataset.device;
      const currentIndex = Array.from(deviceOptions).indexOf(option);
      
      switch (e.key) {
        case 'Enter':
        case ' ': // Space key
          e.preventDefault();
          handleDeviceSelection(deviceType, 'keyboard');
          break;
          
        case 'ArrowLeft':
        case 'ArrowUp':
          e.preventDefault();
          // Move to previous option (with wrapping)
          const prevIndex = currentIndex === 0 ? deviceOptions.length - 1 : currentIndex - 1;
          deviceOptions[prevIndex].focus();
          logDevicePreferenceEvent('keyboard_navigation', { 
            direction: 'previous', 
            from: currentIndex, 
            to: prevIndex 
          });
          break;
          
        case 'ArrowRight':
        case 'ArrowDown':
          e.preventDefault();
          // Move to next option (with wrapping)
          const nextIndex = currentIndex === deviceOptions.length - 1 ? 0 : currentIndex + 1;
          deviceOptions[nextIndex].focus();
          logDevicePreferenceEvent('keyboard_navigation', { 
            direction: 'next', 
            from: currentIndex, 
            to: nextIndex 
          });
          break;
          
        case 'Home':
          e.preventDefault();
          // Move to first option
          deviceOptions[0].focus();
          logDevicePreferenceEvent('keyboard_navigation', { 
            direction: 'home', 
            from: currentIndex, 
            to: 0 
          });
          break;
          
        case 'End':
          e.preventDefault();
          // Move to last option
          const lastIndex = deviceOptions.length - 1;
          deviceOptions[lastIndex].focus();
          logDevicePreferenceEvent('keyboard_navigation', { 
            direction: 'end', 
            from: currentIndex, 
            to: lastIndex 
          });
          break;
          
        case 'Escape':
          e.preventDefault();
          // Clear selection and move focus to first option
          setDevicePreference(null);
          deviceOptions[0].focus();
          logDevicePreferenceEvent('keyboard_clear', { 
            from: currentIndex 
          });
          break;
      }
    });

    // Focus handler for screen reader announcements
    option.addEventListener("focus", () => {
      const deviceType = option.dataset.device;
      const isSelected = devicePreference === deviceType;
      
      // Update aria-describedby to provide context
      const statusText = isSelected ? 'Currently selected' : 'Not selected';
      option.setAttribute('aria-describedby', `device-description device-status-${deviceType}`);
      
      // Create or update status element for screen readers
      let statusElement = document.getElementById(`device-status-${deviceType}`);
      if (!statusElement) {
        statusElement = document.createElement('div');
        statusElement.id = `device-status-${deviceType}`;
        statusElement.className = 'sr-only';
        statusElement.setAttribute('aria-live', 'polite');
        document.body.appendChild(statusElement);
      }
      statusElement.textContent = statusText;
      
      logDevicePreferenceEvent('focus_received', { 
        deviceType, 
        isSelected 
      });
    });
  });

  // Enhance with AI button functionality
  enhanceBtn.addEventListener("click", async () => {
    const currentText = promptInput.value.trim();
    if (!currentText) {
      showStatus("error", "No Text to Enhance", "Please enter some text first before enhancing.");
      return;
    }

    // Show loading state
    enhanceBtn.disabled = true;
    enhanceBtn.innerHTML = `
      <div class="spinner" style="width: 12px; height: 12px; border-width: 2px;"></div>
      Enhancing...
    `;

    // Simulate AI enhancement (you can replace this with actual API call)
    setTimeout(() => {
      const enhancedText = enhancePrompt(currentText);
      promptInput.value = enhancedText;
      charCount.textContent = enhancedText.length;

      // Reset button
      enhanceBtn.disabled = false;
      enhanceBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor"/>
        </svg>
        Enhance with AI
      `;

      showStatus("success", "Text Enhanced!", "Your prompt has been improved with AI suggestions.");
    }, 1500);
  });

  // Copy button functionality
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(codeOutput.textContent);

      // Visual feedback
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Copied!
      `;
      copyBtn.classList.add("copied");

      setTimeout(() => {
        copyBtn.innerHTML = originalText;
        copyBtn.classList.remove("copied");
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  });

  // Generate wireframe
  generateWireframeBtn.addEventListener("click", async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) {
      showStatus("error", "Empty Prompt", "Please describe your UI vision to get started.");
      return;
    }

    if (prompt.length < 10) {
      showStatus("error", "Too Short", "Please provide a more detailed description (at least 10 characters).");
      return;
    }

    // Show loading state
    setButtonLoading(generateWireframeBtn, true);
    showProgress();
    showStatus("loading", "Generating Wireframe", "AI is analyzing your prompt and creating the wireframe...");

    layoutJson = null;
    generateCodeBtn.disabled = true;
    hideOutput();

    try {
      const currentDevicePreference = getDevicePreference();
      console.log("Sending API request with device preference:", currentDevicePreference);
      console.log("Device preference maintained across generation:", currentDevicePreference !== null ? "Yes" : "No (using AI detection)");
      
      const requestPayload = {
        prompt,
        devicePreference: currentDevicePreference
      };
      
      console.log("Full API request payload:", requestPayload);
      logDevicePreferenceEvent('api_request_sent', { 
        devicePreference: currentDevicePreference,
        hasPreference: currentDevicePreference !== null
      });
      
      const res = await fetch("http://localhost:8000/api/v1/generate-wireframe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload)
      });

      const data = await res.json();

      if (data.layout_json) {
        layoutJson = data.layout_json;
        completeProgress();
        
        // Check if device preference was actually used by the backend
        const backendUsedPreference = data.devicePreferenceUsed;
        const backendDetectedDevice = data.detectedDevice;
        
        if (currentDevicePreference && !backendUsedPreference) {
          // Device preference transmission failed, backend fell back to AI detection
          console.warn("Device preference transmission failed - backend used AI detection");
          logDevicePreferenceEvent('transmission_failure', {
            sentPreference: currentDevicePreference,
            backendDetected: backendDetectedDevice,
            fallbackUsed: true
          });
          devicePreferenceErrors.transmissionFailures++;
          devicePreferenceErrors.fallbacksUsed++;
          
          showDevicePreferenceNotification('warning', 
            `Device preference not applied - used AI detection (${backendDetectedDevice || 'unknown'})`);
          showStatus("success", "Wireframe Generated!", 
            `Your wireframe has been created using AI detection (${backendDetectedDevice || 'auto-detected'}) instead of your device preference.`);
        } else if (currentDevicePreference && backendUsedPreference) {
          // Device preference was successfully used
          logDevicePreferenceEvent('preference_applied', {
            preference: currentDevicePreference,
            confirmed: true
          });
          showStatus("success", "Wireframe Generated!", 
            `Your wireframe has been created for ${currentDevicePreference} as requested.`);
        } else {
          // No device preference set, AI detection used normally
          logDevicePreferenceEvent('ai_detection_used', {
            detectedDevice: backendDetectedDevice
          });
          showStatus("success", "Wireframe Generated!", "Your wireframe has been created and added to the Figma canvas.");
        }

        // Send to main thread to render in Figma with fallback handling
        const devicePref = getDevicePreference();
        console.log("Sending device preference to main thread:", devicePref);
        
        try {
          parent.postMessage({ 
            pluginMessage: { 
              type: "render-wireframe", 
              json: layoutJson,
              devicePreference: devicePref,
              fallbackInfo: {
                transmissionFailed: currentDevicePreference && !backendUsedPreference,
                detectedDevice: backendDetectedDevice
              }
            } 
          }, "*");
          
          logDevicePreferenceEvent('render_message_sent', {
            devicePreference: devicePref,
            hasFallbackInfo: true
          });
        } catch (messageError) {
          console.error("Failed to send render message to main thread:", messageError);
          logDevicePreferenceEvent('render_message_error', {
            error: messageError.message,
            devicePreference: devicePref
          });
          
          // Fallback: try without device preference
          try {
            parent.postMessage({ 
              pluginMessage: { 
                type: "render-wireframe", 
                json: layoutJson
              } 
            }, "*");
            
            showDevicePreferenceNotification('warning', 'Rendered without device preference due to communication error');
            logDevicePreferenceEvent('render_fallback_success', {});
          } catch (fallbackError) {
            console.error("Fallback render message also failed:", fallbackError);
            logDevicePreferenceEvent('render_fallback_error', {
              error: fallbackError.message
            });
            throw fallbackError; // Re-throw to trigger main error handling
          }
        }
        
        generateCodeBtn.disabled = false;
      } else {
        hideProgress();
        logDevicePreferenceEvent('generation_failed', {
          devicePreference: currentDevicePreference,
          response: data
        });
        showStatus("error", "Generation Failed", "Unable to generate wireframe. Please try rephrasing your prompt.");
      }
    } catch (err) {
      console.error("Backend connection error:", err);

      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        showStatus("error", "Server Not Running", "Backend server is not running. Please start the server at http://localhost:8000");
      } else if (err.message.includes('NetworkError') || err.message.includes('Failed to fetch')) {
        showStatus("error", "Connection Failed", "Cannot connect to backend server. Ensure the server is running at http://localhost:8000");
      } else {
        showStatus("error", "Backend Error", `Server error: ${err.message}`);
      }
    } finally {
      setButtonLoading(generateWireframeBtn, false);
      if (!layoutJson) hideProgress();
    }
  });

  // Generate code
  generateCodeBtn.addEventListener("click", async () => {
    if (!layoutJson) {
      showStatus("error", "No Wireframe", "Please generate a wireframe first before creating code.");
      return;
    }

    // Show loading state
    setButtonLoading(generateCodeBtn, true);
    showStatus("loading", "Generating Code", "Converting your wireframe into clean React code...");
    hideOutput();

    try {
      const res = await fetch("http://localhost:8000/api/v1/generate-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ layout_json: layoutJson })
      });

      const data = await res.json();

      if (data.react_code) {
        showStatus("success", "Code Generated!", `React code created successfully. Validation: ${data.validation_status || 'Passed'}`);
        showOutput(data.react_code);
      } else {
        showStatus("error", "Code Generation Failed", "Unable to generate React code from the wireframe.");
      }
    } catch (err) {
      console.error("Backend connection error:", err);

      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        showStatus("error", "Server Not Running", "Backend server is not running. Please start the server at http://localhost:8000");
      } else if (err.message.includes('NetworkError') || err.message.includes('Failed to fetch')) {
        showStatus("error", "Connection Failed", "Cannot connect to backend server. Ensure the server is running at http://localhost:8000");
      } else {
        showStatus("error", "Backend Error", `Server error: ${err.message}`);
      }
    } finally {
      setButtonLoading(generateCodeBtn, false);
    }
  });

  // Helper functions
  function setButtonLoading(button, isLoading) {
    if (isLoading) {
      button.classList.add("loading");
      button.disabled = true;
    } else {
      button.classList.remove("loading");
      button.disabled = false;
    }
  }

  function showStatus(type, title, message) {
    const statusIcon = document.getElementById("statusIcon");
    const statusTitle = document.getElementById("statusTitle");
    const statusMessage = document.getElementById("statusMessage");
    const statusCard = statusSection.querySelector(".status-card");

    // Remove existing status classes
    statusCard.classList.remove("success", "error", "loading");
    statusCard.classList.add(type);

    // Set icon based on type
    let iconSvg = "";
    switch (type) {
      case "success":
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`;
        break;
      case "error":
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
        break;
      case "loading":
        iconSvg = `<div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>`;
        break;
    }

    statusIcon.innerHTML = iconSvg;
    statusTitle.textContent = title;
    statusMessage.textContent = message;
    statusSection.style.display = "block";
  }

  function showOutput(code) {
    codeOutput.textContent = code;
    outputSection.style.display = "block";
  }

  function hideOutput() {
    outputSection.style.display = "none";
  }

  // Progress functions
  function showProgress() {
    progressSection.style.display = "block";
    updateProgressStep(1);

    setTimeout(() => updateProgressStep(2), 1000);
    setTimeout(() => updateProgressStep(3), 2000);
  }

  function updateProgressStep(step) {
    const steps = progressSection.querySelectorAll(".progress-step");
    steps.forEach((stepEl, index) => {
      stepEl.classList.remove("active", "completed");
      if (index + 1 < step) {
        stepEl.classList.add("completed");
      } else if (index + 1 === step) {
        stepEl.classList.add("active");
      }
    });
  }

  function completeProgress() {
    const steps = progressSection.querySelectorAll(".progress-step");
    steps.forEach(step => {
      step.classList.remove("active");
      step.classList.add("completed");
    });

    setTimeout(() => {
      hideProgress();
    }, 1500);
  }

  function hideProgress() {
    progressSection.style.display = "none";
  }

  // Template functions
  function getTemplate(type) {
    const templates = {
      dashboard: "Create a modern admin dashboard with a sidebar navigation containing menu items (Dashboard, Analytics, Users, Settings), a top header with user profile and notifications, and a main content area with metric cards showing key statistics, data visualization charts, and a recent activity table.",
      landing: "Design a landing page with a hero section featuring a compelling headline and call-to-action button, followed by a features section with 3-4 feature cards, testimonials section, and a footer with contact information and social links.",
      form: "Build a user registration form with input fields for name, email, password, and confirm password. Include proper validation, clear labels, helpful error messages, and a submit button. Add a clean, professional layout with good spacing.",
      mobile: "Create a mobile app interface with a bottom tab navigation (Home, Search, Profile, Settings), a header with app title and menu icon, and a main content area with cards or list items. Make it touch-friendly with proper spacing."
    };

    return templates[type] || "";
  }

  // Auto-resize textarea
  promptInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 200) + "px";
  });

  // Focus on input when plugin loads
  setTimeout(() => {
    promptInput.focus();
  }, 100);

  // Helper function to enhance prompts
  function enhancePrompt(text) {
    // Simple AI-like enhancement - you can replace this with actual AI API
    const enhancements = {
      'button': 'interactive button with hover states and proper accessibility',
      'card': 'modern card component with subtle shadows and rounded corners',
      'dashboard': 'comprehensive dashboard with data visualization, metrics, and user-friendly navigation',
      'form': 'well-structured form with proper validation, clear labels, and intuitive user flow',
      'navigation': 'intuitive navigation system with clear hierarchy and responsive design',
      'sidebar': 'collapsible sidebar with organized menu items and smooth animations',
      'header': 'professional header with branding, navigation, and user controls',
      'footer': 'informative footer with links, contact information, and social media integration'
    };

    let enhanced = text;

    // Add specific enhancements based on keywords
    Object.keys(enhancements).forEach(keyword => {
      if (text.toLowerCase().includes(keyword) && !text.toLowerCase().includes(enhancements[keyword])) {
        enhanced = enhanced.replace(new RegExp(keyword, 'gi'), enhancements[keyword]);
      }
    });

    // Add general improvements
    if (!enhanced.includes('responsive')) {
      enhanced += ' Make it responsive and mobile-friendly.';
    }

    if (!enhanced.includes('modern') && !enhanced.includes('clean')) {
      enhanced += ' Use a modern, clean design aesthetic.';
    }

    return enhanced;
  }
});

// Session persistence initialization function
function initializeSessionPersistence() {
  console.log("Initializing session persistence for device selection...");
  
  // Attempt to restore device preference from session storage
  const restored = restoreDevicePreference();
  
  if (restored) {
    // Update UI to reflect restored state
    updateDeviceUI();
    console.log("Device preference restored and UI updated");
  } else {
    // Ensure UI is in default state
    devicePreference = null;
    updateDeviceUI();
    console.log("Starting with clean device preference state");
  }
  
  // Set up session monitoring
  setupSessionMonitoring();
}

// Session monitoring to handle plugin lifecycle
function setupSessionMonitoring() {
  try {
    // Listen for beforeunload to clean up if needed
    window.addEventListener('beforeunload', () => {
      console.log("Plugin unloading, session data will persist for next session");
      logDevicePreferenceEvent('plugin_unload', { 
        finalPreference: devicePreference,
        errorCounts: { ...devicePreferenceErrors }
      });
    });
    
    // Listen for focus events to detect if plugin was reopened
    window.addEventListener('focus', () => {
      console.log("Plugin focused, checking session state...");
      
      try {
        // Verify session storage is still valid
        const storedPreference = sessionStorage.getItem('devicePreference');
        const storedTimestamp = sessionStorage.getItem('devicePreferenceTimestamp');
        
        if (storedPreference && storedTimestamp) {
          const timestamp = parseInt(storedTimestamp);
          const currentTime = Date.now();
          const sessionTimeout = 30 * 60 * 1000; // 30 minutes
          
          if (currentTime - timestamp >= sessionTimeout) {
            // Session expired, clear state
            clearDevicePreference();
            console.log("Session expired on focus, cleared device preference");
          } else {
            console.log("Session still valid on focus");
          }
        }
      } catch (focusError) {
        console.error('Error during focus event handling:', focusError);
        logDevicePreferenceEvent('focus_error', { error: focusError.message });
      }
    });
    
    // Periodic session validation (every 5 minutes)
    setInterval(() => {
      try {
        const storedTimestamp = sessionStorage.getItem('devicePreferenceTimestamp');
        if (storedTimestamp) {
          const timestamp = parseInt(storedTimestamp);
          const currentTime = Date.now();
          const sessionTimeout = 30 * 60 * 1000; // 30 minutes
          
          if (currentTime - timestamp >= sessionTimeout) {
            clearDevicePreference();
            console.log("Session expired during periodic check, cleared device preference");
          }
        }
      } catch (intervalError) {
        console.error('Error during periodic session check:', intervalError);
        logDevicePreferenceEvent('periodic_check_error', { error: intervalError.message });
      }
    }, 5 * 60 * 1000); // Check every 5 minutes
    
    logDevicePreferenceEvent('session_monitoring_setup', {});
  } catch (error) {
    console.error('Error setting up session monitoring:', error);
    logDevicePreferenceEvent('session_monitoring_setup_error', { error: error.message });
  }
}

// Debugging and diagnostics functions
window.getDevicePreferenceStats = function() {
  return {
    currentPreference: devicePreference,
    sessionStartTime: sessionStartTime,
    errorCounts: { ...devicePreferenceErrors },
    recentLogs: window.devicePreferenceLogs ? window.devicePreferenceLogs.slice(-10) : [],
    sessionStorage: {
      preference: sessionStorage.getItem('devicePreference'),
      timestamp: sessionStorage.getItem('devicePreferenceTimestamp')
    }
  };
};

window.resetDevicePreferenceErrors = function() {
  const oldErrors = { ...devicePreferenceErrors };
  devicePreferenceErrors = {
    transmissionFailures: 0,
    invalidStates: 0,
    fallbacksUsed: 0
  };
  logDevicePreferenceEvent('error_counts_reset', { oldErrors });
  console.log('Device preference error counts reset');
  return oldErrors;
};

window.testDevicePreferenceError = function(errorType = 'invalid_state') {
  console.log(`Testing device preference error: ${errorType}`);
  
  switch (errorType) {
    case 'invalid_state':
      devicePreference = 'invalid_value';
      getDevicePreference(); // This will trigger validation and reset
      break;
    case 'storage_error':
      // Temporarily break session storage
      const originalSetItem = sessionStorage.setItem;
      sessionStorage.setItem = () => { throw new Error('Test storage error'); };
      setDevicePreference('mobile');
      sessionStorage.setItem = originalSetItem;
      break;
    case 'ui_error':
      updateDeviceUI(); // Test with potentially missing DOM elements
      break;
    default:
      console.log('Unknown error type. Available: invalid_state, storage_error, ui_error');
  }
};