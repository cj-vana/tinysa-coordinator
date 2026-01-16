import { test as base, expect, Page, Locator } from '@playwright/test';

/**
 * Base page object class providing common functionality
 * for all page objects in the test suite.
 */
export class BasePage {
  readonly page: Page;
  readonly navigation: Locator;

  constructor(page: Page) {
    this.page = page;
    this.navigation = page.locator('nav');
  }

  /**
   * Navigate to a specific route
   */
  async goto(path: string = '/') {
    await this.page.goto(path);
  }

  /**
   * Wait for the page to be fully loaded
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get the navigation link by text
   */
  getNavLink(text: string): Locator {
    return this.navigation.getByRole('link', { name: text });
  }

  /**
   * Navigate using the nav bar
   */
  async navigateTo(linkText: string) {
    await this.getNavLink(linkText).click();
  }

  /**
   * Get the page title from the header
   */
  async getPageTitle(): Promise<string> {
    const title = await this.page.locator('h1, h2').first().textContent();
    return title || '';
  }

  /**
   * Wait for API response
   */
  async waitForApiResponse(urlPattern: string | RegExp) {
    return this.page.waitForResponse(urlPattern);
  }

  /**
   * Check if an element is visible
   */
  async isVisible(selector: string): Promise<boolean> {
    return this.page.locator(selector).isVisible();
  }
}

/**
 * Scan page object for interacting with the main scan functionality
 */
export class ScanPage extends BasePage {
  readonly scanControls: Locator;
  readonly frequencyChart: Locator;
  readonly startButton: Locator;
  readonly stopButton: Locator;
  readonly progressIndicator: Locator;

  constructor(page: Page) {
    super(page);
    this.scanControls = page.locator('[data-testid="scan-controls"]');
    this.frequencyChart = page.locator('[data-testid="frequency-chart"]');
    this.startButton = page.getByRole('button', { name: /start/i });
    this.stopButton = page.getByRole('button', { name: /stop/i });
    this.progressIndicator = page.locator('[data-testid="scan-progress"]');
  }

  async goto() {
    await super.goto('/');
  }

  /**
   * Start a frequency scan
   */
  async startScan() {
    await this.startButton.click();
  }

  /**
   * Stop a running scan
   */
  async stopScan() {
    await this.stopButton.click();
  }

  /**
   * Check if a scan is in progress
   */
  async isScanRunning(): Promise<boolean> {
    return this.stopButton.isVisible();
  }

  /**
   * Get the current progress percentage
   */
  async getProgress(): Promise<string> {
    const progressText = await this.progressIndicator.textContent();
    return progressText || '0%';
  }

  /**
   * Wait for scan to complete
   */
  async waitForScanComplete(timeout: number = 60000) {
    await expect(this.startButton).toBeVisible({ timeout });
  }
}

/**
 * History page object for interacting with scan history
 */
export class HistoryPage extends BasePage {
  readonly scanList: Locator;
  readonly exportButton: Locator;
  readonly deleteButton: Locator;

  constructor(page: Page) {
    super(page);
    this.scanList = page.locator('[data-testid="scan-list"]');
    this.exportButton = page.getByRole('button', { name: /export/i });
    this.deleteButton = page.getByRole('button', { name: /delete/i });
  }

  async goto() {
    await super.goto('/history');
  }

  /**
   * Get the number of scan entries in the list
   */
  async getScanCount(): Promise<number> {
    const items = this.scanList.locator('[data-testid="scan-item"]');
    return items.count();
  }

  /**
   * Select a scan by index
   */
  async selectScan(index: number) {
    const items = this.scanList.locator('[data-testid="scan-item"]');
    await items.nth(index).click();
  }
}

/**
 * Settings page object for app configuration
 */
export class SettingsPage extends BasePage {
  readonly deviceSelect: Locator;
  readonly connectButton: Locator;
  readonly deviceStatus: Locator;

  constructor(page: Page) {
    super(page);
    this.deviceSelect = page.locator('[data-testid="device-select"]');
    this.connectButton = page.getByRole('button', { name: /connect/i });
    this.deviceStatus = page.locator('[data-testid="device-status"]');
  }

  async goto() {
    await super.goto('/settings');
  }

  /**
   * Check if device is connected
   */
  async isDeviceConnected(): Promise<boolean> {
    const status = await this.deviceStatus.textContent();
    return status?.toLowerCase().includes('connected') || false;
  }
}

/**
 * Custom test fixture extending the base Playwright test
 * with pre-instantiated page objects
 */
type PageObjects = {
  scanPage: ScanPage;
  historyPage: HistoryPage;
  settingsPage: SettingsPage;
};

export const test = base.extend<PageObjects>({
  scanPage: async ({ page }, use) => {
    const scanPage = new ScanPage(page);
    await use(scanPage);
  },
  historyPage: async ({ page }, use) => {
    const historyPage = new HistoryPage(page);
    await use(historyPage);
  },
  settingsPage: async ({ page }, use) => {
    const settingsPage = new SettingsPage(page);
    await use(settingsPage);
  },
});

export { expect } from '@playwright/test';
