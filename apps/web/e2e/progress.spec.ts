import { expect, test } from "@playwright/test";
import { expectClipPlaying, swipeToNext } from "./helpers";

test("a Detoks feed shows how far through today's videos the viewer is", async ({ page }) => {
  await page.goto("/feed?user=george&ranker=detoks&size=3");
  const progress = page.getByRole("progressbar", { name: "Today's feed" });

  await expectClipPlaying(page);
  await expect(progress).toHaveAttribute("aria-valuetext", "1 of 3");

  await swipeToNext(page);
  await expect(progress).toHaveAttribute("aria-valuetext", "2 of 3");
});

test("the endless Baseline feed shows no daily progress", async ({ page }) => {
  await page.goto("/feed?user=george&ranker=baseline");
  await expectClipPlaying(page);
  await expect(page.getByRole("progressbar", { name: "Today's feed" })).toHaveCount(0);
});
