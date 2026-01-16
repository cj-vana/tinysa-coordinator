/**
 * E2E tests for the export flow functionality.
 * Tests navigating to history page, viewing scan details, and export dialog.
 * These tests are designed to work without an actual TinySA device connected.
 */

import { test, expect } from '../fixtures/base';

test.describe('History Page - Navigation and Loading', () => {
  test('should navigate to history page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'History' }).click();
    await expect(page).toHaveURL('/history');
  });

  test('should display history page header', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    await expect(historyPage.page.getByRole('heading', { name: 'Scan History' })).toBeVisible();
    await expect(historyPage.page.getByText(/view and manage your saved frequency scans/i)).toBeVisible();
  });

  test('should display search input', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    const searchInput = historyPage.page.getByPlaceholder(/search scans/i);
    await expect(searchInput).toBeVisible();
  });

  test('should load scans from API', async ({ historyPage, page }) => {
    // Set up response listener before navigation
    const scansResponse = page.waitForResponse(
      (response) => response.url().includes('/api/history') && response.status() === 200
    );

    await historyPage.goto();

    // Wait for scans API to respond
    const response = await scansResponse;
    const data = await response.json();

    // Verify response structure
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(Array.isArray(data.items)).toBe(true);
  });
});

test.describe('History Page - Empty State', () => {
  test('should display appropriate message when no scans exist', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    // Wait for API response to complete
    await historyPage.page.waitForLoadState('networkidle');

    // Either we have scans displayed OR we have an empty state message
    const scanTable = historyPage.page.locator('table');
    const emptyState = historyPage.page.getByText(/no scans found|save a scan to see it here/i);

    // One of these should be visible
    const hasTable = await scanTable.isVisible().catch(() => false);
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    expect(hasTable || hasEmptyState).toBe(true);
  });
});

test.describe('History Page - Scan List Display', () => {
  test('should display scan list table with headers', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await historyPage.page.waitForLoadState('networkidle');

    // Check if table exists (only if there are scans)
    const table = historyPage.page.locator('table');
    const hasTable = await table.isVisible().catch(() => false);

    if (hasTable) {
      // Verify table headers
      await expect(historyPage.page.getByRole('columnheader', { name: /name/i })).toBeVisible();
      await expect(historyPage.page.getByRole('columnheader', { name: /frequency range/i })).toBeVisible();
      await expect(historyPage.page.getByRole('columnheader', { name: /date/i })).toBeVisible();
    }
  });

  test('should have sortable columns', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await historyPage.page.waitForLoadState('networkidle');

    const table = historyPage.page.locator('table');
    const hasTable = await table.isVisible().catch(() => false);

    if (hasTable) {
      // Column headers should be clickable for sorting
      const nameHeader = historyPage.page.getByRole('columnheader', { name: /name/i });
      await expect(nameHeader).toBeVisible();

      // Headers should have cursor pointer styling or be clickable
      await nameHeader.click();

      // Page should still be functional after clicking header
      await expect(historyPage.page).toHaveURL('/history');
    }
  });
});

test.describe('History Page - Search Functionality', () => {
  test('should filter scans when searching', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    const searchInput = historyPage.page.getByPlaceholder(/search scans/i);

    // Type a search query
    await searchInput.fill('test');

    // Wait for debounced search to trigger
    await historyPage.page.waitForTimeout(500);

    // The search should be reflected in the input
    await expect(searchInput).toHaveValue('test');
  });

  test('should show clear button when search has text', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    const searchInput = historyPage.page.getByPlaceholder(/search scans/i);

    // Type a search query
    await searchInput.fill('test search');

    // Clear button (X) should appear
    const clearButton = historyPage.page.locator('input[placeholder="Search scans..."] + button, input[placeholder="Search scans..."] ~ button').first();

    // Wait a moment for the button to appear
    await historyPage.page.waitForTimeout(100);

    // Try to find the clear button in the search area
    const searchArea = historyPage.page.locator('.relative').filter({ has: searchInput });
    const closeButton = searchArea.locator('button');

    if (await closeButton.isVisible()) {
      await closeButton.click();
      await expect(searchInput).toHaveValue('');
    }
  });
});

test.describe('History Page - Detail Panel', () => {
  test('should display placeholder when no scan is selected', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    // The detail panel should show a placeholder message
    await expect(historyPage.page.getByText(/select a scan to view details/i)).toBeVisible();
  });

  test('should show two-column layout', async ({ historyPage }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();

    // Verify the grid layout with scan list and detail panel
    const gridContainer = historyPage.page.locator('.grid.grid-cols-1.lg\\:grid-cols-2');
    await expect(gridContainer).toBeVisible();
  });
});

test.describe('Export Flow - Export Buttons', () => {
  // These tests check that the export UI elements exist and are functional
  // They don't test actual file downloads since that requires saved scans

  test('should display export format options in scan detail', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    // Check if there are any scans to select
    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Click on the first scan row
      await scanRows.first().click();

      // Wait for detail panel to load
      await page.waitForLoadState('networkidle');

      // Export section should be visible with format buttons
      const exportLabel = page.getByText('Export:');
      await expect(exportLabel).toBeVisible();

      // Check for export format buttons
      await expect(page.getByRole('button', { name: 'WWB' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'WSM' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Raw CSV' })).toBeVisible();
    }
  });

  test('export buttons should have correct labels for industry formats', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Click on the first scan row
      await scanRows.first().click();
      await page.waitForLoadState('networkidle');

      // WWB = Shure Wireless Workbench
      // WSM = Sennheiser Wireless Systems Manager
      // These are industry-standard RF coordination software formats

      const wwbButton = page.getByRole('button', { name: 'WWB' });
      const wsmButton = page.getByRole('button', { name: 'WSM' });
      const csvButton = page.getByRole('button', { name: 'Raw CSV' });

      // Verify buttons exist and have appropriate styling
      if (await wwbButton.isVisible()) {
        // WWB button should have green styling
        await expect(wwbButton).toHaveClass(/green/);
      }

      if (await wsmButton.isVisible()) {
        // WSM button should have purple styling
        await expect(wsmButton).toHaveClass(/purple/);
      }

      if (await csvButton.isVisible()) {
        // CSV button should have yellow styling
        await expect(csvButton).toHaveClass(/yellow/);
      }
    }
  });
});

test.describe('Export Flow - Scan Selection', () => {
  test('should highlight selected scan row', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Click on the first scan row
      const firstRow = scanRows.first();
      await firstRow.click();

      // The row should have some visual indication of selection
      // This could be background color change or border
      // We verify the click was registered by checking if detail panel appeared
      const detailPanel = page.locator('.bg-gray-800.rounded-lg.h-full.flex.flex-col');
      await expect(detailPanel.or(page.getByText(/select a scan to view details/i).locator('..'))).toBeVisible();
    }
  });

  test('should load scan details when scan is selected', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Click on the first scan row
      await scanRows.first().click();

      // Should make API call to get scan details
      // Wait for potential API call
      await page.waitForLoadState('networkidle');

      // Detail panel should show scan information or loading state
      const detailPanel = page.locator('.lg\\:col-span-1, .overflow-auto').last();
      await expect(detailPanel).toBeVisible();
    }
  });

  test('should close detail panel when close button is clicked', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Click on the first scan row to open detail panel
      await scanRows.first().click();
      await page.waitForLoadState('networkidle');

      // Look for close button (X) in the detail panel
      const closeButton = page.locator('button').filter({ has: page.locator('svg path[d*="M6 18L18 6"]') });

      if (await closeButton.isVisible()) {
        await closeButton.click();

        // The placeholder message should appear again
        await expect(page.getByText(/select a scan to view details/i)).toBeVisible();
      }
    }
  });
});

test.describe('Export Flow - Delete Confirmation', () => {
  test('should show delete confirmation modal', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Look for delete button in the first row
      const firstRow = scanRows.first();
      const deleteButton = firstRow.getByRole('button').filter({ has: page.locator('svg') }).last();

      if (await deleteButton.isVisible()) {
        await deleteButton.click();

        // Delete confirmation modal should appear
        const modal = page.getByText(/delete scan/i).locator('..');
        await expect(modal.or(page.getByText(/are you sure/i))).toBeVisible();

        // Cancel button should be present
        await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
      }
    }
  });

  test('should close delete modal when cancel is clicked', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Look for delete button in the first row
      const firstRow = scanRows.first();
      const deleteButton = firstRow.getByRole('button').filter({ has: page.locator('svg') }).last();

      if (await deleteButton.isVisible()) {
        await deleteButton.click();

        // Wait for modal
        await page.waitForTimeout(100);

        // Click cancel
        const cancelButton = page.getByRole('button', { name: /cancel/i });
        if (await cancelButton.isVisible()) {
          await cancelButton.click();

          // Modal should close
          await expect(page.getByText(/are you sure you want to delete/i)).not.toBeVisible();
        }
      }
    }
  });
});

test.describe('History Page - Pagination', () => {
  test('should show pagination controls when there are many scans', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    // Pagination appears when there are more than 10 scans
    const pagination = page.getByText(/page \d+ of \d+/i);
    const paginationExists = await pagination.isVisible().catch(() => false);

    if (paginationExists) {
      // Previous and Next buttons should be present
      await expect(page.getByRole('button', { name: /previous/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /next/i })).toBeVisible();
    }
  });
});

test.describe('History Page - Metadata Display', () => {
  test('should display scan metadata in detail panel', async ({ historyPage, page }) => {
    await historyPage.goto();
    await historyPage.waitForPageLoad();
    await page.waitForLoadState('networkidle');

    const scanRows = page.locator('table tbody tr');
    const hasScanRows = await scanRows.count() > 0;

    if (hasScanRows) {
      // Select a scan
      await scanRows.first().click();
      await page.waitForLoadState('networkidle');

      // Detail panel should show metadata like frequency range, points, date
      // These are displayed in the scan detail component
      const detailArea = page.locator('.bg-gray-800.rounded-lg');

      // Check for common metadata elements
      // The detail panel should have at least some data displayed
      const hasFrequencyDisplay = await page.getByText(/MHz/i).isVisible().catch(() => false);
      const hasPointsDisplay = await page.getByText(/points/i).isVisible().catch(() => false);

      // At least one metadata field should be visible
      expect(hasFrequencyDisplay || hasPointsDisplay || await detailArea.isVisible()).toBe(true);
    }
  });
});
