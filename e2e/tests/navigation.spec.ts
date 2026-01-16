import { test, expect } from '../fixtures/base';

test.describe('Navigation', () => {
  test('should display the app header with correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Frequency Scanner')).toBeVisible();
  });

  test('should navigate to Scan page by default', async ({ page }) => {
    await page.goto('/');
    const scanLink = page.getByRole('link', { name: 'Scan' });
    await expect(scanLink).toHaveClass(/bg-blue-600/);
  });

  test('should navigate to History page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'History' }).click();
    await expect(page).toHaveURL('/history');
    const historyLink = page.getByRole('link', { name: 'History' });
    await expect(historyLink).toHaveClass(/bg-blue-600/);
  });

  test('should navigate to Settings page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL('/settings');
    const settingsLink = page.getByRole('link', { name: 'Settings' });
    await expect(settingsLink).toHaveClass(/bg-blue-600/);
  });

  test('should navigate back to Scan page from other pages', async ({ page }) => {
    await page.goto('/history');
    await page.getByRole('link', { name: 'Scan' }).click();
    await expect(page).toHaveURL('/');
  });
});

test.describe('Scan Page', () => {
  test('should display scan controls', async ({ scanPage }) => {
    await scanPage.goto();
    await expect(scanPage.startButton).toBeVisible();
  });

  test('should have navigation links visible', async ({ scanPage }) => {
    await scanPage.goto();
    await expect(scanPage.getNavLink('Scan')).toBeVisible();
    await expect(scanPage.getNavLink('History')).toBeVisible();
    await expect(scanPage.getNavLink('Settings')).toBeVisible();
  });
});

test.describe('History Page', () => {
  test('should load history page successfully', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await expect(historyPage.page).toHaveURL('/history');
  });
});

test.describe('Settings Page', () => {
  test('should load settings page successfully', async ({ settingsPage }) => {
    await settingsPage.goto();
    await settingsPage.waitForPageLoad();
    await expect(settingsPage.page).toHaveURL('/settings');
  });
});
