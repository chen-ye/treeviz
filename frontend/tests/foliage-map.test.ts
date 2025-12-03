import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import '../src/components/foliage-map';
import { FoliageMap } from '../src/components/foliage-map';

describe('FoliageMap', () => {
  let element: FoliageMap;

  beforeEach(async () => {
    element = document.createElement('foliage-map') as FoliageMap;
    document.body.appendChild(element);
    await element.updateComplete;
  });

  afterEach(() => {
    document.body.removeChild(element);
    vi.clearAllMocks();
  });

  it('renders container', () => {
    const container = element.shadowRoot?.getElementById('map-container');
    expect(container).toBeTruthy();
  });

  it('fetches metadata on load', () => {
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/metadata'));
  });

  it('initializes Map and Overlay', async () => {
      const map = (element as any).map;
      const deck = (element as any).deck;
      expect(map).toBeTruthy();
      expect(deck).toBeTruthy();
  });
});
