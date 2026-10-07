import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testMatch: "*e2e.spec.ts",
  timeout: 120000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
    viewport: { width: 1600, height: 1000 },
  },
  reporter: "list",
});
