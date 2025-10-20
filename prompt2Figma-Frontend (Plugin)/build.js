const esbuild = require('esbuild');

// Build the plugin code
esbuild.build({
  entryPoints: ['src/main/code.ts'],
  bundle: true,
  outfile: 'dist/code.js',
  platform: 'browser',
  target: 'es6',
  format: 'iife', // Immediately Invoked Function Expression - no module system
  logLevel: 'info',
}).catch(() => process.exit(1));
