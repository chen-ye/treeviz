import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import '@shoelace-style/shoelace/dist/components/range/range.js';

@customElement('timeline-slider')
export class TimelineSlider extends LitElement {
  static styles = css`
    :host {
      display: block;
      position: absolute;
      bottom: 2rem;
      left: 50%;
      transform: translateX(-50%);
      width: 90%;
      max-width: 600px;
      z-index: 100;
      background: rgba(255, 255, 255, 0.9);
      padding: 1rem;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .date-display {
        text-align: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #333;
    }
    sl-range {
        width: 100%;
    }
  `;

  @property({ type: Number })
  dayOfYear = 1;

  @property({ type: Number })
  year = 2024;

  private get formattedDate() {
      const date = new Date(this.year, 0); // Jan 1st
      date.setDate(this.dayOfYear);
      return date.toLocaleDateString(undefined, { month: 'long', day: 'numeric' });
  }

  handleInput(e: Event) {
      const target = e.target as HTMLInputElement;
      this.dayOfYear = parseInt(target.value, 10);

      this.dispatchEvent(new CustomEvent('date-change', {
          detail: { dayOfYear: this.dayOfYear },
          bubbles: true,
          composed: true
      }));
  }

  render() {
    return html`
      <div class="date-display">${this.formattedDate}</div>
      <sl-range
        min="1"
        max="365"
        .value=${this.dayOfYear}
        @sl-input=${this.handleInput}
      ></sl-range>
    `;
  }
}
