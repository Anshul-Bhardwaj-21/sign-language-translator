import '@testing-library/jest-dom';

// Mock getUserMedia for tests
Object.defineProperty(global.navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn(),
  },
});

// Mock speechSynthesis
Object.defineProperty(global, 'speechSynthesis', {
  writable: true,
  value: {
    cancel: vi.fn(),
    speak: vi.fn(),
  },
});
