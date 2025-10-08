# Implementation Plan

- [x] 1. Create content validation utilities





  - Implement `resolveTextContent()` function that prioritizes text sources (text > content > title > componentName)
  - Add TypeScript interfaces for `TextContentSource` and `ContentRenderLog`
  - Create `logContentRendering()` function for debugging content decisions
  - Write unit tests for content resolution logic with various input scenarios
  - _Requirements: 1.2, 2.1, 2.2, 3.1_

- [x] 2. Implement JSON structure validation





  - Create `validateWireframeJSON()` function to check JSON structure before rendering
  - Add validation for required fields (type, componentName)
  - Implement recursive validation for nested children components
  - Add specific validation for Text components to detect missing content
  - Write unit tests for JSON validation with valid and invalid structures
  - _Requirements: 4.1, 4.3, 4.4, 3.2_

- [x] 3. Refactor createText function with strict content validation





  - Replace existing content detection logic with `resolveTextContent()` call
  - Remove automatic smart content generation for components with explicit content
  - Add comprehensive logging for all content decisions (explicit vs generated)
  - Implement proper handling of empty strings as explicit content
  - Add type conversion for non-string content values
  - Write unit tests for createText with various content scenarios
  - _Requirements: 1.1, 1.2, 2.1, 2.3, 3.1, 3.3_

- [x] 4. Add JSON validation to wireframe rendering pipeline





  - Integrate `validateWireframeJSON()` call in `createArtboard()` function
  - Log validation results (errors and warnings) to console
  - Display validation errors to user via Figma notifications
  - Continue rendering with warnings but block on critical errors
  - Write integration tests for validation in rendering pipeline
  - _Requirements: 3.2, 3.4, 4.4_

- [x] 5. Enhance logging throughout rendering process





  - Add detailed JSON logging when receiving data from backend
  - Log each component's content source during rendering
  - Add warning logs for content substitutions or fallbacks
  - Create structured log format for easy debugging
  - Add optional log level configuration (verbose/normal/quiet)
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 6. Update createButton and createInput functions






  - Apply same content validation logic to button text rendering
  - Apply same content validation logic to input placeholder text
  - Remove smart content generation from these components
  - Add logging for button and input content decisions
  - Write unit tests for button and input content handling
  - _Requirements: 1.1, 1.2, 2.1, 3.1_

- [x] 7. Add content priority documentation





  - Document the text content priority order (text > content > title > componentName)
  - Add inline code comments explaining content resolution logic
  - Create examples of correct JSON structure with text properties
  - Document fallback behavior when content is missing
  - _Requirements: 4.2_

- [x] 8. Create integration tests for Nykaa use case





  - Create test JSON matching the Nykaa homepage structure from the issue
  - Test that product names ("Product A", "Product B") render exactly as specified
  - Test that category labels ("Makeup", "Skincare", "Hair") render correctly
  - Test that brand names and section titles render without substitution
  - Verify no placeholder text like "Smart Reports" appears in output
  - _Requirements: 1.1, 1.3, 4.1_

- [x] 9. Add error handling for content rendering failures





  - Implement try-catch blocks around content resolution
  - Add graceful fallback when content resolution fails
  - Log detailed error messages with component context
  - Display user-friendly error notifications for rendering failures
  - Write tests for error scenarios (null props, undefined values, etc.)
  - _Requirements: 3.4_

- [x] 10. Create debugging tools for content tracing





  - Add a content trace log that shows the full path of content resolution for each component
  - Create a summary report of all content sources used in a wireframe
  - Add console command to export content trace logs
  - Implement visual indicators in Figma for generated vs explicit content (optional)
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 11. Test with real backend integration












  - Generate wireframe with "Nykaa homepage for mobile" prompt
  - Verify backend JSON contains correct product/category names
  - Confirm rendered wireframe matches backend JSON exactly
  - Test with multiple different prompts to ensure consistency
  - Document any backend issues discovered during testing
  - _Requirements: 1.1, 1.3, 4.1_

- [x] 12. Add regression tests for existing functionality





  - Test that existing wireframes without text properties still render
  - Verify component name fallback works correctly
  - Test backward compatibility with old JSON structures
  - Ensure no breaking changes to other component types (Frame, Rectangle, etc.)
  - _Requirements: 4.3_
