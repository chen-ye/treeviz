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
      this.initDeck(container as HTMLElement);
    }
  }

  async loadMetadata() {
    try {
        // Fetch Mapping
        const metaRes = await fetch('http://localhost:8000/api/metadata');
        const meta = await metaRes.json();
        this.atlasMapping = meta.atlas_mapping || {};
    } catch(e) {
        console.error("Failed to load metadata", e);
    }
  }

  initDeck(container: HTMLElement) {
    this.deck = new Deck({
      parent: container as any,
      initialViewState: {
        longitude: -122.3321,
        latitude: 47.6062,
        zoom: 12,
        pitch: 0,
        bearing: 0
      },
      controller: true,
      onWebGLInitialized: (gl) => {
          // Load Atlas Texture
          const image = new Image();
          image.crossOrigin = "Anonymous";
          image.onload = () => {
              // @ts-ignore
              this.atlasTexture = new Texture(gl, {
                  data: image,
                  parameters: {
                      // @ts-ignore
                      [gl.TEXTURE_MIN_FILTER]: gl.NEAREST,
                      // @ts-ignore
                      [gl.TEXTURE_MAG_FILTER]: gl.NEAREST,
                      // @ts-ignore
                      [gl.TEXTURE_WRAP_S]: gl.CLAMP_TO_EDGE,
                      // @ts-ignore
                      [gl.TEXTURE_WRAP_T]: gl.CLAMP_TO_EDGE
                  }
              });
              this.updateLayers();
          };
          image.src = 'http://localhost:8000/api/phenology/atlas.png';
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
          data: 'http://localhost:8000/api/trees?limit=2000',
          getPosition: (d: any) => d.position,
          // @ts-ignore
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
