import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import '../src/components/timeline-slider';
import { TimelineSlider } from '../src/components/timeline-slider';
import { dayOfYearSignal, yearSignal } from '../src/store';

describe('TimelineSlider', () => {
  let element: TimelineSlider;

  beforeEach(async () => {
    // Reset signals to default state
    dayOfYearSignal.set(280);
    yearSignal.set(2024);

    element = document.createElement('timeline-slider') as TimelineSlider;
    document.body.appendChild(element);
    await element.updateComplete;
  });

  afterEach(() => {
    document.body.removeChild(element);
  });

  it('renders correctly', () => {
    const display = element.shadowRoot?.querySelector('.date-display');
    expect(display).toBeTruthy();
  });

  it('updates date display when dayOfYear signal changes', async () => {
    dayOfYearSignal.set(32); // Feb 1st
    await element.updateComplete;
    const display = element.shadowRoot?.querySelector('.date-display');
    expect(display?.textContent).toContain('February');
  });

  it('updates dayOfYear signal on input', async () => {
    const range = element.shadowRoot?.querySelector('sl-range') as any;
    expect(range).toBeTruthy();

    // Simulate input event by calling handler directly since sl-range behavior
    // is hard to mock perfectly in happy-dom
    const mockEvent = {
        target: { value: '50' }
    } as unknown as Event;

    (element as any).handleInput(mockEvent);

    expect(dayOfYearSignal.get()).toBe(50);
  });
});
