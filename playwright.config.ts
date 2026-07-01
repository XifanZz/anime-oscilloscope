import { defineConfig, devices } from "@playwright/test";

const apiCommand = process.env.E2E_API_COMMAND ?? (
  process.platform === "win32"
    ? ".venv\\Scripts\\python.exe -m uvicorn anime_oscilloscope.main:app --app-dir apps/api/src --host 127.0.0.1 --port 8000"
    : "python -m uvicorn anime_oscilloscope.main:app --app-dir apps/api/src --host 127.0.0.1 --port 8000"
);
const webCommand = "node node_modules/vite/bin/vite.js apps/web --host 127.0.0.1 --port 5173";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: [
    {
      command: apiCommand,
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: webCommand,
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
