import { signal } from '@lit-labs/signals';

/**
 * Shared application state using TC39 signals via lit-labs/signals
 * This provides reactive state management across all components
 */

// Day of year for phenology visualization (1-365)
export const dayOfYearSignal = signal(280); // Default to mid-October

// Debug mode toggle
export const showDebugSignal = signal(false);

// Year for date calculations
export const yearSignal = signal(2024);
