import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import '../src/components/timeline-slider';
import { TimelineSlider } from '../src/components/timeline-slider';

describe('TimelineSlider', () => {
  let element: TimelineSlider;

  beforeEach(async () => {
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

  it('updates date display when dayOfYear changes', async () => {
    element.dayOfYear = 32; // Feb 1st
    await element.updateComplete;
    const display = element.shadowRoot?.querySelector('.date-display');
    expect(display?.textContent).toContain('February');
  });

  it('emits date-change event on input', async () => {
    const range = element.shadowRoot?.querySelector('sl-range') as any;
    expect(range).toBeTruthy();

    const spy = vi.fn();
    element.addEventListener('date-change', spy);

    // Simulate input event by calling handler directly since sl-range behavior
    // is hard to mock perfectly in happy-dom
    const mockEvent = {
        target: { value: '50' }
    } as unknown as Event;

    (element as any).handleInput(mockEvent);

    expect(spy).toHaveBeenCalled();
    expect(spy.mock.calls[0][0].detail.dayOfYear).toBe(50);
  });
});
