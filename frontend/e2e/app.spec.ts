import { test, expect } from '@playwright/test';

test('App loads and title is correct', async ({ page }) => {
  // We assume the app is running on localhost:5173 (default Vite port)
  // or we need to start it.
  // For now, let's assume we can visit the root.
  await page.goto('/');

  // Check title in header
  const header = page.locator('header h1');
  await expect(header).toHaveText('Seattle Foliage Map');
});

test('Map container exists', async ({ page }) => {
  await page.goto('/');
  const map = page.locator('foliage-map');
  await expect(map).toBeVisible();
});

test('Timeline slider interactions', async ({ page }) => {
  await page.goto('/');
  const slider = page.locator('timeline-slider');
  await expect(slider).toBeVisible();

  // Interact with slider (if shadow DOM allows or via JS)
  // Playwright handles shadow DOM automatically usually.

  // Check initial date display
  const display = slider.locator('.date-display');
  // Default is day 280 -> Oct 7 (leap year 2024)
  await expect(display).toContainText('October');
});
