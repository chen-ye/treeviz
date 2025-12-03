import { LitElement, html, css, unsafeCSS } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { MapboxOverlay } from '@deck.gl/mapbox';
import maplibregl from 'maplibre-gl';
import mapLibreCss from 'maplibre-gl/dist/maplibre-gl.css?inline';
import { PhenologyLayer } from './phenology-layer';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Texture } from '@luma.gl/core';

@customElement('foliage-map')
export class FoliageMap extends LitElement {
  static styles = [
    unsafeCSS(mapLibreCss),
    css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
      position: relative;
    }
    #map-container {
      width: 100%;
      height: 100%;
    }
    canvas {
        display: block;
    }
    .maplibregl-map {
      height: 100%;
      width: 100%;
    }
    .debug-toggle {
      position: absolute;
      top: 0.75rem;
      left: 0.75rem;
      z-index: 40;
      pointer-events: auto;
    }
    .debug-toggle button {
      background: rgba(0,0,0,0.6);
      color: white;
      border: none;
      padding: 0.4rem 0.6rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9rem;
    }
    .debug-toggle button:focus { outline: 2px solid rgba(255,255,255,0.2); }
  `];

  private deck: MapboxOverlay | null = null;
  private map: maplibregl.Map | null = null;
  private atlasTexture: Texture | null = null;
  private atlasMapping: Record<string, number> = {};
  @property({ type: Boolean })
  showDebug = false;

  private phenologyLayer: any | null = null;
  private debugLayer: any | null = null;

  // Keep accessor identity stable between renders to avoid unnecessary churn
  private speciesIndexAccessor = (d: any) => {
    const idx = this.atlasMapping[d.species];
    return idx !== undefined ? idx : this.atlasMapping['DEFAULT'] || 0;
  };

  @property({ type: Number })
  dayOfYear = 280; // Default to mid-Oct

  async firstUpdated() {
    const container = this.shadowRoot?.getElementById('map-container');
    if (container) {
      await this.loadMetadata();
      this.initMap(container as HTMLDivElement);
    }
  }

  async loadMetadata() {
    try {
        // Fetch Mapping
        const metaRes = await fetch('./api/metadata');
        const meta = await metaRes.json();
        this.atlasMapping = meta.atlas_mapping || {};
    } catch(e) {
        console.error("Failed to load metadata", e);
    }
  }

  initMap(container: HTMLDivElement) {
    this.map = new maplibregl.Map({
      container,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [-122.3321, 47.6062],
      zoom: 12,
      pitch: 0,
      bearing: 0
    });

    this.deck = new MapboxOverlay({
      layers: [],
      onDeviceInitialized: (device) => {
          // Load Atlas Texture
          const image = new Image();
          image.crossOrigin = "Anonymous";
          image.onload = () => {
              this.atlasTexture = device.createTexture({
                  data: image,
                  width: image.width,
                  height: image.height,
                  sampler: {
                      minFilter: 'nearest',
                      magFilter: 'nearest',
                      addressModeU: 'clamp-to-edge',
                      addressModeV: 'clamp-to-edge'
                  }
              });
              this.updateLayers();
          };
          image.src = './api/phenology/atlas.png';
      } 
    });

    this.map.addControl(this.deck);

    // Initial render attempt (will be empty layers until texture loads)
    this.updateLayers();
  }

  updated(changedProps: Map<string, any>) {
      if (changedProps.has('dayOfYear')) {
          this.updateLayers();
      }
  }

  updateLayers() {
      if (!this.deck || !this.atlasTexture) return;

      const atlasHeight = Object.keys(this.atlasMapping).length || 1;

      // Per deck.gl FAQ: create new layer instances each render (same id) so
      // deck.gl can diff and recycle GPU state efficiently. This avoids in-place
      // mutation of layer props and follows the reactive pattern used by deck.gl.

      // Create a new phenology layer instance (same id so deck.gl matches state)
      this.phenologyLayer = new PhenologyLayer({
        id: 'phenology-layer',
        data: './api/trees?limit=2000',
        getPosition: (d: any) => d.position,
        getSpeciesIndex: this.speciesIndexAccessor,
        uAtlas: this.atlasTexture,
        uAtlasHeight: atlasHeight,
        uTime: this.dayOfYear,

        getRadius: 8,
        radiusMinPixels: 2,
        pickable: true,
        // Ensure attributes depending on atlasMapping are updated when mapping changes
        updateTriggers: {
          getSpeciesIndex: [this.atlasMapping]
        }
      });

      // Create a new debug layer instance (same id retained)
      this.debugLayer = new ScatterplotLayer({
        id: 'debug-locations',
        data: './api/trees?limit=2000',
        getPosition: (d: any) => d.position,
        getFillColor: [0, 0, 255, 180],
        getRadius: 6,
        radiusMinPixels: 2,
        pickable: false,
        visible: this.showDebug
      });

      // Pass fresh layer descriptors to deck; deck.gl will diff and reuse GPU state
      this.deck.setProps({ layers: [this.phenologyLayer, this.debugLayer] });
  }

  render() {
    return html`
      <div id="map-container"></div>
      <div class="debug-toggle">
        <button @click=${() => this.toggleDebug()}>Debug: ${this.showDebug ? 'On' : 'Off'}</button>
      </div>
    `;
  }

  toggleDebug() {
    this.showDebug = !this.showDebug;
    // Recreate layers to follow deck.gl reactive pattern
    this.updateLayers();
  }
}
