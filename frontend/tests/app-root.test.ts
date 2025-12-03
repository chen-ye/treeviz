import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { html, render } from 'lit';
import '../src/components/app-root';
import { AppRoot } from '../src/components/app-root';

describe('AppRoot', () => {
  let element: AppRoot;

  beforeEach(async () => {
    element = document.createElement('app-root') as AppRoot;
    document.body.appendChild(element);
    await element.updateComplete;
  });

  afterEach(() => {
    document.body.removeChild(element);
  });

  it('renders correctly', () => {
    const header = element.shadowRoot?.querySelector('header');
    expect(header).toBeTruthy();
    expect(header?.textContent).toContain('Seattle Foliage Map');
  });

  it('contains foliage-map', () => {
    const map = element.shadowRoot?.querySelector('foliage-map');
    expect(map).toBeTruthy();
  });

  // Note: timeline-slider is used in template but not defined in the code I saw earlier.
  // Wait, I saw <timeline-slider> in app-root.ts but I didn't see the file for it in file list.
  // Let's check if timeline-slider is a real component or just a placeholder in my previous read.
});
