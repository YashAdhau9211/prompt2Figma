/// <reference types="@figma/plugin-typings" />

console.log('Plugin started');

// Show the UI
figma.showUI(__html__, {
  width: 420,
  height: 780,
  themeColors: true
});

console.log('UI shown');

// Handle messages from UI
figma.ui.onmessage = (msg) => {
  console.log('Message received:', msg);
  
  if (msg.type === "test") {
    figma.notify("Test message received!");
  }
  
  if (msg.type === "render-wireframe") {
    figma.notify("Wireframe render requested");
    // For now, just create a simple rectangle
    const rect = figma.createRectangle();
    rect.name = "Test Wireframe";
    rect.resize(200, 100);
    rect.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 1 } }];
    
    figma.currentPage.appendChild(rect);
    figma.viewport.scrollAndZoomIntoView([rect]);
    
    figma.notify("Test wireframe created!");
  }
};

console.log('Message handler set up');