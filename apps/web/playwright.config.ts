import { defineConfig, devices } from '@playwright/test';

// Playwright's automatic error-context DOM snapshot can contain enrollment/recovery secrets.
// Keep assertions and failure output, but never attach authentication page snapshots.
process.env.PLAYWRIGHT_NO_COPY_PROMPT = '1';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    trace: 'off',
    screenshot: 'off',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
  webServer:
    process.env.E2E_EXTERNAL_SERVERS === '1'
      ? undefined
      : [
          {
            command:
              '../../.venv/bin/python -m uvicorn apps.api.main:create_app --factory --app-dir ../.. --host 127.0.0.1 --port 18000 --no-access-log',
            url: 'http://127.0.0.1:18000/health/live',
            reuseExistingServer: false,
          },
          { command: 'npm run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: false },
        ],
});
