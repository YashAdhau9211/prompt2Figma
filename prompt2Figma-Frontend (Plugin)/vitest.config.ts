import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        'tests/',
        '*.config.*',
        'coverage/'
      ]
    },
    include: ['tests/**/*.test.{js,ts}'],
    exclude: ['node_modules/', 'dist/']
  }
});