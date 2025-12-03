import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import { SignalWatcher } from '@lit-labs/signals';
import '@shoelace-style/shoelace/dist/components/range/range.js';
import { dayOfYearSignal, yearSignal } from '../store';

@customElement('timeline-slider')
export class TimelineSlider extends SignalWatcher(LitElement) {
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

  private get formattedDate() {
      const date = new Date(yearSignal.get(), 0); // Jan 1st
      date.setDate(dayOfYearSignal.get());
      return date.toLocaleDateString(undefined, { month: 'long', day: 'numeric' });
  }

  handleInput(e: Event) {
      const target = e.target as HTMLInputElement;
      dayOfYearSignal.set(parseInt(target.value, 10));
  }

  render() {
    return html`
      <div class="date-display">${this.formattedDate}</div>
      <sl-range
        min="1"
        max="365"
        .value=${dayOfYearSignal.get()}
        @sl-input=${this.handleInput}
      ></sl-range>
    `;
  }
}
