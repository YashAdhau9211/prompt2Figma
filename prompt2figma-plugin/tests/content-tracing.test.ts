import { describe, it, expect, beforeEach } from 'vitest';
import {
  getContentTrace,
  traceContentResolution,
  enterComponentTrace,
  exitComponentTrace,
  clearContentTrace,
  enableContentTracing,
  disableContentTracing,
  getContentTraceStats,
  generateContentTraceReport,
  exportContentTraceJSON,
  type TextContentSource
} from '../src/main/content-validation';

describe('Content Tracing System', () => {
  beforeEach(() => {
    // Clear trace before each test
    clearContentTrace();
    enableContentTracing();
  });

  describe('Basic Tracing', () => {
    it('should trace content resolution with path', () => {
      enterComponentTrace('Root');
      enterComponentTrace('ProductCard');
      
      const contentSource: TextContentSource = {
        value: 'Product A',
        source: 'props.text',
        isExplicit: true
      };

      traceContentResolution(
        'ProductName',
        'text',
        { text: 'Product A' },
        contentSource,
        'Product A',
        false
      );

      exitComponentTrace();
      exitComponentTrace();

      const trace = getContentTrace();
      const entries = trace.getEntries();

      expect(entries).toHaveLength(1);
      expect(entries[0].componentName).toBe('ProductName');
      expect(entries[0].componentPath).toBe('Root > ProductCard');
      expect(entries[0].resolution.finalContent).toBe('Product A');
      expect(entries[0].resolution.isExplicit).toBe(true);
      expect(entries[0].resolution.wasGenerated).toBe(false);
    });

    it('should track nested component paths correctly', () => {
      enterComponentTrace('Root');
      enterComponentTrace('Frame1');
      enterComponentTrace('Frame2');
      
      const contentSource: TextContentSource = {
        value: 'Nested Text',
        source: 'props.content',
        isExplicit: true
      };

      traceContentResolution(
        'DeepText',
        'text',
        { content: 'Nested Text' },
        contentSource,
        'Nested Text',
        false
      );

      const trace = getContentTrace();
      const entries = trace.getEntries();

      expect(entries[0].componentPath).toBe('Root > Frame1 > Frame2');
    });

    it('should handle multiple components at same level', () => {
      enterComponentTrace('Root');
      
      const source1: TextContentSource = {
        value: 'Text 1',
        source: 'props.text',
        isExplicit: true
      };

      const source2: TextContentSource = {
        value: 'Text 2',
        source: 'props.text',
        isExplicit: true
      };

      traceContentResolution('Text1', 'text', { text: 'Text 1' }, source1, 'Text 1', false);
      traceContentResolution('Text2', 'text', { text: 'Text 2' }, source2, 'Text 2', false);

      const trace = getContentTrace();
      const entries = trace.getEntries();

      expect(entries).toHaveLength(2);
      expect(entries[0].componentPath).toBe('Root');
      expect(entries[1].componentPath).toBe('Root');
    });
  });

  describe('Content Source Filtering', () => {
    beforeEach(() => {
      enterComponentTrace('Root');
      
      // Add various content sources
      traceContentResolution(
        'ExplicitText',
        'text',
        { text: 'Explicit' },
        { value: 'Explicit', source: 'props.text', isExplicit: true },
        'Explicit',
        false
      );

      traceContentResolution(
        'FallbackText',
        'text',
        {},
        { value: 'FallbackText', source: 'componentName', isExplicit: false },
        'FallbackText',
        false
      );

      traceContentResolution(
        'GeneratedText',
        'text',
        {},
        { value: 'Generated Content', source: 'generated', isExplicit: false },
        'Generated Content',
        true
      );

      exitComponentTrace();
    });

    it('should filter explicit content entries', () => {
      const trace = getContentTrace();
      const explicitEntries = trace.getExplicitEntries();

      expect(explicitEntries).toHaveLength(1);
      expect(explicitEntries[0].componentName).toBe('ExplicitText');
    });

    it('should filter generated content entries', () => {
      const trace = getContentTrace();
      const generatedEntries = trace.getGeneratedEntries();

      expect(generatedEntries).toHaveLength(1);
      expect(generatedEntries[0].componentName).toBe('GeneratedText');
    });

    it('should filter by content source', () => {
      const trace = getContentTrace();
      const textSourceEntries = trace.getEntriesBySource('props.text');
      const componentNameEntries = trace.getEntriesBySource('componentName');

      expect(textSourceEntries).toHaveLength(1);
      expect(componentNameEntries).toHaveLength(1);
    });

    it('should get entries for specific component', () => {
      const trace = getContentTrace();
      const entries = trace.getEntriesForComponent('ExplicitText');

      expect(entries).toHaveLength(1);
      expect(entries[0].resolution.finalContent).toBe('Explicit');
    });
  });

  describe('Content Trace Statistics', () => {
    it('should calculate correct statistics', () => {
      enterComponentTrace('Root');
      
      // Add 3 explicit, 2 fallback, 1 generated
      traceContentResolution('T1', 'text', { text: 'A' }, { value: 'A', source: 'props.text', isExplicit: true }, 'A', false);
      traceContentResolution('T2', 'text', { content: 'B' }, { value: 'B', source: 'props.content', isExplicit: true }, 'B', false);
      traceContentResolution('T3', 'text', { title: 'C' }, { value: 'C', source: 'props.title', isExplicit: true }, 'C', false);
      traceContentResolution('T4', 'text', {}, { value: 'T4', source: 'componentName', isExplicit: false }, 'T4', false);
      traceContentResolution('T5', 'text', {}, { value: 'T5', source: 'componentName', isExplicit: false }, 'T5', false);
      traceContentResolution('T6', 'text', {}, { value: 'Gen', source: 'generated', isExplicit: false }, 'Gen', true);

      const stats = getContentTraceStats();

      expect(stats.total).toBe(6);
      expect(stats.explicit).toBe(3);
      expect(stats.generated).toBe(1);
      expect(stats.bySource['props.text']).toBe(1);
      expect(stats.bySource['props.content']).toBe(1);
      expect(stats.bySource['props.title']).toBe(1);
      expect(stats.bySource['componentName']).toBe(2);
      expect(stats.bySource['generated']).toBe(1);
    });

    it('should track component types', () => {
      enterComponentTrace('Root');
      
      traceContentResolution('T1', 'text', { text: 'A' }, { value: 'A', source: 'props.text', isExplicit: true }, 'A', false);
      traceContentResolution('B1', 'button', { text: 'B' }, { value: 'B', source: 'props.text', isExplicit: true }, 'B', false);
      traceContentResolution('I1', 'input', { placeholder: 'C' }, { value: 'C', source: 'props.text', isExplicit: true }, 'C', false);

      const stats = getContentTraceStats();

      expect(stats.byType['text']).toBe(1);
      expect(stats.byType['button']).toBe(1);
      expect(stats.byType['input']).toBe(1);
    });
  });

  describe('Content Trace Report', () => {
    it('should generate a text report', () => {
      enterComponentTrace('Root');
      enterComponentTrace('ProductCard');
      
      traceContentResolution(
        'ProductName',
        'text',
        { text: 'Product A' },
        { value: 'Product A', source: 'props.text', isExplicit: true },
        'Product A',
        false
      );

      const report = generateContentTraceReport();

      expect(report).toContain('CONTENT TRACE REPORT');
      expect(report).toContain('Total Components: 1');
      expect(report).toContain('Product A');
      expect(report).toContain('props.text');
      expect(report).toContain('Root > ProductCard');
      expect(report).toContain('Type: text');
    });

    it('should handle empty trace', () => {
      const report = generateContentTraceReport();

      expect(report).toContain('No content trace entries recorded');
    });
  });

  describe('Content Trace Export', () => {
    it('should export trace as JSON', () => {
      enterComponentTrace('Root');
      
      traceContentResolution(
        'TestText',
        'text',
        { text: 'Test' },
        { value: 'Test', source: 'props.text', isExplicit: true },
        'Test',
        false
      );

      const jsonStr = exportContentTraceJSON();
      const data = JSON.parse(jsonStr);

      expect(data.summary.totalComponents).toBe(1);
      expect(data.summary.explicitCount).toBe(1);
      expect(data.summary.generatedCount).toBe(0);
      expect(data.entries).toHaveLength(1);
      expect(data.entries[0].componentName).toBe('TestText');
      expect(data.exportedAt).toBeDefined();
    });
  });

  describe('Trace Control', () => {
    it('should enable and disable tracing', () => {
      const trace = getContentTrace();
      
      enableContentTracing();
      expect(trace.isEnabled()).toBe(true);

      disableContentTracing();
      expect(trace.isEnabled()).toBe(false);
    });

    it('should not record when disabled', () => {
      disableContentTracing();
      
      enterComponentTrace('Root');
      traceContentResolution(
        'Test',
        'text',
        { text: 'Test' },
        { value: 'Test', source: 'props.text', isExplicit: true },
        'Test',
        false
      );

      const trace = getContentTrace();
      expect(trace.getCount()).toBe(0);
    });

    it('should clear trace log', () => {
      enterComponentTrace('Root');
      traceContentResolution(
        'Test',
        'text',
        { text: 'Test' },
        { value: 'Test', source: 'props.text', isExplicit: true },
        'Test',
        false
      );

      const trace = getContentTrace();
      expect(trace.getCount()).toBe(1);

      clearContentTrace();
      expect(trace.getCount()).toBe(0);
    });
  });

  describe('Checked Properties Tracking', () => {
    it('should track all checked properties', () => {
      enterComponentTrace('Root');
      
      const props = {
        text: 'Text Value',
        content: 'Content Value',
        title: 'Title Value'
      };

      traceContentResolution(
        'Test',
        'text',
        props,
        { value: 'Text Value', source: 'props.text', isExplicit: true },
        'Text Value',
        false
      );

      const trace = getContentTrace();
      const entries = trace.getEntries();

      expect(entries[0].resolution.checkedProperties.text).toBe('Text Value');
      expect(entries[0].resolution.checkedProperties.content).toBe('Content Value');
      expect(entries[0].resolution.checkedProperties.title).toBe('Title Value');
    });

    it('should track undefined properties', () => {
      enterComponentTrace('Root');
      
      traceContentResolution(
        'Test',
        'text',
        {},
        { value: 'Test', source: 'componentName', isExplicit: false },
        'Test',
        false
      );

      const trace = getContentTrace();
      const entries = trace.getEntries();

      expect(entries[0].resolution.checkedProperties.text).toBeUndefined();
      expect(entries[0].resolution.checkedProperties.content).toBeUndefined();
      expect(entries[0].resolution.checkedProperties.title).toBeUndefined();
    });
  });
});
