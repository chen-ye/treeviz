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

    // Mock value property on the sl-range element
    // sl-range properties might be reactive, so careful
    // But for test in happy-dom, it might just be an HTMLElement

    // We can simulate the event structure that handleInput expects
    // handleInput(e: Event) { const target = e.target as HTMLInputElement; ... }

    // We can create a fake event with a fake target
    const fakeEvent = {
        target: { value: '50' }
    };

    // Call handleInput directly? Access private method?
    // Or dispatch event from an element that has value.

    // Let's try to mock the value property on range element before dispatching.
    // However, Lit might be controlling it.

    // The previous error "Cannot assign to read only property 'value'" suggests conflict.

    // Let's try calling the handler directly if we can't easily simulate the custom element behavior in happy-dom without full implementation.
    // But `handleInput` is public method on class usually if not private.
    // It is `handleInput(e: Event)` in class.

    // Let's try modifying the range element to have value.
    // Using Object.defineProperty was what caused the error maybe?
    // "Cannot assign to read only property 'value' of object '[object Object]'" happened in Lit update cycle, likely because I messed with the property descriptor?

    // Let's try to just dispatch an event that looks like sl-input but we can't easily fake 'target.value' unless target is the element dispatching it.

    // Alternative: mocking the range element? No, it's rendered by Lit.

    // Let's try to set the value attribute.
    range.setAttribute('value', '50');
    // And dispatch event.
    // But handleInput reads `target.value`. HTMLInputElement.value reads attribute if not dirty?
    // sl-range is not HTMLInputElement.

    // Let's try invoking the handler directly by finding it bound in the template?
    // No, that's hard.

    // Best way: invoke the method on the component instance if we can trigger it.
    // But we want to test that the component handles the event.

    // Let's just create a mock event object and call handleInput manually.
    // We need to cast element to any to access handleInput.

    const mockEvent = {
        target: { value: '50' }
    } as unknown as Event;

    (element as any).handleInput(mockEvent);

    expect(spy).toHaveBeenCalled();
    expect(spy.mock.calls[0][0].detail.dayOfYear).toBe(50);
  });
});
