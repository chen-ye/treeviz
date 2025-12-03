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
});
