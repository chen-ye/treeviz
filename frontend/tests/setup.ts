import { vi } from 'vitest';

// Mock MapLibre
vi.mock('maplibre-gl', () => {
  return {
    default: {
      Map: class {
        constructor(options: any) {
           // Simulate container attachment
        }
        addControl() {}
        remove() {}
      }
    }
  };
});

// Mock DeckGL Mapbox Overlay
vi.mock('@deck.gl/mapbox', () => {
  return {
    MapboxOverlay: class {
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

// Mock fetch globally
global.fetch = vi.fn();
(global.fetch as any).mockResolvedValue({
    json: async () => ({ atlas_mapping: { 'TestTree': 0 } })
});
