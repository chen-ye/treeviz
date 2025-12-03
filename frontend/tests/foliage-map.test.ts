import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import '../src/components/foliage-map';
import { FoliageMap } from '../src/components/foliage-map';

// Mock DeckGL
vi.mock('@deck.gl/core', () => {
  return {
    Deck: class {
      constructor(props: any) {
        this.props = props;
        // Simulate initialization callbacks
        if (props.onDeviceInitialized) {
            props.onDeviceInitialized({
                createTexture: vi.fn(() => ({}))
            });
        }
      }
      props: any;
      setProps(newProps: any) {
        this.props = { ...this.props, ...newProps };
      }
      finalize() {}
    }
  };
});

// Mock fetch
global.fetch = vi.fn();

describe('FoliageMap', () => {
  let element: FoliageMap;

  beforeEach(async () => {
    (global.fetch as any).mockResolvedValue({
        json: async () => ({ atlas_mapping: { 'TestTree': 0 } })
    });

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

  it('initializes Deck', async () => {
      const deck = (element as any).deck;
      expect(deck).toBeTruthy();
  });
});
