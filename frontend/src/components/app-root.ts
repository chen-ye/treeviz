import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import { SignalWatcher } from '@lit-labs/signals';
import '@shoelace-style/shoelace/dist/themes/light.css';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import { dayOfYearSignal } from '../store';

@customElement('app-root')
export class AppRoot extends SignalWatcher(LitElement) {
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

  render() {
    // Access signal value to create dependency for reactivity
    dayOfYearSignal.get();

    return html`
      <header>
        <h1>Seattle Foliage Map</h1>
      </header>
      <main>
         <!-- Components now use shared signals store -->
         <foliage-map id="map"></foliage-map>
         <timeline-slider></timeline-slider>
      </main>
    `;
  }
}
