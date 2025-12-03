import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { Deck } from '@deck.gl/core';
import { PhenologyLayer } from './phenology-layer';
import { Texture } from '@luma.gl/core';

@customElement('foliage-map')
export class FoliageMap extends LitElement {
  static styles = css`
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
  `;

  private deck: Deck | null = null;
  private atlasTexture: Texture | null = null;
  private atlasMapping: Record<string, number> = {};

  @property({ type: Number })
  dayOfYear = 280; // Default to mid-Oct

  async firstUpdated() {
    const container = this.shadowRoot?.getElementById('map-container');
    if (container) {
      await this.loadMetadata();
      this.initDeck(container as HTMLDivElement);
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

  initDeck(container: HTMLDivElement) {
    this.deck = new Deck({
      parent: container,
      initialViewState: {
        longitude: -122.3321,
        latitude: 47.6062,
        zoom: 12,
        pitch: 0,
        bearing: 0
      },
      controller: true,
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
      },
      layers: []
    });

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

      const layer = new PhenologyLayer({
          id: 'phenology-layer',
          data: './api/trees?limit=2000',
          getPosition: (d: any) => d.position,
          getSpeciesIndex: (d: any) => {
              const idx = this.atlasMapping[d.species];
              return idx !== undefined ? idx : this.atlasMapping['DEFAULT'] || 0;
          },
          uAtlas: this.atlasTexture,
          uAtlasHeight: Object.keys(this.atlasMapping).length || 1,
          uTime: this.dayOfYear,

          getRadius: 8,
          radiusMinPixels: 2,
          pickable: true,
          // Force update when time changes
          updateTriggers: {
              getSpeciesIndex: [this.atlasMapping]
          }
      });

      this.deck.setProps({ layers: [layer] });
  }

  render() {
    return html`<div id="map-container"></div>`;
  }
}
