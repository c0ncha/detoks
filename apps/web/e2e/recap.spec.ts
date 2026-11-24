import { expect, test } from "@playwright/test";
import { expectClipPlaying, swipeToNext } from "./helpers";

test("a finished Detoks feed ends with a recap of what the viewer watched and shared", async ({ page }) => {
  await page.goto("/feed?user=george&ranker=detoks&size=3");

  for (let clip = 0; clip < 3; clip++) {
    await expectClipPlaying(page, 1.2); // of 3 s: counts as watched, not skipped
    if (clip === 0) await page.getByRole("button", { name: "Send to a friend" }).first().click();
    await swipeToNext(page);
  }

  const recap = page.getByText("That's it for today").locator("..");
  await expect(recap).toBeVisible();
  await expect(recap).toContainText("3 videos · 1 shared");
});
