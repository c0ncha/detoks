import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import path from "node:path";
import { RANKER_PORT, WEB_PORT } from "./e2e/ports";

// E2E runs the real ranker API (on a synthetic fixture dataset) and the real Next dev server.

const repo = path.resolve(__dirname, "../..");
const venvPython = path.join(repo, ".venv/bin/python");
const python = process.env.PYTHON ?? (existsSync(venvPython) ? venvPython : "python3");
const fixture = path.join(__dirname, "e2e/.fixture");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
    ...devices["Pixel 7"],
  },
  webServer: [
    {
      command: `"${python}" e2e/fixture/make_fixture.py "${fixture}" && cd ../../services/ranker && "${python}" -m uvicorn detoks.api:app --port ${RANKER_PORT}`,
      url: `http://localhost:${RANKER_PORT}/health`,
      env: {
        DETOKS_DATA_DIR: path.join(fixture, "data"),
        DETOKS_CLIP_DIR: path.join(fixture, "clips"),
        DETOKS_CORS_ORIGINS: `http://localhost:${WEB_PORT}`,
      },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `npx next dev -p ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}`,
      env: { NEXT_DIST_DIR: ".next-e2e", NEXT_PUBLIC_RANKER_URL: `http://localhost:${RANKER_PORT}` },
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
