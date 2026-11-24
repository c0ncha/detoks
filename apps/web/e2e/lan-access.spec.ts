import { test } from "@playwright/test";
import os from "node:os";
import { expectClipPlaying } from "./helpers";
import { WEB_PORT } from "./ports";

function lanAddress(): string | undefined {
  return Object.values(os.networkInterfaces()).flat()
    .find((a) => a && a.family === "IPv4" && !a.internal)?.address;
}

test("the app works when opened from another device on the network", async ({ page }) => {
  const ip = lanAddress();
  test.skip(!ip, "this machine has no LAN IPv4 address");

  // From a phone, "localhost" is the phone itself, so nothing on this computer is reachable that way.
  await page.route(/^https?:\/\/(localhost|127\.0\.0\.1)[:/]/, (route) => route.abort());

  await page.goto(`http://${ip}:${WEB_PORT}/`);
  await page.getByText("George", { exact: true }).click();
  await page.getByRole("link", { name: "Detoks feed" }).click();
  await expectClipPlaying(page);
});
