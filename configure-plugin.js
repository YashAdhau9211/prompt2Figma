#!/usr/bin/env node

/**
 * Configuration script for Prompt2Figma plugin
 * Updates the backend URL in the plugin source code
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const UI_FILE_PATH = path.join(__dirname, 'prompt2Figma-Frontend (Plugin)', 'src', 'ui', 'ui.js');
const MANIFEST_PATH = path.join(__dirname, 'prompt2Figma-Frontend (Plugin)', 'manifest.json');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

async function main() {
  console.log('\n🚀 Prompt2Figma Plugin Configuration\n');
  console.log('This script will help you configure your plugin with your deployed backend URL.\n');

  // Get backend URL
  const backendUrl = await question('Enter your backend URL (e.g., https://your-app.railway.app): ');
  
  if (!backendUrl || !backendUrl.startsWith('http')) {
    console.error('❌ Invalid URL. Please provide a valid HTTP/HTTPS URL.');
    rl.close();
    return;
  }

  // Remove trailing slash
  const cleanUrl = backendUrl.replace(/\/$/, '');

  console.log('\n📝 Updating plugin configuration...\n');

  // Update ui.js
  try {
    let uiContent = fs.readFileSync(UI_FILE_PATH, 'utf8');
    
    // Replace the backend URL
    const urlRegex = /const backendUrl = ["']http:\/\/localhost:8000["'];/;
    if (urlRegex.test(uiContent)) {
      uiContent = uiContent.replace(urlRegex, `const backendUrl = "${cleanUrl}";`);
      fs.writeFileSync(UI_FILE_PATH, uiContent, 'utf8');
      console.log('✅ Updated backend URL in ui.js');
    } else {
      console.warn('⚠️  Could not find backend URL pattern in ui.js');
    }
  } catch (error) {
    console.error('❌ Error updating ui.js:', error.message);
  }

  // Update manifest.json
  try {
    const manifestContent = fs.readFileSync(MANIFEST_PATH, 'utf8');
    const manifest = JSON.parse(manifestContent);
    
    // Extract domain from URL
    const domain = new URL(cleanUrl).hostname;
    
    // Add network access if not present
    if (!manifest.networkAccess) {
      manifest.networkAccess = {
        allowedDomains: []
      };
    }
    
    // Add domain if not already present
    if (!manifest.networkAccess.allowedDomains.includes(domain)) {
      manifest.networkAccess.allowedDomains.push(domain);
      manifest.networkAccess.allowedDomains.push('generativelanguage.googleapis.com');
      
      fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2), 'utf8');
      console.log('✅ Updated network access in manifest.json');
    }
  } catch (error) {
    console.error('❌ Error updating manifest.json:', error.message);
  }

  console.log('\n✨ Configuration complete!\n');
  console.log('Next steps:');
  console.log('1. cd "prompt2Figma-Frontend (Plugin)"');
  console.log('2. npm install');
  console.log('3. npm run build');
  console.log('4. Test the plugin in Figma Desktop\n');

  rl.close();
}

main().catch(error => {
  console.error('❌ Error:', error.message);
  rl.close();
  process.exit(1);
});
