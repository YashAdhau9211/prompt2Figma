const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');

// Read the HTML file
const htmlPath = path.join(__dirname, 'dist', 'ui.html');
const htmlContent = fs.readFileSync(htmlPath, 'utf8');

// Build the plugin code with HTML content injected
esbuild.build({
  entryPoints: ['src/main/code.ts'],
  bundle: true,
  outfile: 'dist/code.js',
  platform: 'browser',
  target: 'es6',
  format: 'iife', // Immediately Invoked Function Expression - no module system
  logLevel: 'info',
  define: {
    '__html__': JSON.stringify(htmlContent)
  }
}).catch(() => process.exit(1));
