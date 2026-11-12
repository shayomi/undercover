import { defineConfig } from "@playwright/test";

// The end-to-end run has its own backend, dashboard and freshly seeded
// database, on ports apart from `npm run dev`, so it never touches dev data.
const env = {
  UNDERCOVER_DB: "backend/e2e.db",
  UNDERCOVER_BACKEND_URL: "http://localhost:8001",
  BACKEND_PORT: "8001",
};

export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  use: { baseURL: "http://localhost:5174" },
  webServer: [
    {
      command:
        "uv run -m backend.seed && uv run -m uvicorn backend.main:app --port 8001",
      url: "http://127.0.0.1:8001/api/health",
      reuseExistingServer: false,
      env,
    },
    {
      command: "npx vite dashboard --port 5174 --strictPort",
      url: "http://localhost:5174",
      reuseExistingServer: false,
      env,
    },
  ],
});
