import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import '@shoelace-style/shoelace/dist/themes/light.css';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';

@customElement('app-root')
export class AppRoot extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
      font-family: var(--sl-font-sans);
    }
    header {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      z-index: 10;
      padding: 1rem;
      pointer-events: none;
    }
    h1 {
      margin: 0;
      color: white;
      text-shadow: 0 1px 3px rgba(0,0,0,0.8);
      pointer-events: auto;
    }
    main {
      height: 100%;
      width: 100%;
    }
  `;

  // State for bridging sibling components
  // In a larger app, use a store or context.
  // Here we assume app-root orchestrates.

  handleDateChange(e: CustomEvent) {
      const map = this.querySelector('foliage-map') as any;
      if (map) {
          map.dayOfYear = e.detail.dayOfYear;
      }
  }

  render() {
    return html`
      <header>
        <h1>Seattle Foliage Map</h1>
      </header>
      <main>
         <!-- Hardcoded orchestration for prototype -->
         <foliage-map id="map"></foliage-map>
         <timeline-slider
            dayOfYear="280"
            @date-change=${this.handleDateChange}
         ></timeline-slider>
      </main>
    `;
  }
}
