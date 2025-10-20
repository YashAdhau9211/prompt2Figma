// Test setup file for device selection functionality tests

// Mock sessionStorage for testing
const mockSessionStorage = (() => {
  let store: Record<string, string> = {};
  
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    }
  };
})();

// Mock global objects for browser environment
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
  writable: true
});

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
};

// Mock DOM methods that might be used
Object.defineProperty(document, 'createElement', {
  value: vi.fn(() => ({
    style: {},
    setAttribute: vi.fn(),
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
    textContent: '',
    innerHTML: '',
    parentNode: null
  })),
  writable: true
});

Object.defineProperty(document, 'getElementById', {
  value: vi.fn(),
  writable: true
});

Object.defineProperty(document, 'querySelectorAll', {
  value: vi.fn(() => []),
  writable: true
});

Object.defineProperty(document, 'querySelector', {
  value: vi.fn(),
  writable: true
});

Object.defineProperty(document.body, 'appendChild', {
  value: vi.fn(),
  writable: true
});

Object.defineProperty(document.head, 'appendChild', {
  value: vi.fn(),
  writable: true
});

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
  mockSessionStorage.clear();
  
  // Reset global variables that might be set by the device selection code
  if (typeof window !== 'undefined') {
    (window as any).devicePreferenceLogs = [];
  }
});